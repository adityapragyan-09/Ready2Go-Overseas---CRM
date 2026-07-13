"""
Ready2Go CRM — User Model

Represents employees and administrators who operate the CRM.
Passwords are stored as bcrypt hashes via passlib.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import EMPLOYEE
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    # Relationships
    activity_logs = relationship("ActivityLog", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    assigned_applicants = relationship("Applicant", back_populates="assigned_employee", lazy="dynamic")
    sent_messages = relationship("Message", back_populates="sender", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
