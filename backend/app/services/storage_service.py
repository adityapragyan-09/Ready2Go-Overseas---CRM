"""
Ready2Go CRM — Supabase Storage REST Client Service

Handles raw HTTP communications with Supabase Storage API for uploading,
deleting, and signing download links for applicant documents.
"""

import logging
import os
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
    """Resolve a local file path and guard against directory traversal.

    Raises HTTPException 400 if the resolved path escapes the upload directory.
    """
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
    Returns the public access URL of the uploaded asset.
    """
    # Local filesystem fallback allowed only outside production.
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

    try:
        response = requests.post(url, data=file_data, headers=headers, timeout=settings.UPLOAD_TIMEOUT_SECONDS)
        if response.status_code != 200:
            logger.error(
                "Supabase upload failed [status=%s url=%s bucket=%s path=%s] response=%s",
                response.status_code,
                settings.SUPABASE_URL,
                settings.SUPABASE_BUCKET,
                storage_path,
                response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed. Check SUPABASE_URL and SUPABASE_KEY configuration.",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="File upload to storage failed. Please try again later.",
            )
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{storage_path}"
    except requests.RequestException as e:
        logger.exception("Storage upload network error for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable. Please try again later.",
        )


def delete_file(storage_path: str) -> None:
    """
    Remove a file from the Supabase Storage bucket.
    """
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

    try:
        response = requests.delete(url, json={"prefixes": [storage_path]}, headers=headers, timeout=60)
        if response.status_code not in (200, 204):
            logger.error(
                "Supabase delete failed [status=%s path=%s] response=%s",
                response.status_code,
                storage_path,
                response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed. Check SUPABASE_URL and SUPABASE_KEY configuration.",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="File deletion from storage failed.",
            )
    except requests.RequestException as e:
        logger.exception("Storage delete network error for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable.",
        )


def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary, secure signed URL to retrieve a file from private storage.
    """
    if settings.ENVIRONMENT != "production" and (
        not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "dummy" in settings.SUPABASE_URL or "dummy" in settings.SUPABASE_KEY
    ):
        _safe_local_path(storage_path)
        return f"http://localhost:8000/uploads/{storage_path}"

    url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{settings.SUPABASE_BUCKET}/{storage_path}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    try:
        response = requests.post(url, json={"expiresIn": expires_in}, headers=headers, timeout=60)
        if response.status_code != 200:
            logger.error(
                "Supabase signed URL failed [status=%s path=%s] response=%s",
                response.status_code,
                storage_path,
                response.text,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Storage authentication failed. Check SUPABASE_URL and SUPABASE_KEY configuration.",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to generate document access URL.",
            )
        data = response.json()
        signed_url = data.get("signedURL") or data.get("signedUrl")
        if not signed_url:
            logger.error("Supabase signed URL response missing signedURL field: %s", data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Storage service returned an unexpected response.",
            )

        if signed_url.startswith("/"):
            signed_url = f"{settings.SUPABASE_URL}{signed_url}"

        return signed_url
    except requests.RequestException as e:
        logger.exception("Storage signed URL network error for path %s", storage_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service is currently unavailable.",
        )
