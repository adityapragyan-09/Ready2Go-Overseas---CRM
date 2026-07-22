"""
Ready2Go CRM — Employee Service

Business logic for Employee/User administration.
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeProfileUpdate


def generate_next_employee_code(db: Session) -> str:
    """Generate sequential employee code e.g. EMP-000001, EMP-000002."""
    last_user = (
        db.query(User)
        .filter(User.employee_code.isnot(None))
        .order_by(User.id.desc())
        .first()
    )
    if not last_user or not last_user.employee_code:
        # Seed first user to start sequence if none has employee code
        return "EMP-000001"
    
    try:
        code_part = last_user.employee_code.replace("EMP-", "")
        next_num = int(code_part) + 1
        return f"EMP-{next_num:06d}"
    except (ValueError, TypeError):
        return "EMP-000001"


def list_employees(
    db: Session,
    search: str | None = None,
    role: str | None = None,
    department: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> tuple[int, list[User]]:
    """Retrieve filtered, paginated list of employees ordered by created_at DESC."""
    query = db.query(User)

    # 1. Search filter
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(search_filter),
                User.email.ilike(search_filter),
                User.employee_code.ilike(search_filter),
                User.department.ilike(search_filter),
            )
        )

    # 2. Field filters
    if role:
        query = query.filter(User.role == role)
    if department:
        query = query.filter(User.department.ilike(f"%{department}%"))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Count total entries before pagination
    total_count = query.count()

    # Pagination sizing
    limit = page_size or settings.DEFAULT_PAGE_SIZE
    offset = (page - 1) * limit

    items = (
        query.order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total_count, items


def get_employee_by_id(db: Session, employee_id: int) -> User:
    """Fetch single user from database by ID or raise HTTP 404."""
    user = db.query(User).filter(User.id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found in the registry.",
        )
    return user


def create_employee(db: Session, payload: EmployeeCreate, created_by: int) -> User:
    """Register a new user, auto-generating sequential employee_code and hashing password."""
    # Check email uniqueness
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee account with this email address already exists.",
        )

    # Make sure all active database entries have employee codes seeded if they lack one
    # This prevents counter restarts
    unseeded_users = db.query(User).filter(User.employee_code.is_(None)).order_by(User.id.asc()).all()
    if unseeded_users:
        counter = 1
        for u in unseeded_users:
            u.employee_code = f"EMP-{counter:06d}"
            counter += 1
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    code = generate_next_employee_code(db)
    hashed_pwd = hash_password(payload.password)

    new_user = User(
        employee_code=code,
        name=payload.full_name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hashed_pwd,
        role=payload.role,
        designation=payload.designation,
        department=payload.department,
        profile_photo=payload.profile_photo,
        is_active=True,
        created_by=created_by,
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    # Notification trigger: Employee created
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="New Employee Registered",
            message=f"Employee '{new_user.name}' ({code}) has been provisioned.",
            type="success",
            module="employee",
            priority="high",
            recipient_user_id=created_by,
            created_by=created_by,
            reference_type="user",
            reference_id=new_user.id,
        )
    except Exception:
        pass

    return new_user


def update_employee(db: Session, employee_id: int, payload: EmployeeUpdate) -> User:
    """Update employee registry details (Admin-only action)."""
    user = get_employee_by_id(db, employee_id)

    if payload.full_name is not None:
        user.name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.role is not None:
        user.role = payload.role
    if payload.designation is not None:
        user.designation = payload.designation
    if payload.department is not None:
        user.department = payload.department
    if payload.profile_photo is not None:
        user.profile_photo = payload.profile_photo

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    # Notification trigger: Employee updated
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Employee Profile Modified",
            message=f"Employee '{user.name}' registry has been updated by admin.",
            type="info",
            module="employee",
            priority="low",
            recipient_user_id=employee_id,
            reference_type="user",
            reference_id=employee_id,
        )
    except Exception:
        pass

    return user


def update_own_profile(db: Session, employee_id: int, payload: EmployeeProfileUpdate) -> User:
    """Update own employee profile (Designation, Department, Phone, Photo)."""
    user = get_employee_by_id(db, employee_id)

    if payload.phone is not None:
        user.phone = payload.phone
    if payload.designation is not None:
        user.designation = payload.designation
    if payload.department is not None:
        user.department = payload.department
    if payload.profile_photo is not None:
        user.profile_photo = payload.profile_photo

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def update_employee_status(db: Session, employee_id: int, is_active: bool, action_by: int) -> User:
    """Activate or deactivate user account. Prevents self-deactivation."""
    user = get_employee_by_id(db, employee_id)

    if not is_active and user.id == action_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-deactivation is prohibited. You cannot deactivate your logged in account.",
        )

    user.is_active = is_active
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    # Notification trigger: Employee activated/deactivated
    try:
        from app.services.notification_service import create_notification
        action = "Activated" if is_active else "Deactivated"
        create_notification(
            db,
            title=f"Employee {action}",
            message=f"Employee '{user.name}' account has been {action.lower()}.",
            type="success" if is_active else "warning",
            module="employee",
            priority="high",
            recipient_user_id=action_by,
            created_by=action_by,
            reference_type="user",
            reference_id=employee_id,
        )
    except Exception:
        pass

    return user


def list_activity_logs(
    db: Session,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list]:
    """
    Retrieve audit logs database rows joining with User model for employee metadata.
    """
    from app.models.activity_log import ActivityLog
    from app.models.user import User

    query = db.query(ActivityLog, User.name, User.employee_code).join(User, ActivityLog.user_id == User.id)

    if user_id is not None:
        query = query.filter(ActivityLog.user_id == user_id)

    total_count = query.count()
    offset = (page - 1) * page_size
    
    results = (
        query.order_by(ActivityLog.login_time.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for log, name, code in results:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "employee_name": name,
            "employee_code": code,
            "login_time": log.login_time,
            "logout_time": log.logout_time,
            "ip_address": log.ip_address,
            "browser": log.browser,
            "device": log.device,
        })

    return total_count, items
