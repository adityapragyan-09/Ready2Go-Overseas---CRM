"""
Ready2Go CRM — Internal Chat Service

Handles messages dispatch, soft-deletes, system alerts seeding, and timeline lookup optimization.
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.applicant import Applicant
from app.models.message import Message
from app.models.user import User


def get_conversation(db: Session, applicant_id: int) -> list[Message]:
    """
    Retrieve the complete, chronological chat timeline for an applicant.
    Optimized with joined loading of the sender to prevent N+1 queries.
    Sorts newest messages last (created_at ASC).
    """
    # Verify applicant exists and is active
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    return (
        db.query(Message)
        .filter(Message.applicant_id == applicant_id, Message.is_deleted == False)  # noqa: E712
        .options(joinedload(Message.sender))
        .order_by(Message.created_at.asc())
        .all()
    )


def create_message(
    db: Session,
    *,
    applicant_id: int,
    sender_id: int,
    content: str,
    message_type: str = "text",
    attachment_url: str | None = None,
    is_system: bool = False,
) -> Message:
    """
    Post a new chat message inside the applicant collaboration thread.
    Restricted to authenticated CRM employees/admins.
    """
    # 1. Verify applicant exists
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    # 2. Verify sender role permissions
    sender = db.query(User).filter(User.id == sender_id, User.is_active == True).first()  # noqa: E712
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender account does not exist or is inactive."
        )
    
    if sender.role not in ["admin", "employee"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authenticated counselors/admins are allowed to post messages."
        )

    # 3. Create message record
    message = Message(
        applicant_id=applicant_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
        attachment_url=attachment_url,
        is_system_message=is_system,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # Load sender backref for serialization
    db.query(Message).options(joinedload(Message.sender)).filter(Message.id == message.id).first()

    # Notification trigger: New chat message
    if not is_system:
        try:
            from app.services.notification_service import create_notification
            create_notification(
                db,
                title="New Internal Message",
                message=f"New message in applicant #{applicant_id} thread.",
                type="info",
                module="chat",
                priority="medium",
                recipient_user_id=None,  # broadcast to all with access
                created_by=sender_id,
                reference_type="applicant",
                reference_id=applicant_id,
            )
        except Exception:
            pass

    return message


def log_system_message(
    db: Session,
    *,
    applicant_id: int,
    content: str,
    action_by: int | None = None,
) -> Message:
    """
    Automatically append an immutable system log message to the applicant chat thread.
    Falls back to first active admin if action_by is not provided.
    """
    # Resolve sender id (foreign key requirement)
    sender_id = action_by
    if not sender_id:
        admin = db.query(User).filter(User.role == "admin", User.is_active == True).first()  # noqa: E712
        sender_id = admin.id if admin else 1

    return create_message(
        db,
        applicant_id=applicant_id,
        sender_id=sender_id,
        content=content,
        message_type="system",
        is_system=True,
    )


def soft_delete_message(
    db: Session,
    *,
    message_id: int,
    user_id: int,
) -> Message:
    """
    Soft delete a chat message.
    Users can only delete their own messages, unless they hold the 'admin' role.
    """
    message = db.query(Message).filter(Message.id == message_id, Message.is_deleted == False).first()  # noqa: E712
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with ID {message_id} does not exist or has already been deleted."
        )

    # Authorization Check: sender ownership or admin role
    requester = db.query(User).filter(User.id == user_id).first()
    is_admin = requester.role == "admin" if requester else False

    if message.sender_id != user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You can only delete your own chat messages."
        )

    message.is_deleted = True
    message.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)

    return message


def get_latest_message(db: Session, applicant_id: int) -> Message:
    """
    Retrieve the most recent active message in the applicant's chat thread.
    """
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id, Applicant.is_deleted == False).first()  # noqa: E712
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicant with ID {applicant_id} does not exist or has been deleted."
        )

    entry = (
        db.query(Message)
        .filter(Message.applicant_id == applicant_id, Message.is_deleted == False)  # noqa: E712
        .options(joinedload(Message.sender))
        .order_by(Message.created_at.desc())
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No messages exist in this applicant's chat thread."
        )
    return entry
