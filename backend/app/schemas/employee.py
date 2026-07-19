"""
Ready2Go CRM — Employee Schemas

Pydantic models for employee serialization, creation, updates, and profile management.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class EmployeeOut(BaseModel):
    """Detailed employee information returned in responses."""
    id: int
    employee_code: str | None = Field(default=None, serialization_alias="employee_code")
    full_name: str = Field(..., validation_alias="name", serialization_alias="full_name")
    email: str
    phone: str | None = None
    role: str
    designation: str | None = None
    department: str | None = None
    profile_photo: str | None = Field(default=None, serialization_alias="profile_photo")
    is_active: bool
    archived_at: datetime | None = Field(default=None, serialization_alias="archived_at")
    last_login: datetime | None = None
    last_logout: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class EmployeeCreate(BaseModel):
    """Schema for registering a new employee by Admin."""
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = None
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="employee", pattern="^(admin|employee)$")
    designation: str | None = None
    department: str | None = None
    profile_photo: str | None = None


class EmployeeUpdate(BaseModel):
    """Schema for updating employee details by Admin."""
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    role: str | None = Field(default=None, pattern="^(admin|employee)$")
    designation: str | None = None
    department: str | None = None
    profile_photo: str | None = None


class EmployeeProfileUpdate(BaseModel):
    """Schema for updating own profile properties by Employee."""
    phone: str | None = None
    designation: str | None = None
    department: str | None = None
    profile_photo: str | None = None


class EmployeeStatusUpdate(BaseModel):
    """Schema for activating/deactivating an employee by Admin."""
    is_active: bool


class EmployeePasswordReset(BaseModel):
    """Schema for resetting user password by Admin."""
    password: str = Field(..., min_length=6, max_length=128)


class EmployeeListResponse(BaseModel):
    """Paginated list of employees."""
    total_count: int
    page: int
    page_size: int
    items: list[EmployeeOut]
