"""
Ready2Go CRM — Lead Advisor Notes Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field


class LeadNoteCreate(BaseModel):
    """Schema for creating a new lead note."""
    note: str = Field(..., min_length=1, max_length=5000)


class LeadNoteUpdate(BaseModel):
    """Schema for updating an existing lead note."""
    note: str = Field(..., min_length=1, max_length=5000)


class LeadNoteResponse(BaseModel):
    """Lead note data returned in API responses."""
    id: int
    uuid: str
    lead_id: int
    note: str
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
