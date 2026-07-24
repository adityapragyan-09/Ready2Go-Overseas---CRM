"""
Ready2Go CRM — Audit Log Service

Provides create_audit_entry() for recording enterprise actions and
query_audit_logs() for the Audit Center with full filtering.

Also includes login/logout events from the legacy activity_logs table
so the Audit Center shows data immediately.

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
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
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


def _activity_log_to_dict(log: ActivityLog, user_name: str | None, user_code: str | None) -> dict:
    """Convert a legacy ActivityLog (login/logout) to the unified audit format."""
    action_parts = []
    if log.login_time:
        action_parts.append("Login")
    if log.logout_time:
        action_parts.append("Logout")
    action = " / ".join(action_parts) if action_parts else "Session Activity"

    return {
        "id": log.id,
        "category": "security",
        "severity": "INFO",
        "action": action,
        "description": f"User {user_name or '#' + str(log.user_id or 0)} logged in" if log.login_time else None,
        "performed_by_id": log.user_id,
        "performed_by_name": user_name,
        "target_type": None,
        "target_id": None,
        "target_name": None,
        "metadata": None,
        "old_value": None,
        "new_value": None,
        "ip_address": log.ip_address,
        "request_id": None,
        "created_at": log.login_time or log.logout_time,
    }


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

    When no category filter is applied, also includes legacy login/logout
    events from the activity_logs table so the Audit Center shows data
    immediately without waiting for enterprise audit events.

    Returns (total_count, items).
    """
    # When category is not specified, include legacy login/logout data
    if category is None:
        return _query_all_events(db, severity, employee_id, date_from, date_to,
                                  target_type, target_id, search, page, page_size)

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

    # 6. Text search
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

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return total, items


def _query_all_events(
    db: Session,
    severity: str | None = None,
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list]:
    """Query both audit_logs and legacy activity_logs, combine, sort, paginate."""
    # 1. Query audit_logs
    audit_q = db.query(AuditLog)
    if employee_id is not None:
        audit_q = audit_q.filter(AuditLog.performed_by_id == employee_id)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            audit_q = audit_q.filter(AuditLog.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            audit_q = audit_q.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    audit_items = audit_q.order_by(AuditLog.created_at.desc()).all()

    # 2. Query legacy activity_logs (login/logout)
    act_q = db.query(ActivityLog, User.name, User.employee_code).outerjoin(
        User, ActivityLog.user_id == User.id
    )
    if employee_id is not None:
        act_q = act_q.filter(ActivityLog.user_id == employee_id)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            act_q = act_q.filter(ActivityLog.login_time >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            act_q = act_q.filter(ActivityLog.login_time <= dt_to)
        except ValueError:
            pass

    act_rows = act_q.order_by(ActivityLog.login_time.desc()).all()

    # 3. Convert activity logs to unified format
    act_dicts = []
    for log, user_name, user_code in act_rows:
        d = _activity_log_to_dict(log, user_name, user_code)
        # Mark as from activity_logs for dedup
        d["_source"] = "activity_log"
        act_dicts.append(d)

    # 4. Convert audit logs to dicts
    audit_dicts = []
    for a in audit_items:
        d = {
            "id": a.id,
            "category": a.category,
            "severity": a.severity,
            "action": a.action,
            "description": a.description,
            "performed_by_id": a.performed_by_id,
            "performed_by_name": a.performed_by_name,
            "target_type": a.target_type,
            "target_id": a.target_id,
            "target_name": a.target_name,
            "metadata": a.metadata_,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "ip_address": a.ip_address,
            "request_id": a.request_id,
            "created_at": a.created_at,
            "_source": "audit_log",
        }
        audit_dicts.append(d)

    # 5. Combine and sort by created_at descending
    combined = audit_dicts + act_dicts
    MIN_DT = datetime(2020, 1, 1, tzinfo=timezone.utc)
    combined.sort(key=lambda x: x["created_at"] or MIN_DT, reverse=True)

    # 6. Apply text search on combined results
    if search:
        search_term = search.lower()
        combined = [
            e for e in combined
            if search_term in (e.get("action") or "").lower()
            or search_term in (e.get("description") or "").lower()
            or search_term in (e.get("target_name") or "").lower()
            or search_term in (e.get("performed_by_name") or "").lower()
        ]

    # 7. Paginate
    total = len(combined)
    offset = (page - 1) * page_size
    paged = combined[offset:offset + page_size]

    return total, paged


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
        # Handle both AuditLog objects and dicts (from combined query)
        if isinstance(entry, dict):
            writer.writerow([
                entry.get("created_at", "").isoformat() if hasattr(entry.get("created_at"), "isoformat") else str(entry.get("created_at", "")),
                entry.get("category", ""),
                entry.get("severity", ""),
                entry.get("action", ""),
                entry.get("description", "") or "",
                entry.get("performed_by_name", "") or "",
                entry.get("target_type", "") or "",
                entry.get("target_name", "") or "",
                entry.get("old_value", "") or "",
                entry.get("new_value", "") or "",
                entry.get("ip_address", "") or "",
            ])
        else:
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
