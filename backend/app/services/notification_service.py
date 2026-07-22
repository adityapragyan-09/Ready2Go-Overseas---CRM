"""
Ready2Go CRM — Notification Service

Handles creation, retrieval, read flags, and retention pruning of notifications.
"""

from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.config import settings
from app.models.notification import Notification
from app.models.user import User


def generate_next_notification_code(db: Session) -> str:
    """Generate sequential notification code e.g. NOT-000001, NOT-000002."""
    last_notif = (
        db.query(Notification)
        .order_by(Notification.id.desc())
        .first()
    )
    if not last_notif:
        return "NOT-000001"
    
    try:
        code_part = last_notif.notification_code.replace("NOT-", "")
        next_num = int(code_part) + 1
        return f"NOT-{next_num:06d}"
    except (ValueError, TypeError):
        return "NOT-000001"


def create_notification(
    db: Session,
    title: str,
    message: str,
    type: str = "info",
    module: str = "system",
    priority: str = "medium",
    recipient_user_id: int | None = None,
    created_by: int | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
) -> Notification:
    """Create a new notification entry, auto-generating sequential code."""
    code = generate_next_notification_code(db)

    notification = Notification(
        notification_code=code,
        title=title,
        message=message,
        type=type,
        module=module,
        priority=priority,
        recipient_user_id=recipient_user_id,
        created_by=created_by,
        reference_type=reference_type,
        reference_id=reference_id,
        is_read=False,
    )

    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    except Exception:
        db.rollback()
        raise


def get_latest_notifications(
    db: Session,
    user_id: int,
    is_admin: bool,
    page: int = 1,
    page_size: int | None = None,
    module_filter: str | None = None,
    search: str | None = None,
) -> tuple[int, list[Notification]]:
    """
    Retrieve paginated notifications ordered by created_at DESC.
    Supports optional module filter and search.
    """
    if is_admin:
        filter_cond = or_(
            Notification.recipient_user_id == user_id,
            Notification.recipient_user_id.is_(None)
        )
    else:
        filter_cond = Notification.recipient_user_id == user_id

    query = db.query(Notification).filter(filter_cond)

    if module_filter:
        module_map = {
            "applicant": "applicant",
            "assignment": "employee",
            "employee": "employee",
            "document": "document",
            "chat": "chat",
            "internal_chat": "chat",
            "authentication": "authentication",
            "progress": "progress",
            "system": "authentication",
        }
        db_module = module_map.get(module_filter)
        if db_module:
            query = query.filter(Notification.module == db_module)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Notification.title.ilike(search_term),
                Notification.message.ilike(search_term),
            )
        )

    total = query.count()
    limit = page_size or settings.DEFAULT_PAGE_SIZE
    offset = (page - 1) * limit

    items = (
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, items


def get_unread_count(db: Session, user_id: int, is_admin: bool) -> int:
    """Return count of unread notifications matching the user's privilege view filter."""
    if is_admin:
        filter_cond = or_(
            Notification.recipient_user_id == user_id,
            Notification.recipient_user_id.is_(None)
        )
    else:
        filter_cond = Notification.recipient_user_id == user_id

    return (
        db.query(Notification)
        .filter(and_(filter_cond, Notification.is_read == False))
        .count()
    )


def mark_read(db: Session, notification_id: int, user_id: int, is_admin: bool) -> Notification:
    """Mark a specific notification as read if user is authorized."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    # Authorization Check
    # Employees can only mark their own notifications as read.
    # Admins can read system-wide notifications too.
    if notif.recipient_user_id is not None and notif.recipient_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this notification."
        )
    if notif.recipient_user_id is None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to administrators."
        )

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(notif)
        except Exception:
            db.rollback()
            raise

    return notif


def mark_all_read(db: Session, user_id: int, is_admin: bool) -> int:
    """Mark all unread notifications visible to the user as read."""
    if is_admin:
        filter_cond = or_(
            Notification.recipient_user_id == user_id,
            Notification.recipient_user_id.is_(None)
        )
    else:
        filter_cond = Notification.recipient_user_id == user_id

    unread_notifs = (
        db.query(Notification)
        .filter(and_(filter_cond, Notification.is_read == False))
        .all()
    )

    now_utc = datetime.now(timezone.utc)
    for notif in unread_notifs:
        notif.is_read = True
        notif.read_at = now_utc

    try:
        db.commit()
        return len(unread_notifs)
    except Exception:
        db.rollback()
        raise


def delete_notification(db: Session, notification_id: int, user_id: int, is_admin: bool) -> Notification:
    """Delete (remove) a specific notification from the database."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    # Authorization Check
    if notif.recipient_user_id is not None and notif.recipient_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this notification."
        )
    if notif.recipient_user_id is None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to administrators."
        )

    try:
        db.delete(notif)
        db.commit()
        return notif
    except Exception:
        db.rollback()
        raise


