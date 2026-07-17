"""
Ready2Go CRM — Authentication & Security Routes

Router: /api/v1/auth (prefix set in main.py)

Endpoints:
    POST   /login            — Authenticate user and return JWT
    GET    /me               — Return the currently authenticated user profile
    POST   /logout           — Record logout in activity logs
    POST   /change-password  — Change own password
    GET    /sessions         — Get active sessions
    GET    /login-history    — Get login history
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest
from app.schemas.user import UserOut
from app.services.auth_service import (
    authenticate_user,
    change_password,
    generate_token,
    get_active_sessions,
    get_login_history,
    record_login,
    record_logout,
)
from app.utils.response import error_response, success_response

router = APIRouter()


# ── POST /login ──────────────────────────────

@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Validate credentials, issue a JWT, and record the login event.
    Includes account lock protection.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user = authenticate_user(db, body.email, body.password, ip_address=ip, browser=ua)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = generate_token(user)

    record_login(
        db=db,
        user_id=user.id,
        ip_address=ip,
        browser=ua,
    )

    user_data = UserOut.model_validate(user).model_dump()

    return success_response(
        "Login successful.",
        data={"token": token, "user": user_data},
    )


# ── GET /me ──────────────────────────────────

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    user_data = UserOut.model_validate(user).model_dump()
    return success_response("User profile retrieved.", data=user_data)


# ── POST /logout ─────────────────────────────

@router.post("/logout")
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record the logout event in activity logs."""
    updated = record_logout(db, user.id)
    if not updated:
        return error_response("No active session found to close.")
    return success_response("Logout recorded successfully.")


# ── POST /change-password ────────────────────

@router.post("/change-password")
def change_password_route(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change password with policy validation and history check.
    Increments token_version to invalidate other sessions.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user = change_password(
        db,
        user_id=current_user.id,
        current_password=body.current_password,
        new_password=body.new_password,
        confirm_password=body.confirm_password,
        ip_address=ip,
        browser=ua,
    )

    user_data = UserOut.model_validate(user).model_dump()
    return success_response("Password changed successfully.", data=user_data)


# ── GET /sessions ────────────────────────────

@router.get("/sessions")
def get_sessions_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active sessions for the current user."""
    sessions = get_active_sessions(db, current_user.id)
    return success_response("Active sessions retrieved.", data=sessions)


# ── GET /login-history ───────────────────────

@router.get("/login-history")
def login_history_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get login history for the current user."""
    history = get_login_history(db, current_user.id)
    return success_response("Login history retrieved.", data=history)
