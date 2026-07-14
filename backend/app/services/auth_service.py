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

    # Notification trigger: Login event
    try:
        from app.services.notification_service import create_notification
        user_obj = db.query(User).filter(User.id == user_id).first()
        user_name = user_obj.name if user_obj else f"User #{user_id}"
        create_notification(
            db,
            title="Employee Login",
            message=f"{user_name} logged into the CRM portal.",
            type="info",
            module="authentication",
            priority="low",
            recipient_user_id=user_id,
            created_by=user_id,
            reference_type="user",
            reference_id=user_id,
        )
    except Exception:
        pass  # Non-critical — never block auth flow

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

    now_utc = datetime.now(timezone.utc)
    log.logout_time = now_utc
    
    # Automatically update user.last_logout
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_logout = now_utc
        
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Notification trigger: Logout event
    try:
        from app.services.notification_service import create_notification
        user_obj = db.query(User).filter(User.id == user_id).first()
        user_name = user_obj.name if user_obj else f"User #{user_id}"
        create_notification(
            db,
            title="Employee Logout",
            message=f"{user_name} logged out of the CRM portal.",
            type="info",
            module="authentication",
            priority="low",
            recipient_user_id=user_id,
            created_by=user_id,
            reference_type="user",
            reference_id=user_id,
        )
    except Exception:
        pass

    return True


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a single user by primary key."""
    return db.query(User).filter(User.id == user_id).first()
