"""
Ready2Go CRM — Message Model

Internal chat messages between CRM users, scoped to a specific applicant.
Used for collaboration on applicant cases.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    applicant = relationship("Applicant", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} type={self.message_type} sender={self.sender_id} applicant={self.applicant_id}>"


# Composite Index for optimized chronological chat timelines query
Index("ix_messages_applicant_id_created_at", Message.applicant_id, Message.created_at)
