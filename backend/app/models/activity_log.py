"""
Ready2Go CRM — Activity Log Model

Captures login/logout events and audit trail for user sessions.
Used by admins to monitor employee activity within the CRM.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    logout_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(256), nullable=True)
    device: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # ── Composite indexes for efficient querying ─────
    __table_args__ = (
        Index("ix_activity_logs_user_login", "user_id", "login_time"),
        Index("ix_activity_logs_login_logout", "login_time", "logout_time"),
    )

    # Relationships
    user = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog user_id={self.user_id} login={self.login_time}>"
