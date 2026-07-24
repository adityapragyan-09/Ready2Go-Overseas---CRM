"""
Ready2Go CRM — Document Repository (DB Layer)

Pure database operations for the ``documents`` table.
No business logic, no storage calls, no HTTP.
"""

import logging
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.errors.document_errors import DocumentError, doc_not_found
from app.models.document import Document

logger = logging.getLogger(__name__)

_CODE_PREFIX = "DOC"


class DocumentRepository:
    """All database access for Document records."""

    def __init__(self, db: Session):
        self.db = db

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_id(self, doc_id: int, include_deleted: bool = False) -> Document:
        """Fetch a document by ID. Raises ``DOCUMENT_NOT_FOUND`` if missing."""
        q = self.db.query(Document).filter(Document.id == doc_id)
        if not include_deleted:
            q = q.filter(Document.is_deleted == False)  # noqa: E712
        doc = q.first()
        if not doc:
            raise doc_not_found(doc_id)
        return doc

    def list_by_applicant(self, applicant_id: int) -> Sequence[Document]:
        """Return all active documents for an applicant, newest first."""
        return (
            self.db.query(Document)
            .filter(Document.applicant_id == applicant_id, Document.is_deleted == False)  # noqa: E712
            .order_by(Document.uploaded_at.desc())
            .all()
        )

    def list_deleted_by_applicant(self, applicant_id: int) -> Sequence[Document]:
        """Return soft-deleted documents for an applicant."""
        return (
            self.db.query(Document)
            .filter(Document.applicant_id == applicant_id, Document.is_deleted == True)  # noqa: E712
            .order_by(Document.deleted_at.desc())
            .all()
        )

    def count_by_applicant(self, applicant_id: int) -> int:
        """Count active documents for an applicant."""
        return (
            self.db.query(Document)
            .filter(Document.applicant_id == applicant_id, Document.is_deleted == False)  # noqa: E712
            .count()
        )

    # ── Mutations ────────────────────────────────────────────────────

    def _next_code(self) -> str:
        """Generate the next document code (DOC-000001 format)."""
        max_id = self.db.query(func.max(Document.id)).scalar()
        return f"{_CODE_PREFIX}-{(max_id or 0) + 1:06d}"

    def create(
        self,
        *,
        applicant_id: int,
        document_type: str,
        original_name: str,
        stored_name: str,
        storage_path: str,
        mime_type: str,
        file_extension: str,
        file_size: int,
        uploaded_by: int,
    ) -> Document:
        """Insert a new document record and return it."""
        doc = Document(
            document_code=self._next_code(),
            applicant_id=applicant_id,
            document_type=document_type,
            original_file_name=original_name,
            stored_file_name=stored_name,
            storage_path=storage_path,
            mime_type=mime_type,
            file_extension=file_extension,
            file_size=file_size,
            uploaded_by=uploaded_by,
        )
        self.db.add(doc)
        self.db.flush()
        self.db.refresh(doc)
        logger.info("DB CREATED: id=%s code=%s path='%s'", doc.id, doc.document_code, storage_path)
        return doc

    def soft_delete(self, doc: Document, deleted_by: int) -> Document:
        """Mark a document as deleted."""
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        doc.deleted_by = deleted_by
        self.db.flush()
        self.db.refresh(doc)
        logger.info("DB SOFT-DELETED: id=%s by user=%s", doc.id, deleted_by)
        return doc

    def restore(self, doc: Document) -> Document:
        """Restore a soft-deleted document."""
        doc.is_deleted = False
        doc.deleted_at = None
        doc.deleted_by = None
        self.db.flush()
        self.db.refresh(doc)
        logger.info("DB RESTORED: id=%s", doc.id)
        return doc

    def update_path(self, doc: Document, new_storage_path: str) -> Document:
        """Update the storage_path (used by migration script)."""
        old = doc.storage_path
        doc.storage_path = new_storage_path
        self.db.flush()
        self.db.refresh(doc)
        logger.info("DB PATH UPDATED: id=%s '%s' → '%s'", doc.id, old, new_storage_path)
        return doc

    def commit(self):
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.db.rollback()
