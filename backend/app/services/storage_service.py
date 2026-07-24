"""
Ready2Go CRM — Supabase Storage REST Client Service

Handles raw HTTP communications with Supabase Storage API for uploading,
deleting, and signing download links for applicant documents.

CANONICAL STORAGE PATH FORMAT:
    applicants/APP-000048/file.pdf

NEVER store paths with the bucket name prefix:
    WRONG: ready2go-documents/applicants/APP-000048/file.pdf
    RIGHT: applicants/APP-000048/file.pdf
"""

import logging
import os
import urllib.parse
from pathlib import Path

import requests
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

logger.info(
    "Storage service initialized — using raw REST (no supabase-py SDK). "
    "All paths normalized to canonical form (bucket prefix stripped)."
)


# ═══════════════════════════════════════════════════════════════════════
# Module 2 — Storage Path Normalizer
# ═══════════════════════════════════════════════════════════════════════

def normalize_storage_path(path: str) -> str:
    """
    Normalize a storage path to canonical form.

    Supabase Storage sometimes returns the Key with the bucket name
    prefixed (e.g. ``ready2go-documents/applicants/...``).  This
    function strips that prefix and normalises separators so the rest of
    the application always works with clean paths.

    Rules:
    - Strip leading/trailing whitespace
    - Convert Windows backslashes to forward slashes
    - Remove leading slash
    - Strip ``{bucket_name}/`` prefix if present
    - Collapse duplicate slashes (``//`` → ``/``)

    Examples::

        "ready2go-documents/applicants/APP-000048/file.pdf"
        → "applicants/APP-000048/file.pdf"

        "/applicants//APP-000048\\\\file.pdf"
        → "applicants/APP-000048/file.pdf"
    """
    if not path:
        return path

    # 1. Trim whitespace
    path = path.strip()

    # 2. Convert Windows backslashes to forward slashes
    path = path.replace("\\", "/")

    # 3. Remove leading slash
    path = path.lstrip("/")

    # 4. Remove bucket prefix if present
    bucket_prefix = f"{settings.SUPABASE_BUCKET}/"
    if path.startswith(bucket_prefix):
        logger.debug(
            "normalize_storage_path: stripped bucket prefix '%s' from '%s...'",
            bucket_prefix, path[:100],
        )
        path = path[len(bucket_prefix):]

    # 5. Remove leading slash again (bucket prefix strip may have left one)
    path = path.lstrip("/")

    # 6. Collapse duplicate slashes
    while "//" in path:
        path = path.replace("//", "/")

    # 7. Re-strip (in case of trailing spaces after normalization)
    path = path.strip()

    return path


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

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


def _verify_file_in_storage(storage_path: str, log_prefix: str = "") -> bool:
    """
    Verify a file exists in Supabase Storage by listing its parent prefix.

    Returns ``True`` if the file was found, ``False`` otherwise.
    Logs all discovered objects on failure for debugging.
    """
    parent = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]
    try:
        objects = list_storage_objects(prefix=parent, limit=200)
        names = [o.get("name", "") for o in objects]
        if filename in names:
            logger.info(
                "%s VERIFIED OK: '%s' found under prefix '%s'",
                log_prefix, filename, parent,
            )
            return True
        logger.error(
            "%s VERIFICATION FAILED: '%s' NOT found under prefix '%s'. "
            "Objects in folder: %s",
            log_prefix, filename, parent, names,
        )
        return False
    except Exception as exc:
        logger.warning(
            "%s verification skipped (could not list objects): %s",
            log_prefix, exc,
        )
        return False


# ═══════════════════════════════════════════════════════════════════════
# Module 1 & 4 — Upload File
# ═══════════════════════════════════════════════════════════════════════

