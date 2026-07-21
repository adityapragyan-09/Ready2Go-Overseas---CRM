"""Add normalized_email and normalized_phone to lead_inquiries

Revision ID: e2f8d2e51e09
Revises: d2f8d2e51e08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2f8d2e51e09"
down_revision: Union[str, None] = "d2f8d2e51e08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("lead_inquiries") as batch_op:
        batch_op.add_column(sa.Column("normalized_email", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("normalized_phone", sa.String(30), nullable=True))
        batch_op.create_index("ix_lead_inquiries_normalized_email", ["normalized_email"], unique=False)
        batch_op.create_index("ix_lead_inquiries_normalized_phone", ["normalized_phone"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("lead_inquiries") as batch_op:
        batch_op.drop_index("ix_lead_inquiries_normalized_phone")
        batch_op.drop_index("ix_lead_inquiries_normalized_email")
        batch_op.drop_column("normalized_phone")
        batch_op.drop_column("normalized_email")
