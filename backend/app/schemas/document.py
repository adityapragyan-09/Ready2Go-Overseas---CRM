"""
Ready2Go CRM — Document Schemas

Pydantic models for document upload metadata.
"""

from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    """Document metadata returned in API responses."""
    id: int
    applicant_id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_type: str | None = None
    file_size: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
