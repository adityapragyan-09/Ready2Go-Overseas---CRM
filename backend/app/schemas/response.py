"""
Ready2Go CRM — Standard API Response Schema

Every API endpoint returns this envelope format:
{
    "success": true | false,
    "message": "Human-readable description",
    "data": { ... } | null
}
"""

from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response envelope."""
    success: bool
    message: str
    data: Any = None
    errors: dict[str, list[str]] | None = None
