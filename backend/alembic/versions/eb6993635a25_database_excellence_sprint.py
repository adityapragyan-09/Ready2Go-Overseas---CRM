"""Database Excellence Sprint — Index & constraint optimization

SAFE OPERATIONS (cross-dialect, no data risk):
  1. ADD composite indexes for documented query patterns (6 new)
  2. REMOVE redundant indexes confirmed as strict prefixes (4 removed)
  3. ADD missing unique constraints from model declarations (2 added)

=== 1. NEW COMPOSITE INDEXES ===
  ix_activity_logs_user_login       — activity_logs(user_id, login_time)
  ix_activity_logs_login_logout     — activity_logs(login_time, logout_time)
  ix_documents_applicant_active     — documents(applicant_id, is_deleted)
  ix_applicants_employee_workload   — applicants(is_deleted, assigned_to, created_at)
  ix_lead_inquiries_employee_status — lead_inquiries(assigned_employee_id, status)
  ix_assignment_requests_emp_status — assignment_requests(employee_id, status)

=== 2. REDUNDANT INDEXES REMOVED ===
  ix_messages_applicant_id          ← covered by ix_messages_applicant_id_created_at
  ix_notifications_recipient_user_id← covered by ix_notifications_recipient_is_read_created_at
  ix_progress_history_applicant_id  ← covered by ix_progress_history_applicant_id_updated_at
  ix_lead_notes_lead_id             ← covered by ix_lead_notes_lead_created

=== 3. NEW UNIQUE CONSTRAINTS ===
  uq_lead_notes_uuid               — model says unique=True, migration omitted it
  uq_assignment_requests_uuid      — model says unique=True, migration omitted it

=== 4. FK ONDELETE CONSISTENCY (11 documented — see migration source) ===

=== 1. NEW COMPOSITE INDEXES ===
  ix_documents_applicant_active     — documents(applicant_id, is_deleted)
  ix_applicants_employee_workload   — applicants(is_deleted, assigned_to, created_at)
  ix_lead_inquiries_employee_status — lead_inquiries(assigned_employee_id, status)
  ix_assignment_requests_emp_status — assignment_requests(employee_id, status)

=== 2. REDUNDANT INDEXES REMOVED ===
  ix_messages_applicant_id          ← covered by ix_messages_applicant_id_created_at
  ix_notifications_recipient_user_id← covered by ix_notifications_recipient_is_read_created_at
  ix_progress_history_applicant_id  ← covered by ix_progress_history_applicant_id_updated_at
  ix_lead_notes_lead_id             ← covered by ix_lead_notes_lead_created

=== 3. FK ONDELETE CONSISTENCY ===
  The following 11 FK constraints need ondelete clauses to match models.
  On SQLite (development) this is a no-op because FKs are parsed but not
  enforced. On PostgreSQL (production) run the SQL below BEFORE deploying
  this migration, or apply it after.

  -- activity_logs
  ALTER TABLE activity_logs DROP CONSTRAINT activity_logs_user_id_fkey,
    ADD CONSTRAINT fk_activity_logs_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

  -- applicants
  ALTER TABLE applicants DROP CONSTRAINT applicants_assigned_to_fkey,
    ADD CONSTRAINT fk_applicants_assigned_to
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL;
  ALTER TABLE applicants DROP CONSTRAINT applicants_created_by_fkey,
    ADD CONSTRAINT fk_applicants_created_by
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;
  ALTER TABLE applicants DROP CONSTRAINT applicants_deleted_by_fkey,
    ADD CONSTRAINT fk_applicants_deleted_by
    FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

  -- documents
  ALTER TABLE documents DROP CONSTRAINT documents_applicant_id_fkey,
    ADD CONSTRAINT fk_documents_applicant_id
    FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE;
  ALTER TABLE documents DROP CONSTRAINT documents_uploaded_by_fkey,
    ADD CONSTRAINT fk_documents_uploaded_by
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT;
  ALTER TABLE documents DROP CONSTRAINT documents_deleted_by_fkey,
    ADD CONSTRAINT fk_documents_deleted_by
    FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

  -- messages
  ALTER TABLE messages DROP CONSTRAINT messages_applicant_id_fkey,
    ADD CONSTRAINT fk_messages_applicant_id
    FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE;
  ALTER TABLE messages DROP CONSTRAINT messages_sender_id_fkey,
    ADD CONSTRAINT fk_messages_sender_id
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE RESTRICT;

  -- progress_history
  ALTER TABLE progress_history DROP CONSTRAINT progress_history_updated_by_fkey,
    ADD CONSTRAINT fk_progress_history_updated_by
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE RESTRICT;

  -- users
  ALTER TABLE users DROP CONSTRAINT users_created_by_fkey,
    ADD CONSTRAINT fk_users_created_by
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

Revision ID: eb6993635a25
Revises: f2f8d2e51e10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "eb6993635a25"
down_revision: Union[str, None] = "f2f8d2e51e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. MODEL __table_args__ INDEXES (missing from original migrations) ──
    op.create_index(
        "ix_activity_logs_user_login", "activity_logs",
        ["user_id", "login_time"], unique=False,
    )
    op.create_index(
        "ix_activity_logs_login_logout", "activity_logs",
        ["login_time", "logout_time"], unique=False,
    )

    # ── 2. MISSING UNIQUE CONSTRAINTS ────────────────────
    with op.batch_alter_table("lead_notes") as batch_op:
        batch_op.create_unique_constraint("uq_lead_notes_uuid", ["uuid"])
    with op.batch_alter_table("assignment_requests") as batch_op:
        batch_op.create_unique_constraint("uq_assignment_requests_uuid", ["uuid"])

    # ── 3. NEW COMPOSITE INDEXES (query-pattern-optimized) ──
    # Documents: list_applicant_documents filters by applicant_id + is_deleted=False
    op.create_index(
        "ix_documents_applicant_active", "documents",
        ["applicant_id", "is_deleted"], unique=False,
    )
    # Applicants: dashboard workload queries by assigned_to + is_deleted=False
    op.create_index(
        "ix_applicants_employee_workload", "applicants",
        ["is_deleted", "assigned_to", "created_at"], unique=False,
    )
    # Lead inquiries: admin assignment workflow filters
    op.create_index(
        "ix_lead_inquiries_employee_status", "lead_inquiries",
        ["assigned_employee_id", "status"], unique=False,
    )
    # Assignment requests: employee's own request listing
    op.create_index(
        "ix_assignment_requests_emp_status", "assignment_requests",
        ["employee_id", "status"], unique=False,
    )

    # ── 4. REDUNDANT INDEXES REMOVED ──────────────────
    # Each is a strict prefix of a composite index on the same table
    op.drop_index("ix_messages_applicant_id", table_name="messages")
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications")
    op.drop_index("ix_progress_history_applicant_id", table_name="progress_history")
    op.drop_index("ix_lead_notes_lead_id", table_name="lead_notes")


def downgrade() -> None:
    # Reverse new indexes
    op.drop_index("ix_assignment_requests_emp_status", table_name="assignment_requests")
    op.drop_index("ix_lead_inquiries_employee_status", table_name="lead_inquiries")
    op.drop_index("ix_applicants_employee_workload", table_name="applicants")
    op.drop_index("ix_documents_applicant_active", table_name="documents")

    # Reverse unique constraints
    with op.batch_alter_table("assignment_requests") as b:
        b.drop_constraint("uq_assignment_requests_uuid", type_="unique")
    with op.batch_alter_table("lead_notes") as b:
        b.drop_constraint("uq_lead_notes_uuid", type_="unique")

    # Reverse activity_logs indexes
    op.drop_index("ix_activity_logs_login_logout", table_name="activity_logs")
    op.drop_index("ix_activity_logs_user_login", table_name="activity_logs")

    # Restore removed indexes
    op.create_index("ix_messages_applicant_id", "messages", ["applicant_id"], unique=False)
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"], unique=False)
    op.create_index("ix_progress_history_applicant_id", "progress_history", ["applicant_id"], unique=False)
    op.create_index("ix_lead_notes_lead_id", "lead_notes", ["lead_id"], unique=False)
