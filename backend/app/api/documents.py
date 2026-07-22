"""
Ready2Go CRM — Document Management Routes

Router: /api/v1/documents
Access Level: Authenticated Users (JWT required)

Endpoints:
    POST   /upload                                    — Upload a new document
    GET    /applicant/{applicant_id}                   — List documents for an applicant
    GET    /applicant/{applicant_id}/download-all      — Download all docs as ZIP
    GET    /{document_id}/download                     — Get signed download URL
    GET    /{document_id}/view                         — Get signed view URL
    DELETE /{document_id}                              — Soft-delete a document
"""

import io
import zipfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentDownloadResponse, DocumentResponse, DocumentViewResponse
from app.services.document_service import (
    create_document,
    generate_document_download,
    get_document_by_id,
    list_applicant_documents,
    soft_delete_document,
)
from app.services.storage_service import download_file_as_bytes, generate_signed_url
from app.utils.response import success_response

router = APIRouter()


# ── POST /upload ─────────────────────────────────

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document_route(
    file: UploadFile = File(...),
    applicant_id: int = Form(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and register a new applicant document.
    Validates file extension (PDF, JPG, JPEG, PNG, DOC, DOCX) and size (max 500MB).
    """
    # Dynamically determine file size without reading bytes into RAM
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    document = create_document(
        db,
        file=file,
        file_size=file_size,
        applicant_id=applicant_id,
        document_type=document_type,
        uploaded_by=current_user.id,
    )
    
    document_data = DocumentResponse.model_validate(document).model_dump(by_alias=True)
    return success_response(
        message="Document uploaded successfully.",
        data=document_data,
    )


# ── GET /applicant/{applicant_id} ────────────────

@router.get("/applicant/{applicant_id}")
def list_applicant_documents_route(
    applicant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all active (non-deleted) documents for a specific applicant.
    """
    documents = list_applicant_documents(db, applicant_id)
    documents_data = [
        DocumentResponse.model_validate(doc).model_dump(by_alias=True)
        for doc in documents
    ]
    
    return success_response(
        message="Applicant documents retrieved successfully.",
        data=documents_data,
    )


# ── GET /{document_id}/download ──────────────────

@router.get("/{document_id}/download")
def download_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a secure, temporary signed download URL for a document.
    """
    signed_url = generate_document_download(db, document_id)
    # Fetch document metadata for response body
    document = get_document_by_id(db, document_id)

    download_data = DocumentDownloadResponse(
        document_code=document.document_code,
        original_file_name=document.original_file_name,
        download_url=signed_url,
    ).model_dump()
    
    return success_response(
        message="Document download URL generated successfully.",
        data=download_data,
    )


# ── GET /{document_id}/view ──────────────────────

@router.get("/{document_id}/view")
def view_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a secure, temporary signed view URL for a document.
    """
    signed_url = generate_document_download(db, document_id)
    # Fetch document metadata for response body
    from app.services.document_service import get_document_by_id
    document = get_document_by_id(db, document_id)
    
    view_data = DocumentViewResponse(
        document_code=document.document_code,
        original_file_name=document.original_file_name,
        view_url=signed_url,
    ).model_dump()
    
    return success_response(
        message="Document view URL generated successfully.",
        data=view_data,
    )


# ── GET /applicant/{applicant_id}/download-all ───

@router.get("/applicant/{applicant_id}/download-all")
def download_all_documents_route(
    applicant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download all active documents for an applicant as a ZIP archive.
    """
    from app.models.applicant import Applicant
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found.")

    documents = list_applicant_documents(db, applicant_id)
    if not documents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No documents available for this applicant.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in documents:
            try:
                signed_url = generate_signed_url(doc.storage_path, expires_in=300)
                file_bytes = download_file_as_bytes(signed_url)
                arcname = f"{doc.document_type}/{doc.original_file_name}"
                zf.writestr(arcname, file_bytes)
            except Exception:
                # Skip files that can't be downloaded
                continue

    zip_buffer.seek(0)
    filename = f"{applicant.full_name.replace(' ', '_')}_documents.zip"

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── DELETE /{document_id} ────────────────────────

@router.delete("/{document_id}")
def delete_document_route(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a document record.
    """
    document = soft_delete_document(db, document_id, deleted_by=current_user.id)
    
    return success_response(
        message=f"Document '{document.original_file_name}' deleted successfully.",
    )
