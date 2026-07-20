"""Create lead_activity_logs table

Revision ID: b2f8d2e51e06
Revises: a2f8d2e51e05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f8d2e51e06"
down_revision: Union[str, None] = "a2f8d2e51e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_activity_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("old_value", sa.String(100), nullable=True),
        sa.Column("new_value", sa.String(100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_inquiries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_activity_logs_lead_id"), "lead_activity_logs", ["lead_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lead_activity_logs_lead_id"), table_name="lead_activity_logs")
    op.drop_table("lead_activity_logs")
