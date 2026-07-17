"""
Ready2Go CRM — Authentication Routes

Router: /api/v1/auth (prefix set in main.py)

Endpoints:
    POST   /login   — Authenticate user and return JWT
    GET    /me      — Return the currently authenticated user profile
    POST   /logout  — Record logout in activity logs
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.user import UserOut
from app.services.auth_service import (
    authenticate_user,
    generate_token,
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
    """
    user = authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = generate_token(user)

    record_login(
        db=db,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        browser=request.headers.get("user-agent"),
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
