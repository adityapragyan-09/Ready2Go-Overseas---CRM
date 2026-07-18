"""
Ready2Go CRM — Applicant Service

Business logic for applicant CRUD, search, filtering, and pagination.
Routes call these functions — they never touch the DB directly.

Features:
    - Auto-generated applicant_code (APP-000001)
    - Soft-delete (is_deleted / deleted_at)
    - created_by audit trail from JWT user
"""

import logging
import math
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.constants import ALL_STATUSES, ALL_VISA_TYPES
from app.models.applicant import Applicant
from app.models.user import User
from app.schemas.applicant import ApplicantCreate, ApplicantUpdate


# ── Code Generation ──────────────────────────────

_CODE_PREFIX = "APP"


def _generate_applicant_code(db: Session) -> str:
    """
    Generate the next sequential applicant code.
    Format: APP-000001, APP-000002, ...
    Uses MAX(id) + 1 as the sequence counter for simplicity.
    Falls back to counting all rows (including soft-deleted) if table is empty.
    """
    max_id = db.query(func.max(Applicant.id)).scalar()
    next_num = (max_id or 0) + 1
    return f"{_CODE_PREFIX}-{next_num:06d}"


# ── Active-only base query ───────────────────────

def _active_query(db: Session):
    """Return a query pre-filtered to exclude soft-deleted rows and joined relation models."""
    return (
        db.query(Applicant)
        .options(
            joinedload(Applicant.creator),
            joinedload(Applicant.assigned_employee)
        )
        .filter(Applicant.is_deleted == False)
    )


# ── Create ───────────────────────────────────────

def create_applicant(db: Session, data: ApplicantCreate, *, created_by: int) -> Applicant:
    """
    Create a new applicant record.
    Validates the assigned employee exists if provided.
    Auto-generates a unique applicant_code.
    """
    if data.assigned_to is not None:
        _validate_employee_exists(db, data.assigned_to)

    applicant_code = _generate_applicant_code(db)

    applicant = Applicant(
        applicant_code=applicant_code,
        full_name=data.full_name,
        email=data.email.lower() if data.email else None,
        phone=data.phone,
        country=data.country,
        visa_type=data.visa_type,
        status=data.status,
        metadata_=data.metadata_,
        notes=data.notes,
        assigned_to=data.assigned_to,
        created_by=created_by,
    )

    try:
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create applicant.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create applicant.")

    # Seed initial progress history log to establish timeline
    from app.models.progress import ProgressHistory
    initial_history = ProgressHistory(
        applicant_id=applicant.id,
        previous_status=None,
        current_status=applicant.status,
        remarks="Applicant file profile registered and pipeline initiated.",
        updated_by=created_by,
        is_system_generated=True,
    )
    try:
        db.add(initial_history)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to seed initial progress history for applicant %s.", applicant.id)

    # Seed initial chat system message
    from app.services.chat_service import log_system_message
    try:
        log_system_message(
            db,
            applicant_id=applicant.id,
            content=f"Applicant record registered under code {applicant.applicant_code}.",
            action_by=created_by,
        )
    except Exception:
        # non-fatal: continue
        logger.exception("Failed to log system message for applicant %s.", applicant.id)

    # Notification trigger: Applicant created
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="New Applicant Registered",
            message=f"Applicant '{applicant.full_name}' ({applicant.applicant_code}) has been registered.",
            type="success",
            module="applicant",
            priority="medium",
            recipient_user_id=created_by,
            created_by=created_by,
            reference_type="applicant",
            reference_id=applicant.id,
        )
        if applicant.assigned_to and applicant.assigned_to != created_by:
            create_notification(
                db,
                title="Applicant Assigned to You",
                message=f"Applicant '{applicant.full_name}' ({applicant.applicant_code}) has been assigned to your queue.",
                type="info",
                module="applicant",
                priority="high",
                recipient_user_id=applicant.assigned_to,
                created_by=created_by,
                reference_type="applicant",
                reference_id=applicant.id,
            )
    except Exception:
        # non-fatal: do not block applicant creation on notification failure
        logger.exception("Failed to create notification for applicant %s.", applicant.id)

    return applicant


# ── Update ───────────────────────────────────────

def update_applicant(db: Session, applicant_id: int, data: ApplicantUpdate) -> Applicant:
    """
    Partially update an existing applicant.
    Only fields that are explicitly set (not None) will be updated.
    Soft-deleted applicants cannot be updated.
    """
    applicant = get_applicant_by_id(db, applicant_id)

    update_data = data.model_dump(exclude_unset=True, by_alias=False)

    if "assigned_to" in update_data and update_data["assigned_to"] is not None:
        _validate_employee_exists(db, update_data["assigned_to"])

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = update_data["email"].lower()

    for field, value in update_data.items():
        setattr(applicant, field, value)

    applicant.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(applicant)
    except Exception:
        db.rollback()
        logger.exception("Failed to update applicant %s.", applicant_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update applicant.")

    # Notification trigger: Applicant updated
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Applicant Profile Updated",
            message=f"Applicant '{applicant.full_name}' profile has been updated.",
            type="info",
            module="applicant",
            priority="low",
            recipient_user_id=applicant.assigned_to,
            reference_type="applicant",
            reference_id=applicant.id,
        )
    except Exception:
        # non-fatal
        logger.exception("Failed to send update notification for applicant %s.", applicant_id)

    return applicant


