"""
Ready2Go CRM — Standardized JSON Response Helpers

Every API endpoint MUST use these helpers to ensure a
consistent response envelope across the entire application.

Envelope format:
{
    "success": true | false,
    "message": "Human-readable description",
    "data": { ... } | null,
    "error": "Machine-readable error code (only on failure)",
    "timestamp": "ISO-8601 timestamp",
    "request_id": "Unique request identifier (uuid)"
}
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.response import APIResponse


def _build_envelope(
    success: bool,
    message: str,
    data: Any = None,
    errors: dict[str, list[str]] | None = None,
    error: str | None = None,
    request_id: str | None = None,
) -> dict:
    """Build the standard API response envelope with metadata."""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        errors=errors,
        error=error,
    ).model_dump()


def success_response(
    message: str,
    data: Any = None,
    request_id: str | None = None,
) -> dict:
    """Build a success response with timestamp and request_id."""
    return _build_envelope(
        success=True,
        message=message,
        data=data,
        request_id=request_id,
    )


def error_response(
    message: str,
    errors: dict[str, list[str]] | None = None,
    error: str = "INTERNAL_ERROR",
    request_id: str | None = None,
) -> dict:
    """Build an error response with error code and optional field-level errors."""
    return _build_envelope(
        success=False,
        message=message,
        data=None,
        errors=errors,
        error=error,
        request_id=request_id,
    )
