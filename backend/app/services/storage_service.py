"""
Ready2Go CRM — Enterprise Storage Service (v2)

The **only** module that communicates with Supabase Storage.

No business logic.
No database logic.
No applicant logic.

Every public method returns structured dicts with ``success`` and
either ``data`` or ``error`` keys.
"""

import io
import logging
import urllib.parse
import zipfile
from pathlib import Path
from typing import Any

import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.errors.document_errors import (
    DocumentError,
    object_not_found,
    signed_url_failed,
    storage_unavailable,
)

logger = logging.getLogger(__name__)

BUCKET = settings.SUPABASE_BUCKET
ORIGIN = settings.SUPABASE_URL
SERVICE_KEY = settings.SUPABASE_KEY
TIMEOUT = settings.UPLOAD_TIMEOUT_SECONDS
IS_PRODUCTION = settings.ENVIRONMENT == "production"
UPLOAD_DIR = Path(settings.UPLOAD_DIR)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _is_local() -> bool:
    """Return True when running in dev/test mode (no real Supabase)."""
    return not IS_PRODUCTION or not ORIGIN or not SERVICE_KEY or "dummy" in ORIGIN or "dummy" in SERVICE_KEY


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {SERVICE_KEY}"}


def _safe_local_path(storage_path: str) -> Path:
    """Resolve local path and guard against directory traversal."""
    resolved = (UPLOAD_DIR / storage_path).resolve()
    if not str(resolved).startswith(str(UPLOAD_DIR.resolve())):
        raise DocumentError("INVALID_STORAGE_PATH", "Directory traversal detected.", 400)
    return resolved


def _normalize(storage_path: str) -> str:
    """
    Normalise a storage path to canonical form:
        applicants/APP-000001/uuid.pdf

    Strips leading slash, bucket prefix, duplicate slashes,
    and converts Windows backslashes.
    """
    if not storage_path:
        return storage_path
    path = storage_path.strip().replace("\\", "/").lstrip("/")
    bucket_prefix = f"{BUCKET}/"
    if path.startswith(bucket_prefix):
        path = path[len(bucket_prefix):]
    path = path.lstrip("/")
    while "//" in path:
        path = path.replace("//", "/")
    return path.strip()


def _extract_signed_url(response: requests.Response) -> str | None:
    """Extract a signed URL string from any Supabase response format."""
    raw = response.text or ""
    if not raw.strip():
        return None
    try:
        data = response.json()
    except Exception:
        cleaned = raw.strip().strip('"').strip("'")
        return cleaned if (cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("/")) else None

    flat = {}

    def _flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _flatten(v, f"{prefix}{k}.")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _flatten(v, f"{prefix}{i}.")
        else:
            flat[prefix.rstrip(".")] = obj
    _flatten(data)

    for field in ["signedURL", "signedUrl", "signed_url", "url", "URL", "data"]:
        val = flat.get(field) or (data.get(field) if isinstance(data, dict) else None)
        if val and isinstance(val, str) and (val.startswith("http") or val.startswith("/")):
            return val
    for k, v in flat.items():
        if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://") or v.startswith("/")):
            if "token" in v or "sign" in v:
                return v
    return None


# ═══════════════════════════════════════════════════════════════════════
# 1. upload_file
# ═══════════════════════════════════════════════════════════════════════

