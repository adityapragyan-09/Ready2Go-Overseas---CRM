"""
Ready2Go CRM — Supabase Storage REST Client Service

Handles raw HTTP communications with Supabase Storage API for uploading,
deleting, and signing download links for applicant documents.
"""

import logging
import os
import urllib.parse
from pathlib import Path

import requests
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_headers(mime_type: str = None) -> dict:
    """Prepare auth and request headers for Supabase Storage."""
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    if mime_type:
        headers["Content-Type"] = mime_type
    return headers


def _safe_local_path(storage_path: str) -> Path:
    """Resolve a local file path and guard against directory traversal."""
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    resolved = (upload_dir / storage_path).resolve()
    if os.path.commonpath([str(resolved), str(upload_dir)]) != str(upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path: directory traversal detected.",
        )
    return resolved


def upload_file(file_data, storage_path: str, mime_type: str) -> str:
    """
    Upload a file to Supabase Storage.

    Stores the object at `{bucket}/{storage_path}`. The storage_path is
    stored verbatim in the DB and later used for signed URL generation.
    """
    storage_path = storage_path.strip()

    if settings.ENVIRONMENT != "production" and (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        local_path = _safe_local_path(storage_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            content = file_data.read() if hasattr(file_data, "read") else file_data
            f.write(content)
        return f"/uploads/{storage_path}"

    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}/{storage_path}"
    headers = _get_headers(mime_type)

    logger.info(
        "UPLOAD: bucket=%s path=%s url=%s",
        settings.SUPABASE_BUCKET, storage_path,
        url.replace(settings.SUPABASE_KEY, "***") if settings.SUPABASE_KEY else url,
    )

    try:
        response = requests.post(url, data=file_data, headers=headers, timeout=settings.UPLOAD_TIMEOUT_SECONDS)
        logger.info(
            "UPLOAD RESPONSE: status=%s body=%s",
            response.status_code, response.text[:500] if response.text else "(empty)",
        )

        if response.status_code != 200:
            if response.status_code in (401, 403):
                raise HTTPException(status_code=502, detail="Storage authentication failed.")
            raise HTTPException(status_code=502, detail="File upload to storage failed.")

        try:
            resp_data = response.json()
            returned_key = resp_data.get("Key")
            logger.info("UPLOAD KEY: returned=%s expected=%s", returned_key, storage_path)
        except Exception:
            pass

        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{storage_path}"
    except requests.RequestException as e:
        logger.exception("Storage upload network error for path %s", storage_path)
        raise HTTPException(status_code=502, detail="Storage service is currently unavailable.")


def delete_file(storage_path: str) -> None:
    """Remove a file from the Supabase Storage bucket."""
    storage_path = storage_path.strip()
    if settings.ENVIRONMENT != "production" and (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        local_path = _safe_local_path(storage_path)
        if local_path.exists():
            local_path.unlink()
        return

    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    logger.info("DELETE: bucket=%s path=%s", settings.SUPABASE_BUCKET, storage_path)

    try:
        response = requests.delete(url, json={"prefixes": [storage_path]}, headers=headers, timeout=60)
        if response.status_code not in (200, 204):
            logger.error("DELETE FAILED: status=%s body=%s", response.status_code, response.text)
            if response.status_code in (401, 403):
                raise HTTPException(status_code=502, detail="Storage authentication failed.")
        else:
            logger.info("DELETE SUCCESS: path=%s", storage_path)
    except requests.RequestException as e:
        logger.exception("Storage delete network error for path %s", storage_path)
        raise HTTPException(status_code=502, detail="Storage service is currently unavailable.")


def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary signed URL for a file in private storage.

    Tries two API formats in order:
      1) Body API:  POST /object/sign/{bucket}       body={"path":p, "expiresIn":N}
      2) Legacy API: POST /object/sign/{bucket}/{path} body={"expiresIn":N}

    Logs the COMPLETE raw response from Supabase for debugging.
    Handles ALL known response formats:
      - {"signedURL": "/storage/...?token=..."}
      - {"signedUrl": "https://...?token=..."}
      - {"data": {"signedUrl": "..."}}
      - Plain string URL
      - Array containing URL
    """
    storage_path = storage_path.strip()

    if settings.ENVIRONMENT != "production" and (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        _safe_local_path(storage_path)
        return f"http://localhost:8000/uploads/{storage_path}"

    headers = _get_headers()
    headers["Content-Type"] = "application/json"
    base_url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{settings.SUPABASE_BUCKET}"

    logger.info("=== SIGNED URL REQUEST ===")
    logger.info("  bucket=%s", settings.SUPABASE_BUCKET)
    logger.info("  storage_path='%s'", storage_path)
    logger.info("  expires_in=%s", expires_in)

    def _extract_signed_url(response) -> str | None:
        """Extract a signed URL from ANY response format.

        Returns the raw signed URL string (possibly relative),
        or None if no URL could be extracted.
        """
        raw_text = response.text
        logger.info("RAW SUPABASE RESPONSE (status=%s): %s", response.status_code, raw_text[:2000])

        if not raw_text or raw_text.strip() == "":
            logger.warning("Empty response body")
            return None

        # Try to parse as JSON
        try:
            data = response.json()
        except Exception:
            # Not JSON — maybe plain string URL
            cleaned = raw_text.strip().strip('"').strip("'")
            if cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("/"):
                logger.info("EXTRACTED as plain string: %s...", cleaned[:100])
                return cleaned
            logger.warning("Response is not JSON or URL string: %s", raw_text[:200])
            return None

        # It's JSON — try all known signed URL field locations
        # Flatten nested structures
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

        # Log all fields for debugging
        logger.info("PARSED RESPONSE FIELDS: %s", flat)

        # Known signed URL field names (in priority order)
        known_fields = [
            "signedURL", "signedUrl", "signed_url",
            "data.signedURL", "data.signedUrl", "data.signed_url",
            "url", "URL",
            "data",
        ]

        for field in known_fields:
            val = flat.get(field) or (data.get(field) if isinstance(data, dict) else None)
            if val and isinstance(val, str) and (val.startswith("http") or val.startswith("/")):
                logger.info("EXTRACTED from field '%s': %s...", field, val[:100])
                return val

        # Last resort: check if any string-typed value looks like a URL
        for k, v in flat.items():
            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://") or v.startswith("/")):
                if "token" in v or "sign" in v:
                    logger.info("EXTRACTED from field '%s' (heuristic): %s...", k, v[:100])
                    return v

        logger.error("COULD NOT EXTRACT signed URL from response. Raw=%s", raw_text[:2000])
        return None

    def _make_absolute(raw_url: str) -> str:
        """Convert a possibly-relative signed URL to an absolute URL."""
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url
        if raw_url.startswith("/"):
            # The signed URL path should look like:
            #   /storage/v1/object/sign/{bucket}/{path}?token=...
            # Prepend the Supabase origin
            return f"{settings.SUPABASE_URL}{raw_url}"
        # Relative without leading slash — treat as relative to SUPABASE_URL
        return f"{settings.SUPABASE_URL}/{raw_url}"

    # ── Attempt 1: Current API (path in request body) ──
    try:
        response = requests.post(base_url, json={"path": storage_path, "expiresIn": expires_in}, headers=headers, timeout=60)
        raw_url = _extract_signed_url(response)
        if raw_url:
            full_url = _make_absolute(raw_url)
            logger.info("SIGNED URL RESULT (body API): final_url=%s", full_url)
            return full_url
    except requests.RequestException as e:
        logger.warning("SIGNED URL attempt 1 network error: %s", e)

    # ── Attempt 2: Legacy API (path in URL) ──
    try:
        encoded_path = urllib.parse.quote(storage_path, safe="/")
        legacy_url = f"{base_url}/{encoded_path}"
        response = requests.post(legacy_url, json={"expiresIn": expires_in}, headers=headers, timeout=60)
        raw_url = _extract_signed_url(response)
        if raw_url:
            full_url = _make_absolute(raw_url)
            logger.info("SIGNED URL RESULT (legacy API): final_url=%s", full_url)
            return full_url
    except requests.RequestException as e:
        logger.warning("SIGNED URL attempt 2 network error: %s", e)

    raise HTTPException(status_code=502, detail="Failed to generate document access URL.")


def download_file_as_bytes(file_url: str) -> bytes:
    """Download a file from a signed URL."""
    try:
        response = requests.get(file_url, timeout=60)
        response.raise_for_status()
        logger.info("DOWNLOAD: status=%s size=%s", response.status_code, len(response.content))
        return response.content
    except requests.RequestException as e:
        logger.exception("Failed to download file from %s", file_url[:80])
        raise HTTPException(status_code=502, detail="Failed to download file from storage.")


# ── Diagnostics ────────────────────────────

def list_storage_objects(prefix: str = "", limit: int = 100) -> list[dict]:
    """List objects in the bucket with the given prefix. Returns list of {name, id, ...}."""
    if not settings.SUPABASE_URL or "dummy" in settings.SUPABASE_URL:
        return []

    url = f"{settings.SUPABASE_URL}/storage/v1/object/list/{settings.SUPABASE_BUCKET}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    # Ensure prefix ends with / for directory listing
    list_prefix = prefix
    if list_prefix and not list_prefix.endswith("/"):
        list_prefix = f"{list_prefix}/"

    try:
        resp = requests.post(
            url,
            json={"prefix": list_prefix, "limit": limit, "sortBy": {"column": "name", "order": "asc"}},
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            items = resp.json()
            # items is a list of objects: [{name, id, updated_at, ...}]
            logger.info("LIST %s: found %d objects, response=%s", list_prefix, len(items), resp.text[:500])
            return items
        else:
            logger.warning("LIST %s failed: status=%s body=%s", list_prefix, resp.status_code, resp.text[:200])
            return []
    except Exception as e:
        logger.warning("LIST %s error: %s", list_prefix, e)
        return []


def diagnose_storage_path(storage_path: str) -> dict:
    """
    Full storage path diagnostics.
    Compares DB storage_path with actual bucket contents.
    Never raises — returns a dict with all findings.
    """
    storage_path = storage_path.strip()
    result = {
        "db_storage_path": storage_path,
        "bucket": settings.SUPABASE_BUCKET,
        "supabase_url": settings.SUPABASE_URL.replace(settings.SUPABASE_KEY, "***") if settings.SUPABASE_KEY else settings.SUPABASE_URL,
        "errors": [],
    }

    if not settings.SUPABASE_URL or "dummy" in settings.SUPABASE_URL:
        result["error"] = "SUPABASE_URL not configured"
        return result

    # Extract path components
    path_parts = storage_path.split("/")
    result["filename"] = path_parts[-1] if path_parts else storage_path
    result["parent_dir"] = "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""

    # 1. Ping the bucket
    try:
        root_items = list_storage_objects(prefix="", limit=1)
        result["bucket_reachable"] = True
        result["has_applicants_folder"] = any(
            item.get("name") == "applicants" for item in root_items
        )
    except Exception as e:
        result["bucket_reachable"] = False
        result["errors"].append(f"Bucket ping failed: {e}")
        result["has_applicants_folder"] = "unknown"

    # 2. List applicant directory to find all APP- folders
    try:
        applicant_items = list_storage_objects(prefix="applicants", limit=100)
        app_folders = [item.get("name", "") for item in applicant_items]
        result["applicant_folders_in_storage"] = app_folders

        # Check if our specific APP folder exists
        app_folder = path_parts[0] + "/" + path_parts[1] if len(path_parts) >= 2 else ""
        result["app_folder_in_list"] = app_folder in app_folders
        result["expected_app_folder"] = app_folder
    except Exception as e:
        result["errors"].append(f"Applicant folder list failed: {e}")

    # 3. List objects in the specific APP- folder
    parent_dir = result["parent_dir"]
    if parent_dir:
        try:
            dir_items = list_storage_objects(prefix=parent_dir, limit=100)
            result["objects_in_folder"] = [item.get("name", "") for item in dir_items]
            result["file_exists_in_storage"] = result["filename"] in result["objects_in_folder"]

            # Compare full paths (some APIs return full path, some return basename)
            full_paths = [
                f"{parent_dir}/{item.get('name', '')}" if not item.get("name", "").startswith(parent_dir) else item.get("name", "")
                for item in dir_items
            ]
            result["full_paths_in_folder"] = full_paths
            result["full_path_matches_db"] = storage_path in full_paths
        except Exception as e:
            result["errors"].append(f"File list failed: {e}")

    # 4. Try to generate a signed URL
    try:
        signed_url = generate_signed_url(storage_path, expires_in=120)
        result["signed_url_generated"] = True
        result["signed_url_full"] = signed_url

        # Verify the signed URL by making a HEAD request
        try:
            head_resp = requests.head(signed_url, timeout=10)
            result["signed_url_head_status"] = head_resp.status_code
            result["signed_url_head_headers"] = dict(head_resp.headers)

            # If HEAD fails, try GET with range (just first byte)
            if head_resp.status_code != 200:
                get_resp = requests.get(signed_url, headers={"Range": "bytes=0-0"}, timeout=10)
                result["signed_url_get_range_status"] = get_resp.status_code
                result["signed_url_get_range_body"] = get_resp.text[:200]
        except requests.RequestException as e:
            result["signed_url_verify_error"] = str(e)
    except Exception as e:
        result["signed_url_generated"] = False
        result["signed_url_error"] = str(e)

    # 5. Check for common path issues
    result["path_has_leading_slash"] = storage_path.startswith("/")
    result["path_has_trailing_slash"] = storage_path.endswith("/")
    result["path_has_bucket_prefix"] = storage_path.startswith(settings.SUPABASE_BUCKET)

    return result
