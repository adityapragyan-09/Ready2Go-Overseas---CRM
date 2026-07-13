"""
Ready2Go CRM — Employee Management Routes

Router: /api/v1/employees (prefix set in main.py)
Access Level: Admin Only

Endpoints:
    GET    /       — Retrieve a list of all system users (employees & admins)
    POST   /       — Register a new user (employee or admin) with hashed credentials
    DELETE /{id}   — Delete an existing user account from the registry
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.utils.response import error_response, success_response

router = APIRouter()


# ── GET / ───────────────────────────────────

@router.get("/")
def list_employees(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retrieve a list of all active registered employees and admins.
    Access restricted to administrators.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    users_data = [UserOut.model_validate(u).model_dump() for u in users]
    
    return success_response(
        message="Users list retrieved successfully.",
        data=users_data,
    )


# ── POST / ──────────────────────────────────

@router.post("/")
def create_employee(
    body: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Register a new system user with designated credentials and role.
    Access restricted to administrators.
    """
    # Check email duplicate
    existing_user = db.query(User).filter(User.email == body.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Hash plain text password
    hashed_pwd = hash_password(body.password)

    # Create user model instance
    new_user = User(
        name=body.name,
        email=body.email.lower(),
        phone=body.phone,
        password_hash=hashed_pwd,
        role=body.role,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_data = UserOut.model_validate(new_user).model_dump()

    return success_response(
        message="Employee account created successfully.",
        data=user_data,
    )


# ── DELETE /{id} ─────────────────────────────

@router.delete("/{id}")
def delete_employee(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a user account from the registry.
    Prevents self-deletion. Access restricted to administrators.
    """
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found in the registry.",
        )

    # Prevent deleting current admin user
    if target_user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-deletion is prohibited. You cannot delete your logged in account.",
        )

    db.delete(target_user)
    db.commit()

    return success_response(
        message=f"Employee account '{target_user.name}' successfully deleted."
    )
