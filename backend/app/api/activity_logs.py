"""
Ready2Go CRM — Activity Log Routes

Router: /api/v1/activity-logs
Access Level: Administrators only (require_admin dependency)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.services import employee_service
from app.utils.response import success_response

router = APIRouter()


@router.get("")
def get_activity_logs(
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retrieve paginated audit logs for logins/logouts. Admin only.
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
            "total_count": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        },
    )


@router.delete("/date/{log_date}")
def delete_activity_logs_by_date(
    log_date: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete all activity logs from a specific date (YYYY-MM-DD format).
    Admin only operation.
    """
    # Validate date format
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
