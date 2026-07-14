"""
Ready2Go CRM — Progress Tracking Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ProgressHistoryResponse(BaseModel):
    """Schema representing a single progress timeline event."""
    id: int
    applicant_id: int
    previous_status: str | None = None
    current_status: str
    remarks: str
    updated_by: int
    updated_at: datetime
    is_system_generated: bool
    updated_by_name: str = Field(default="System", description="Name of user who updated status")

    model_config = {"from_attributes": True}


class StatusUpdatePayload(BaseModel):
    """Schema for updating applicant status."""
    status: str = Field(..., min_length=2, max_length=30, description="New workflow status")
    remarks: str = Field(..., min_length=2, description="Remarks or details for the update")


class NoteCreatePayload(BaseModel):
    """Schema for adding additional remarks to progress history without changing status."""
    applicant_id: int = Field(..., description="ID of the applicant")
    remarks: str = Field(..., min_length=2, description="Additional remark content")
