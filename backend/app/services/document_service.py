"""
Ready2Go CRM — Document Service

Business logic for document management: uploads, listings, signed URL downloads,
validations (type/size), file-collision prevention, and soft deletes.
"""

import logging
import uuid

logger = logging.getLogger(__name__)
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants.document_types import ALL_DOCUMENT_TYPES
from app.core.config import settings
from app.models.applicant import Applicant
from app.models.document import Document
from app.services.storage_service import upload_file, delete_file, generate_signed_url

# ── Validations ──────────────────────────────────

_CODE_PREFIX = "DOC"


def _generate_document_code(db: Session) -> str:
    """Generate sequential unique document code (DOC-000001 format)."""
    max_id = db.query(func.max(Document.id)).scalar()
    next_num = (max_id or 0) + 1
    return f"{_CODE_PREFIX}-{next_num:06d}"


def _active_query(db: Session):
    """Base query pre-filtered to exclude soft-deleted documents."""
    return db.query(Document).filter(Document.is_deleted == False)  # noqa: E712


# ── Upload Document ──────────────────────────────

def create_document(
    db: Session,
    *,
    file: UploadFile,
    file_size: int,
    applicant_id: int,
    document_type: str,
    uploaded_by: int,
) -> Document:
    """
    Validate, process, upload, and save a document.
    
    Validations:
        - Allowed file extension (PDF, JPG, JPEG, PNG, DOC, DOCX)
        - Max file size (500 MB)
        - Valid applicant_id
        - Valid document_type
    """
    # 1. Validate Applicant
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active applicant with ID {applicant_id} does not exist."
        )

    # 2. Validate Document Type
    if document_type not in ALL_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type '{document_type}'. Allowed: {', '.join(ALL_DOCUMENT_TYPES)}"
        )

    # 3. Validate File Extension
    original_name = file.filename or "unknown"
    ext = Path(original_name).suffix.lower()
    if ext not in settings.ALLOWED_DOCUMENT_TYPES_SET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' not allowed. Allowed: {', '.join(settings.ALLOWED_DOCUMENT_TYPES_LIST)}"
        )

    # 4. Validate File Size
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum upload size is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # 5. Prevent Collisions & Generate Unique Stored Filename
    unique_stored_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"applicants/{applicant.applicant_code}/{unique_stored_name}"

    # 6. Upload to Supabase Storage
    # Falls back to application/octet-stream if mime_type is missing
    mime_type = file.content_type or "application/octet-stream"
    storage_path_from_storage = upload_file(file.file, storage_path, mime_type)

    # If Supabase returned a different path (e.g., normalized), use that instead
    if storage_path_from_storage and storage_path_from_storage != storage_path:
        logger.warning(
            "STORAGE PATH CORRECTED: '%s' → '%s' (from Supabase response Key)",
            storage_path, storage_path_from_storage,
        )
        stored_file_name = Path(storage_path_from_storage).name
        storage_path = storage_path_from_storage
    else:
        stored_file_name = unique_stored_name

    # Verify the file exists in Supabase Storage (best-effort)
    try:
        from app.services.storage_service import list_storage_objects
        parent = "/".join(storage_path.split("/")[:-1])
        objects = list_storage_objects(prefix=parent, limit=50)
        names = [o.get("name", "") for o in objects]
        uploaded_file_name = storage_path.split("/")[-1]
        if uploaded_file_name not in names:
            logger.error(
                "UPLOAD VERIFICATION FAILED: file '%s' not found in bucket '%s' "
                "under prefix '%s'. Found objects: %s. Storage path in DB: %s",
                uploaded_file_name, settings.SUPABASE_BUCKET, parent,
                names, storage_path,
            )
        else:
            logger.info(
                "UPLOAD VERIFICATION OK: '%s' found at '%s' in bucket '%s'",
                uploaded_file_name, parent, settings.SUPABASE_BUCKET,
            )
    except Exception as exc:
        logger.warning("Upload verification skipped (non-fatal): %s", exc)

    # 7. Save to Database
    doc_code = _generate_document_code(db)
    document = Document(
        document_code=doc_code,
        applicant_id=applicant_id,
        document_type=document_type,
        original_file_name=original_name,
        stored_file_name=stored_file_name,
        storage_path=storage_path,
        mime_type=mime_type,
        file_extension=ext.lstrip("."),
        file_size=file_size,
        uploaded_by=uploaded_by,
    )

    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        # Attempt to remove the uploaded storage asset to avoid orphans
        logger.exception("Failed to save document record. Cleaning up storage path %s.", storage_path)
        try:
            delete_file(storage_path)
        except Exception:
            pass
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document record.")

    # Log document upload system message
    from app.services.chat_service import log_system_message
    doc_lbl = document.document_type.replace('_', ' ').title()
    log_system_message(
        db,
        applicant_id=document.applicant_id,
        content=f"Document '{document.original_file_name}' (type: {doc_lbl}) uploaded successfully.",
        action_by=uploaded_by,
    )

    # Notification trigger: Document uploaded
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Document Uploaded",
            message=f"'{document.original_file_name}' uploaded for applicant {applicant.full_name}.",
            type="success",
            module="document",
            priority="medium",
            recipient_user_id=uploaded_by,
            created_by=uploaded_by,
            reference_type="document",
            reference_id=document.id,
        )
    except Exception:
        logger.exception("Failed to send upload notification for document %s.", document.id if document else None)

    return document


# ── List Applicant Documents ────────────────────

def list_applicant_documents(db: Session, applicant_id: int) -> list[Document]:
    """Retrieve all active (non-deleted) documents for a given applicant."""
    return (
        _active_query(db)
        .filter(Document.applicant_id == applicant_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


# ── Retrieve Document ────────────────────────────

def get_document_by_id(db: Session, document_id: int) -> Document:
    """Fetch single active document by ID or raise 404."""
    document = _active_query(db).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has been deleted."
        )
    return document


# ── Secure Download Link ─────────────────────────

def generate_document_download(db: Session, document_id: int, expires_in: int = 3600) -> str:
    """Generate temporary secure signed download URL for the document."""
    document = get_document_by_id(db, document_id)
    return generate_signed_url(document.storage_path, expires_in)


# ── Soft Delete Document ─────────────────────────

def soft_delete_document(db: Session, document_id: int, deleted_by: int) -> Document:
    """Soft delete document in metadata DB. The storage asset is retained for recovery."""
    document = get_document_by_id(db, document_id)

    document.is_deleted = True
    document.deleted_at = datetime.now(timezone.utc)
    document.deleted_by = deleted_by

    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        logger.exception("Failed to soft-delete document %s.", document_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document.")

    # Notification trigger: Document deleted
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Document Deleted",
            message=f"Document '{document.original_file_name}' has been soft-deleted.",
            type="warning",
            module="document",
            priority="medium",
            recipient_user_id=deleted_by,
            created_by=deleted_by,
            reference_type="document",
            reference_id=document.id,
        )
    except Exception:
        logger.exception("Failed to send document deletion notification for document %s.", document_id)

    return document