def upload_file(file_data: bytes, storage_path: str, mime_type: str) -> dict:
    """
    Upload a file to Supabase Storage.

    Returns::

        {"success": True, "data": {"canonical_path": "applicants/APP-.../uuid.pdf"}}
        {"success": False, "error": "...", "status_code": 502}
    """
    storage_path = _normalize(storage_path)

    # ── Local fallback ────────────────────────────────────────────────
    if _is_local():
        local_path = _safe_local_path(storage_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        content = file_data.read() if hasattr(file_data, "read") else file_data
        with open(local_path, "wb") as f:
            f.write(content)
        logger.info("LOCAL UPLOAD: %s (%d bytes)", storage_path, len(content))
        return {"success": True, "data": {"canonical_path": storage_path}}

    # ── Supabase upload ───────────────────────────────────────────────
    url = f"{ORIGIN}/storage/v1/object/{BUCKET}/{storage_path}"
    headers = _auth_headers()
    headers["Content-Type"] = mime_type
    content = file_data.read() if hasattr(file_data, "read") else file_data

    try:
        resp = requests.post(url, data=content, headers=headers, timeout=TIMEOUT)
        if resp.status_code != 200:
            if resp.status_code in (401, 403):
                return {"success": False, "error": "STORAGE_AUTH_FAILED", "status_code": 502}
            return {"success": False, "error": "UPLOAD_FAILED", "status_code": 502, "detail": resp.text[:500]}

        # Normalise returned Key
        try:
            returned_key = resp.json().get("Key")
            if returned_key:
                canonical = _normalize(returned_key)
                if canonical != storage_path:
                    logger.info("PATH NORMALISED: '%s' → '%s' (from Key)", storage_path, canonical)
                    storage_path = canonical
        except Exception:
            pass

        logger.info("UPLOAD OK: %s (%d bytes)", storage_path, len(content))
        return {"success": True, "data": {"canonical_path": storage_path}}

    except requests.RequestException as e:
        logger.exception("UPLOAD NETWORK ERROR: %s", storage_path)
        return {"success": False, "error": "STORAGE_UNAVAILABLE", "status_code": 502}


# ═══════════════════════════════════════════════════════════════════════
# 2. generate_signed_url
# ═══════════════════════════════════════════════════════════════════════

def generate_signed_url(storage_path: str, expires_in: int = 3600) -> dict:
    """
    Generate a temporary signed URL for an object in Supabase Storage.

    Uses the single-object endpoint::

        POST /storage/v1/object/sign/{bucket}/{path}  body={"expiresIn": N}

    Returns::

        {"success": True, "data": {"signed_url": "https://...", "expires_in": 3600}}
        {"success": False, "error": "...", "status_code": 502}
    """
    raw_input = storage_path
    storage_path = _normalize(storage_path)

    if _is_local():
        _safe_local_path(storage_path)
        return {"success": True, "data": {"signed_url": f"http://localhost:8000/uploads/{storage_path}", "expires_in": expires_in}}

    encoded = urllib.parse.quote(storage_path, safe="/")
    endpoint = f"{ORIGIN}/storage/v1/object/sign/{BUCKET}/{encoded}"
    body = {"expiresIn": expires_in}
    headers = _auth_headers()
    headers["Content-Type"] = "application/json"

    logger.info("SIGNED URL: path='%s' → POST %s body=%s", storage_path,
                endpoint.replace(ORIGIN, "<origin>", 1), body)

    try:
        resp = requests.post(endpoint, json=body, headers=headers, timeout=60)

        logger.info("SIGNED URL RESPONSE: status=%s body=%.2000s", resp.status_code, resp.text or "")

        if resp.status_code < 200 or resp.status_code >= 300:
            return {"success": False, "error": "SIGNED_URL_FAILED",
                    "status_code": 502, "detail": f"HTTP {resp.status_code}: {resp.text[:500]}"}

        raw_url = _extract_signed_url(resp)
        if not raw_url:
            return {"success": False, "error": "SIGNED_URL_FAILED",
                    "status_code": 502, "detail": "Could not extract URL from response"}

        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            signed = raw_url
        elif raw_url.startswith("/"):
            signed = f"{ORIGIN}{raw_url}"
        else:
            signed = f"{ORIGIN}/{raw_url}"

        logger.info("SIGNED URL OK: %s", signed)
        return {"success": True, "data": {"signed_url": signed, "expires_in": expires_in}}

    except requests.RequestException as e:
        logger.exception("SIGNED URL NETWORK ERROR: %s", storage_path)
        return {"success": False, "error": "STORAGE_UNAVAILABLE", "status_code": 502}


# ═══════════════════════════════════════════════════════════════════════
# 3. delete_file
# ═══════════════════════════════════════════════════════════════════════

def delete_file(storage_path: str) -> dict:
    """Remove an object from Supabase Storage."""
    storage_path = _normalize(storage_path)

    if _is_local():
        local_path = _safe_local_path(storage_path)
        if local_path.exists():
            local_path.unlink()
        return {"success": True, "data": {"deleted": True}}

    url = f"{ORIGIN}/storage/v1/object/{BUCKET}"
    headers = _auth_headers()
    headers["Content-Type"] = "application/json"

    try:
        resp = requests.delete(url, json={"prefixes": [storage_path]}, headers=headers, timeout=60)
        if resp.status_code in (200, 204):
            logger.info("DELETE OK: %s", storage_path)
            return {"success": True, "data": {"deleted": True}}
        logger.error("DELETE FAILED: %s status=%s body=%s", storage_path, resp.status_code, resp.text[:300])
        return {"success": False, "error": "DELETE_FAILED", "status_code": 502, "detail": resp.text[:300]}
    except requests.RequestException as e:
        logger.exception("DELETE NETWORK ERROR: %s", storage_path)
        return {"success": False, "error": "STORAGE_UNAVAILABLE", "status_code": 502}


# ═══════════════════════════════════════════════════════════════════════
# 4. download_file
# ═══════════════════════════════════════════════════════════════════════

def download_file(signed_url: str) -> dict:
    """Download a file from a signed URL. Returns raw bytes."""
    try:
        resp = requests.get(signed_url, timeout=60)
        resp.raise_for_status()
        logger.info("DOWNLOAD OK: %d bytes", len(resp.content))
        return {"success": True, "data": {"content": resp.content, "headers": dict(resp.headers)}}
    except requests.RequestException as e:
        logger.exception("DOWNLOAD ERROR")
        return {"success": False, "error": "DOWNLOAD_FAILED", "status_code": 502}


# ═══════════════════════════════════════════════════════════════════════
# 5. verify_file_exists
# ═══════════════════════════════════════════════════════════════════════

def verify_file_exists(storage_path: str) -> dict:
    """
    Verify an object exists in the bucket by listing its folder.

    Returns::

        {"success": True, "data": {"exists": True, "objects_in_folder": [...]}}
        {"success": True, "data": {"exists": False, "objects_in_folder": [...]}}
    """
    storage_path = _normalize(storage_path)
    parent = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]

    if _is_local():
        local_path = _safe_local_path(storage_path)
        return {"success": True, "data": {"exists": local_path.exists(), "objects_in_folder": [filename] if local_path.exists() else []}}

    listing = list_folder(parent)
    if not listing["success"]:
        return listing

    names = listing["data"]["objects"]
    exists = filename in names

    logger.info("VERIFY: path='%s' exists=%s in=%s", storage_path, exists, names)
    return {"success": True, "data": {"exists": exists, "objects_in_folder": names}}


