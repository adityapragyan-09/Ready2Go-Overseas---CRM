"""
Ready2Go CRM — Dashboard & Analytics Endpoints Router
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardChartsResponse,
    DashboardRecentResponse,
    DashboardEmployeeResponse,
    DashboardSystemResponse,
)
from app.services import dashboard_service
from app.utils.response import success_response

router = APIRouter()


@router.get("/summary")
def get_summary_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve high-level overview metrics count cards.
    Accessible to all logged-in advisors.
    """
    stats = dashboard_service.get_summary(db, current_user)
    return success_response(
        message="Dashboard summary retrieved successfully.",
        data=stats,
    )


@router.get("/charts", response_model=None)
def get_charts_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve detailed metrics and datasets for visualizations and trends.
    Counselors see metrics scoped to their assigned applicants.
    """
    stats = dashboard_service.get_charts(db, current_user)
    return success_response(
        message="Dashboard charts data retrieved successfully.",
        data=stats,
    )


@router.get("/recent", response_model=None)
def get_recent_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve recent activity feed across applicants, chat, documents, and notifications.
    """
    stats = dashboard_service.get_recent(db, current_user)
    return success_response(
        message="Dashboard recent activity feed retrieved successfully.",
        data=stats,
    )


@router.get("/employees", response_model=None)
def get_employees_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve counselor performance workload analytics.
    Admins see metrics for all employees; counselors see only their own stats.
    """
    stats = dashboard_service.get_employees(db, current_user)
    return success_response(
        message="Dashboard employee analytics retrieved successfully.",
        data=stats,
    )


@router.get("/system", response_model=None)
def get_system_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Retrieve SQLite database performance parameters and overview.
    Strictly Admin-only access.
    """
    stats = dashboard_service.get_system(db, current_user)
    return success_response(
        message="System analytics parameters retrieved successfully.",
        data=stats,
    )
