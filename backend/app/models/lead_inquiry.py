"""
Ready2Go CRM — Lead Inquiry Model

Captures inquiries from website, phone, walk-in, WhatsApp, and social media.
Phase 1: CRM-side management only (manual entry by employees).
Phase 2: Website API integration.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeadInquiry(Base):
    __tablename__ = "lead_inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True
    )
    lead_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    visa_type: Mapped[str] = mapped_column(String(30), nullable=False, default="student")
    preferred_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="WEBSITE")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="NEW")
    assigned_employee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    converted_to_applicant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    converted_applicant_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    assigned_employee = relationship("User", foreign_keys=[assigned_employee_id])
    activities = relationship("LeadActivity", back_populates="lead", lazy="dynamic")
    notes = relationship("LeadNote", back_populates="lead", lazy="dynamic")

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_lead_inquiries_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LeadInquiry {self.lead_number}: {self.full_name}>"
