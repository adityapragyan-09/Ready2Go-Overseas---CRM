"""
Ready2Go CRM — Employee Management Routes

Router: /api/v1/employees
Access Level:
    - Profile me: Authenticated Users (JWT required)
    - All other endpoints: Administrators only (require_admin dependency)

Archive replaces hard delete. Documents, messages, and notifications
never prevent archiving — only assigned applicants matter.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.employee import (
    EmployeeArchiveRequest,
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeOut,
    EmployeePasswordReset,
    EmployeeProfileUpdate,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)
import logging
import math

from app.services import employee_service
from app.services.auth_service import reset_employee_password
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)


def _safe_employee_out(user) -> dict:
    """Serialize an employee, gracefully handling deferred columns not yet migrated."""
    try:
        return EmployeeOut.model_validate(user).model_dump(by_alias=True)
    except Exception as e:
        logger.warning("Employee serialization failed for user %s: %s", user.id, e)
        data = {
            "id": user.id,
            "employee_code": getattr(user, "employee_code", None),
            "full_name": getattr(user, "name", ""),
            "email": getattr(user, "email", ""),
            "phone": getattr(user, "phone", None),
            "role": getattr(user, "role", "employee"),
            "designation": getattr(user, "designation", None),
            "department": getattr(user, "department", None),
            "profile_photo": getattr(user, "profile_photo", None),
            "is_active": getattr(user, "is_active", True),
            "archived_at": None,
            "archived_reason": getattr(user, "archived_reason", None),
            "leave_start": getattr(user, "leave_start", None),
            "leave_end": getattr(user, "leave_end", None),
            "last_login": getattr(user, "last_login", None),
            "last_logout": getattr(user, "last_logout", None),
            "created_at": getattr(user, "created_at", None),
            "updated_at": getattr(user, "updated_at", None),
            "created_by": getattr(user, "created_by", None),
        }
        return data

router = APIRouter()


# ── GET /profile/me ──────────────────────────

@router.get("/profile/me")
def get_own_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve own profile information."""
    data = _safe_employee_out(current_user)
    return success_response(
        message="Profile retrieved successfully.",
        data=data,
    )


# ── PUT /profile/me ──────────────────────────

@router.put("/profile/me")
def update_own_profile(
    body: EmployeeProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update own profile fields (Phone, Photo, Designation, Department)."""
    updated_user = employee_service.update_own_profile(db, current_user.id, body)
    data = _safe_employee_out(updated_user)
    return success_response(
        message="Profile updated successfully.",
        data=data,
    )


# ── GET / ───────────────────────────────────

@router.get("")
def list_employees_route(
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    department: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    include_archived: bool = Query(default=False, description="Include archived employees in results"),
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all employees with search, filters, and pagination.
    Accessible to all authenticated users (needed for assignment dropdowns).
    By default excludes archived employees unless include_archived=true
    or is_active filter is explicitly provided.
    """
    total, items = employee_service.list_employees(
        db,
        search=search,
        role=role,
        department=department,
        is_active=is_active,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )

    serialized_items = [_safe_employee_out(u) for u in items]
    data = {
        "total": total,
        "page": page,
        "page_size": page_size or 10,
        "items": serialized_items,
        "total_pages": max(1, math.ceil(total / (page_size or 10))),
    }

    return success_response(
        message="Employees retrieved successfully.",
        data=data,
    )


# ── POST / ──────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_employee_route(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Register a new system user and auto-generate an employee code."""
    new_emp = employee_service.create_employee(db, body, created_by=admin.id)
    data = _safe_employee_out(new_emp)
    return success_response(
        message="Employee account registered successfully.",
        data=data,
    )


# ── GET /{id} ───────────────────────────────

@router.get("/{id}")
def get_employee_route(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieve single employee detail by ID."""
    emp = employee_service.get_employee_by_id(db, id)
    data = _safe_employee_out(emp)
    return success_response(
        message="Employee retrieved successfully.",
        data=data,
    )


# ── PUT /{id} ───────────────────────────────

@router.put("/{id}")
def update_employee_route(
    id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update employee record properties."""
    updated_emp = employee_service.update_employee(db, id, body)
    data = _safe_employee_out(updated_emp)
    return success_response(
        message="Employee updated successfully.",
        data=data,
    )


# ── PATCH /{id}/status ───────────────────────

@router.patch("/{id}/status")
def update_employee_status_route(
    id: int,
    body: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Toggle employee status (active/inactive). Self-deactivation prohibited."""
    updated_emp = employee_service.update_employee_status(db, id, is_active=body.is_active, action_by=admin.id)
    data = _safe_employee_out(updated_emp)
    return success_response(
        message="Employee status updated successfully.",
        data=data,
    )


# ── PATCH /{id}/reset-password ───────────────

@router.patch("/{id}/reset-password")
def reset_employee_password_route(
    id: int,
    body: EmployeePasswordReset,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Reset employee account password."""
    updated_emp = reset_employee_password(db, employee_id=id, new_password=body.password)
    data = _safe_employee_out(updated_emp)
    return success_response(
        message="Employee password reset successfully.",
        data=data,
    )


# ── PATCH /{id}/archive ──────────────────────────

@router.patch("/{id}/archive")
def archive_employee_route(
    id: int,
    body: EmployeeArchiveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Archive an employee with reason, optional leave dates, and optional
    applicant reassignment.

    Documents, messages, and notifications NEVER prevent archiving.
    Only assigned applicants matter — and they must be reassigned before
    archiving if they exist.

    Query parameters for reassignment:
      reassignment_mode = "auto"   — evenly distribute among active employees
      reassignment_mode = "manual" — assign all to target_employee_id

    If the employee has assigned applicants, one of the above modes is required.
    If they have no applicants, the employee is archived immediately.
    """
    result = employee_service.archive_employee(
        db,
        employee_id=id,
        admin_id=admin.id,
        reason=body.reason,
        leave_start=body.leave_start,
        leave_end=body.leave_end,
        reassignment_mode=body.reassignment_mode,
        target_employee_id=body.target_employee_id,
    )

    data = _safe_employee_out(result["employee"])
    data["archive_result"] = result["archive_result"]

    return success_response(
        message=f"Employee '{result['employee'].name}' archived successfully.",
        data=data,
    )


# ── PATCH /{id}/unarchive ────────────────────────

@router.patch("/{id}/unarchive")
def unarchive_employee_route(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Unarchive an employee and restore active status.
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    user.is_active = True
    user.archived_at = None
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to unarchive employee.")

    data = _safe_employee_out(user)
    return success_response(message="Employee unarchived and reactivated successfully.", data=data)