def delete_old_notifications(db: Session, days_limit: int = 30) -> int:
    """Prune/delete read notifications older than the threshold limit (e.g. 30 days)."""
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days_limit)
    
    deleted_count = (
        db.query(Notification)
        .filter(and_(Notification.is_read == True, Notification.created_at < threshold_date))
        .delete()
    )
    try:
        db.commit()
        return deleted_count
    except Exception:
        db.rollback()
        raise


def delete_notifications_batch(
    db: Session,
    user_id: int | None = None,
    is_admin: bool = True,
    batch_size: int = 25,
) -> tuple[int, int]:
    """
    Delete up to batch_size notifications visible to the given user/admin (or all if user_id is None).
    Returns tuple of (deleted_count, remaining_count).
    """
    if user_id is not None:
        if is_admin:
            filter_cond = or_(
                Notification.recipient_user_id == user_id,
                Notification.recipient_user_id.is_(None),
            )
        else:
            filter_cond = Notification.recipient_user_id == user_id
        base_query = db.query(Notification).filter(filter_cond)
    else:
        base_query = db.query(Notification)

    target_ids = [row[0] for row in base_query.with_entities(Notification.id).limit(batch_size).all()]

    if not target_ids:
        remaining = base_query.count()
        return 0, remaining

    deleted_count = (
        db.query(Notification)
        .filter(Notification.id.in_(target_ids))
        .delete(synchronize_session=False)
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    remaining_count = base_query.count()
    return deleted_count, remaining_count


def purge_all_notifications_batched(
    db: Session,
    batch_size: int = 25,
) -> tuple[int, int]:
    """
    Purge all notifications from the table in batches of `batch_size`.
    Returns tuple of (total_deleted, remaining_count).
    """
    total_deleted = 0
    while True:
        deleted, remaining = delete_notifications_batch(
            db, user_id=None, is_admin=True, batch_size=batch_size
        )
        total_deleted += deleted
        if deleted == 0 or remaining == 0:
            break
    return total_deleted, remaining


def verify_notification_cleanup(
    db: Session,
    user_id: int | None = None,
    is_admin: bool = True,
) -> dict:
    """
    Run comprehensive validation checks after notification cleanup:
    1. Verify notifications table contains exactly 0 records.
    2. Verify Inbox list query returns empty state (total_count == 0, items == []).
    3. Verify unread notification count is 0.
    4. Verify no orphaned notification references remain in database.
    """
    table_count = db.query(Notification).count()

    if user_id:
        total_inbox, items = get_latest_notifications(
            db, user_id=user_id, is_admin=is_admin, page=1, page_size=20
        )
        unread = get_unread_count(db, user_id=user_id, is_admin=is_admin)
    else:
        total_inbox = table_count
        items = []
        unread = (
            db.query(Notification)
            .filter(Notification.is_read == False)
            .count()
        )

    orphaned_recipients = (
        db.query(Notification)
        .outerjoin(User, Notification.recipient_user_id == User.id)
        .filter(Notification.recipient_user_id.isnot(None), User.id.is_(None))
        .count()
    )
    orphaned_creators = (
        db.query(Notification)
        .outerjoin(User, Notification.created_by == User.id)
        .filter(Notification.created_by.isnot(None), User.id.is_(None))
        .count()
    )
    orphaned_count = orphaned_recipients + orphaned_creators

    all_passed = (
        table_count == 0
        and total_inbox == 0
        and len(items) == 0
        and unread == 0
        and orphaned_count == 0
    )

    return {
        "notifications_table_count": table_count,
        "inbox_empty_state": total_inbox == 0 and len(items) == 0,
        "unread_count": unread,
        "orphaned_references_count": orphaned_count,
        "all_checks_passed": all_passed,
    }

