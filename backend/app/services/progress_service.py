"""
Ready2Go CRM — Progress Tracking Service

Handles status transition validations, appending immutable progress logs, and additional remarks.
"""

from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.constants.application_status import (
    INQUIRY,
    DOCUMENTS_PENDING,
    DOCUMENTS_SUBMITTED,
    APPLICATION_PROCESSING,
    INTERVIEW_SCHEDULED,
    VISA_APPROVED,
    VISA_REJECTED,
    CANCELLED,
    COMPLETED,
    ALL_STATUSES,
)
from app.models.applicant import Applicant
from app.models.progress import ProgressHistory

# Strict state transition matrix
VALID_TRANSITIONS = {
    INQUIRY: {DOCUMENTS_PENDING, CANCELLED},
    DOCUMENTS_PENDING: {DOCUMENTS_SUBMITTED, CANCELLED},
    DOCUMENTS_SUBMITTED: {APPLICATION_PROCESSING, CANCELLED},
    APPLICATION_PROCESSING: {INTERVIEW_SCHEDULED, VISA_APPROVED, VISA_REJECTED, CANCELLED},
    INTERVIEW_SCHEDULED: {VISA_APPROVED, VISA_REJECTED, CANCELLED},
    VISA_APPROVED: {COMPLETED, CANCELLED},
    COMPLETED: set(),
    VISA_REJECTED: set(),
    CANCELLED: set(),
}


def get_timeline(db: Session, applicant_id: int) -> list[ProgressHistory]:
    """
    Retrieve the complete, chronological progress history timeline for an applicant.
    Optimized with joined loading of the updating user to avoid N+1 queries.
    """
    # 1. Verify applicant exists and is active
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    # 2. Query history timeline
    return (
        db.query(ProgressHistory)
        .filter(ProgressHistory.applicant_id == applicant_id)
        .options(joinedload(ProgressHistory.updater))
        .order_by(ProgressHistory.updated_at.asc())
        .all()
    )


def update_status(
    db: Session,
    *,
    applicant_id: int,
    new_status: str,
    remarks: str,
    user_id: int,
    is_system: bool = False,
) -> ProgressHistory:
    """
    Validate and execute a status transition for an applicant.
    Appends an immutable entry to the progress history and updates Applicant.status.
    """
    # 1. Fetch Applicant
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    old_status = applicant.status
    
    # 2. Check if new status is valid constant
    if new_status not in ALL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'."
        )

    # 3. Reject if new status is same as current status
    if old_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Applicant is already in '{new_status}' status. Use comments to append notes instead."
        )

    # 4. Enforce strict transition rules
    allowed_next_states = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed_next_states:
        # User-friendly representation
        old_lbl = old_status.replace('_', ' ').title()
        new_lbl = new_status.replace('_', ' ').title()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow transition: Cannot move state from '{old_lbl}' to '{new_lbl}'."
        )

    # 5. Update Applicant Status
    applicant.status = new_status
    applicant.updated_at = datetime.now(timezone.utc)

    # 6. Append Immutable Progress Record
    history_entry = ProgressHistory(
        applicant_id=applicant_id,
        previous_status=old_status,
        current_status=new_status,
        remarks=remarks,
        updated_by=user_id,
        is_system_generated=is_system,
    )

    db.add(history_entry)
    try:
        db.commit()
        db.refresh(history_entry)
    except Exception:
        db.rollback()
        logger.exception("Failed to update status for applicant %s.", applicant_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update status.")

    # Log status change system message
    from app.services.chat_service import log_system_message
    old_lbl = old_status.replace('_', ' ').title()
    new_lbl = new_status.replace('_', ' ').title()
    log_system_message(
        db,
        applicant_id=applicant_id,
        content=f"Status transitioned from {old_lbl} to {new_lbl}: {remarks}",
        action_by=user_id,
    )

    # Load updater backref for payload serialization
    db.query(ProgressHistory).options(joinedload(ProgressHistory.updater)).filter(ProgressHistory.id == history_entry.id).first()

    # Notification trigger: Status updated
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Applicant Status Updated",
            message=f"Status changed from {old_lbl} to {new_lbl} for applicant #{applicant_id}.",
            type="info",
            module="progress",
            priority="high",
            recipient_user_id=applicant.assigned_to,
            created_by=user_id,
            reference_type="applicant",
            reference_id=applicant_id,
        )
    except Exception:
        logger.exception("Failed to send status update notification for applicant %s.", applicant_id)

    return history_entry


def add_note(
    db: Session,
    *,
    applicant_id: int,
    remarks: str,
    user_id: int,
) -> ProgressHistory:
    """
    Append an additional progress comment/note without changing the applicant's status.
    """
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    # Append note linked to current status
    history_entry = ProgressHistory(
        applicant_id=applicant_id,
        previous_status=applicant.status,
        current_status=applicant.status,
        remarks=remarks,
        updated_by=user_id,
        is_system_generated=False,
    )

    db.add(history_entry)
    try:
        db.commit()
        db.refresh(history_entry)
    except Exception:
        db.rollback()
        logger.exception("Failed to add progress note for applicant %s.", applicant_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add progress note.")

    # Load updater backref for response
    db.query(ProgressHistory).options(joinedload(ProgressHistory.updater)).filter(ProgressHistory.id == history_entry.id).first()

    # Notification trigger: Progress note added
    try:
        from app.services.notification_service import create_notification
        create_notification(
            db,
            title="Progress Note Added",
            message=f"New note added for applicant #{applicant_id}: {remarks[:80]}...",
            type="info",
            module="progress",
            priority="low",
            recipient_user_id=applicant.assigned_to,
            created_by=user_id,
            reference_type="applicant",
            reference_id=applicant_id,
        )
    except Exception:
        logger.exception("Failed to send notification for progress note on applicant %s.", applicant_id)

    return history_entry


def get_latest_progress(db: Session, applicant_id: int) -> ProgressHistory:
    """
    Retrieve the most recent progress history entry for an applicant.
    """
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    entry = (
        db.query(ProgressHistory)
        .filter(ProgressHistory.applicant_id == applicant_id)
        .options(joinedload(ProgressHistory.updater))
        .order_by(ProgressHistory.updated_at.desc())
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress history records exist for this applicant."
        )
    return entry
