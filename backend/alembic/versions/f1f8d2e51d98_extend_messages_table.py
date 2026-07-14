"""extend_messages_table

Revision ID: f1f8d2e51d98
Revises: e1f8d2e51d97
Create Date: 2026-07-14 08:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1f8d2e51d98'
down_revision: Union[str, None] = 'e1f8d2e51d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add extended columns to messages table ─────
    op.add_column('messages', sa.Column('message_type', sa.String(length=20), server_default='text', nullable=False))
    op.add_column('messages', sa.Column('attachment_url', sa.String(length=255), nullable=True))
    op.add_column('messages', sa.Column('is_system_message', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('messages', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('messages', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))

    # Individual index on is_deleted
    op.create_index('ix_messages_is_deleted', 'messages', ['is_deleted'], unique=False)
    
    # Composite index for optimized chronological timeline queries
    op.create_index('ix_messages_applicant_id_created_at', 'messages', ['applicant_id', 'created_at'], unique=False)


def downgrade() -> None:
    # ── Remove indexes and extended columns ───────
    op.drop_index('ix_messages_applicant_id_created_at', table_name='messages')
    op.drop_index('ix_messages_is_deleted', table_name='messages')
    op.drop_column('messages', 'is_deleted')
    op.drop_column('messages', 'updated_at')
    op.drop_column('messages', 'is_system_message')
    op.drop_column('messages', 'attachment_url')
    op.drop_column('messages', 'message_type')
