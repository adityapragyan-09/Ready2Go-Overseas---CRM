"""create_progress_history_table

Revision ID: e1f8d2e51d97
Revises: d1f8d2e51d96
Create Date: 2026-07-14 08:35:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f8d2e51d97'
down_revision: Union[str, None] = 'd1f8d2e51d96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create progress_history table ─────────────
    op.create_table('progress_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('previous_status', sa.String(length=30), nullable=True),
        sa.Column('current_status', sa.String(length=30), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_system_generated', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name='fk_progress_history_applicant_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_progress_history_updated_by'),
        sa.PrimaryKeyConstraint('id')
    )
    # Individual column indexes
    op.create_index('ix_progress_history_applicant_id', 'progress_history', ['applicant_id'], unique=False)
    op.create_index('ix_progress_history_updated_by', 'progress_history', ['updated_by'], unique=False)
    op.create_index('ix_progress_history_updated_at', 'progress_history', ['updated_at'], unique=False)
    
    # Composite index for timeline lookups
    op.create_index('ix_progress_history_applicant_id_updated_at', 'progress_history', ['applicant_id', 'updated_at'], unique=False)


def downgrade() -> None:
    # ── Drop progress_history table ───────────────
    op.drop_index('ix_progress_history_applicant_id_updated_at', table_name='progress_history')
    op.drop_index('ix_progress_history_updated_at', table_name='progress_history')
    op.drop_index('ix_progress_history_updated_by', table_name='progress_history')
    op.drop_index('ix_progress_history_applicant_id', table_name='progress_history')
    op.drop_table('progress_history')
