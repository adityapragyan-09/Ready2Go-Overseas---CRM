"""Add missing composite indexes and unique constraints

Adds composite indexes that are defined in SQLAlchemy model
__table_args__ but were never created by a migration:

  - ix_activity_logs_user_login       (user_id, login_time)
  - ix_activity_logs_login_logout     (login_time, logout_time)

Adds unique constraints on uuid columns that the model specifies
as unique=True but the original migration omitted:

  - lead_notes.uuid                   -> uq_lead_notes_uuid
  - assignment_requests.uuid          -> uq_assignment_requests_uuid

This migration does NOT fix FK ondelete drifts (those require a
database-dialect-aware strategy and are low-risk on SQLite where
FKs are parsed but not enforced).

Revision ID: 10b64bf0996f
Revises: f2f8d2e51e10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "10b64bf0996f"
down_revision: Union[str, None] = "f2f8d2e51e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- 1. Missing composite indexes (model __table_args__) ------
    op.create_index("ix_activity_logs_user_login", "activity_logs", ["user_id", "login_time"], unique=False)
    op.create_index("ix_activity_logs_login_logout", "activity_logs", ["login_time", "logout_time"], unique=False)

    # -- 2. Unique constraints omitted by original migrations -----
    with op.batch_alter_table("lead_notes") as batch_op:
        batch_op.create_unique_constraint("uq_lead_notes_uuid", ["uuid"])

    with op.batch_alter_table("assignment_requests") as batch_op:
        batch_op.create_unique_constraint("uq_assignment_requests_uuid", ["uuid"])


def downgrade() -> None:
    op.drop_index("ix_activity_logs_login_logout", table_name="activity_logs")
    op.drop_index("ix_activity_logs_user_login", table_name="activity_logs")

    with op.batch_alter_table("lead_notes") as batch_op:
        batch_op.drop_constraint("uq_lead_notes_uuid", type_="unique")

    with op.batch_alter_table("assignment_requests") as batch_op:
        batch_op.drop_constraint("uq_assignment_requests_uuid", type_="unique")
