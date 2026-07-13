"""
Ready2Go CRM — Message Schemas

Pydantic models for internal chat messages.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for sending a new chat message."""
    content: str = Field(min_length=1)


class MessageOut(BaseModel):
    """Message data returned in API responses."""
    id: int
    applicant_id: int
    sender_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
