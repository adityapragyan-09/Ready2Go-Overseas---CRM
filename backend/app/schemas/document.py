"""
Ready2Go CRM — Document Schemas (v2)

Pydantic models for API serialization and validation.
"""

from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document metadata returned in API responses."""
    id: int
    document_code: str
    applicant_id: int
    document_type: str
    original_file_name: str
    stored_file_name: str
    storage_path: str
    mime_type: str
    file_extension: str
    file_size: int
    uploaded_by: int
    uploaded_at: datetime | None = None
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: int | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentViewResponse(BaseModel):
    """Response for signed view URL."""
    document_code: str
    original_file_name: str
    view_url: str
    expires_in: int = 3600


class DocumentDownloadResponse(BaseModel):
    """Response for signed download URL."""
    document_code: str
    original_file_name: str
    download_url: str
    expires_in: int = 3600


class DocumentUploadResponse(BaseModel):
    """Response after successful upload."""
    id: int
    document_code: str
    applicant_id: int
    document_type: str
    original_file_name: str
    stored_file_name: str
    storage_path: str
    mime_type: str
    file_extension: str
    file_size: int
    uploaded_by: int
    uploaded_at: datetime
