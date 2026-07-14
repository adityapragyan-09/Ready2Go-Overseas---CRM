"""
Ready2Go CRM — Supabase Storage REST Client Service

Handles raw HTTP communications with Supabase Storage API for uploading,
deleting, and signing download links for applicant documents.
"""

import requests
from fastapi import HTTPException, status
from app.core.config import settings


def _get_headers(mime_type: str = None) -> dict:
    """Prepare auth and request headers for Supabase Storage."""
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    if mime_type:
        headers["Content-Type"] = mime_type
    return headers


def upload_file(file_data, storage_path: str, mime_type: str) -> str:
    """
    Upload a file to Supabase Storage. Supports streaming via file-like objects.
    Returns the public access URL of the uploaded asset.
    """
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}/{storage_path}"
    headers = _get_headers(mime_type)

    try:
        response = requests.post(url, data=file_data, headers=headers, timeout=600)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase Storage upload failed: {response.text}",
            )
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{storage_path}"
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage service request error: {str(e)}",
        )


def delete_file(storage_path: str) -> None:
    """
    Remove a file from the Supabase Storage bucket.
    """
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    try:
        response = requests.delete(url, json={"prefixes": [storage_path]}, headers=headers, timeout=30)
        if response.status_code not in (200, 204):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase Storage deletion failed: {response.text}",
            )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage service request error: {str(e)}",
        )


def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary, secure signed URL to retrieve a file from private storage.
    """
    url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{settings.SUPABASE_BUCKET}/{storage_path}"
    headers = _get_headers()
    headers["Content-Type"] = "application/json"

    try:
        response = requests.post(url, json={"expiresIn": expires_in}, headers=headers, timeout=30)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase Storage url signature failed: {response.text}",
            )
        data = response.json()
        signed_url = data.get("signedURL") or data.get("signedUrl")
        if not signed_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Signed URL missing in Supabase response.",
            )

        if signed_url.startswith("/"):
            signed_url = f"{settings.SUPABASE_URL}{signed_url}"

        return signed_url
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage service request error: {str(e)}",
        )
