"""
Ready2Go CRM — User Schemas

Pydantic models for user serialization and input validation.
The password_hash is never included in any output schema.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.constants import EMPLOYEE, ALL_ROLES


class UserOut(BaseModel):
    """User data returned in API responses (excludes password_hash)."""
    id: int
    name: str
    email: str
    phone: str | None = None
    role: str
    is_active: bool
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Schema for creating a new user (employee management)."""
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default=EMPLOYEE, pattern=f"^({'|'.join(ALL_ROLES)})$")


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    role: str | None = Field(default=None, pattern=f"^({'|'.join(ALL_ROLES)})$")
    is_active: bool | None = None