# ═══════════════════════════════════════════════════════════════════════
# 6. list_folder
# ═══════════════════════════════════════════════════════════════════════

def list_folder(prefix: str = "", limit: int = 200) -> dict:
    """List objects in the bucket with the given prefix."""
    prefix = _normalize(prefix)

    if _is_local():
        base = UPLOAD_DIR.resolve() / prefix
        names = []
        if base.exists() and base.is_dir():
            names = [p.name for p in base.iterdir() if p.is_file()]
        return {"success": True, "data": {"objects": names}}

    url = f"{ORIGIN}/storage/v1/object/list/{BUCKET}"
    headers = _auth_headers()
    headers["Content-Type"] = "application/json"
    list_pfx = f"{prefix}/" if prefix and not prefix.endswith("/") else prefix

    try:
        resp = requests.post(url, json={"prefix": list_pfx, "limit": limit, "sortBy": {"column": "name", "order": "asc"}},
                             headers=headers, timeout=15)
        if resp.status_code == 200:
            names = [item.get("name", "") for item in resp.json()]
            return {"success": True, "data": {"objects": names}}
        return {"success": False, "error": "BUCKET_UNAVAILABLE", "status_code": 502, "detail": resp.text[:300]}
    except Exception as e:
        logger.warning("LIST FOLDER ERROR: prefix=%s %s", prefix, e)
        return {"success": False, "error": "BUCKET_UNAVAILABLE", "status_code": 502}


