"""
Ready2Go CRM — Internal Chat Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    """Schema representing an internal chat message in the response body."""
    id: int
    applicant_id: int
    sender_id: int
    content: str = Field(..., serialization_alias="message")
    message_type: str
    attachment_url: str | None = None
    is_system_message: bool
    created_at: datetime
    updated_at: datetime
    sender_name: str = Field(default="System", description="Name of user who sent message")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ChatMessageCreate(BaseModel):
    """Schema for creating a new internal chat message."""
    content: str = Field(..., min_length=1, description="Message text or attachment details")
    message_type: str = Field(default="text", description="Type of message: text, attachment, system")
    attachment_url: str | None = Field(default=None, max_length=255, description="Storage URL of file attachment")
