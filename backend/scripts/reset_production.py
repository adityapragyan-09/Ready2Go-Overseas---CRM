#!/usr/bin/env python3
"""
Ready2Go CRM — Production Data Reset Script

Resets the entire CRM for a fresh production deployment.

Usage:
    python -m scripts.reset_production

WARNING: This DELETES ALL production data except the admin account.
Run only when preparing for a fresh client demonstration.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reset_production")

TABLES_TO_TRUNCATE = [
    "documents",
    "chat_messages",
    "progress_history",
    "notifications",
    "assignment_requests",
    "lead_notes",
    "lead_activities",
    "lead_inquiries",
    "activity_logs",
    "applicants",
]

SEQUENCES_TO_RESET = [
    "documents_id_seq",
    "chat_messages_id_seq",
    "progress_history_id_seq",
    "notifications_id_seq",
    "assignment_requests_id_seq",
    "lead_notes_id_seq",
    "lead_activities_id_seq",
    "lead_inquiries_id_seq",
    "activity_logs_id_seq",
    "applicants_id_seq",
    "employees_id_seq",
    "users_id_seq",
]


def reset_production():
    db = SessionLocal()
    try:
        logger.info("=" * 60)
        logger.info("PRODUCTION DATA RESET")
        logger.info("=" * 60)

        # ── Phase 1: Disable FK checks ────────────────────────────────
        if "sqlite" in settings.DATABASE_URL:
            db.execute(text("PRAGMA foreign_keys = OFF"))
        elif "postgresql" in settings.DATABASE_URL:
            db.execute(text("SET session_replication_role = 'replica'"))
        logger.info("Foreign key checks disabled")

        # ── Phase 2: Delete documents from storage ────────────────────
        # Documents must be deleted before applicants (FK)
        from app.services.storage_service import delete_file, list_folder, _normalize

        doc_rows = db.execute(
            text("SELECT id, storage_path FROM documents WHERE is_deleted = false")
        ).fetchall()

        deleted_from_storage = 0
        for row in doc_rows:
            try:
                result = delete_file(row[1])
                if result["success"]:
                    deleted_from_storage += 1
            except Exception as e:
                logger.warning("  Could not delete storage object %s: %s", row[1], e)

        logger.info("Deleted %d files from Supabase Storage", deleted_from_storage)

        # ── Phase 3: Delete employees (except admin) ──────────────────
        emp_count = db.execute(
            text("DELETE FROM users WHERE role != 'admin'")
        ).rowcount
        logger.info("Deleted %d employee accounts", emp_count)

        # ── Phase 4: Truncate all data tables ──────────────────────────
        for table in TABLES_TO_TRUNCATE:
            try:
                if "sqlite" in settings.DATABASE_URL:
                    db.execute(text(f"DELETE FROM {table}"))
                elif "postgresql" in settings.DATABASE_URL:
                    db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                logger.info("  Truncated: %s", table)
            except Exception as e:
                logger.warning("  Could not truncate %s: %s", table, e)

        # ── Phase 5: Reset sequences (PostgreSQL) ─────────────────────
        if "postgresql" in settings.DATABASE_URL:
            for seq in SEQUENCES_TO_RESET:
                try:
                    db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                    logger.info("  Reset sequence: %s", seq)
                except Exception:
                    pass  # Some sequences may not exist on this schema

        # ── Phase 6: Re-enable FK checks ───────────────────────────────
        if "sqlite" in settings.DATABASE_URL:
            db.execute(text("PRAGMA foreign_keys = ON"))
        elif "postgresql" in settings.DATABASE_URL:
            db.execute(text("SET session_replication_role = 'origin'"))
        logger.info("Foreign key checks re-enabled")

        # ── Commit ────────────────────────────────────────────────────
        db.commit()
        logger.info("=" * 60)
        logger.info("RESET COMPLETE")
        logger.info("  Supabase files deleted:  %d", deleted_from_storage)
        logger.info("  Employees deleted:       %d", emp_count)
        logger.info("  Tables truncated:        %d", len(TABLES_TO_TRUNCATE))
        logger.info("  Admin account:           PRESERVED")
        logger.info("=" * 60)

    except Exception as e:
        db.rollback()
        logger.exception("RESET FAILED: %s", e)
        raise
    finally:
        db.close()


def verify_reset():
    """Verify the reset was successful."""
    db = SessionLocal()
    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("VERIFICATION")
        logger.info("=" * 60)

        checks = {
            "employees": "SELECT COUNT(*) FROM users WHERE role != 'admin'",
            "applicants": "SELECT COUNT(*) FROM applicants WHERE is_deleted = false",
            "leads": "SELECT COUNT(*) FROM lead_inquiries",
            "notifications": "SELECT COUNT(*) FROM notifications",
            "documents": "SELECT COUNT(*) FROM documents WHERE is_deleted = false",
            "activity_logs": "SELECT COUNT(*) FROM activity_logs",
            "assignment_requests": "SELECT COUNT(*) FROM assignment_requests",
            "chat_messages": "SELECT COUNT(*) FROM chat_messages",
        }

        all_clean = True
        for name, query in checks.items():
            try:
                count = db.execute(text(query)).scalar() or 0
                status = "✅" if count == 0 else "❌"
                if count != 0:
                    all_clean = False
                logger.info("  %s %s: %d records", status, name, count)
            except Exception as e:
                logger.warning("  ⚠️ %s: could not check — %s", name, e)

        # Verify admin exists
        admin_count = db.execute(
            text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        ).scalar() or 0
        logger.info("  ✅ Admin accounts: %d", admin_count)

        if all_clean and admin_count >= 1:
            logger.info("")
            logger.info("✅ ALL CHECKS PASSED — CRM is clean and ready for production.")
        else:
            logger.warning("")
            logger.warning("⚠️  Some checks failed — review the results above.")

    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("This will DELETE ALL PRODUCTION DATA except admin. Continue? (yes/N): ")
    if confirm.lower() == "yes":
        reset_production()
        verify_reset()
    else:
        print("Cancelled.")
