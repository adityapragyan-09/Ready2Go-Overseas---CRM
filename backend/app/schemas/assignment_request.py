"""
Ready2Go CRM — Assignment Request Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field


class AssignmentRequestCreate(BaseModel):
    """Schema for an employee requesting lead assignment."""
    lead_id: int
    remarks: str | None = None


class AssignmentRequestReview(BaseModel):
    """Schema for admin approving/rejecting an assignment request."""
    remarks: str | None = None


class AssignmentRequestResponse(BaseModel):
    """Assignment request data returned in API responses."""
    id: int
    uuid: str
    lead_id: int
    employee_id: int
    status: str
    requested_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: int | None = None
    remarks: str | None = None
    employee_name: str | None = None
    employee_email: str | None = None
    lead_number: str | None = None
    lead_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
