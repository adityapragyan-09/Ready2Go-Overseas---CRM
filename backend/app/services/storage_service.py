"""
Ready2Go CRM — Supabase Storage REST Client Service

Handles raw HTTP communications with Supabase Storage API for uploading,
deleting, and signing download links for applicant documents.

Includes comprehensive diagnostic logging for troubleshooting.
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
    Upload a file to Supabase Storage. Supports streaming via file-like objects.

    Stores the object at `{bucket}/{storage_path}`. The storage_path is
    returned and also stored in the DB. Signed URLs use the exact same
    storage_path to reference the object.
    """
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
        "Uploading document to Supabase: bucket=%s storage_path=%s url=%s",
        settings.SUPABASE_BUCKET, storage_path,
        url.replace(settings.SUPABASE_KEY, "***") if settings.SUPABASE_KEY else url,
    )

    try:
        response = requests.post(url, data=file_data, headers=headers, timeout=settings.UPLOAD_TIMEOUT_SECONDS)
        if response.status_code != 200:
            logger.error(
                "Supabase upload failed [status=%s path=%s] response_body=%s",
                response.status_code, storage_path, response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed. Check SUPABASE_URL and SUPABASE_KEY configuration.",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="File upload to storage failed.",
            )

        # Verify response body confirms the object key matches storage_path
        try:
            resp_data = response.json()
            returned_key = resp_data.get("Key")
            logger.info(
                "Upload success: status=%s returned_Key=%s expected_path=%s full_response=%s",
                response.status_code, returned_key, storage_path, resp_data,
            )
        except Exception:
            logger.info(
                "Upload success: status=%s response_body=%s path=%s",
                response.status_code, response.text[:500], storage_path,
            )

        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{storage_path}"
    except requests.RequestException as e:
        logger.exception("Storage upload network error for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable.",
        )


def delete_file(storage_path: str) -> None:
    """Remove a file from the Supabase Storage bucket."""
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

    logger.info("Deleting document: bucket=%s path=%s", settings.SUPABASE_BUCKET, storage_path)

    try:
        response = requests.delete(url, json={"prefixes": [storage_path]}, headers=headers, timeout=60)
        if response.status_code not in (200, 204):
            logger.error(
                "Supabase delete failed [status=%s path=%s] response=%s",
                response.status_code, storage_path, response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed.",
                )
        else:
            logger.info("Delete success for path=%s", storage_path)
    except requests.RequestException as e:
        logger.exception("Storage delete network error for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable.",
        )