# ═══════════════════════════════════════════════════════════════════════
# 7. create_zip
# ═══════════════════════════════════════════════════════════════════════

def create_zip(files: list[dict], zip_name: str = "documents.zip") -> dict:
    """
    Create a ZIP archive in memory from a list of file descriptors.

    Each entry in ``files``::

        {"signed_url": "...", "arcname": "type/filename.pdf", "storage_path": "..."}

    Returns::

        {"success": True, "data": {"zip_bytes": b"...", "filename": "documents.zip"}}
    """
    buffer = io.BytesIO()
    errors = []

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in files:
            try:
                dl = download_file(entry["signed_url"])
                if dl["success"]:
                    zf.writestr(entry["arcname"], dl["data"]["content"])
                else:
                    errors.append({"storage_path": entry.get("storage_path", ""), "error": dl.get("error", "DOWNLOAD_FAILED")})
            except Exception as exc:
                errors.append({"storage_path": entry.get("storage_path", ""), "error": str(exc)})

    buffer.seek(0)
    logger.info("ZIP CREATED: %s %d files %d errors %d bytes", zip_name, len(files), len(errors), buffer.getbuffer().nbytes)
    return {"success": True, "data": {"zip_bytes": buffer.getvalue(), "filename": zip_name, "errors": errors}}


# ═══════════════════════════════════════════════════════════════════════
# 8. diagnose
# ═══════════════════════════════════════════════════════════════════════

def diagnose_path(storage_path: str) -> dict:
    """
    Run full diagnostics on a storage path.

    Never raises. Returns a dict with all findings.
    """
    raw_path = storage_path.strip()
    normalised = _normalize(raw_path)
    result = {
        "bucket": BUCKET,
        "db_storage_path": raw_path,
        "normalized_storage_path": normalised,
        "bucket_prefix_removed": raw_path.startswith(f"{BUCKET}/"),
    }

    if _is_local():
        result["error"] = "Not connected to Supabase (dev/test mode)"
        return result

    # List root
    root = list_folder("", 200)
    result["bucket_reachable"] = root["success"]

    # Walk path segments
    parts = normalised.split("/")
    current = ""
    segments = []
    for seg in parts:
        listing = list_folder(current, 200)
        names = listing.get("data", {}).get("objects", []) if listing["success"] else []
        matches = seg in names or any(n == seg for n in names)
        segments.append({"segment": seg, "prefix": f"{current}{seg}/", "matches": matches, "found": names})
        current = f"{current}{seg}/"
    result["path_segments"] = segments

    # Check object existence
    parent = "/".join(parts[:-1]) if len(parts) > 1 else ""
    filename = parts[-1] if parts else normalised
    if parent:
        listing = list_folder(parent, 200)
        if listing["success"]:
            names = listing["data"]["objects"]
            result["object_exists"] = filename in names
            result["objects_in_folder"] = names
        else:
            result["object_exists"] = None
            result["objects_in_folder"] = []

    # Try signed URL
    signed = generate_signed_url(normalised, 120)
    result["signed_url_generated"] = signed["success"]
    if signed["success"]:
        result["signed_url"] = signed["data"]["signed_url"]
        try:
            head = requests.head(signed["data"]["signed_url"], timeout=10)
            result["signed_url_status"] = head.status_code
            result["signed_url_headers"] = dict(head.headers)
        except Exception as e:
            result["signed_url_verify_error"] = str(e)
    else:
        result["signed_url_error"] = signed.get("error")

    return result
