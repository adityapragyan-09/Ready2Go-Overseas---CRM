"""
Ready2Go CRM — Local Disk Storage Provider

Implementation of BaseStorage that stores files on the local filesystem.
"""

import os
from pathlib import Path
import shutil
from fastapi import UploadFile

from app.core.config import settings
from app.storage import BaseStorage


class LocalStorage(BaseStorage):
    """Local disk storage implementation for development and small deployments."""

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, folder: str = "") -> str:
        # Determine target directory
        target_dir = self.upload_dir / folder if folder else self.upload_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Build unique file name to prevent collisions
        file_name = file.filename or "unnamed_file"
        file_path = target_dir / file_name

        # If file exists, append timestamp or counter to filename
        counter = 1
        stem = Path(file_name).stem
        suffix = Path(file_name).suffix
        while file_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            file_path = target_dir / new_name
            counter += 1

        # Write file chunk by chunk to avoid high memory usage
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative path from backend root (or absolute)
        # Using forward slashes for cross-platform compatibility
        return str(file_path.relative_to(self.upload_dir.parent)).replace("\\", "/")

    async def delete_file(self, file_path: str) -> bool:
        path = Path(file_path)
        # Security check: Ensure we don't delete files outside the upload directory
        try:
            resolved_path = path.resolve()
            resolved_upload_dir = self.upload_dir.resolve()
            if resolved_upload_dir not in resolved_path.parents:
                return False
            
            if resolved_path.exists() and resolved_path.is_file():
                os.remove(resolved_path)
                return True
        except Exception:
            return False
        return False


def get_storage_client() -> BaseStorage:
    """
    Factory function returning the configured storage backend.
    In the future, read 'STORAGE_PROVIDER' from settings to return
    SupabaseStorage, S3Storage, etc.
    """
    return LocalStorage()
