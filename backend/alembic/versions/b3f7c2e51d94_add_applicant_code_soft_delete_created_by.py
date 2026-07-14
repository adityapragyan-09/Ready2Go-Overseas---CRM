"""add_applicant_code_soft_delete_created_by

Revision ID: b3f7c2e51d94
Revises: ea018d20aa27
Create Date: 2026-07-14 07:36:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f7c2e51d94'
down_revision: Union[str, None] = 'ea018d20aa27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── applicant_code (unique, not-null) ────────
    # Add as nullable first, backfill, then set NOT NULL.
    op.add_column('applicants', sa.Column('applicant_code', sa.String(length=20), nullable=True))

    # Backfill existing rows with APP-{id zero-padded}
    op.execute(
        "UPDATE applicants SET applicant_code = 'APP-' || LPAD(CAST(id AS TEXT), 6, '0') "
        "WHERE applicant_code IS NULL"
    )

    op.alter_column('applicants', 'applicant_code', nullable=False)
    op.create_index('ix_applicants_applicant_code', 'applicants', ['applicant_code'], unique=True)

    # ── created_by (FK to users.id) ──────────────
    # Add as nullable first, backfill with the first admin user, then set NOT NULL.
    op.add_column('applicants', sa.Column('created_by', sa.Integer(), nullable=True))

    # Backfill: use the lowest user id as the creator for existing rows
    op.execute(
        "UPDATE applicants SET created_by = (SELECT MIN(id) FROM users) "
        "WHERE created_by IS NULL"
    )

    op.alter_column('applicants', 'created_by', nullable=False)
    op.create_foreign_key('fk_applicants_created_by', 'applicants', 'users', ['created_by'], ['id'])
    op.create_index('ix_applicants_created_by', 'applicants', ['created_by'], unique=False)

    # ── Soft delete fields ───────────────────────
    op.add_column('applicants', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('applicants', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # ── Composite indexes for common queries ─────
    op.create_index('ix_applicants_active_created', 'applicants', ['is_deleted', 'created_at'])
    op.create_index('ix_applicants_active_status', 'applicants', ['is_deleted', 'status'])


def downgrade() -> None:
    op.drop_index('ix_applicants_active_status', table_name='applicants')
    op.drop_index('ix_applicants_active_created', table_name='applicants')
    op.drop_column('applicants', 'deleted_at')
    op.drop_column('applicants', 'is_deleted')
    op.drop_index('ix_applicants_created_by', table_name='applicants')
    op.drop_constraint('fk_applicants_created_by', 'applicants', type_='foreignkey')
    op.drop_column('applicants', 'created_by')
    op.drop_index('ix_applicants_applicant_code', table_name='applicants')
    op.drop_column('applicants', 'applicant_code')
