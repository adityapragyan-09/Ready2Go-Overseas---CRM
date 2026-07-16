"""Make activity_log.user_id nullable to allow audit records to survive user deletion

Revision ID: f2f8d2e51d99
Revises: c1f8d2e51d95_add_deleted_by_column
Create Date: 2026-07-15 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2f8d2e51d99"
down_revision: Union[str, None] = "7b6f8779f472"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change user_id column to nullable=True."""
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Revert user_id column to nullable=False."""
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
