"""
Ready2Go CRM — Applicant Schemas

Pydantic models for the unified applicant CRUD.
Supports all visa types via the visa_type field and metadata JSONB.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.constants import ALL_VISA_TYPES, ALL_STATUSES, INQUIRY


class ApplicantCreate(BaseModel):
    """Schema for creating a new applicant."""
    full_name: str = Field(min_length=1, max_length=150)
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    visa_type: str = Field(pattern=f"^({'|'.join(ALL_VISA_TYPES)})$")
    status: str = Field(default=INQUIRY, pattern=f"^({'|'.join(ALL_STATUSES)})$")
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    notes: str | None = None
    assigned_to: int | None = None

    model_config = {"populate_by_name": True}


class ApplicantUpdate(BaseModel):
    """Schema for updating an existing applicant."""
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    status: str | None = Field(default=None, pattern=f"^({'|'.join(ALL_STATUSES)})$")
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    notes: str | None = None
    assigned_to: int | None = None

    model_config = {"populate_by_name": True}


class ApplicantOut(BaseModel):
    """Applicant data returned in API responses."""
    id: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    visa_type: str
    status: str
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    notes: str | None = None
    assigned_to: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
