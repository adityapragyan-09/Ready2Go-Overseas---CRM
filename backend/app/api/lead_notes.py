"""
Ready2Go CRM — Lead Advisor Notes Routes

Router: /api/v1/lead-inquiries/{lead_id}/notes
Access Level: Authenticated Users (JWT required)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.lead_note import LeadNote
from app.models.user import User
from app.schemas.lead_note import LeadNoteCreate, LeadNoteResponse, LeadNoteUpdate
from app.services.lead_activity_service import log_activity
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_note(note: LeadNote) -> dict:
    return LeadNoteResponse(
        id=note.id,
        uuid=note.uuid,
        lead_id=note.lead_id,
        note=note.note,
        author_name=note.author.name if note.author else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
    ).model_dump()


# ── POST /{lead_id}/notes ─────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_note_route(
    lead_id: int,
    body: LeadNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an internal advisor note to a lead inquiry."""
    from app.models.lead_inquiry import LeadInquiry
    lead = db.query(LeadInquiry).filter(LeadInquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    note = LeadNote(lead_id=lead_id, note=body.note, created_by=current_user.id)
    db.add(note)
    try:
        db.commit()
        db.refresh(note)
    except Exception:
        db.rollback()
        logger.exception("Failed to create note for lead %s", lead_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create note.")

    log_activity(db, lead_id=lead_id, action="NOTE_ADDED",
                 description="Advisor note added", created_by=current_user.id)

    return success_response(message="Note added successfully.", data=_serialize_note(note))


# ── GET /{lead_id}/notes ─────────────────

@router.get("")
def list_notes_route(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all notes for a lead inquiry, newest first."""
    from app.models.lead_inquiry import LeadInquiry
    lead = db.query(LeadInquiry).filter(LeadInquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    notes = (
        db.query(LeadNote)
        .filter(LeadNote.lead_id == lead_id, LeadNote.deleted_at.is_(None))
        .order_by(LeadNote.created_at.desc())
        .all()
    )

    return success_response(
        message="Notes retrieved successfully.",
        data=[_serialize_note(n) for n in notes],
    )


# ── PUT /notes/{note_id} ─────────────────
# Route at /api/v1/notes/{id} — separate router

notes_router = APIRouter()


@notes_router.put("/{note_id}")
def update_note_route(
    note_id: int,
    body: LeadNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing advisor note."""
    note = db.query(LeadNote).filter(LeadNote.id == note_id, LeadNote.deleted_at.is_(None)).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    note.note = body.note
    note.updated_by = current_user.id

    try:
        db.commit()
        db.refresh(note)
    except Exception:
        db.rollback()
        logger.exception("Failed to update note %s", note_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update note.")

    log_activity(db, lead_id=note.lead_id, action="NOTE_EDITED",
                 description="Advisor note edited", created_by=current_user.id)

    return success_response(message="Note updated successfully.", data=_serialize_note(note))


# ── DELETE /notes/{note_id} ──────────────

@notes_router.delete("/{note_id}")
def delete_note_route(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete an advisor note."""
    note = db.query(LeadNote).filter(LeadNote.id == note_id, LeadNote.deleted_at.is_(None)).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    from datetime import datetime, timezone
    note.deleted_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete note %s", note_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete note.")

    log_activity(db, lead_id=note.lead_id, action="NOTE_DELETED",
                 description="Advisor note removed", created_by=current_user.id)

    return success_response(message="Note deleted successfully.")
