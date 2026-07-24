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

    if _is_local():
        local_path = _safe_local_path(storage_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        content = file_data.read() if hasattr(file_data, "read") else file_data
        with open(local_path, "wb") as f:
            f.write(content)
        logger.info("LOCAL UPLOAD: %s (%d bytes)", storage_path, len(content))
        return {"success": True, "data": {"canonical_path": storage_path}}

    url = f"{ORIGIN}/storage/v1/object/{BUCKET}/{storage_path}"
    headers = _auth_headers()
    headers["Content-Type"] = mime_type
    content = file_data.read() if hasattr(file_data, "read") else file_data

    logger.error("=" * 70)
    logger.error("UPLOAD FILE — FULL TRACE")
    logger.error("=" * 70)
    logger.error("  endpoint:        POST %s", url.replace(SERVICE_KEY, "***") if SERVICE_KEY else url)
    logger.error("  bucket:          '%s'", BUCKET)
    logger.error("  storage_path:    '%s'", storage_path)
    logger.error("  storage_path chars: %s", [c for c in storage_path])
    logger.error("  content_type:    '%s'", mime_type)
    logger.error("  content_length:  %d bytes", len(content))

    try:
        resp = requests.post(url, data=content, headers=headers, timeout=TIMEOUT)
        logger.error("  RESPONSE status: %d", resp.status_code)
        logger.error("  RESPONSE headers: %s", dict(resp.headers))
        logger.error("  RESPONSE body:    %.3000s", resp.text or "(empty)")

        if resp.status_code != 200:
            if resp.status_code in (401, 403):
                return {"success": False, "error": "STORAGE_AUTH_FAILED", "status_code": 502}
            return {"success": False, "error": "UPLOAD_FAILED", "status_code": 502, "detail": resp.text[:500]}

        returned_key = None
        try:
            resp_data = resp.json()
            returned_key = resp_data.get("Key")
        except Exception as exc:
            logger.error("  could not parse JSON: %s", exc)

        if returned_key:
            logger.error("  RETURNED Key:       '%s'", returned_key)
            logger.error("  RETURNED Key chars: %s", [c for c in returned_key])
            canonical = _normalize(returned_key)
            logger.error("  normalized Key:     '%s'", canonical)
            if canonical != storage_path:
                logger.error("  *** PATH CHANGED: '%s' → '%s' ***", storage_path, canonical)
                storage_path = canonical
        else:
            logger.error("  RETURNED Key: (none/empty)")

        logger.error("  FINAL canonical:    '%s'", storage_path)
        logger.error("  FINAL canonical chars: %s", [c for c in storage_path])
        logger.error("=" * 70)
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
    normalized_path = _normalize(storage_path)

    logger.error("=" * 70)
    logger.error("GENERATE SIGNED URL — FULL TRACE")
    logger.error("=" * 70)
    logger.error("  >>> Step 0: Input <<<")
    logger.error("    raw from DB:       '%s'", raw_input)
    logger.error("    normalized:        '%s'", normalized_path)
    logger.error("    char repr DB:      %s", [c for c in raw_input])
    logger.error("    char repr norm:    %s", [c for c in normalized_path])
    logger.error("    len DB:            %d", len(raw_input))
    logger.error("    len norm:          %d", len(normalized_path))
    logger.error("    BUCKET config:     '%s'", BUCKET)
    logger.error("    ORIGIN config:     '%s'", ORIGIN)

    if _is_local():
        _safe_local_path(normalized_path)
        return {"success": True, "data": {"signed_url": f"http://localhost:8000/uploads/{normalized_path}", "expires_in": expires_in}}

    # ── Step 1: Verify object exists in the bucket ───────────────────
    parent = "/".join(normalized_path.split("/")[:-1])
    filename = normalized_path.split("/")[-1]

    logger.error("  >>> Step 1: Object verification <<<")
    logger.error("    parent folder:  '%s'", parent)
    logger.error("    expected file:  '%s'", filename)

    listing = list_folder(parent)
    if listing["success"]:
        names = listing["data"]["objects"]
        logger.error("    list_folder OK: %d objects found in '%s'", len(names), parent)
        for i, n in enumerate(names):
            logger.error("      [%d] '%s' (len=%d, chars=%s)", i, n, len(n), [c for c in n])
        exists = filename in names
        logger.error("    file_in_list:  %s", exists)
        if not exists:
            logger.error("    *** OBJECT NOT FOUND in folder '%s' ***", parent)
            logger.error("    DB path:       '%s'", normalized_path)
            logger.error("    Expected file: '%s'", filename)
            # Try with bucket prefix variants
            bucket_variant = f"{BUCKET}/{parent}"
            listing2 = list_folder(bucket_variant)
            if listing2["success"] and listing2["data"]["objects"]:
                for j, m in enumerate(listing2["data"]["objects"]):
                    logger.error("      PREFIXED[%d] '%s' (len=%d, chars=%s)", j, m, len(m), [c for c in m])
            return {
                "success": False, "error": "OBJECT_NOT_FOUND",
                "status_code": 404,
                "detail": f"Object '{filename}' not found in folder '{parent}'."
                          f" Objects in folder: {names}",
            }
    else:
        logger.error("    *** list_folder FAILED: %s ***", listing.get("error"))
        logger.error("    parent folder:  '%s'", parent)
        logger.error("    expected file:  '%s'", filename)
        logger.error("    aborting signed URL generation")
        return {
            "success": False, "error": "BUCKET_UNAVAILABLE",
            "status_code": 502,
            "detail": f"Cannot verify object existence: {listing.get('error')}",
        }

    # ── Step 2: Build the sign request ─────────────────────
    encoded = urllib.parse.quote(normalized_path, safe="/")
    endpoint = f"{ORIGIN}/storage/v1/object/sign/{BUCKET}/{encoded}"
    body = {"expiresIn": expires_in}
    req_headers = _auth_headers()
    req_headers["Content-Type"] = "application/json"

    logger.error("  >>> Step 2: Sign request <<<")
    logger.error("    bucket:           '%s'", BUCKET)
    logger.error("    object_path:      '%s'", normalized_path)
    logger.error("    encoded_path:     '%s'", encoded)
    logger.error("    endpoint(raw):    %s", endpoint)
    logger.error("    endpoint(safe):   %s", endpoint.replace(ORIGIN, "<origin>", 1))
    logger.error("    method:           POST")
    logger.error("    body:             %s", body)
    logger.error("    auth_header:      Bearer %s...", SERVICE_KEY[:20] if SERVICE_KEY else "(none)")

    # ── Step 3: Call Supabase sign endpoint ─────────────────
    try:
        resp = requests.post(endpoint, json=body, headers=req_headers, timeout=60)

        logger.error("  >>> Step 3: Supabase response <<<")
        logger.error("    status:          %d", resp.status_code)
        logger.error("    headers:         %s", dict(resp.headers))
        logger.error("    body:            %.3000s", resp.text or "(empty)")

        if resp.status_code < 200 or resp.status_code >= 300:
            return {"success": False, "error": "SIGNED_URL_FAILED",
                    "status_code": 502,
                    "detail": f"HTTP {resp.status_code}: {resp.text[:500]}"}

        # ── Step 4: Extract URL from response ───────────────
        raw_url = _extract_signed_url(resp)
        logger.error("  >>> Step 4: Extract signed URL <<<")
        logger.error("    extracted:       '%s'", raw_url[:120] if raw_url else "None")

        if not raw_url:
            return {"success": False, "error": "SIGNED_URL_FAILED",
                    "status_code": 502, "detail": "Could not extract URL from response"}

        # ── Step 5: Make absolute ─────────────────────
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            signed = raw_url
        elif raw_url.startswith("/"):
            signed = f"{ORIGIN}{raw_url}"
        else:
            signed = f"{ORIGIN}/{raw_url}"

        logger.error("  >>> Step 5: Absolute URL <<<")
        logger.error("    signed_url:      '%s'", signed)

        # ── Step 6: Backend-verify the signed URL ────────────
        logger.error("  >>> Step 6: Backend verification GET <<<")
        verified = False
        try:
            verify_resp = requests.get(signed, timeout=15, allow_redirects=False)
            logger.error("    GET status:      %d", verify_resp.status_code)
            logger.error("    GET headers:     %s", dict(verify_resp.headers))
            logger.error("    GET body:        %.3000s", verify_resp.text or "(empty)")
            logger.error("    GET body chars:  %s", [c for c in (verify_resp.text or "")][:200])
            if verify_resp.status_code == 200:
                logger.error("    *** SIGNED URL VERIFIED OK ***")
                verified = True
            elif verify_resp.status_code == 302:
                redirect_url = verify_resp.headers.get("Location", "")
                logger.error("    REDIRECT to:     '%s'", redirect_url)
                try:
                    redirect_resp = requests.get(redirect_url, timeout=15)
                    if redirect_resp.status_code == 200:
                        logger.error("    *** REDIRECT VERIFIED OK ***")
                        verified = True
                    else:
                        logger.error("    *** REDIRECT FAILED (HTTP %d) ***", redirect_resp.status_code)
                except Exception as redirect_err:
                    logger.error("    *** REDIRECT ERROR: %s", redirect_err)
            else:
                logger.error("    *** SIGNED URL VERIFICATION FAILED (HTTP %d) ***", verify_resp.status_code)
        except requests.RequestException as e:
            logger.error("    *** SIGNED URL VERIFICATION NETWORK ERROR: %s", e)

        if not verified:
            return {
                "success": False, "error": "SIGNED_URL_FAILED",
                "status_code": 502,
                "detail": "Signed URL verification failed (backend GET returned non-200).",
            }

        logger.error("=" * 70)
        return {"success": True, "data": {"signed_url": signed, "expires_in": expires_in}}

    except requests.RequestException as e:
        logger.exception("  SIGNED URL NETWORK ERROR: %s", normalized_path)
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
            objects = resp.json()
            names = [item.get("name", "") for item in objects]
            logger.info("LIST: prefix='%s' → %d objects", list_pfx, len(names))
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

    root = list_folder("", 200)
    result["bucket_reachable"] = root["success"]

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
