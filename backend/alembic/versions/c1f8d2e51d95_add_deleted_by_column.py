"""add_deleted_by_column

Revision ID: c1f8d2e51d95
Revises: b3f7c2e51d94
Create Date: 2026-07-14 07:47:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f8d2e51d95'
down_revision: Union[str, None] = 'b3f7c2e51d94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── deleted_by (FK to users.id) ──────────────
    op.add_column('applicants', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_applicants_deleted_by', 'applicants', 'users', ['deleted_by'], ['id'])
    op.create_index('ix_applicants_deleted_by', 'applicants', ['deleted_by'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_applicants_deleted_by', table_name='applicants')
    op.drop_constraint('fk_applicants_deleted_by', 'applicants', type_='foreignkey')
    op.drop_column('applicants', 'deleted_by')
