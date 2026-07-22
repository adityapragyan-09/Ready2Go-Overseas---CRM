"""
Ready2Go CRM — User Schemas

Pydantic models for user serialization and input validation.
The password_hash is never included in any output schema.
"""

from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    """User data returned in API responses (excludes password_hash)."""
    id: int
    name: str
    email: str
    phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

