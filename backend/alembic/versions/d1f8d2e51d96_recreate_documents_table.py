"""recreate_documents_table

Revision ID: d1f8d2e51d96
Revises: c1f8d2e51d95
Create Date: 2026-07-14 08:09:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f8d2e51d96'
down_revision: Union[str, None] = 'c1f8d2e51d95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop old documents table ──────────────────
    op.drop_table('documents')

    # ── Create new documents table ────────────────
    op.create_table('documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_code', sa.String(length=20), nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('original_file_name', sa.String(length=256), nullable=False),
        sa.Column('stored_file_name', sa.String(length=256), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_extension', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name='fk_documents_applicant_id'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_documents_uploaded_by'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], name='fk_documents_deleted_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_file_name', name='uq_documents_stored_file_name')
    )
    op.create_index('ix_documents_document_code', 'documents', ['document_code'], unique=True)
    op.create_index('ix_documents_applicant_id', 'documents', ['applicant_id'], unique=False)
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'], unique=False)
    op.create_index('ix_documents_deleted_by', 'documents', ['deleted_by'], unique=False)


def downgrade() -> None:
    # ── Drop new documents table ──────────────────
    op.drop_index('ix_documents_deleted_by', table_name='documents')
    op.drop_index('ix_documents_uploaded_by', table_name='documents')
    op.drop_index('ix_documents_applicant_id', table_name='documents')
    op.drop_index('ix_documents_document_code', table_name='documents')
    op.drop_table('documents')

    # ── Recreate old documents table ──────────────
    op.create_table('documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=256), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_applicant_id', 'documents', ['applicant_id'], unique=False)
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'], unique=False)
