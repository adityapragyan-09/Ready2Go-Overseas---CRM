"""Create assignment_requests table

Revision ID: f2f8d2e51e10
Revises: e2f8d2e51e09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2f8d2e51e10"
down_revision: Union[str, None] = "e2f8d2e51e09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assignment_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_inquiries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_requests_lead_id"), "assignment_requests", ["lead_id"], unique=False)
    op.create_index(op.f("ix_assignment_requests_employee_id"), "assignment_requests", ["employee_id"], unique=False)
    op.create_index(op.f("ix_assignment_requests_status"), "assignment_requests", ["status"], unique=False)
    op.create_index("ix_assignment_requests_status_created", "assignment_requests", ["status", "requested_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assignment_requests_status_created", table_name="assignment_requests")
    op.drop_index(op.f("ix_assignment_requests_status"), table_name="assignment_requests")
    op.drop_index(op.f("ix_assignment_requests_employee_id"), table_name="assignment_requests")
    op.drop_index(op.f("ix_assignment_requests_lead_id"), table_name="assignment_requests")
    op.drop_table("assignment_requests")
