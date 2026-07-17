"""
Ready2Go CRM — Authentication & Security Service

Business logic for:
    • Credential validation with account lock protection
    • JWT token creation and session management
    • Password management (change, reset, history, policy)
    • Login/logout activity recording
    • Security event logging

Routes call these functions — they never touch the DB directly.
"""

import re
import secrets
import string
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.activity_log import ActivityLog
from app.models.user import PasswordHistory, User

# ── Password Policy ──────────────────────────────

_MIN_PASSWORD_LENGTH = 8
_PASSWORD_HISTORY_COUNT = 3
_MAX_FAILED_LOGIN_ATTEMPTS = 5
_ACCOUNT_LOCK_MINUTES = 30


def _validate_password_policy(password: str) -> str | None:
    """
    Validate password against enterprise policy.
    Returns an error message string if invalid, or None if valid.
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", password):
        return "Password must contain at least one special character."
    return None


def _check_password_history(db: Session, user_id: int, new_password_hash: str) -> bool:
    """Check if the new password was used recently (last N entries)."""
    recent_entries = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(_PASSWORD_HISTORY_COUNT)
        .all()
    )
    for entry in recent_entries:
        if verify_password(new_password_hash, entry.password_hash):
            return False
    return True


def _record_password_history(db: Session, user_id: int, password_hash: str) -> None:
    """Store hashed password in history and trim to max count."""
    entry = PasswordHistory(user_id=user_id, password_hash=password_hash)
    db.add(entry)

    # Trim old entries, keeping only the most recent N
    total = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .count()
    )
    if total > _PASSWORD_HISTORY_COUNT:
        excess = total - _PASSWORD_HISTORY_COUNT
        old_entries = (
            db.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.asc())
            .limit(excess)
            .all()
        )
        for old in old_entries:
            db.delete(old)


def _log_security_event(
    db: Session,
    user_id: int,
    event_type: str,
    details: str | None = None,
    ip_address: str | None = None,
    browser: str | None = None,
) -> None:
    """Record a security event in the activity log."""
    log = ActivityLog(
        user_id=user_id,
        login_time=datetime.now(timezone.utc),
        ip_address=ip_address,
        browser=browser,
        device=event_type,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(chars) for _ in range(length))


# ── Authentication ───────────────────────────────

def authenticate_user(
    db: Session,
    email: str,
    password: str,
    ip_address: str | None = None,
    browser: str | None = None,
) -> User | None:
    """
    Validate credentials with account lock protection.
    Returns None when authentication fails.
    Raises HTTPException if the account is locked.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        return None

    now = datetime.now(timezone.utc)

    # Safely access new columns (may not exist in DB until migration runs)
    try:
        locked_until = user.locked_until
        failed_attempts = user.failed_login_attempts or 0
    except (OperationalError, ProgrammingError):
        locked_until = None
        failed_attempts = 0

    # Check account lock
    if locked_until and locked_until > now:
        _log_security_event(db, user.id, "LOGIN_LOCKED", "Attempt while locked", ip_address, browser)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Your account has been temporarily locked due to too many failed login attempts. Please contact your administrator or try again later.",
        )

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        # Increment failed attempts (if security columns exist)
        try:
            user.failed_login_attempts = failed_attempts + 1
            if user.failed_login_attempts >= _MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=_ACCOUNT_LOCK_MINUTES)
                _log_security_event(db, user.id, "ACCOUNT_LOCKED", f"Locked after {_MAX_FAILED_LOGIN_ATTEMPTS} failures", ip_address, browser)
            db.commit()
        except Exception:
            db.rollback()

        _log_security_event(db, user.id, "LOGIN_FAILED", f"Failed ({failed_attempts + 1}/{_MAX_FAILED_LOGIN_ATTEMPTS})", ip_address, browser)
        return None

    # Successful login — reset (if security columns exist)
    from sqlalchemy.exc import OperationalError, ProgrammingError
    try:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
    except (OperationalError, ProgrammingError):
        db.rollback()
        # Columns don't exist yet — login still succeeds without tracking
    except Exception:
        db.rollback()

    return user


