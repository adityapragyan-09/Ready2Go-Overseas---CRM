"""
Ready2Go CRM — Standard API Response Schema

Every API endpoint returns this enterprise envelope format:
{
    "success": true | false,
    "message": "Human-readable description",
    "data": { ... } | null,
    "error": "Machine-readable error code (only on failure)",
    "timestamp": "ISO-8601 timestamp",
    "request_id": "Unique request identifier (uuid)"
}
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Enterprise standard API response envelope."""

    success: bool
    message: str
    data: Any = None
    errors: dict[str, list[str]] | None = None
    error: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_id: str | None = None
