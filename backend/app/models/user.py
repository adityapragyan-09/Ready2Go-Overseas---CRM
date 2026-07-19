"""
Ready2Go CRM — User Model

Represents employees and administrators who operate the CRM.
Passwords are stored as bcrypt hashes via passlib.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.constants import EMPLOYEE
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_code: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=EMPLOYEE)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_photo: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    archived_at: Mapped[datetime | None] = deferred(mapped_column(DateTime(timezone=True), nullable=True))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_logout: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    )
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    activity_logs = relationship("ActivityLog", back_populates="user", lazy="dynamic")
    assigned_applicants = relationship(
        "Applicant", foreign_keys="[Applicant.assigned_to]",
        back_populates="assigned_employee", lazy="dynamic",
    )
    created_applicants = relationship(
        "Applicant", foreign_keys="[Applicant.created_by]",
        back_populates="creator", lazy="dynamic",
    )
    deleted_applicants = relationship(
        "Applicant", foreign_keys="[Applicant.deleted_by]",
        back_populates="deleter", lazy="dynamic",
    )
    uploaded_documents = relationship(
        "Document", foreign_keys="[Document.uploaded_by]",
        back_populates="uploader", lazy="dynamic",
    )
    deleted_documents = relationship(
        "Document", foreign_keys="[Document.deleted_by]",
        back_populates="deleter", lazy="dynamic",
    )
    sent_messages = relationship("Message", back_populates="sender", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
