"""
Ready2Go CRM — Activity Log & Audit Log Routes

Endpoints:
    GET   /activity-logs         — Session login/logout logs (legacy)
    GET   /activity-logs/audit   — Enterprise Audit Center (structured audit trail)
    GET   /activity-logs/export  — Export filtered audit logs as CSV
    DELETE /activity-logs/date/{log_date} — Delete login/logout logs by date
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.audit_log import AuditLogOut
from app.services import audit_service, employee_service
from app.utils.response import success_response

router = APIRouter()


# ── LEGACY: GET / — Login/Logout Activity Logs ──

@router.get("")
def get_activity_logs(
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieve paginated login/logout session logs. Admin only.

    This is the legacy endpoint showing authentication sessions.
    For structured enterprise audit events, use GET /activity-logs/audit.
    """
    total, items = employee_service.list_activity_logs(
        db,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )

    return success_response(
        message="Activity logs retrieved successfully.",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, math.ceil(total / page_size)),
            "items": items,
        },
    )


# ── ENTERPRISE AUDIT: GET /audit — Structured Audit Trail ──

@router.get("/audit")
def get_audit_logs(
    category: str | None = Query(default=None, description="Filter by category"),
    severity: str | None = Query(default=None, description="Filter by severity (INFO, SUCCESS, WARNING, ERROR, CRITICAL)"),
    employee_id: int | None = Query(default=None, alias="employee_id", description="Filter by performer employee ID"),
    date_from: str | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    target_type: str | None = Query(default=None, description="Filter by target type (applicant, employee, lead, etc.)"),
    target_id: int | None = Query(default=None, alias="target_id", description="Filter by target ID"),
    search: str | None = Query(default=None, description="Search in action, description, target name, performer name"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieve structured enterprise audit trail with full filtering.

    Returns paginated audit log entries with category, severity, action,
    performer, target, and metadata. This replaces the legacy activity
    logs view for day-to-day auditing.
    """
    total, items = audit_service.query_audit_logs(
        db,
        category=category,
        severity=severity,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        target_type=target_type,
        target_id=target_id,
        search=search,
        page=page,
        page_size=page_size,
    )

    serialized = [AuditLogOut.model_validate(e).model_dump(by_alias=True) for e in items]

    return success_response(
        message="Audit logs retrieved successfully.",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, math.ceil(total / page_size)),
            "items": serialized,
        },
    )


# ── EXPORT: GET /export — Download filtered audit logs as CSV ──

@router.get("/export")
def export_audit_logs(
    category: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    employee_id: int | None = Query(default=None, alias="employee_id"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: int | None = Query(default=None, alias="target_id"),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Export filtered audit logs as a CSV file download."""
    csv_content = audit_service.export_audit_logs_csv(
        db,
        category=category,
        severity=severity,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        target_type=target_type,
        target_id=target_id,
        search=search,
    )

    filename = f"audit_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── DELETE /date/{log_date} — Delete login/logout logs by date ──

@router.delete("/date/{log_date}")
def delete_activity_logs_by_date(
    log_date: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete all login/logout activity logs from a specific date (YYYY-MM-DD)."""
    try:
        target_date = datetime.strptime(log_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        next_date = target_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    deleted = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.login_time >= target_date,
            ActivityLog.login_time <= next_date,
        )
        .delete()
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete activity logs.",
        )

    return success_response(
        message=f"Successfully deleted {deleted} activity log entries from {log_date}.",
        data={"deleted_count": deleted, "date": log_date},
    )
