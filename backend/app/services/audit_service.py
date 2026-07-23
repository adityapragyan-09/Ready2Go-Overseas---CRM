"""
Ready2Go CRM — Audit Log Service

Provides create_audit_entry() for recording enterprise actions and
query_audit_logs() for the Audit Center with full filtering.

Usage:
    from app.services.audit_service import create_audit_entry

    create_audit_entry(
        db,
        category="employee_management",
        severity="SUCCESS",
        action="Employee Archived",
        description="Employee 'Rahul Sharma' archived. Reason: Resigned.",
        performed_by=admin_user,
        target_type="employee",
        target_id=emp_id,
        target_name="Rahul Sharma",
        metadata={"reason": "Resigned", "applicants_reassigned": 5},
    )
"""

import csv
import io
import math
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_entry(
    db: Session,
    *,
    category: str,
    severity: str,
    action: str,
    description: str | None = None,
    performed_by: User | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    target_name: str | None = None,
    metadata: dict | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> AuditLog:
    """Create a structured enterprise audit log entry.

    All fields are optional except category, severity, and action.
    The performer's name is denormalized for query performance.
    Returns the created AuditLog instance.
    """
    entry = AuditLog(
        category=category,
        severity=severity,
        action=action,
        description=description,
        performed_by_id=performed_by.id if performed_by else None,
        performed_by_name=performed_by.name if performed_by else None,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        metadata_=metadata,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        request_id=request_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
    except Exception:
        db.rollback()
        raise
    return entry


def query_audit_logs(
    db: Session,
    *,
    category: str | None = None,
    severity: str | None = None,
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[AuditLog]]:
    """Query audit logs with optional filters and pagination.

    Returns (total_count, items).
    """
    query = db.query(AuditLog)

    # 1. Category filter
    if category:
        query = query.filter(AuditLog.category == category)

    # 2. Severity filter
    if severity:
        query = query.filter(AuditLog.severity == severity)

    # 3. Employee filter
    if employee_id is not None:
        query = query.filter(AuditLog.performed_by_id == employee_id)

    # 4. Date range filter
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(AuditLog.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            query = query.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    # 5. Target type + id filter
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if target_id is not None:
        query = query.filter(AuditLog.target_id == target_id)

    # 6. Text search (matches action, description, target_name, performed_by_name)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(search_term),
                AuditLog.description.ilike(search_term),
                AuditLog.target_name.ilike(search_term),
                AuditLog.performed_by_name.ilike(search_term),
            )
        )

    # Count total before pagination
    total = query.count()

    # Pagination
    offset = (page - 1) * page_size
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return total, items


def export_audit_logs_csv(
    db: Session,
    *,
    category: str | None = None,
    severity: str | None = None,
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    search: str | None = None,
) -> str:
    """Export filtered audit logs as CSV string."""
    total, items = query_audit_logs(
        db,
        category=category,
        severity=severity,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        target_type=target_type,
        target_id=target_id,
        search=search,
        page=1,
        page_size=10000,  # Max export size
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Timestamp", "Category", "Severity", "Action", "Description",
        "Performed By", "Target Type", "Target Name", "Old Value", "New Value",
        "IP Address",
    ])

    for entry in items:
        writer.writerow([
            entry.created_at.isoformat() if entry.created_at else "",
            entry.category,
            entry.severity,
            entry.action,
            entry.description or "",
            entry.performed_by_name or "",
            entry.target_type or "",
            entry.target_name or "",
            entry.old_value or "",
            entry.new_value or "",
            entry.ip_address or "",
        ])

    return output.getvalue()
