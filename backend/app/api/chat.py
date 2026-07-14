"""
Ready2Go CRM — Internal Chat Routes

Router: /api/v1/chat
Access Level: Authenticated Users (JWT required)

Endpoints:
    GET    /applicant/{id}  — Fetch conversation thread history
    POST   /applicant/{id}  — Post a message inside the thread
    DELETE /{message_id}    — Soft delete own message
    GET    /latest/{id}     — Fetch latest message in thread
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.message import Message
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse
from app.services.chat_service import (
    create_message,
    get_conversation,
    get_latest_message,
    soft_delete_message,
)
from app.utils.response import success_response

router = APIRouter()


def _serialize_message(entry: Message) -> dict:
    """Helper to convert ORM message to standard payload dictionary matching alias keys."""
    return ChatMessageResponse(
        id=entry.id,
        applicant_id=entry.applicant_id,
        sender_id=entry.sender_id,
        content=entry.content,
        message_type=entry.message_type,
        attachment_url=entry.attachment_url,
        is_system_message=entry.is_system_message,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        sender_name=entry.sender.name if entry.sender else "System",
    ).model_dump(by_alias=True)


# ── GET /applicant/{id} ──────────────────────────

@router.get("/applicant/{id}")
def get_conversation_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full historical conversation timeline for an applicant.
    """
    messages = get_conversation(db, applicant_id=id)
    chat_data = [_serialize_message(m) for m in messages]

    return success_response(
        message="Conversation retrieved successfully.",
        data=chat_data,
    )


# ── POST /applicant/{id} ──────────────────────────

@router.post("/applicant/{id}", status_code=status.HTTP_201_CREATED)
def create_message_route(
    id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new chat message inside the applicant collaboration thread.
    """
    entry = create_message(
        db,
        applicant_id=id,
        sender_id=current_user.id,
        content=payload.content,
        message_type=payload.message_type,
        attachment_url=payload.attachment_url,
        is_system=False,
    )

    return success_response(
        message="Message sent successfully.",
        data=_serialize_message(entry),
    )


# ── DELETE /{message_id} ──────────────────────────

@router.delete("/{message_id}")
def delete_message_route(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a message. Sender owner or Admin role required.
    """
    entry = soft_delete_message(
        db,
        message_id=message_id,
        user_id=current_user.id,
    )

    return success_response(
        message="Message deleted successfully.",
        data=_serialize_message(entry),
    )


# ── GET /latest/{id} ─────────────────────────────

@router.get("/latest/{id}")
def get_latest_message_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve latest message from conversation thread.
    """
    entry = get_latest_message(db, applicant_id=id)

    return success_response(
        message="Latest message details retrieved successfully.",
        data=_serialize_message(entry),
    )
