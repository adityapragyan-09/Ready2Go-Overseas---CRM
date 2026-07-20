"""
Ready2Go CRM — Employee Management Routes

Router: /api/v1/employees
Access Level:
    - Profile me: Authenticated Users (JWT required)
    - All other endpoints: Administrators only (require_admin dependency)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeOut,
    EmployeePasswordReset,
    EmployeeProfileUpdate,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)
import logging
from datetime import datetime, timezone

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.applicant import Applicant
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
        # Fallback: serialize without triggering deferred loads
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
    """
    Retrieve own profile information.
    Accessible to all authenticated employees and admins.
    """
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
    """
    Update own profile fields (Phone, Photo, Designation, Department).
    Accessible to all authenticated employees and admins.
    """
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
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all employees with search query, filters, and paginated defaults.
    Access restricted to administrators.
    """
    total, items = employee_service.list_employees(
        db,
        search=search,
        role=role,
        department=department,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    
    serialized_items = [_safe_employee_out(u) for u in items]
    data = {
        "total_count": total,
        "page": page,
        "page_size": page_size or 10,
        "items": serialized_items,
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
    """
    Register a new system user and auto-generate an employee code.
    Access restricted to administrators.
    """
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
    """
    Retrieve single employee detail by ID.
    Access restricted to administrators.
    """
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
    """
    Update employee record properties.
    Access restricted to administrators.
    """
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
    """
    Toggle employee status (active/inactive). Self-deactivation is prohibited.
    Access restricted to administrators.
    """
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
    """
    Reset employee account password.
    Access restricted to administrators.
    """
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
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Archive an employee. Archived employees cannot login or be assigned.
    Access restricted to administrators.
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot archive your own account.")

    user.is_active = False
    user.archived_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to archive employee.")

    data = _safe_employee_out(user)
    return success_response(message="Employee archived successfully.", data=data)


# ── PATCH /{id}/unarchive ────────────────────────

@router.patch("/{id}/unarchive")
def unarchive_employee_route(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Unarchive an employee and restore active status.
    Access restricted to administrators.
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


# ── DELETE /{id} ────────────────────────────────

@router.delete("/{id}")
def delete_employee_route(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Permanently delete an employee.
    Only allowed if the employee has no assigned applicants.
    Access restricted to administrators.
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account.")

    name = user.name

    # Check all RESTRICT foreign keys before attempting deletion
    from app.models.document import Document
    from app.models.message import Message
    from app.models.progress import ProgressHistory

    blockers = []

    # applicant.created_by (RESTRICT)
    created_apps = db.query(Applicant.id).filter(Applicant.created_by == id).count()
    if created_apps > 0:
        blockers.append(f"applicants (created_by): {created_apps} records")

    # document.uploaded_by (RESTRICT)
    uploaded_docs = db.query(Document.id).filter(Document.uploaded_by == id).count()
    if uploaded_docs > 0:
        blockers.append(f"documents (uploaded_by): {uploaded_docs} records")

    # message.sender_id (RESTRICT)
    sent_msgs = db.query(Message.id).filter(Message.sender_id == id).count()
    if sent_msgs > 0:
        blockers.append(f"messages (sender_id): {sent_msgs} records")

    # progress.updated_by (RESTRICT)
    progress_updates = db.query(ProgressHistory.id).filter(ProgressHistory.updated_by == id).count()
    if progress_updates > 0:
        blockers.append(f"progress_history (updated_by): {progress_updates} records")

    # Also check assigned_to (should be SET NULL, but check anyway)
    assigned_count = db.query(Applicant).filter(Applicant.assigned_to == id, Applicant.is_deleted == False).count()
    if assigned_count > 0:
        blockers.append(f"applicants (assigned_to): {assigned_count} active applicants")

    if blockers:
        detail = "Employee cannot be deleted. The following references exist:\n" + "\n".join(f"  - {b}" for b in blockers)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    try:
        db.delete(user)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete employee. Database error: {exc}",
        )

    return success_response(message=f"Employee '{name}' deleted permanently.")


# ── POST /{id}/transfer-applicants ──────────────

@router.post("/{id}/transfer-applicants")
def transfer_applicants_route(
    id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Transfer all applicants from one employee to another.
    Access restricted to administrators.
    """
    from pydantic import BaseModel

    class TransferSchema(BaseModel):
        target_employee_id: int

    transfer = TransferSchema(**body)

    source_user = db.query(User).filter(User.id == id).first()
    if not source_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source employee not found.")

    target_user = db.query(User).filter(User.id == transfer.target_employee_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target employee not found.")

    applicants = db.query(Applicant).filter(Applicant.assigned_to == id, Applicant.is_deleted == False).all()
    count = len(applicants)

    for app in applicants:
        app.assigned_to = transfer.target_employee_id

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to transfer applicants.")

    return success_response(
        message=f"Successfully transferred {count} applicant(s) to '{target_user.name}'.",
        data={"transferred_count": count, "target_employee": target_user.name},
    )
