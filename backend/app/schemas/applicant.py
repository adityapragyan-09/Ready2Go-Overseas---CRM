"""
Ready2Go CRM — Applicant Schemas

Pydantic models for the unified applicant CRUD.
Supports all visa types via the visa_type field and metadata JSONB.
"""

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.constants import ALL_VISA_TYPES, ALL_STATUSES, INQUIRY


# ── Validators ───────────────────────────────────

_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


# ── Create ───────────────────────────────────────

class ApplicantCreate(BaseModel):
    """Schema for creating a new applicant."""
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=80)
    visa_type: str = Field(pattern=f"^({'|'.join(ALL_VISA_TYPES)})$")
    status: str = Field(default=INQUIRY, pattern=f"^({'|'.join(ALL_STATUSES)})$")
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    notes: str | None = None
    assigned_to: int | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not _PHONE_RE.match(v):
            raise ValueError(
                "Invalid phone format. Expected international format, e.g. +919876543210"
            )
        return v

    model_config = {"populate_by_name": True}


# ── Update ───────────────────────────────────────

class ApplicantUpdate(BaseModel):
    """Schema for updating an existing applicant. All fields optional."""
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, pattern=f"^({'|'.join(ALL_STATUSES)})$")
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    notes: str | None = None
    assigned_to: int | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not _PHONE_RE.match(v):
            raise ValueError(
                "Invalid phone format. Expected international format, e.g. +919876543210"
            )
        return v

    model_config = {"populate_by_name": True}


# ── Response (single) ───────────────────────────

class ApplicantResponse(BaseModel):
    """Applicant data returned in API responses."""
    id: int
    applicant_code: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    visa_type: str
    status: str
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata", validation_alias="metadata_")
    notes: str | None = None
    assigned_to: int | None = None
    created_by: int
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# ── Response (list) ──────────────────────────────

class ApplicantListResponse(BaseModel):
    """Paginated list of applicants returned in API responses."""
    items: list[ApplicantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