def upload_file(file_data, storage_path: str, mime_type: str) -> str:
    """
    Upload a file to Supabase Storage.

    Stores the object at ``{bucket}/{storage_path}``.  The returned
    canonical storage path (with bucket prefix stripped) should be
    persisted in the database — never the raw ``Key`` from the response.

    Returns the canonical object path, e.g. ``applicants/APP-000001/uuid.pdf``.

    Raises ``HTTPException`` 502 if the upload fails, or 500 if
    post-upload verification confirms the file was not persisted.
    """
    storage_path = normalize_storage_path(storage_path)

    # ── Local dev/test fallback ─────────────────────────────────────
    if settings.ENVIRONMENT in ("development", "test") or (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY
        or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        local_path = _safe_local_path(storage_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            content = file_data.read() if hasattr(file_data, "read") else file_data
            f.write(content)
        logger.info("LOCAL UPLOAD (dev/test): path=%s", storage_path)
        return storage_path

    # ── Supabase upload ────────────────────────────────────────────────
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}/{storage_path}"
    headers = _get_headers(mime_type)
    safe_url = url.replace(settings.SUPABASE_KEY, "***") if settings.SUPABASE_KEY else url

    logger.info("=== UPLOAD REQUEST ===")
    logger.info("  bucket=%s", settings.SUPABASE_BUCKET)
    logger.info("  storage_path=%s", storage_path)
    logger.info("  mime_type=%s", mime_type)
    logger.info("  url=%s", safe_url)

    try:
        response = requests.post(
            url,
            data=file_data,
            headers=headers,
            timeout=settings.UPLOAD_TIMEOUT_SECONDS,
        )

        logger.info("=== UPLOAD RESPONSE ===")
        logger.info("  status=%s", response.status_code)
        logger.info("  body=%.2000s", response.text or "(empty)")

        if response.status_code != 200:
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=502,
                    detail="Storage authentication failed.",
                )
            raise HTTPException(
                status_code=502,
                detail=f"File upload to storage failed (HTTP {response.status_code}).",
            )

        # ── Extract and normalise the returned Key ─────────────────────
        returned_key = None
        try:
            resp_data = response.json()
            returned_key = resp_data.get("Key")
        except Exception:
            pass

        if returned_key:
            canonical_key = normalize_storage_path(returned_key)

            # Log if the raw Key differed from our input path
            if returned_key != storage_path:
                logger.info(
                    "UPLOAD RAW KEY: '%s' → canonical='%s' (bucket prefix stripped)",
                    returned_key[:120], canonical_key,
                )

            if canonical_key != storage_path:
                logger.info(
                    "UPLOAD PATH NORMALISED: '%s' → '%s' (Key differed from input)",
                    storage_path, canonical_key,
                )
                storage_path = canonical_key
        else:
            logger.info("UPLOAD KEY: (none returned from API)")

        # ── Post-upload verification ────────────────────────────────────
        if not _verify_file_in_storage(storage_path, log_prefix="UPLOAD"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File upload completed but verification failed — "
                       "object not found in storage. Aborting.",
            )

        logger.info("  canonical_storage_path=%s", storage_path)
        return storage_path

    except requests.RequestException as e:
        logger.exception(
            "Storage upload NETWORK ERROR for path %s", storage_path,
        )
        raise HTTPException(
            status_code=502,
            detail="Storage service is currently unavailable.",
        )


# ═══════════════════════════════════════════════════════════════════════
# Delete File
# ═══════════════════════════════════════════════════════════════════════

