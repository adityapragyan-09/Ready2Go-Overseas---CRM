"""
Ready2Go CRM — Notification Model

Represents user alerts and audit trail notifications.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    module: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    
    recipient_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_user_id], backref="notifications")
    creator = relationship("User", foreign_keys=[created_by], backref="created_notifications")

    # Composite index for performance sorting and filtering of unread counts
    __table_args__ = (
        Index("ix_notifications_recipient_is_read_created_at", "recipient_user_id", "is_read", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.notification_code} is_read={self.is_read}>"