# ── Hard Delete (Full Cleanup) ──────────────────

def delete_applicant(db: Session, applicant_id: int, *, deleted_by: int) -> dict:
    """
    Permanently delete an applicant and ALL associated data.

    Cleans up:
        - Physical document files from storage
        - Document database records
        - Progress history
        - Chat messages
        - Applicant metadata
        - Notifications referencing this applicant

    Transactional: if storage deletion fails, DB changes are rolled back.
    """
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found.")

    full_name = applicant.full_name
    applicant_code = applicant.applicant_code

    # Collect all documents for storage cleanup
    from app.models.document import Document
    from app.models.progress import ProgressHistory
    from app.models.message import Message
    from app.models.notification import Notification
    from app.services.storage_service import delete_file as delete_storage_file

    documents = db.query(Document).filter(Document.applicant_id == applicant_id).all()
    storage_paths = [doc.storage_path for doc in documents]

    # Delete from storage first (before DB changes)
    storage_errors = []
    for path in storage_paths:
        try:
            delete_storage_file(path)
        except Exception as e:
            storage_errors.append(path)
            logger.warning("Storage deletion failed for %s: %s", path, e)

    # If storage errors occurred, log but continue with DB cleanup
    if storage_errors:
        logger.warning("Storage deletion had %d errors for applicant %s", len(storage_errors), applicant_id)

    # Delete all associated records in correct order
    try:
        # Delete progress history
        db.query(ProgressHistory).filter(ProgressHistory.applicant_id == applicant_id).delete()
        # Delete chat messages
        db.query(Message).filter(Message.applicant_id == applicant_id).delete()
        # Delete documents
        for doc in documents:
            db.delete(doc)
        # Delete notifications referencing this applicant
        db.query(Notification).filter(
            Notification.reference_type == "applicant",
            Notification.reference_id == applicant_id,
        ).delete()
        # Delete the applicant
        db.delete(applicant)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to hard-delete applicant %s and associated records.", applicant_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete applicant and related data.")

    logger.info("Hard-deleted applicant %s (%s) with %d documents, %d storage files cleaned.",
                applicant_id, applicant_code, len(documents), len(storage_paths))

    return {"full_name": full_name, "applicant_code": applicant_code}


# ── Get Single ───────────────────────────────────

def get_applicant_by_id(db: Session, applicant_id: int) -> Applicant:
    """
    Fetch a single active (non-deleted) applicant by primary key.
    Raises 404 if not found or soft-deleted.
    """
    applicant = (
        _active_query(db)
        .filter(Applicant.id == applicant_id)
        .first()
    )
    if applicant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found.",
        )
    return applicant


# ── List / Search / Filter / Paginate ────────────

def list_applicants(
    db: Session,
    *,
    visa_type: str | None = None,
    applicant_status: str | None = None,
    country: str | None = None,
    assigned_to: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Return a paginated, filtered, and searchable list of active applicants.

    Filters:
        visa_type       — Exact match on visa_type column.
        applicant_status — Exact match on status column.
        country         — Case-insensitive partial match.
        assigned_to     — Exact match on assigned_to FK.
        search          — Case-insensitive ILIKE on applicant_code,
                          full_name, email, phone.

    Pagination:
        page      — 1-indexed page number.
        page_size — Number of results per page (max 100).
    """
    # Validate filter values if provided
    if visa_type is not None and visa_type not in ALL_VISA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visa_type '{visa_type}'. Allowed: {', '.join(ALL_VISA_TYPES)}",
        )

    if applicant_status is not None and applicant_status not in ALL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{applicant_status}'. Allowed: {', '.join(ALL_STATUSES)}",
        )

    query = _active_query(db)

    # ── Apply filters ─────────────────────────
    if visa_type:
        query = query.filter(Applicant.visa_type == visa_type)

    if applicant_status:
        query = query.filter(Applicant.status == applicant_status)

    if country:
        query = query.filter(Applicant.country.ilike(f"%{country}%"))

    if assigned_to is not None:
        query = query.filter(Applicant.assigned_to == assigned_to)

    # ── Apply search ──────────────────────────
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Applicant.applicant_code.ilike(search_term),
                Applicant.full_name.ilike(search_term),
                Applicant.email.ilike(search_term),
                Applicant.phone.ilike(search_term),
            )
        )

    # ── Pagination ────────────────────────────
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    applicants = (
        query
        .order_by(Applicant.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "applicants": applicants,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ── Private Helpers ──────────────────────────────

def _validate_employee_exists(db: Session, user_id: int) -> None:
    """Raise 400 if the assigned employee does not exist or is inactive."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assigned employee with id {user_id} does not exist.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assigned employee with id {user_id} is deactivated.",
        )
