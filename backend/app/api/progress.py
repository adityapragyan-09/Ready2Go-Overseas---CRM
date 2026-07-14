"""
Ready2Go CRM — Progress Tracking Routes

Router: /api/v1/progress
Access Level: Authenticated Users (JWT required)

Endpoints:
    GET    /applicant/{id}  — Fetch entire progress history timeline
    PUT    /applicant/{id}  — Update applicant status (validates transition rules)
    POST   /note            — Add comment/remark note to current status
    GET    /latest/{id}     — Fetch most recent progress node
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.progress import ProgressHistory
from app.schemas.progress import (
    NoteCreatePayload,
    ProgressHistoryResponse,
    StatusUpdatePayload,
)
from app.services.progress_service import (
    add_note,
    get_latest_progress,
    get_timeline,
    update_status,
)
from app.utils.response import success_response

router = APIRouter()


def _serialize_entry(entry: ProgressHistory) -> dict:
    """Helper to convert ORM entry to standard dict mapping updater name."""
    return ProgressHistoryResponse(
        id=entry.id,
        applicant_id=entry.applicant_id,
        previous_status=entry.previous_status,
        current_status=entry.current_status,
        remarks=entry.remarks,
        updated_by=entry.updated_by,
        updated_at=entry.updated_at,
        is_system_generated=entry.is_system_generated,
        updated_by_name=entry.updater.name if entry.updater else "System",
    ).model_dump()


# ── GET /applicant/{id} ──────────────────────────

@router.get("/applicant/{id}")
def get_timeline_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full historical progress timeline for an applicant.
    """
    entries = get_timeline(db, applicant_id=id)
    timeline_data = [_serialize_entry(e) for e in entries]

    return success_response(
        message="Applicant progress history retrieved successfully.",
        data=timeline_data,
    )


# ── PUT /applicant/{id} ──────────────────────────

@router.put("/applicant/{id}")
def update_status_route(
    id: int,
    payload: StatusUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger workflow transition and log immutable progress node.
    """
    entry = update_status(
        db,
        applicant_id=id,
        new_status=payload.status,
        remarks=payload.remarks,
        user_id=current_user.id,
        is_system=False,
    )

    return success_response(
        message="Applicant status updated successfully.",
        data=_serialize_entry(entry),
    )


# ── POST /note ───────────────────────────────────

@router.post("/note", status_code=status.HTTP_201_CREATED)
def add_note_route(
    payload: NoteCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Append progress comment log linked to current applicant status.
    """
    entry = add_note(
        db,
        applicant_id=payload.applicant_id,
        remarks=payload.remarks,
        user_id=current_user.id,
    )

    return success_response(
        message="Progress note appended successfully.",
        data=_serialize_entry(entry),
    )


# ── GET /latest/{id} ─────────────────────────────

@router.get("/latest/{id}")
def get_latest_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve latest recorded progress log node.
    """
    entry = get_latest_progress(db, applicant_id=id)

    return success_response(
        message="Latest progress details retrieved successfully.",
        data=_serialize_entry(entry),
    )
