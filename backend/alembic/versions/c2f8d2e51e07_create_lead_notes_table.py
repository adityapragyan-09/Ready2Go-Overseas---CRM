"""Create lead_notes table

Revision ID: c2f8d2e51e07
Revises: b2f8d2e51e06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f8d2e51e07"
down_revision: Union[str, None] = "b2f8d2e51e06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_inquiries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_notes_lead_id"), "lead_notes", ["lead_id"], unique=False)
    op.create_index("ix_lead_notes_lead_created", "lead_notes", ["lead_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_notes_lead_created", table_name="lead_notes")
    op.drop_index(op.f("ix_lead_notes_lead_id"), table_name="lead_notes")
    op.drop_table("lead_notes")