def delete_file(storage_path: str) -> None:
    """Remove a file from the Supabase Storage bucket."""
    storage_path = normalize_storage_path(storage_path)

    if settings.ENVIRONMENT in ("development", "test") or (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY
        or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
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
        response = requests.delete(
            url, json={"prefixes": [storage_path]}, headers=headers, timeout=60,
        )
        if response.status_code not in (200, 204):
            logger.error(
                "DELETE FAILED: status=%s body=%s",
                response.status_code, response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(status_code=502, detail="Storage authentication failed.")
        else:
            logger.info("DELETE SUCCESS: path=%s", storage_path)
    except requests.RequestException as e:
        logger.exception("Storage delete network error for path %s", storage_path)
        raise HTTPException(status_code=502, detail="Storage service is currently unavailable.")


# ═══════════════════════════════════════════════════════════════════════
# Module 3 — Signed URL Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary signed URL for a file in Supabase Storage.

    Uses the correct single-object endpoint::

        POST /storage/v1/object/sign/{bucket}/{path}
        body={"expiresIn": N}

    The ``storage_path`` is normalised before use so the bucket prefix
    is never accidentally included in the object path.

    Returns an absolute ``https://`` signed URL ready for browser consumption.
    """
    storage_path = normalize_storage_path(storage_path)

    if settings.ENVIRONMENT in ("development", "test") or (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY
        or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        _safe_local_path(storage_path)
        return f"http://localhost:8000/uploads/{storage_path}"

    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    encoded_path = urllib.parse.quote(storage_path, safe="/")
    signed_url_endpoint = (
        f"{settings.SUPABASE_URL}/storage/v1/object/sign/"
        f"{settings.SUPABASE_BUCKET}/{encoded_path}"
    )

    request_body = {"expiresIn": expires_in}
    supabase_origin = settings.SUPABASE_URL

    logger.info("=== GENERATE SIGNED URL ===")
    logger.info("  bucket=%s", settings.SUPABASE_BUCKET)
    logger.info("  storage_path='%s'", storage_path)
    logger.info("  expires_in=%s", expires_in)
    logger.info("  POST %s", signed_url_endpoint.replace(supabase_origin, "<origin>", 1))
    logger.info("  body=%s", request_body)

    # ── Response parser (inline) ───────────────────────────────────────
    def _extract_signed_url(response) -> str | None:
        raw_text = response.text or ""
        logger.info("RESPONSE: status=%s body=%.2000s", response.status_code, raw_text)

        if response.status_code < 200 or response.status_code >= 300:
            logger.error("Non-success status %s. body=%s", response.status_code, raw_text[:500])
            return None

        if not raw_text.strip():
            logger.warning("Empty response body from status %s", response.status_code)
            return None

        try:
            data = response.json()
        except Exception:
            cleaned = raw_text.strip().strip('"').strip("'")
            if cleaned and (cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("/")):
                logger.info("EXTRACTED as plain string: %s", cleaned[:120])
                return cleaned
            logger.warning("Response not JSON or URL: %.200s", raw_text)
            return None

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
        logger.info("PARSED JSON fields=%s", flat)

        known_fields = [
            "signedURL", "signedUrl", "signed_url",
            "data.signedURL", "data.signedUrl", "data.signed_url",
            "url", "URL", "data",
        ]
        for field in known_fields:
            val = flat.get(field) or (data.get(field) if isinstance(data, dict) else None)
            if val and isinstance(val, str) and (val.startswith("http") or val.startswith("/")):
                logger.info("EXTRACTED from field '%s': %s", field, val[:120])
                return val

        for k, v in flat.items():
            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://") or v.startswith("/")):
                if "token" in v or "sign" in v:
                    logger.info("EXTRACTED (heuristic) from '%s': %s", k, v[:120])
                    return v

        logger.error("Could not extract signed URL. Raw=%.2000s", raw_text)
        return None

    def _make_absolute(raw_url: str) -> str:
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url
        if raw_url.startswith("/"):
            return f"{supabase_origin}{raw_url}"
        return f"{supabase_origin}/{raw_url}"

    # ── Call the single-object endpoint ────────────────────────────────
    try:
        response = requests.post(
            signed_url_endpoint, json=request_body,
            headers=headers, timeout=60,
        )
        raw_url = _extract_signed_url(response)
        if raw_url:
            full_url = _make_absolute(raw_url)
            logger.info("SIGNED URL SUCCESS: %s", full_url)
            return full_url
    except requests.RequestException as e:
        logger.warning("Signed URL network error: %s", e)

    raise HTTPException(status_code=502, detail="Failed to generate document access URL.")


# ═══════════════════════════════════════════════════════════════════════
# Download File as Bytes (for ZIP bulk download)
# ═══════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════
# List Storage Objects
# ═══════════════════════════════════════════════════════════════════════

def list_storage_objects(prefix: str = "", limit: int = 100) -> list[dict]:
    """List objects in the bucket with the given prefix. Returns [{name, id, ...}]."""
    if settings.ENVIRONMENT in ("development", "test") or not settings.SUPABASE_URL or "dummy" in settings.SUPABASE_URL:
        return []

    prefix = normalize_storage_path(prefix)

    url = f"{settings.SUPABASE_URL}/storage/v1/object/list/{settings.SUPABASE_BUCKET}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

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
            logger.info("LIST '%s': found %d objects", list_prefix, len(items))
            return items
        else:
            logger.warning("LIST '%s' failed: status=%s body=%s", list_prefix, resp.status_code, resp.text[:200])
            return []
    except Exception as e:
        logger.warning("LIST '%s' error: %s", list_prefix, e)
        return []


# ═══════════════════════════════════════════════════════════════════════
# Module 6 — Storage Path Diagnostics
# ═══════════════════════════════════════════════════════════════════════

def diagnose_storage_path(storage_path: str) -> dict:
    """
    Full storage path diagnostics.

    Compares the database ``storage_path`` with actual bucket contents.
    Never raises — returns a dict with all findings, including
    normalised path, prefix-removal status, and signed URL verification.
    """
    raw_path = storage_path.strip()
    normalised_path = normalize_storage_path(raw_path)
    supabase_origin = settings.SUPABASE_URL
    bucket = settings.SUPABASE_BUCKET

    result = {
        "bucket": bucket,
        "db_storage_path": raw_path,
        "normalized_storage_path": normalised_path,
        "bucket_prefix_removed": raw_path.startswith(f"{bucket}/"),
        "supabase_url": supabase_origin.replace(settings.SUPABASE_KEY, "***") if settings.SUPABASE_KEY else supabase_origin,
        "errors": [],
    }

    if settings.ENVIRONMENT in ("development", "test") or not supabase_origin or "dummy" in supabase_origin:
        result["error"] = "SUPABASE_URL not configured"
        return result

    # Use the normalised path for all lookups
    path_parts = normalised_path.split("/")
    result["filename"] = path_parts[-1] if path_parts else normalised_path
    result["parent_dir"] = "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""

    # ── 1. Bucket reachability + root objects ─────────────────────────
    try:
        root_items = list_storage_objects(prefix="", limit=200)
        result["bucket_reachable"] = True
        root_names = [item.get("name", "") for item in root_items]
        result["all_root_objects"] = root_names
        first_segment = path_parts[0] if path_parts else ""
        result["first_segment"] = first_segment
        result["first_segment_exists"] = (
            first_segment in root_names
            or any(n.startswith(first_segment) for n in root_names)
        )
    except Exception as e:
        result["bucket_reachable"] = False
        result["errors"].append(f"Bucket ping failed: {e}")

    # ── 2. Walk path segments ─────────────────────────────────────────
    current_prefix = ""
    result["path_segment_verification"] = []
    for segment in path_parts:
        try:
            items = list_storage_objects(prefix=current_prefix, limit=200)
            item_names = [item.get("name", "") for item in items]
            result["path_segment_verification"].append({
                "prefix": f"{current_prefix}{segment}/",
                "items_found": item_names,
                "segment": segment,
                "segment_matches": segment in item_names or any(n == segment for n in item_names),
            })
            current_prefix = f"{current_prefix}{segment}/"
        except Exception as e:
            result["path_segment_verification"].append({
                "prefix": f"{current_prefix}{segment}/",
                "error": str(e),
            })

    # ── 3. List objects in the target folder ───────────────────────────
    parent_dir = result["parent_dir"]
    if parent_dir:
        try:
            dir_items = list_storage_objects(prefix=parent_dir, limit=200)
            raw_names = [item.get("name", "") for item in dir_items]
            result["objects_in_folder_raw"] = raw_names
            result["object_exists"] = result["filename"] in raw_names
        except Exception as e:
            result["errors"].append(f"File list failed: {e}")

    # ── 4. Generate signed URL and verify ──────────────────────────────
    try:
        signed_url = generate_signed_url(normalised_path, expires_in=120)
        result["signed_url_generated"] = True
        result["signed_url"] = signed_url

        try:
            head_resp = requests.head(signed_url, timeout=10)
            result["signed_url_status"] = head_resp.status_code
            result["signed_url_headers"] = dict(head_resp.headers)

            if head_resp.status_code != 200:
                get_resp = requests.get(signed_url, headers={"Range": "bytes=0-0"}, timeout=10)
                result["signed_url_range_status"] = get_resp.status_code
                result["signed_url_range_body"] = get_resp.text[:500]
        except requests.RequestException as e:
            result["signed_url_verify_error"] = str(e)
    except Exception as e:
        result["signed_url_generated"] = False
        result["signed_url_error"] = str(e)

    return result
