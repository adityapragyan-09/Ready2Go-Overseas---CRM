"""Add account security fields and password_history table

Revision ID: b4f8d2e51e01
Revises: a3f8d2e51d00
Create Date: 2026-07-16 15:00:00.000000

Adds:
- users.failed_login_attempts (Integer, default 0)
- users.locked_until (DateTime, nullable)
- users.token_version (Integer, default 0)
- users.last_password_change (DateTime, nullable)
- password_history table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4f8d2e51e01"
down_revision: Union[str, None] = "a3f8d2e51d00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("last_password_change", sa.DateTime(timezone=True), nullable=True))

    # Create password_history table
    op.create_table(
        "password_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_history_user_id"), "password_history", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_password_history_user_id"), table_name="password_history")
    op.drop_table("password_history")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("last_password_change")
        batch_op.drop_column("token_version")
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_attempts")
