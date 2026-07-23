"""
Ready2Go CRM — Employee Service

Business logic for Employee/User administration.
Archive replaces hard delete. Only assigned applicants block archiving —
documents, messages, notifications never prevent it.
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.applicant import Applicant
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
    include_archived: bool = False,
    page: int = 1,
    page_size: int | None = None,
) -> tuple[int, list[User]]:
    """Retrieve filtered, paginated list of employees ordered by created_at DESC.

    By default excludes archived employees. Pass include_archived=True to
    include them, or is_active explicitly to override the default filter.
    """
    query = db.query(User)

    # Default: exclude archived unless is_active is explicitly provided
    # or include_archived is True
    if is_active is None and not include_archived:
        query = query.filter(User.archived_at.is_(None))

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

    total_count = query.count()

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


def get_active_employees(db: Session, exclude_id: int | None = None) -> list[User]:
    """Return all active, non-archived employees for reassignment dropdowns."""
    query = db.query(User).filter(
        User.is_active == True,
        User.archived_at.is_(None),
    )
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.order_by(User.name.asc()).all()


def count_assigned_applicants(db: Session, employee_id: int) -> int:
    """Count active applicants assigned to an employee."""
    return (
        db.query(Applicant.id)
        .filter(
            Applicant.assigned_to == employee_id,
            Applicant.is_deleted == False,
        )
        .count()
    )


def _auto_distribute_applicants(
    db: Session,
    source_employee_id: int,
) -> dict:
    """Evenly distribute the source employee's applicants among all active
    non-archived employees using a round-robin by current workload.

    Returns a dict of {target_employee_id: [applicant_ids]} and a summary.
    """
    # Get all active employees excluding the source
    active_employees = get_active_employees(db, exclude_id=source_employee_id)
    if not active_employees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active employees available to receive the reassigned applicants.",
        )

    # Get the applicants to reassign
    applicants = (
        db.query(Applicant)
        .filter(
            Applicant.assigned_to == source_employee_id,
            Applicant.is_deleted == False,
        )
        .all()
    )

    if not applicants:
        return {"assignments": {}, "summary": []}

    # Build workload map
    workload = {
        e.id: count_assigned_applicants(db, e.id)
        for e in active_employees
    }

    # Sort employees by current workload (ascending) for even distribution
    # Use a priority queue approach: always assign to the least loaded
    assignments = {e.id: [] for e in active_employees}

    for applicant in applicants:
        # Find employee with lowest current workload
        target_id = min(workload, key=workload.get)
        assignments[target_id].append(applicant.id)
        workload[target_id] += 1

    # Build summary
    summary = []
    for e in active_employees:
        count = len(assignments.get(e.id, []))
        if count > 0:
            summary.append({
                "employee_id": e.id,
                "employee_name": e.name,
                "applicants_assigned": count,
            })

    # Execute reassignments
    for target_id, applicant_ids in assignments.items():
        if not applicant_ids:
            continue
        (
            db.query(Applicant)
            .filter(Applicant.id.in_(applicant_ids))
            .update({"assigned_to": target_id}, synchronize_session=False)
        )

    return {
        "assignments": {str(k): v for k, v in assignments.items() if v},
        "summary": summary,
    }


def _manual_reassign_applicants(
    db: Session,
    source_employee_id: int,
    target_employee_id: int,
) -> dict:
    """Reassign all applicants from source to target employee."""
    target = db.query(User).filter(User.id == target_employee_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_BAD_REQUEST,
            detail="Target employee not found.",
        )
    if not target.is_active or target.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target employee is not active or is archived.",
        )
    if target.id == source_employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reassign applicants to the same employee being archived.",
        )

    applicants = (
        db.query(Applicant)
        .filter(
            Applicant.assigned_to == source_employee_id,
            Applicant.is_deleted == False,
        )
        .all()
    )

    count = len(applicants)
    for app in applicants:
        app.assigned_to = target_employee_id

    return {
        "target_employee_id": target.id,
        "target_employee_name": target.name,
        "transferred_count": count,
    }


def archive_employee(
    db: Session,
    employee_id: int,
    admin_id: int,
    reason: str,
    leave_start: str | None = None,
    leave_end: str | None = None,
    reassignment_mode: str | None = None,
    target_employee_id: int | None = None,
) -> dict:
    """Archive an employee with full workflow:
    - Validates employee exists and is not self
    - Checks for assigned applicants
    - Handles reassignment if needed (auto or manual)
    - Sets archive fields
    - Logs activity
    - SINGLE TRANSACTION — rollback on any failure
    """
    user = db.query(User).filter(User.id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        )
    if user.id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot archive your own account.",
        )
    if user.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already archived.",
        )

    assigned_count = count_assigned_applicants(db, employee_id)
    reassignment_summary = None

    try:
        # Handle reassignment if employee has assigned applicants
        if assigned_count > 0:
            if reassignment_mode == "auto":
                result = _auto_distribute_applicants(db, employee_id)
                reassignment_summary = {
                    "mode": "auto",
                    "total_transferred": assigned_count,
                    "details": result["summary"],
                }
            elif reassignment_mode == "manual":
                if not target_employee_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Target employee ID is required for manual reassignment.",
                    )
                result = _manual_reassign_applicants(db, employee_id, target_employee_id)
                reassignment_summary = {
                    "mode": "manual",
                    "total_transferred": result["transferred_count"],
                    "target_employee_name": result["target_employee_name"],
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"This employee has {assigned_count} assigned applicant(s). "
                        "Specify reassignment_mode='auto' or 'manual' with a target_employee_id."
                    ),
                )

        # Set archive fields
        user.is_active = False
        user.archived_at = datetime.now(timezone.utc)
        user.archived_reason = reason

        if leave_start:
            try:
                user.leave_start = datetime.strptime(leave_start, "%Y-%m-%d")
            except ValueError:
                pass
        if leave_end:
            try:
                user.leave_end = datetime.strptime(leave_end, "%Y-%m-%d")
            except ValueError:
                pass

        db.flush()

        # Build result
        result_data = {
            "employee_id": employee_id,
            "employee_name": user.name,
            "reason": reason,
            "assigned_applicants_before": assigned_count,
            "reassignment": reassignment_summary,
        }

        # Create notification for archive
        try:
            from app.services.notification_service import create_notification
            create_notification(
                db,
                title="Employee Archived",
                message=f"Employee '{user.name}' archived. Reason: {reason}.",
                type="warning",
                module="employee",
                priority="high",
                created_by=admin_id,
                reference_type="user",
                reference_id=employee_id,
            )
        except Exception:
            pass

        # Create notification for reassignment if any
        if reassignment_summary:
            try:
                if reassignment_summary["mode"] == "manual":
                    create_notification(
                        db,
                        title="Applicants Reassigned",
                        message=(
                            f"{reassignment_summary['total_transferred']} applicant(s) "
                            f"reassigned to '{reassignment_summary['target_employee_name']}' "
                            f"after '{user.name}' was archived."
                        ),
                        type="info",
                        module="employee",
                        priority="medium",
                        created_by=admin_id,
                        reference_type="user",
                        reference_id=employee_id,
                    )
                elif reassignment_summary["mode"] == "auto":
                    for entry in reassignment_summary["details"]:
                        create_notification(
                            db,
                            title="Applicants Auto-Distributed",
                            message=(
                                f"{entry['applicants_assigned']} applicant(s) auto-assigned "
                                f"to '{entry['employee_name']}' after '{user.name}' was archived."
                            ),
                            type="info",
                            module="employee",
                            priority="medium",
                            created_by=admin_id,
                            reference_type="user",
                            reference_id=entry["employee_id"],
                        )
            except Exception:
                pass

        db.commit()
        db.refresh(user)

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive employee: {exc}",
        )

    return {"employee": user, "archive_result": result_data}


def create_employee(db: Session, payload: EmployeeCreate, created_by: int) -> User:
    """Register a new user, auto-generating sequential employee_code and hashing password."""
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee account with this email address already exists.",
        )

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
    """Retrieve audit logs joined with User model for employee metadata."""
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
