"""
Ready2Go CRM — Audit Log Model

Structured enterprise audit trail for every meaningful action in the CRM.
Preserves existing activity_logs (login/logout) as-is; this is a separate,
richer table for the Audit Center.

Categories:
  - employee_management, applicant_management, lead_management, documents,
    communication, leave_hr, notifications, security, system

Severity levels:
  - INFO, SUCCESS, WARNING, ERROR, CRITICAL
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Classification ────────────────────────────
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # ── Performer (denormalized name for query speed) ──
    performed_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    performed_by_name: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )

    # ── Target ────────────────────────────────────
    target_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    target_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    target_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    # ── Structured metadata ───────────────────────
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    old_value: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    new_value: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # ── Request context ───────────────────────────
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )

    # ── Timestamp ─────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ── Composite indexes for common query patterns ──
    __table_args__ = (
        Index("ix_audit_logs_target", "target_type", "target_id"),
        Index("ix_audit_logs_performed_category", "performed_by_id", "category", "created_at"),
        Index("ix_audit_logs_category_severity", "category", "severity", "created_at"),
    )

    # Relationships
    performed_by = relationship("User", backref="audit_logs", foreign_keys=[performed_by_id])

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} severity={self.severity}>"
