"""
Ready2Go CRM — Employee Management Routes

Router: /api/v1/employees
Access Level:
    - Profile me: Authenticated Users (JWT required)
    - All other endpoints: Administrators only (require_admin dependency)
"""

from fastapi import APIRouter, Depends, Query, status
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
from app.services import employee_service
from app.utils.response import success_response

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

@router.get("/")
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

@router.post("/", status_code=status.HTTP_201_CREATED)
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
    updated_emp = employee_service.reset_employee_password(db, id, new_password=body.password)
    data = EmployeeOut.model_validate(updated_emp).model_dump(by_alias=True)
    return success_response(
        message="Employee password reset successfully.",
        data=data,
    )
