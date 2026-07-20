"""Add leave management fields to users table

Revision ID: e5f8d2e51e04
Revises: d5f8d2e51e03

Adds:
- users.archived_reason (VARCHAR(100), nullable)
- users.leave_start (TIMESTAMP, nullable)
- users.leave_end (TIMESTAMP, nullable)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f8d2e51e04"
down_revision: Union[str, None] = "d5f8d2e51e03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("archived_reason", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("leave_start", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("leave_end", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("leave_end")
        batch_op.drop_column("leave_start")
        batch_op.drop_column("archived_reason")
