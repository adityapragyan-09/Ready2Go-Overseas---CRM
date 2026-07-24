#!/usr/bin/env python3
"""
Ready2Go CRM — Production Data Reset Script

Resets the entire CRM for a fresh production deployment.
Can also update admin credentials without resetting.

Usage:
    Full reset + update admin:
        python -m scripts.reset_production --admin-email admin@example.com --admin-password MyStr0ng!Pass

    Update admin only (no reset):
        python -m scripts.reset_production --update-admin-only --admin-email admin@example.com --admin-password MyStr0ng!Pass

    Reset only (keep existing admin):
        python -m scripts.reset_production

WARNING: Reset DELETES ALL production data except the admin account.
"""

import argparse
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
    "audit_logs",
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
    "audit_logs_id_seq",
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

        if "sqlite" in settings.DATABASE_URL:
            db.execute(text("PRAGMA foreign_keys = OFF"))
        elif "postgresql" in settings.DATABASE_URL:
            db.execute(text("SET session_replication_role = 'replica'"))
        logger.info("Foreign key checks disabled")

        # Delete documents from storage
        from app.services.storage_service import delete_file
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

        # Delete employees except admin
        emp_count = db.execute(
            text("DELETE FROM users WHERE role != 'admin'")
        ).rowcount
        logger.info("Deleted %d employee accounts", emp_count)

        # Truncate all data tables
        for table in TABLES_TO_TRUNCATE:
            try:
                if "sqlite" in settings.DATABASE_URL:
                    db.execute(text(f"DELETE FROM {table}"))
                elif "postgresql" in settings.DATABASE_URL:
                    db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                logger.info("  Truncated: %s", table)
            except Exception as e:
                logger.warning("  Could not truncate %s: %s", table, e)

        # Reset sequences (PostgreSQL)
        if "postgresql" in settings.DATABASE_URL:
            for seq in SEQUENCES_TO_RESET:
                try:
                    db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                    logger.info("  Reset sequence: %s", seq)
                except Exception:
                    pass

        if "sqlite" in settings.DATABASE_URL:
            db.execute(text("PRAGMA foreign_keys = ON"))
        elif "postgresql" in settings.DATABASE_URL:
            db.execute(text("SET session_replication_role = 'origin'"))
        logger.info("Foreign key checks re-enabled")

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


def update_admin(email: str = None, password: str = None):
    """Update admin account credentials. Uses the app's password hashing."""
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        admin = db.execute(
            text("SELECT id, email, name FROM users WHERE role = 'admin' LIMIT 1")
        ).first()
        if not admin:
            logger.error("No admin account found!")
            return False

        admin_id, current_email, admin_name = admin
        updates = []

        if email:
            db.execute(
                text("UPDATE users SET email = :email WHERE id = :id"),
                {"email": email.strip().lower(), "id": admin_id},
            )
            updates.append(f"email → {email}")

        if password:
            pw_hash = hash_password(password)
            db.execute(
                text("UPDATE users SET password_hash = :hash WHERE id = :id"),
                {"hash": pw_hash, "id": admin_id},
            )
            updates.append("password → [updated]")

        if not updates:
            logger.info("No credential changes requested.")
            return True

        db.commit()
        logger.info("=" * 60)
        logger.info("ADMIN CREDENTIALS UPDATED")
        logger.info("  Admin ID:    %d", admin_id)
        logger.info("  Admin name:  %s", admin_name)
        logger.info("  Admin email: %s", email or current_email)
        for u in updates:
            logger.info("  Updated:     %s", u)
        logger.info("=" * 60)

        # Verify the password hash was stored correctly
        if password:
            verify = db.execute(
                text("SELECT password_hash FROM users WHERE id = :id"),
                {"id": admin_id},
            ).scalar()
            if verify and verify.startswith("$2"):
                logger.info("  Password hash verified (bcrypt)")
            else:
                logger.error("  Password hash verification FAILED!")

        return True
    except Exception as e:
        db.rollback()
        logger.exception("Failed to update admin: %s", e)
        return False
    finally:
        db.close()


def verify_reset():
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
    parser = argparse.ArgumentParser(description="Ready2Go CRM Production Reset")
    parser.add_argument("--admin-email", help="New admin email address")
    parser.add_argument("--admin-password", help="New admin password")
    parser.add_argument("--update-admin-only", action="store_true", help="Only update admin credentials, skip reset")
    args = parser.parse_args()

    if args.update_admin_only:
        update_admin(email=args.admin_email, password=args.admin_password)
    elif args.admin_email or args.admin_password:
        confirm = input("This will RESET ALL DATA and update admin credentials. Continue? (yes/N): ")
        if confirm.lower() == "yes":
            reset_production()
            update_admin(email=args.admin_email, password=args.admin_password)
            verify_reset()
        else:
            print("Cancelled.")
    else:
        confirm = input("This will DELETE ALL PRODUCTION DATA except admin. Continue? (yes/N): ")
        if confirm.lower() == "yes":
            reset_production()
            verify_reset()
        else:
            print("Cancelled.")
