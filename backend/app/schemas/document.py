"""
Ready2Go CRM — Document Schemas

Pydantic models for Document metadata serialization and validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field


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
    uploaded_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentDownloadResponse(BaseModel):
    """Signed URL response for downloading a secure document."""
    document_code: str
    original_file_name: str
    download_url: str


class DocumentViewResponse(BaseModel):
    """Signed URL response for viewing a secure document."""
    document_code: str
    original_file_name: str
    view_url: str


