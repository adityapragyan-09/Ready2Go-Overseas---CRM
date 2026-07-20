"""
Ready2Go CRM — Lead Inquiry Schemas
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.constants.lead_inquiry import ALL_SOURCES, ALL_STATUSES


class LeadInquiryCreate(BaseModel):
    """Schema for creating a new lead inquiry."""
    full_name: str = Field(..., min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    visa_type: str = Field(default="student", max_length=30)
    preferred_country: str | None = Field(default=None, max_length=100)
    message: str | None = Field(default=None)
    source: str = Field(default="WEBSITE", max_length=30)
    assigned_employee_id: int | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        if v.upper() not in [s.upper() for s in ALL_SOURCES]:
            raise ValueError(f"Invalid source. Allowed: {', '.join(ALL_SOURCES)}")
        return v.upper()

    @field_validator("visa_type")
    @classmethod
    def validate_visa_type(cls, v: str) -> str:
        allowed = ["student", "visit", "tourist", "business"]
        if v.lower() not in allowed:
            raise ValueError(f"Invalid visa type. Allowed: {', '.join(allowed)}")
        return v.lower()


class LeadInquiryUpdate(BaseModel):
    """Schema for updating an existing lead inquiry."""
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    visa_type: str | None = Field(default=None, max_length=30)
    preferred_country: str | None = Field(default=None, max_length=100)
    message: str | None = None
    source: str | None = Field(default=None, max_length=30)
    assigned_employee_id: int | None = None


class LeadInquiryStatusUpdate(BaseModel):
    """Schema for updating lead status."""
    status: str = Field(..., max_length=30)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v.upper() not in [s.upper() for s in ALL_STATUSES]:
            raise ValueError(f"Invalid status. Allowed: {', '.join(ALL_STATUSES)}")
        return v.upper()


class LeadInquiryAssign(BaseModel):
    """Schema for assigning a lead to an employee."""
    employee_id: int


class LeadInquiryResponse(BaseModel):
    """Lead inquiry data returned in API responses."""
    id: int
    uuid: str
    lead_number: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    visa_type: str
    preferred_country: str | None = None
    message: str | None = None
    source: str
    status: str
    assigned_employee_id: int | None = None
    converted_to_applicant: bool = False
    assigned_employee_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadInquiryListResponse(BaseModel):
    """Paginated list of lead inquiries."""
    total: int
    page: int
    page_size: int
    total_pages: int
    leads: list[LeadInquiryResponse]
