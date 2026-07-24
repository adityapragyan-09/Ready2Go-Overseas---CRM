"""
Ready2Go CRM — Enterprise Document Service (v2)

Business logic for document management.
Orchestrates StorageService and DocumentRepository.
No direct DB queries. No direct Supabase calls.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings
from app.errors.document_errors import (
    DocumentError,
    doc_not_found,
    object_not_found,
    signed_url_failed,
    upload_failed,
    INVALID_FILE_TYPE,
    FILE_TOO_LARGE,
    VERIFICATION_FAILED,
)
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import (
    upload_file as storage_upload,
    generate_signed_url as storage_sign,
    delete_file as storage_delete,
    verify_file_exists as storage_verify,
    list_folder as storage_list,
    create_zip as storage_zip,
    diagnose_path as storage_diagnose,
)
from app.constants.document_types import ALL_DOCUMENT_TYPES

logger = logging.getLogger(__name__)


class DocumentService:
    """Enterprise document management business logic."""

    def __init__(self, repo: DocumentRepository):
        self.repo = repo

    # ═══════════════════════════════════════════════════════════════════
    # Upload
    # ═══════════════════════════════════════════════════════════════════

    def upload(
        self,
        *,
        file: UploadFile,
        file_size: int,
        applicant_id: int,
        document_type: str,
        uploaded_by: int,
        applicant_code: str,
    ) -> dict:
        """
        Full upload workflow:
          1. Validate applicant, type, extension, size
          2. Upload to storage
          3. Verify object exists
          4. Save DB record
          5. Return document data

        On verification failure: rollback DB, delete storage object, raise 500.
        """
        # 1. Validate document type
        if document_type not in ALL_DOCUMENT_TYPES:
            raise DocumentError(INVALID_FILE_TYPE, f"Invalid document type '{document_type}'.", 400)

        # 2. Validate file extension
        original_name = file.filename or "unknown"
        ext = Path(original_name).suffix.lower()
        if ext not in settings.ALLOWED_DOCUMENT_TYPES_SET:
            raise DocumentError(INVALID_FILE_TYPE, f"Extension '{ext}' not allowed.", 400)

        # 3. Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise DocumentError(FILE_TOO_LARGE, f"Max upload size is {settings.MAX_UPLOAD_SIZE_MB} MB.", 400)

        # 4. Build storage path
        unique_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = f"applicants/{applicant_code}/{unique_name}"

        # 5. Upload to storage
        mime_type = file.content_type or "application/octet-stream"
        upload_result = storage_upload(file.file, storage_path, mime_type)

        if not upload_result["success"]:
            raise DocumentError("UPLOAD_FAILED", upload_result.get("error", "Upload failed"),
                                upload_result.get("status_code", 500))

        # 6. Use canonical path from storage
        canonical_path = upload_result["data"]["canonical_path"]
        stored_name = Path(canonical_path).name

        # 7. Verify object exists in storage
        verify_result = storage_verify(canonical_path)
        if not verify_result["success"] or not verify_result["data"].get("exists"):
            # Cleanup: delete the orphaned storage object
            storage_delete(canonical_path)
            raise DocumentError(VERIFICATION_FAILED,
                                "Upload verification failed — object not found in storage.", 500)

        # 8. Save DB record
        doc = self.repo.create(
            applicant_id=applicant_id,
            document_type=document_type,
            original_name=original_name,
            stored_name=stored_name,
            storage_path=canonical_path,
            mime_type=mime_type,
            file_extension=ext.lstrip("."),
            file_size=file_size,
            uploaded_by=uploaded_by,
        )
        self.repo.commit()

        logger.info(
            "UPLOAD COMPLETE: id=%s code=%s path='%s' size=%s",
            doc.id, doc.document_code, canonical_path, file_size,
        )
        return self._serialize(doc)

    # ═══════════════════════════════════════════════════════════════════
    # View (generate signed URL)
    # ═══════════════════════════════════════════════════════════════════

    def get_view_url(self, doc_id: int, expires_in: int = 3600) -> dict:
        """Generate a signed view URL for a document."""
        doc = self.repo.get_by_id(doc_id)
        result = storage_sign(doc.storage_path, expires_in)
        if not result["success"]:
            raise signed_url_failed(doc.storage_path)
        return {
            "document_code": doc.document_code,
            "original_file_name": doc.original_file_name,
            "view_url": result["data"]["signed_url"],
            "expires_in": expires_in,
        }

    # ═══════════════════════════════════════════════════════════════════
    # Download (generate signed URL)
    # ═══════════════════════════════════════════════════════════════════

    def get_download_url(self, doc_id: int, expires_in: int = 3600) -> dict:
        """Generate a signed download URL for a document."""
        doc = self.repo.get_by_id(doc_id)
        result = storage_sign(doc.storage_path, expires_in)
        if not result["success"]:
            raise signed_url_failed(doc.storage_path)
        return {
            "document_code": doc.document_code,
            "original_file_name": doc.original_file_name,
            "download_url": result["data"]["signed_url"],
            "expires_in": expires_in,
        }

    # ═══════════════════════════════════════════════════════════════════
    # List
    # ═══════════════════════════════════════════════════════════════════

    def list_by_applicant(self, applicant_id: int) -> list[dict]:
        """List all active documents for an applicant."""
        docs = self.repo.list_by_applicant(applicant_id)
        return [self._serialize(d) for d in docs]

    def list_deleted_by_applicant(self, applicant_id: int) -> list[dict]:
        """List soft-deleted documents for an applicant."""
        docs = self.repo.list_deleted_by_applicant(applicant_id)
        return [self._serialize(d) for d in docs]

    # ═══════════════════════════════════════════════════════════════════
    # Soft Delete
    # ═══════════════════════════════════════════════════════════════════

    def delete(self, doc_id: int, deleted_by: int) -> dict:
        """Soft-delete a document (storage retained)."""
        doc = self.repo.get_by_id(doc_id)
        doc = self.repo.soft_delete(doc, deleted_by)
        self.repo.commit()
        logger.info("DELETE: id=%s code=%s by=%s", doc_id, doc.document_code, deleted_by)
        return self._serialize(doc)

    # ═══════════════════════════════════════════════════════════════════
    # Restore
    # ═══════════════════════════════════════════════════════════════════

    def restore(self, doc_id: int) -> dict:
        """Restore a soft-deleted document."""
        doc = self.repo.get_by_id(doc_id, include_deleted=True)
        if not doc.is_deleted:
            raise DocumentError("RESTORE_FAILED", f"Document {doc_id} is not deleted.", 400)
        doc = self.repo.restore(doc)
        self.repo.commit()
        logger.info("RESTORE: id=%s code=%s", doc_id, doc.document_code)
        return self._serialize(doc)

    # ═══════════════════════════════════════════════════════════════════
    # ZIP Download
    # ═══════════════════════════════════════════════════════════════════

    def download_zip(self, applicant_id: int) -> dict:
        """Generate a ZIP archive of all active documents for an applicant."""
        docs = self.repo.list_by_applicant(applicant_id)
        if not docs:
            raise DocumentError("ZIP_FAILED", "No documents available for this applicant.", 404)

        files = []
        for doc in docs:
            sign_result = storage_sign(doc.storage_path, expires_in=300)
            if sign_result["success"]:
                files.append({
                    "signed_url": sign_result["data"]["signed_url"],
                    "arcname": f"{doc.document_type}/{doc.original_file_name}",
                    "storage_path": doc.storage_path,
                })

        if not files:
            raise DocumentError("ZIP_FAILED", "No downloadable files available.", 500)

        zip_name = f"applicant_{applicant_id}_documents.zip"
        zip_result = storage_zip(files, zip_name)
        if not zip_result["success"]:
            raise DocumentError("ZIP_FAILED", "Failed to create ZIP archive.", 500)

        return {
            "zip_bytes": zip_result["data"]["zip_bytes"],
            "filename": zip_name,
            "total_files": len(files),
            "errors": zip_result["data"]["errors"],
        }

    # ═══════════════════════════════════════════════════════════════════
    # Get single document metadata
    # ═══════════════════════════════════════════════════════════════════

    def get_metadata(self, doc_id: int) -> dict:
        """Return document metadata."""
        doc = self.repo.get_by_id(doc_id)
        return self._serialize(doc)

    # ═══════════════════════════════════════════════════════════════════
    # Diagnostics
    # ═══════════════════════════════════════════════════════════════════

    def diagnose(self, doc_id: int) -> dict:
        """Run full storage diagnostics for a document."""
        doc = self.repo.get_by_id(doc_id, include_deleted=True)
        result = storage_diagnose(doc.storage_path)
        result["document_id"] = doc.id
        result["document_code"] = doc.document_code
        result["stored_file_name"] = doc.stored_file_name
        result["original_file_name"] = doc.original_file_name
        result["mime_type"] = doc.mime_type
        result["file_size"] = doc.file_size
        result["is_deleted"] = doc.is_deleted
        return result

    # ═══════════════════════════════════════════════════════════════════
    # Serialization
    # ═══════════════════════════════════════════════════════════════════

    def _serialize(self, doc) -> dict:
        return {
            "id": doc.id,
            "document_code": doc.document_code,
            "applicant_id": doc.applicant_id,
            "document_type": doc.document_type,
            "original_file_name": doc.original_file_name,
            "stored_file_name": doc.stored_file_name,
            "storage_path": doc.storage_path,
            "mime_type": doc.mime_type,
            "file_extension": doc.file_extension,
            "file_size": doc.file_size,
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "is_deleted": doc.is_deleted,
            "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
            "deleted_by": doc.deleted_by,
        }
