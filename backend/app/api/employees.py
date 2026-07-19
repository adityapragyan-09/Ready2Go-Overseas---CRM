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
from datetime import datetime, timezone

from app.models.applicant import Applicant
from app.services import employee_service
from app.services.auth_service import reset_employee_password
from app.utils.response import error_response, success_response

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
    data = EmployeeOut.model_validate(current_user).model_dump(by_alias=True)
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
    data = EmployeeOut.model_validate(updated_user).model_dump(by_alias=True)
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
    
    serialized_items = [EmployeeOut.model_validate(u).model_dump(by_alias=True) for u in items]
    data = EmployeeListResponse(
        total_count=total,
        page=page,
        page_size=page_size or 10,  # Central default representation
        items=serialized_items,
    ).model_dump(by_alias=True)

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
    data = EmployeeOut.model_validate(new_emp).model_dump(by_alias=True)
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
    data = EmployeeOut.model_validate(emp).model_dump(by_alias=True)
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
    data = EmployeeOut.model_validate(updated_emp).model_dump(by_alias=True)
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
    data = EmployeeOut.model_validate(updated_emp).model_dump(by_alias=True)
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
    data = EmployeeOut.model_validate(updated_emp).model_dump(by_alias=True)
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

    data = EmployeeOut.model_validate(user).model_dump(by_alias=True)
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

    data = EmployeeOut.model_validate(user).model_dump(by_alias=True)
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

    assigned_count = db.query(Applicant).filter(Applicant.assigned_to == id, Applicant.is_deleted == False).count()
    if assigned_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This employee currently has {assigned_count} assigned applicant(s). Transfer them before deleting.",
        )

    name = user.name
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete employee.")

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
