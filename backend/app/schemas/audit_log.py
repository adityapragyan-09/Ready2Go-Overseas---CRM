"""
Ready2Go CRM — Audit Log Schemas

Pydantic models for the structured enterprise audit trail.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


CATEGORIES = [
    "employee_management", "applicant_management", "lead_management",
    "documents", "communication", "leave_hr", "notifications",
    "security", "system",
]

SEVERITIES = ["INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


class AuditLogOut(BaseModel):
    """Full audit log entry returned in API responses."""
    id: int
    category: str
    severity: str
    action: str
    description: str | None = None

    performed_by_id: int | None = None
    performed_by_name: str | None = None

    target_type: str | None = None
    target_id: int | None = None
    target_name: str | None = None

    metadata: dict[str, Any] | None = Field(
        default=None, validation_alias="metadata_"
    )
    old_value: str | None = None
    new_value: str | None = None

    ip_address: str | None = None
    request_id: str | None = None

    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[AuditLogOut]


class AuditLogFilterParams(BaseModel):
    """Filters accepted by the audit log query endpoint."""
    category: str | None = None
    severity: str | None = None
    employee_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    target_type: str | None = None
    target_id: int | None = None
    search: str | None = None
