"""
Ready2Go CRM — Storage Interface

Exposes the BaseStorage interface and the factory function to get the
configured storage client.
"""

from abc import ABC, abstractmethod
from fastapi import UploadFile


class BaseStorage(ABC):
    """Abstract base class defining the storage backend interface."""

    @abstractmethod
    async def save_file(self, file: UploadFile, folder: str = "") -> str:
        """
        Save an uploaded file to the storage backend.

        Args:
            file: The Starlette/FastAPI UploadFile object.
            folder: Subfolder path inside the storage.

        Returns:
            The unique file path or URL of the stored file.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from the storage backend.

        Args:
            file_path: The file path or URL of the file to delete.

        Returns:
            True if deletion succeeded, False otherwise.
        """
        pass
