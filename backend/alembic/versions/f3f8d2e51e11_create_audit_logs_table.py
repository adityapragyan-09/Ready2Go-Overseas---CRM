"""Create audit_logs table for enterprise Audit Center

Revision ID: f3f8d2e51e11
Revises: eb6993635a25
Create Date: 2026-07-23 17:00:00.000000

Adds a structured audit trail table alongside the existing activity_logs
(which only tracks login/logout sessions). The audit_logs table captures
every meaningful enterprise action with category, severity, and metadata.

Categories: employee_management, applicant_management, lead_management,
            documents, communication, leave_hr, notifications, security, system

Severities: INFO, SUCCESS, WARNING, ERROR, CRITICAL
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision: str = "f3f8d2e51e11"
down_revision: Union[str, None] = "eb6993635a25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),

        # Classification
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),

        # Performer (denormalized name for query speed)
        sa.Column("performed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("performed_by_name", sa.String(120), nullable=True),

        # Target
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("target_name", sa.String(255), nullable=True),

        # Structured metadata
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),

        # Request context
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),

        # Timestamp
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),

        sa.PrimaryKeyConstraint("id"),
    )

    # Composite indexes for common query patterns
    op.create_index("ix_audit_logs_target", "audit_logs", ["target_type", "target_id"])
    op.create_index(
        "ix_audit_logs_performed_category",
        "audit_logs",
        ["performed_by_id", "category", "created_at"],
    )
    op.create_index(
        "ix_audit_logs_category_severity",
        "audit_logs",
        ["category", "severity", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_category_severity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_performed_category", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target", table_name="audit_logs")
    op.drop_table("audit_logs")
