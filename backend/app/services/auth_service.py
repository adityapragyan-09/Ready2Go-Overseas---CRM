"""
Ready2Go CRM — Authentication Service

Business logic for user authentication:
    • Credential validation
    • JWT token creation
    • Login/logout activity recording

Routes call these functions — they never touch the DB directly.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.activity_log import ActivityLog
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Validate credentials and return the User if successful.
    Returns None when the email is not found, the password is
    wrong, or the account has been deactivated.
    """
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def generate_token(user: User) -> str:
    """Create a JWT access token with the user's identity and role."""
    return create_access_token(
        subject=user.id,
        role=user.role,
        name=user.name,
    )


def record_login(
    db: Session,
    user_id: int,
    ip_address: str | None = None,
    browser: str | None = None,
    device: str | None = None,
) -> ActivityLog:
    """Create a new ActivityLog row capturing the login event."""
    now_utc = datetime.now(timezone.utc)
    log = ActivityLog(
        user_id=user_id,
        ip_address=ip_address,
        browser=browser,
        device=device,
        login_time=now_utc,
    )
    db.add(log)

    # Automatically update user.last_login
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_login = now_utc

    try:
        db.commit()
        db.refresh(log)
    except Exception:
        db.rollback()
        raise

    return log


def record_logout(db: Session, user_id: int) -> bool:
    """Find the most recent login entry and stamp it with logout time."""
    log = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id, ActivityLog.logout_time.is_(None))
        .order_by(ActivityLog.login_time.desc())
        .first()
    )
    if log is None:
        return False

    now_utc = datetime.now(timezone.utc)
    log.logout_time = now_utc

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_logout = now_utc

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True


def reset_employee_password(db: Session, employee_id: int, new_password: str) -> User:
    """Reset employee password by Admin."""
    user = db.query(User).filter(User.id == employee_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    user.password_hash = hash_password(new_password)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password.")

    return user