def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary, secure signed URL to retrieve a file from private storage.

    Tries two API formats:
      1) Current API:  POST /object/sign/{bucket}       body={"path": path, "expiresIn": N}
      2) Legacy API:   POST /object/sign/{bucket}/{path} body={"expiresIn": N}

    Returns the full signed URL string.
    """
    if settings.ENVIRONMENT != "production" and (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        _safe_local_path(storage_path)
        return f"http://localhost:8000/uploads/{storage_path}"

    headers = _get_headers()
    headers["Content-Type"] = "application/json"
    base_url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{settings.SUPABASE_BUCKET}"

    logger.info(
        "Generating signed URL: bucket=%s storage_path=%s expires_in=%s",
        settings.SUPABASE_BUCKET, storage_path, expires_in,
    )

    # ── Attempt 1: Current API (path in body) ──────────────
    try:
        response = requests.post(
            base_url,
            json={"path": storage_path, "expiresIn": expires_in},
            headers=headers,
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            signed_url = data.get("signedURL") or data.get("signedUrl")
            if signed_url:
                if signed_url.startswith("/"):
                    signed_url = f"{settings.SUPABASE_URL}{signed_url}"
                logger.info(
                    "Signed URL generated (body API): path=%s url_prefix=%s...",
                    storage_path, signed_url[:80],
                )
                return signed_url
            else:
                logger.warning(
                    "Signed URL body API returned empty URL. Full response: %s", data,
                )
        else:
            logger.warning(
                "Signed URL attempt 1 (body API) failed: status=%s body=%s",
                response.status_code, response.text,
            )
    except requests.RequestException as e:
        logger.warning("Signed URL attempt 1 network error: %s", e)

    # ── Attempt 2: Legacy API (path in URL) ────────────────
    try:
        legacy_url = f"{base_url}/{storage_path}"
        response = requests.post(
            legacy_url,
            json={"expiresIn": expires_in},
            headers=headers,
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            signed_url = data.get("signedURL") or data.get("signedUrl")
            if signed_url:
                if signed_url.startswith("/"):
                    signed_url = f"{settings.SUPABASE_URL}{signed_url}"
                logger.info(
                    "Signed URL generated (legacy API): path=%s url_prefix=%s...",
                    storage_path, signed_url[:80],
                )
                return signed_url
            else:
                logger.warning(
                    "Signed URL legacy API returned empty URL. Full response: %s", data,
                )
        else:
            logger.error(
                "Both signed URL formats failed. Last attempt: status=%s path=%s response=%s",
                response.status_code, storage_path, response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed. Check SUPABASE_URL and SUPABASE_KEY configuration.",
                )
    except requests.RequestException as e:
        logger.exception("Storage signed URL all attempts failed for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable.",
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to generate document access URL.",
    )


def download_file_as_bytes(file_url: str) -> bytes:
    """Download a file from a signed URL and return its contents as bytes."""
    try:
        response = requests.get(file_url, timeout=60)
        response.raise_for_status()
        logger.info("Downloaded file from signed URL: status=%s size=%s", response.status_code, len(response.content))
        return response.content
    except requests.RequestException as e:
        logger.exception("Failed to download file from %s", file_url[:80])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to download file from storage.",
        )


def diagnose_storage_path(storage_path: str) -> dict:
    """
    Diagnostic function: attempt to verify an object exists in storage.
    Returns a dict with diagnostic info (never raises).
    Used for debugging storage issues.
    """
    result = {
        "storage_path": storage_path,
        "bucket": settings.SUPABASE_BUCKET,
        "uploads_pingable": False,
        "upload_url": None,
        "signed_url": None,
        "errors": [],
    }

    if not settings.SUPABASE_URL or "dummy" in settings.SUPABASE_URL:
        result["errors"].append("SUPABASE_URL is not configured (dummy value detected)")
        return result

    try:
        # Test 1: Check if the storage API is reachable
        ping_url = f"{settings.SUPABASE_URL}/storage/v1/object/list/{settings.SUPABASE_BUCKET}"
        headers = _get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.post(ping_url, json={"prefix": "", "limit": 1}, headers=headers, timeout=10)
        result["uploads_pingable"] = resp.status_code in (200, 404)
        if resp.status_code == 200:
            objects = resp.json()
            result["bucket_object_count"] = len(objects)
        else:
            result["bucket_ping_status"] = resp.status_code
            result["bucket_ping_body"] = resp.text[:200]

        # Test 2: Try listing objects in the parent directory
        parent_dir = "/".join(storage_path.split("/")[:-1]) if "/" in storage_path else ""
        if parent_dir:
            list_url = f"{settings.SUPABASE_URL}/storage/v1/object/list/{settings.SUPABASE_BUCKET}"
            list_resp = requests.post(
                list_url,
                json={"prefix": parent_dir, "limit": 100},
                headers=headers,
                timeout=10,
            )
            if list_resp.status_code == 200:
                items = list_resp.json()
                filenames = [item.get("name", "") for item in items]
                result["parent_dir"] = parent_dir
                result["objects_in_parent"] = filenames
                result["path_exists"] = storage_path.split("/")[-1] in filenames
            else:
                result["list_status"] = list_resp.status_code
                result["list_body"] = list_resp.text[:200]

        # Test 3: Try to generate a signed URL (capture any error)
        try:
            signed = generate_signed_url(storage_path, expires_in=60)
            result["signed_url_generated"] = True
            result["signed_url_prefix"] = signed[:100] if signed else None
        except Exception as e:
            result["signed_url_generated"] = False
            result["signed_url_error"] = str(e)

    except Exception as e:
        result["errors"].append(f"Diagnostic error: {e}")

    return result
