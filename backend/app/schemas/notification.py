"""
Ready2Go CRM — Notification Schemas

Pydantic models for notification serialization and output validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    """Detailed notification schema returned in API responses."""
    id: int
    notification_code: str = Field(..., serialization_alias="notification_code")
    title: str
    message: str
    type: str
    module: str
    priority: str
    recipient_user_id: int | None = Field(default=None, serialization_alias="recipient_user_id")
    created_by: int | None = Field(default=None, serialization_alias="created_by")
    reference_type: str | None = Field(default=None, serialization_alias="reference_type")
    reference_id: int | None = Field(default=None, serialization_alias="reference_id")
    is_read: bool = Field(..., serialization_alias="is_read")
    read_at: datetime | None = Field(default=None, serialization_alias="read_at")
    created_at: datetime = Field(..., serialization_alias="created_at")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class NotificationCountResponse(BaseModel):
    """Schema returning the total number of unread notifications."""
    unread_count: int = Field(..., serialization_alias="unread_count")


class NotificationListResponse(BaseModel):
    """Paginated list response of notifications."""
    total: int = Field(..., serialization_alias="total")
    page: int
    page_size: int
    total_pages: int
    items: list[NotificationOut]
