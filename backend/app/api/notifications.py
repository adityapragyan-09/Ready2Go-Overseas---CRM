"""
Ready2Go CRM — Notification Center Routes

Router: /api/v1/notifications
Access Level: Authenticated Users (JWT required)
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationCountResponse,
    NotificationListResponse,
    NotificationOut,
)
from app.services import notification_service
from app.utils.response import success_response

router = APIRouter()


# ── GET /unread-count ────────────────────────

@router.get("/unread-count")
def get_unread_count_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the total count of unread notifications matching the user's privilege view.
    """
    is_admin = current_user.role == "admin"
    count = notification_service.get_unread_count(db, current_user.id, is_admin)
    
    data = NotificationCountResponse(unread_count=count).model_dump(by_alias=True)
    return success_response(
        message="Unread notification count retrieved successfully.",
        data=data,
    )


# ── GET / ───────────────────────────────────

@router.get("")
def list_notifications_route(
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    module: str | None = Query(default=None, description="Filter by module (applicant, assignment, employee, document, chat, internal_chat, authentication)"),
    search: str | None = Query(default=None, description="Search in title and message"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve paginated notifications visible to the authenticated user.
    Optional module filter and search.
    """
    is_admin = current_user.role == "admin"
    total, items = notification_service.get_latest_notifications(
        db,
        user_id=current_user.id,
        is_admin=is_admin,
        page=page,
        page_size=page_size,
        module_filter=module,
        search=search,
    )
    
    serialized_items = [NotificationOut.model_validate(n).model_dump(by_alias=True) for n in items]
    data = NotificationListResponse(
        total_count=total,
        page=page,
        page_size=page_size or 10,
        items=serialized_items,
    ).model_dump(by_alias=True)

    return success_response(
        message="Notifications retrieved successfully.",
        data=data,
    )


# ── DELETE /batch & DELETE /all ──────────────

@router.delete("/batch")
def delete_notifications_batch_route(
    batch_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete notifications in batches (25-50 items per batch).
    Prevents large request timeouts on cloud deployments.
    """
    is_admin = current_user.role == "admin"
    deleted, remaining = notification_service.delete_notifications_batch(
        db, user_id=current_user.id, is_admin=is_admin, batch_size=batch_size
    )
    return success_response(
        message=f"Deleted batch of {deleted} notification(s). {remaining} remaining.",
        data={"deleted": deleted, "remaining": remaining},
    )


@router.delete("/all")
def delete_all_notifications_route(
    batch_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all notifications visible to user, processed in batches internally."""
    is_admin = current_user.role == "admin"
    total_deleted = 0
    while True:
        deleted, remaining = notification_service.delete_notifications_batch(
            db, user_id=current_user.id, is_admin=is_admin, batch_size=batch_size
        )
        total_deleted += deleted
        if deleted == 0 or remaining == 0:
            break

    return success_response(
        message=f"Deleted {total_deleted} notification(s).",
        data={"deleted": total_deleted, "remaining": remaining},
    )


@router.patch("/{id}/read")
def mark_read_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a specific notification as read.
    """
    is_admin = current_user.role == "admin"
    notif = notification_service.mark_read(db, id, current_user.id, is_admin)
    data = NotificationOut.model_validate(notif).model_dump(by_alias=True)
    
    return success_response(
        message="Notification marked as read.",
        data=data,
    )


# ── PATCH /read-all ──────────────────────────

@router.patch("/read-all")
def mark_all_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark all unread notifications visible to the user as read.
    """
    is_admin = current_user.role == "admin"
    updated_count = notification_service.mark_all_read(db, current_user.id, is_admin)
    
    return success_response(
        message=f"Successfully marked {updated_count} notifications as read.",
        data={"updated_count": updated_count},
    )


# ── DELETE /{id} ─────────────────────────────

@router.delete("/{id}")
def delete_notification_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific notification from the database.
    """
    is_admin = current_user.role == "admin"
    notif = notification_service.delete_notification(db, id, current_user.id, is_admin)
    data = NotificationOut.model_validate(notif).model_dump(by_alias=True)
    
    return success_response(
        message="Notification deleted successfully.",
        data=data,
    )
