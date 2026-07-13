"""
Ready2Go CRM — Authentication Service

Business logic for user authentication:
    • Credential validation
    • JWT token creation
    • Login/logout activity recording

Routes call these functions — they never touch the DB directly.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
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
    """
    Create a JWT access token with the user's identity and role.
    """
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
    """
    Create a new ActivityLog row capturing the login event.
    """
    log = ActivityLog(
        user_id=user_id,
        ip_address=ip_address,
        browser=browser,
        device=device,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def record_logout(db: Session, user_id: int) -> bool:
    """
    Find the most recent login entry for this user that has no
    logout_time and stamp it with the current UTC time.
    Returns True if a matching row was found and updated.
    """
    log = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id, ActivityLog.logout_time.is_(None))
        .order_by(ActivityLog.login_time.desc())
        .first()
    )
    if log is None:
        return False

    log.logout_time = datetime.now(timezone.utc)
    db.commit()
    return True


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a single user by primary key."""
    return db.query(User).filter(User.id == user_id).first()
