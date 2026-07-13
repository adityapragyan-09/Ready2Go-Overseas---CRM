"""
Ready2Go CRM — Message Model

Internal chat messages between CRM users, scoped to a specific applicant.
Used for collaboration on applicant cases.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applicants.id"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    applicant = relationship("Applicant", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

    def __repr__(self) -> str:
        return f"<Message sender={self.sender_id} applicant={self.applicant_id}>"
