"""
Ready2Go CRM — Document Model

Represents file upload metadata for applicant documents stored in Supabase Storage.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applicants.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    stored_file_name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Soft delete ──────────────────────────────
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    # ── Relationships ────────────────────────────
    applicant = relationship("Applicant", foreign_keys=[applicant_id], back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="uploaded_documents")
    deleter = relationship("User", foreign_keys=[deleted_by], back_populates="deleted_documents")

    def __repr__(self) -> str:
        return f"<Document {self.document_code} — {self.original_file_name}>"
