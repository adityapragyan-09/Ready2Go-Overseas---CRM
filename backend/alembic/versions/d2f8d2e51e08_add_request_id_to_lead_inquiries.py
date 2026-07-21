"""Add request_id to lead_inquiries table

Revision ID: d2f8d2e51e08
Revises: c2f8d2e51e07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2f8d2e51e08"
down_revision: Union[str, None] = "c2f8d2e51e07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("lead_inquiries") as batch_op:
        batch_op.add_column(sa.Column("request_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_lead_inquiries_request_id", ["request_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("lead_inquiries") as batch_op:
        batch_op.drop_index("ix_lead_inquiries_request_id")
        batch_op.drop_column("request_id")
