"""
Ready2Go CRM — Standardized JSON Response Helpers

Every API endpoint should use these helpers to ensure a
consistent response envelope across the entire application.

Envelope format:
{
    "success": true | false,
    "message": "Human-readable description",
    "data": { ... } | null
}
"""

from typing import Any

from app.schemas.response import APIResponse


def success_response(
    message: str,
    data: Any = None,
) -> dict:
    """Build a success response dict."""
    return APIResponse(
        success=True,
        message=message,
        data=data,
    ).model_dump()


def error_response(
    message: str,
    errors: dict[str, list[str]] | None = None,
) -> dict:
    """Build an error response dict."""
    return APIResponse(
        success=False,
        message=message,
        data=None,
        errors=errors,
    ).model_dump()
