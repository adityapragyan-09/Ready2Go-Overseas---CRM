"""
Ready2Go CRM — Document Management Routes (v2)

Router: /api/v1/documents

Architecture:
    Router → DocumentService → StorageService
          ↳ DocumentRepository (via DocumentService)

Every request goes through DocumentService.
No router calls StorageService or DB directly.
"""

import io
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.errors.document_errors import DocumentError
from app.models.applicant import Applicant
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> DocumentService:
    """Factory: inject DocumentRepository into DocumentService."""
    repo = DocumentRepository(db)
    return DocumentService(repo)


# ═══════════════════════════════════════════════════════════════════════
# POST /upload
# ═══════════════════════════════════════════════════════════════════════

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document_route(
    file: UploadFile = File(...),
    applicant_id: int = Form(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """
    Upload a document for an applicant.

    Validates file type, size, and applicant. Uploads to Supabase Storage,
    verifies the object exists, then persists the DB record.
    """
    # Validate applicant exists
    applicant = db.query(Applicant).filter(
        Applicant.id == applicant_id, Applicant.is_deleted == False  # noqa: E712
    ).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found.")

    # Get file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    try:
        document_data = svc.upload(
            file=file,
            file_size=file_size,
            applicant_id=applicant_id,
            document_type=document_type,
            uploaded_by=current_user.id,
            applicant_code=applicant.applicant_code,
        )
        logger.info(
            "UPLOAD: user=%s applicant=%s doc=%s type=%s path='%s' size=%s",
            current_user.id, applicant_id, document_data["document_code"],
            document_type, document_data["storage_path"], file_size,
        )
        return success_response("Document uploaded successfully.", data=document_data)
    except DocumentError as e:
        logger.error("UPLOAD ERROR: %s — %s", e.code, e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message, headers={"X-Error-Code": e.code})


# ═══════════════════════════════════════════════════════════════════════
# GET /applicant/{applicant_id}  — List documents for an applicant
# ═══════════════════════════════════════════════════════════════════════

@router.get("/applicant/{applicant_id}")
def list_applicant_documents_route(
    applicant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """List all active documents for an applicant."""
    docs = svc.list_by_applicant(applicant_id)
    return success_response("Documents retrieved successfully.", data=docs)


# ═══════════════════════════════════════════════════════════════════════
# GET /applicant/{applicant_id}/deleted  — List deleted documents
# ═══════════════════════════════════════════════════════════════════════

@router.get("/applicant/{applicant_id}/deleted")
def list_deleted_documents_route(
    applicant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """List soft-deleted documents for an applicant (admin)."""
    docs = svc.list_deleted_by_applicant(applicant_id)
    return success_response("Deleted documents retrieved successfully.", data=docs)


# ═══════════════════════════════════════════════════════════════════════
# GET /applicant/{applicant_id}/download-all  — ZIP download
# ═══════════════════════════════════════════════════════════════════════

@router.get("/applicant/{applicant_id}/download-all")
def download_all_documents_route(
    applicant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Download all active documents for an applicant as a ZIP archive."""
    try:
        result = svc.download_zip(applicant_id)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return StreamingResponse(
        io.BytesIO(result["zip_bytes"]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
    )


# ═══════════════════════════════════════════════════════════════════════
# GET /{document_id}  — Get document metadata
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{document_id}")
def get_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Get document metadata by ID."""
    try:
        data = svc.get_metadata(document_id)
        return success_response("Document retrieved successfully.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════
# GET /{document_id}/view  — Generate signed view URL
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{document_id}/view")
def view_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Generate a secure, temporary signed view URL."""
    try:
        data = svc.get_view_url(document_id)
        logger.info(
            "VIEW: id=%s code=%s path='%s' url=%s",
            document_id, data["document_code"], "",
            data["view_url"][:80] + "..." if len(data["view_url"]) > 80 else data["view_url"],
        )
        return success_response("View URL generated successfully.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════
# GET /{document_id}/download  — Generate signed download URL
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{document_id}/download")
def download_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Generate a secure, temporary signed download URL."""
    try:
        data = svc.get_download_url(document_id)
        logger.info(
            "DOWNLOAD: id=%s code=%s file='%s'",
            document_id, data["document_code"], data["original_file_name"],
        )
        return success_response("Download URL generated successfully.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════
# DELETE /{document_id}  — Soft-delete
# ═══════════════════════════════════════════════════════════════════════

@router.delete("/{document_id}")
def delete_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Soft-delete a document."""
    try:
        data = svc.delete(document_id, deleted_by=current_user.id)
        return success_response(f"Document '{data['original_file_name']}' deleted successfully.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════
# PATCH /{document_id}/restore  — Restore soft-deleted document
# ═══════════════════════════════════════════════════════════════════════

@router.patch("/{document_id}/restore")
def restore_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Restore a soft-deleted document."""
    try:
        data = svc.restore(document_id)
        return success_response(f"Document '{data['original_file_name']}' restored successfully.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════
# GET /{document_id}/diagnose  — Storage diagnostics
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{document_id}/diagnose")
def diagnose_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_get_service),
):
    """Run full storage diagnostics for a document."""
    try:
        data = svc.diagnose(document_id)
        return success_response("Storage diagnostics completed.", data=data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
