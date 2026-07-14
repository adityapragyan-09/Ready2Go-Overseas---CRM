"""
Ready2Go CRM — Dashboard & Analytics Service
"""

import os
import time
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.models.applicant import Applicant
from app.models.document import Document
from app.models.user import User
from app.models.progress import ProgressHistory
from app.models.message import Message
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.services.notification_service import get_unread_count

# Track application start time for system uptime
_START_TIME = time.time()


def get_summary(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Returns global CRM metrics for summary cards.
    Accessible by both Admin and Counselor.
    """
    # 1. Total applicants
    total_applicants = db.query(func.count(Applicant.id)).filter(Applicant.is_deleted == False).scalar() or 0

    # 2. Grouped by status
    status_counts = dict(
        db.query(Applicant.status, func.count(Applicant.id))
        .filter(Applicant.is_deleted == False)
        .group_by(Applicant.status)
        .all()
    )

    # 3. Grouped by visa type
    visa_counts = dict(
        db.query(Applicant.visa_type, func.count(Applicant.id))
        .filter(Applicant.is_deleted == False)
        .group_by(Applicant.visa_type)
        .all()
    )

    # 4. Document counts
    documents_uploaded = db.query(func.count(Document.id)).filter(Document.is_deleted == False).scalar() or 0

    # 5. Completed applications (completed, approved, visa_approved, visa_issued)
    completed_statuses = ["completed", "approved", "visa_approved", "visa_issued"]
    completed_applications = sum(status_counts.get(status, 0) for status in completed_statuses)

    # 6. Employee stats
    total_employees = db.query(func.count(User.id)).scalar() or 0
    active_employees = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    inactive_employees = total_employees - active_employees

    # 7. Today's logins (UTC)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    todays_logins = (
        db.query(func.count(ActivityLog.id))
        .filter(ActivityLog.login_time >= today_start)
        .scalar() or 0
    )

    # 8. Unread notifications
    is_admin = current_user.role == "admin"
    unread_notifs = get_unread_count(db, current_user.id, is_admin)

    return {
        "total_applicants": total_applicants,
        "student_visa": visa_counts.get("student", 0),
        "visit_visa": visa_counts.get("visit", 0),
        "tourist_visa": visa_counts.get("tourist", 0),
        "business_visa": visa_counts.get("business", 0),
        "applications_processing": status_counts.get("application_processing", 0),
        "documents_pending": status_counts.get("documents_pending", 0),
        "documents_uploaded": documents_uploaded,
        "visa_approved": status_counts.get("visa_approved", 0),
        "visa_rejected": status_counts.get("visa_rejected", 0),
        "completed_applications": completed_applications,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "todays_logins": todays_logins,
        "unread_notifications": unread_notifs,
    }


def get_charts(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Returns data arrays for chart visualizations.
    Filtered to the employee's assigned workload if the user is not an Admin.
    """
    is_admin = current_user.role == "admin"

    # Define applicant baseline condition
    app_cond = (Applicant.is_deleted == False)
    if not is_admin:
        app_cond = and_(app_cond, Applicant.assigned_to == current_user.id)

    # ── APPLICANT ANALYTICS ──
    # Country breakdown
    by_country_raw = (
        db.query(Applicant.country, func.count(Applicant.id))
        .filter(app_cond)
        .group_by(Applicant.country)
        .all()
    )
    by_country = [{"label": c[0] or "Unknown", "value": c[1]} for c in by_country_raw]

    # Visa type breakdown
    by_visa_raw = (
        db.query(Applicant.visa_type, func.count(Applicant.id))
        .filter(app_cond)
        .group_by(Applicant.visa_type)
        .all()
    )
    by_visa_type = [{"label": v[0], "value": v[1]} for v in by_visa_raw]

    # Status breakdown
    by_status_raw = (
        db.query(Applicant.status, func.count(Applicant.id))
        .filter(app_cond)
        .group_by(Applicant.status)
        .all()
    )
    by_status = [{"label": s[0], "value": s[1]} for s in by_status_raw]

    # Monthly registrations (Current Year)
    current_year = datetime.now(timezone.utc).year
    year_start = datetime(current_year, 1, 1, tzinfo=timezone.utc)
    
    monthly_raw = (
        db.query(
            func.strftime("%m", Applicant.created_at).label("month"),
            func.count(Applicant.id)
        )
        .filter(and_(app_cond, Applicant.created_at >= year_start))
        .group_by("month")
        .all()
    )
    
    months_names = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
        "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }
    
    monthly_map = {m: 0 for m in months_names.values()}
    for m in monthly_raw:
        m_name = months_names.get(m[0])
        if m_name:
            monthly_map[m_name] = m[1]
    monthly_registrations = [{"label": k, "value": v} for k, v in monthly_map.items()]

    # Yearly registrations
    yearly_raw = (
        db.query(
            func.strftime("%Y", Applicant.created_at).label("year"),
            func.count(Applicant.id)
        )
        .filter(app_cond)
        .group_by("year")
        .all()
    )
    yearly_registrations = [{"label": y[0], "value": y[1]} for y in yearly_raw]

    applicant_analytics = {
        "by_country": by_country,
        "by_visa_type": by_visa_type,
        "by_status": by_status,
        "monthly_registrations": monthly_registrations,
        "yearly_registrations": yearly_registrations,
    }

    # ── DOCUMENT ANALYTICS ──
    doc_query = db.query(Document).filter(Document.is_deleted == False)
    if not is_admin:
        doc_query = doc_query.join(Applicant, Document.applicant_id == Applicant.id).filter(Applicant.assigned_to == current_user.id)
    
    total_docs = doc_query.count()
    
    pending_docs_query = db.query(func.count(Applicant.id)).filter(Applicant.status == "documents_pending", Applicant.is_deleted == False)
    if not is_admin:
        pending_docs_query = pending_docs_query.filter(Applicant.assigned_to == current_user.id)
    pending_docs_count = pending_docs_query.scalar() or 0

    doc_types_raw = (
        db.query(Document.document_type, func.count(Document.id))
        .filter(Document.is_deleted == False)
    )
    if not is_admin:
        doc_types_raw = doc_types_raw.join(Applicant, Document.applicant_id == Applicant.id).filter(Applicant.assigned_to == current_user.id)
    by_type_raw = doc_types_raw.group_by(Document.document_type).all()
    by_type = [{"label": t[0], "value": t[1]} for t in by_type_raw]

    size_query = db.query(func.sum(Document.file_size)).filter(Document.is_deleted == False)
    if not is_admin:
        size_query = size_query.join(Applicant, Document.applicant_id == Applicant.id).filter(Applicant.assigned_to == current_user.id)
    storage_usage = size_query.scalar() or 0

    largest_query = (
        db.query(Document, Applicant.full_name)
        .join(Applicant, Document.applicant_id == Applicant.id)
        .filter(Document.is_deleted == False)
    )
    if not is_admin:
        largest_query = largest_query.filter(Applicant.assigned_to == current_user.id)
    largest_docs_raw = largest_query.order_by(Document.file_size.desc()).limit(5).all()
    largest_documents = [
        {
            "document_code": d[0].document_code,
            "original_file_name": d[0].original_file_name,
            "file_size": d[0].file_size,
            "applicant_name": d[1],
        } for d in largest_docs_raw
    ]

    document_analytics = {
        "documents_uploaded": total_docs,
        "pending_documents": pending_docs_count,
        "by_type": by_type,
        "storage_usage": storage_usage,
        "largest_documents": largest_documents,
    }

    # ── PROGRESS ANALYTICS ──
    # Avg completion time in days
    completed_app_query = db.query(Applicant.id).filter(
        Applicant.is_deleted == False,
        Applicant.status.in_(["completed", "approved", "visa_approved", "visa_issued"])
    )
    if not is_admin:
        completed_app_query = completed_app_query.filter(Applicant.assigned_to == current_user.id)
    completed_ids = [r[0] for r in completed_app_query.all()]

    avg_completion_time = None
    if completed_ids:
        times_raw = (
            db.query(
                ProgressHistory.applicant_id,
                func.min(ProgressHistory.updated_at),
                func.max(ProgressHistory.updated_at)
            )
            .filter(ProgressHistory.applicant_id.in_(completed_ids))
            .group_by(ProgressHistory.applicant_id)
            .all()
        )
        diffs = [(t[2] - t[1]).total_seconds() / 86400.0 for t in times_raw if t[1] and t[2]]
        if diffs:
            avg_completion_time = sum(diffs) / len(diffs)

    # Current pipeline (active, non-completed, non-cancelled)
    pipeline_statuses = [
        "inquiry", "documents_pending", "documents_submitted", 
        "application_processing", "under_review", "interview_scheduled"
    ]
    pipeline_raw = (
        db.query(Applicant.status, func.count(Applicant.id))
        .filter(and_(app_cond, Applicant.status.in_(pipeline_statuses)))
        .group_by(Applicant.status)
        .all()
    )
    current_pipeline = [{"label": s[0], "value": s[1]} for s in pipeline_raw]

    progress_analytics = {
        "status_distribution": by_status,
        "average_completion_time": avg_completion_time,
        "current_pipeline": current_pipeline,
    }

    # ── CHAT ANALYTICS ──
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    msg_base = db.query(Message).join(Applicant, Message.applicant_id == Applicant.id).filter(
        Message.is_deleted == False,
        Applicant.is_deleted == False
    )
    if not is_admin:
        msg_base = msg_base.filter(Applicant.assigned_to == current_user.id)
        
    messages_today = msg_base.filter(Message.created_at >= today_start).count()
    system_messages = msg_base.filter(Message.is_system_message == True).count()
    employee_messages = msg_base.filter(Message.is_system_message == False).count()

    chat_analytics = {
        "messages_today": messages_today,
        "system_messages": system_messages,
        "employee_messages": employee_messages,
    }

    # ── NOTIFICATION ANALYTICS ──
    notif_cond = True
    if not is_admin:
        notif_cond = Notification.recipient_user_id == current_user.id
    else:
        notif_cond = or_(Notification.recipient_user_id == current_user.id, Notification.recipient_user_id.is_(None))

    unread_notifs = get_unread_count(db, current_user.id, is_admin)
    notifs_today = db.query(Notification).filter(and_(notif_cond, Notification.created_at >= today_start)).count()
    
    by_module_raw = (
        db.query(Notification.module, func.count(Notification.id))
        .filter(notif_cond)
        .group_by(Notification.module)
        .all()
    )
    notifications_by_module = [{"label": m[0], "value": m[1]} for m in by_module_raw]

    notification_analytics = {
        "unread_notifications": unread_notifs,
        "notifications_today": notifs_today,
        "notifications_by_module": notifications_by_module,
    }

    return {
        "applicant_analytics": applicant_analytics,
        "document_analytics": document_analytics,
        "progress_analytics": progress_analytics,
        "chat_analytics": chat_analytics,
        "notification_analytics": notification_analytics,
    }


def get_recent(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Returns latest 5 elements of activity logs across the CRM.
    Filtered to the employee's assigned workload if the user is not an Admin.
    """
    is_admin = current_user.role == "admin"

    # Baseline conditions
    app_cond = (Applicant.is_deleted == False)
    if not is_admin:
        app_cond = and_(app_cond, Applicant.assigned_to == current_user.id)

    # 1. Recent Applicants
    recent_apps_raw = (
        db.query(Applicant)
        .filter(app_cond)
        .order_by(Applicant.created_at.desc())
        .limit(5)
        .all()
    )
    recent_applicants = [
        {
            "id": a.id,
            "full_name": a.full_name,
            "visa_type": a.visa_type,
            "status": a.status,
            "created_at": a.created_at,
        } for a in recent_apps_raw
    ]

    # 2. Recent Documents
    doc_query = (
        db.query(Document, Applicant.full_name)
        .join(Applicant, Document.applicant_id == Applicant.id)
        .filter(Document.is_deleted == False)
    )
    if not is_admin:
        doc_query = doc_query.filter(Applicant.assigned_to == current_user.id)
    recent_docs_raw = doc_query.order_by(Document.uploaded_at.desc()).limit(5).all()
    recent_documents = [
        {
            "id": d[0].id,
            "original_file_name": d[0].original_file_name,
            "document_type": d[0].document_type,
            "uploaded_at": d[0].uploaded_at,
            "applicant_name": d[1],
        } for d in recent_docs_raw
    ]

    # 3. Recent Status Updates
    status_query = (
        db.query(ProgressHistory, Applicant.full_name, User.name)
        .join(Applicant, ProgressHistory.applicant_id == Applicant.id)
        .join(User, ProgressHistory.updated_by == User.id)
        .filter(Applicant.is_deleted == False)
    )
    if not is_admin:
        status_query = status_query.filter(Applicant.assigned_to == current_user.id)
    recent_status_raw = status_query.order_by(ProgressHistory.updated_at.desc()).limit(5).all()
    recent_status_updates = [
        {
            "id": s[0].id,
            "current_status": s[0].current_status,
            "previous_status": s[0].previous_status,
            "remarks": s[0].remarks,
            "updated_at": s[0].updated_at,
            "applicant_name": s[1],
            "updater_name": s[2],
        } for s in recent_status_raw
    ]

    # 4. Recent Chat Messages
    chat_query = (
        db.query(Message, User.name, Applicant.full_name)
        .join(User, Message.sender_id == User.id)
        .join(Applicant, Message.applicant_id == Applicant.id)
        .filter(Message.is_deleted == False, Applicant.is_deleted == False)
    )
    if not is_admin:
        chat_query = chat_query.filter(Applicant.assigned_to == current_user.id)
    recent_chat_raw = chat_query.order_by(Message.created_at.desc()).limit(5).all()
    recent_chat_messages = [
        {
            "id": m[0].id,
            "content": m[0].content,
            "sender_name": m[1],
            "applicant_name": m[2],
            "created_at": m[0].created_at,
        } for m in recent_chat_raw
    ]

    # 5. Recent Employees (Admins only)
    recent_employees = []
    if is_admin:
        recent_emp_raw = db.query(User).filter(User.is_active == True).order_by(User.created_at.desc()).limit(5).all()
        recent_employees = [
            {
                "id": u.id,
                "name": u.name,
                "designation": u.designation,
                "department": u.department,
                "created_at": u.created_at,
            } for u in recent_emp_raw
        ]

    # 6. Recent Notifications
    notif_cond = True
    if not is_admin:
        notif_cond = Notification.recipient_user_id == current_user.id
    else:
        notif_cond = or_(Notification.recipient_user_id == current_user.id, Notification.recipient_user_id.is_(None))
    recent_notifs_raw = db.query(Notification).filter(notif_cond).order_by(Notification.created_at.desc()).limit(5).all()
    recent_notifications = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "created_at": n.created_at,
        } for n in recent_notifs_raw
    ]

    quick_actions = {
        "create_applicant": True,
        "upload_document": True,
        "create_employee": is_admin,
        "update_progress": True,
    }

    return {
        "recent_applicants": recent_applicants,
        "recent_documents": recent_documents,
        "recent_status_updates": recent_status_updates,
        "recent_chat_messages": recent_chat_messages,
        "recent_employees": recent_employees,
        "recent_notifications": recent_notifications,
        "quick_actions": quick_actions,
    }


def get_employees(db: Session, current_user: User) -> List[Dict[str, Any]]:
    """
    Returns workload and analytics metrics for employee entities.
    Admins: metrics for all employees.
    Employees: their own statistics as a single-element list.
    """
    is_admin = current_user.role == "admin"

    if is_admin:
        users = db.query(User).filter(User.is_active == True).all()
    else:
        users = [current_user]

    # Run bulk-grouped queries to aggregate data instantly and prevent N+1 queries
    assigned_counts = dict(
        db.query(Applicant.assigned_to, func.count(Applicant.id))
        .filter(Applicant.is_deleted == False)
        .group_by(Applicant.assigned_to)
        .all()
    )

    completed_counts = dict(
        db.query(Applicant.assigned_to, func.count(Applicant.id))
        .filter(
            Applicant.is_deleted == False,
            Applicant.status.in_(["completed", "approved", "visa_approved", "visa_issued"])
        )
        .group_by(Applicant.assigned_to)
        .all()
    )

    docs_pending_counts = dict(
        db.query(Applicant.assigned_to, func.count(Applicant.id))
        .filter(Applicant.is_deleted == False, Applicant.status == "documents_pending")
        .group_by(Applicant.assigned_to)
        .all()
    )

    docs_uploaded_counts = dict(
        db.query(Applicant.assigned_to, func.count(Document.id))
        .join(Applicant, Document.applicant_id == Applicant.id)
        .filter(Document.is_deleted == False)
        .group_by(Applicant.assigned_to)
        .all()
    )

    # Get processing times for completed cases
    completed_apps = (
        db.query(Applicant.id, Applicant.assigned_to)
        .filter(
            Applicant.is_deleted == False,
            Applicant.status.in_(["completed", "approved", "visa_approved", "visa_issued"])
        )
        .all()
    )
    app_to_emp = {r[0]: r[1] for r in completed_apps}
    completed_app_ids = list(app_to_emp.keys())

    avg_processing_times = {}
    if completed_app_ids:
        times_raw = (
            db.query(
                ProgressHistory.applicant_id,
                func.min(ProgressHistory.updated_at),
                func.max(ProgressHistory.updated_at)
            )
            .filter(ProgressHistory.applicant_id.in_(completed_app_ids))
            .group_by(ProgressHistory.applicant_id)
            .all()
        )
        emp_durations = {}
        for t in times_raw:
            if t[1] and t[2]:
                dur = (t[2] - t[1]).total_seconds() / 86400.0
                emp_id = app_to_emp.get(t[0])
                if emp_id is not None:
                    if emp_id not in emp_durations:
                        emp_durations[emp_id] = []
                    emp_durations[emp_id].append(dur)
        
        for emp_id, durs in emp_durations.items():
            avg_processing_times[emp_id] = sum(durs) / len(durs)

    analytics = []
    for u in users:
        assigned = assigned_counts.get(u.id, 0)
        completed = completed_counts.get(u.id, 0)
        pending = assigned - completed
        docs_pending = docs_pending_counts.get(u.id, 0)
        docs_uploaded = docs_uploaded_counts.get(u.id, 0)
        avg_time = avg_processing_times.get(u.id)

        analytics.append({
            "employee_id": u.id,
            "name": u.name,
            "role": u.role,
            "applicants_assigned": assigned,
            "completed_cases": completed,
            "pending_cases": pending,
            "documents_pending": docs_pending,
            "documents_uploaded": docs_uploaded,
            "average_processing_time": avg_time,
            "latest_login": u.last_login,
            "latest_logout": u.last_logout,
        })

    return analytics


def get_system(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Returns SQLite database performance parameters and overview.
    Strictly admin-only.
    """
    # 1. SQLite Database file size
    db_size = 0
    db_path = "crm.db"
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)

    # 2. SQLite version
    sqlite_version = sqlite3.sqlite_version

    # 3. System Uptime (seconds)
    uptime_seconds = time.time() - _START_TIME

    # 4. Active user sessions (distinct active user logins in last 24h)
    active_sessions_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    active_sessions = (
        db.query(func.count(func.distinct(ActivityLog.user_id)))
        .filter(ActivityLog.login_time >= active_sessions_threshold)
        .scalar() or 0
    )

    # 5. Approx query workload size (Sum of records across primary transactional tables)
    users_count = db.query(func.count(User.id)).scalar() or 0
    applicants_count = db.query(func.count(Applicant.id)).scalar() or 0
    docs_count = db.query(func.count(Document.id)).scalar() or 0
    messages_count = db.query(func.count(Message.id)).scalar() or 0
    progress_count = db.query(func.count(ProgressHistory.id)).scalar() or 0
    notifs_count = db.query(func.count(Notification.id)).scalar() or 0
    
    total_queries_logged = (
        users_count + applicants_count + docs_count + 
        messages_count + progress_count + notifs_count
    )

    return {
        "total_db_size_bytes": db_size,
        "sqlite_version": sqlite_version,
        "system_uptime_seconds": uptime_seconds,
        "active_user_sessions": active_sessions,
        "total_queries_logged": total_queries_logged,
    }
