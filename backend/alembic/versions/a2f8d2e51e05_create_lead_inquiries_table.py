"""Create lead_inquiries table

Revision ID: a2f8d2e51e05
Revises: e5f8d2e51e04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2f8d2e51e05"
down_revision: Union[str, None] = "e5f8d2e51e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_inquiries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("lead_number", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("visa_type", sa.String(30), nullable=False, server_default="student"),
        sa.Column("preferred_country", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="WEBSITE"),
        sa.Column("status", sa.String(30), nullable=False, server_default="NEW"),
        sa.Column("assigned_employee_id", sa.Integer(), nullable=True),
        sa.Column("converted_to_applicant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("converted_applicant_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_employee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_inquiries_uuid"), "lead_inquiries", ["uuid"], unique=True)
    op.create_index(op.f("ix_lead_inquiries_lead_number"), "lead_inquiries", ["lead_number"], unique=True)
    op.create_index(op.f("ix_lead_inquiries_email"), "lead_inquiries", ["email"], unique=False)
    op.create_index(op.f("ix_lead_inquiries_assigned_employee_id"), "lead_inquiries", ["assigned_employee_id"], unique=False)
    op.create_index(op.f("ix_lead_inquiries_updated_at"), "lead_inquiries", ["updated_at"], unique=False)
    op.create_index("ix_lead_inquiries_status_created", "lead_inquiries", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_inquiries_status_created", table_name="lead_inquiries")
    op.drop_index(op.f("ix_lead_inquiries_updated_at"), table_name="lead_inquiries")
    op.drop_index(op.f("ix_lead_inquiries_assigned_employee_id"), table_name="lead_inquiries")
    op.drop_index(op.f("ix_lead_inquiries_email"), table_name="lead_inquiries")
    op.drop_index(op.f("ix_lead_inquiries_lead_number"), table_name="lead_inquiries")
    op.drop_index(op.f("ix_lead_inquiries_uuid"), table_name="lead_inquiries")
    op.drop_table("lead_inquiries")
