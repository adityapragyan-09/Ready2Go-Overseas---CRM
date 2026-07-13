"""
Ready2Go CRM — Activity Log Schemas

Pydantic models for audit log serialization.
"""

from datetime import datetime

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    """Activity log entry returned in API responses."""
    id: int
    user_id: int
    login_time: datetime
    logout_time: datetime | None = None
    ip_address: str | None = None
    browser: str | None = None
    device: str | None = None

    model_config = {"from_attributes": True}
