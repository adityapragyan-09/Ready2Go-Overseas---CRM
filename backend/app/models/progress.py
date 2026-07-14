"""
Ready2Go CRM — Progress History Model
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProgressHistory(Base):
    __tablename__ = "progress_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applicants.id"), nullable=False, index=True
    )
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    current_status: Mapped[str] = mapped_column(String(30), nullable=False)
    remarks: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    is_system_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Relationships ────────────────────────────
    applicant = relationship("Applicant", back_populates="progress_history")
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<ProgressHistory {self.id} — Applicant {self.applicant_id}: {self.previous_status} -> {self.current_status}>"


# Indexing Lookups for optimized performance
Index("ix_progress_history_applicant_id_updated_at", ProgressHistory.applicant_id, ProgressHistory.updated_at)
