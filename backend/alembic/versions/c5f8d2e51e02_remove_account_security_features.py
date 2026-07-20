"""Remove account security columns and password_history table

Revision ID: c5f8d2e51e02
Revises: f2f8d2e51d99
Create Date: 2026-07-17 12:00:00.000000

Drops:
- password_history table (if exists)
- users.must_change_password column (if exists)
- users.failed_login_attempts column (if exists)
- users.locked_until column (if exists)
- users.token_version column (if exists)
- users.last_password_change column (if exists)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5f8d2e51e02"
down_revision: Union[str, None] = "f2f8d2e51d99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop password_history table if it exists
    op.execute("DROP TABLE IF EXISTS password_history")

    # Drop security columns from users table if they exist.
    # Using raw SQL with IF EXISTS to handle the case where these columns
    # were never added (the migration files that created them have since been
    # deleted from the repository).
    for col in ["must_change_password", "failed_login_attempts", "locked_until", "token_version", "last_password_change"]:
        op.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}")


def downgrade() -> None:
    # Re-add columns (without restoring data — this is a clean removal)
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("last_password_change", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "password_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