def generate_token(user: User) -> str:
    """Create a JWT access token with the user's identity and role."""
    return create_access_token(
        subject=user.id,
        role=user.role,
        name=user.name,
    )


# ── Password Management ──────────────────────────

def change_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str,
    confirm_password: str,
    ip_address: str | None = None,
    browser: str | None = None,
) -> User:
    """
    Change a user's own password after verification.
    Validates policy, history, and current credential.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not verify_password(current_password, user.password_hash):
        _log_security_event(db, user_id, "PASSWORD_CHANGE_FAILED", "Incorrect current password", ip_address, browser)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirm password do not match.")

    # Validate password policy
    policy_error = _validate_password_policy(new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password.")

    # Check password history
    if not _check_password_history(db, user_id, new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You cannot reuse any of your last {_PASSWORD_HISTORY_COUNT} passwords.",
        )

    # Update password
    new_hash = hash_password(new_password)
    user.password_hash = new_hash
    user.must_change_password = False

    # Safely access new columns (may not exist in DB until migration runs)
    try:
        user.last_password_change = datetime.now(timezone.utc)
        user.token_version += 1
    except Exception:
        pass

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password.")

    # Record password history
    _record_password_history(db, user_id, new_hash)

    _log_security_event(db, user_id, "PASSWORD_CHANGED", "Password changed successfully", ip_address, browser)

    return user


def admin_reset_password(
    db: Session,
    target_user_id: int,
    new_password: str,
    action_by: int,
    ip_address: str | None = None,
    browser: str | None = None,
) -> User:
    """
    Admin-only: Reset a user's password with policy validation
    and set must_change_password flag.
    """
    if action_by == target_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reset your own password. Use Change Password instead.")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    policy_error = _validate_password_policy(new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    new_hash = hash_password(new_password)
    user.password_hash = new_hash
    user.must_change_password = True

    # Safely access new columns (may not exist in DB until migration runs)
    try:
        user.token_version += 1
    except Exception:
        pass

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password.")

    # Record to password history
    _record_password_history(db, target_user_id, new_hash)

    _log_security_event(db, target_user_id, "PASSWORD_RESET", f"Password reset by admin #{action_by}", ip_address, browser)

    return user


def unlock_account(db: Session, target_user_id: int, action_by: int) -> User:
    """Admin-only: Unlock a locked user account."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Safely access new columns (may not exist in DB until migration runs)
    try:
        user.failed_login_attempts = 0
        user.locked_until = None
    except Exception:
        pass

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to unlock account.")

    _log_security_event(db, target_user_id, "ACCOUNT_UNLOCKED", f"Account unlocked by admin #{action_by}")

    return user


# ── Session Management ───────────────────────────

def get_login_history(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    """Retrieve login history for a user."""
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.login_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "login_time": log.login_time,
            "logout_time": log.logout_time,
            "ip_address": log.ip_address,
            "browser": log.browser,
            "event_type": log.device or ("login" if log.logout_time is None else "logout"),
        }
        for log in logs
    ]


def get_active_sessions(db: Session, user_id: int) -> list[dict]:
    """Retrieve currently active sessions for a user."""
    sessions = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.logout_time.is_(None),
            ActivityLog.login_time.isnot(None),
        )
        .order_by(ActivityLog.login_time.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "login_time": s.login_time,
            "ip_address": s.ip_address,
            "browser": s.browser,
        }
        for s in sessions
    ]


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
        device=device or "LOGIN_SUCCESS",
        login_time=now_utc,
    )
    db.add(log)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_login = now_utc

    try:
        db.commit()
        db.refresh(log)
    except Exception:
        db.rollback()
        raise

    _log_security_event(db, user_id, "LOGIN_SUCCESS", "Successful login", ip_address, browser)

    return log


def record_logout(db: Session, user_id: int) -> bool:
    """Find and stamp the most recent login entry with logout time."""
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

    _log_security_event(db, user_id, "LOGOUT", "User logged out")

    return True


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a single user by primary key."""
    return db.query(User).filter(User.id == user_id).first()
