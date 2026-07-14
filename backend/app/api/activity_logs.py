"""
Ready2Go CRM — Activity Log Routes

Router: /api/v1/activity-logs
Access Level: Administrators only (require_admin dependency)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
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
