"""
Ready2Go CRM — Database Maintenance Utility

Usage:
    python scripts/maintenance.py [command]

Commands:
    cleanup-notifications   — Delete read notifications older than 30 days
    db-stats                — Print database table statistics
    check-integrity         — Verify foreign key integrity
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.user import User
from app.models.applicant import Applicant
from app.models.document import Document
from app.models.message import Message
from app.models.progress import ProgressHistory
from app.models.activity_log import ActivityLog
from sqlalchemy import func, text


def cleanup_notifications():
    """Delete read notifications older than 30 days."""
    db = SessionLocal()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        deleted = (
            db.query(Notification)
            .filter(Notification.is_read == True, Notification.created_at < threshold)
            .delete()
        )
        db.commit()
        print(f"[OK] Deleted {deleted} old notifications.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


def db_stats():
    """Print record counts for all tables."""
    db = SessionLocal()
    try:
        tables = {
            "users": db.query(func.count(User.id)).scalar() or 0,
            "applicants": db.query(func.count(Applicant.id)).scalar() or 0,
            "documents": db.query(func.count(Document.id)).scalar() or 0,
            "messages": db.query(func.count(Message.id)).scalar() or 0,
            "progress_history": db.query(func.count(ProgressHistory.id)).scalar() or 0,
            "notifications": db.query(func.count(Notification.id)).scalar() or 0,
            "activity_logs": db.query(func.count(ActivityLog.id)).scalar() or 0,
        }
        print("=== Database Statistics ===")
        for name, count in tables.items():
            print(f"  {name}: {count}")
        print(f"  Total records: {sum(tables.values())}")
    finally:
        db.close()


def check_integrity():
    """Verify foreign key integrity across tables."""
    db = SessionLocal()
    try:
        # Check for orphan documents (applicant deleted)
        orphans = (
            db.query(Document)
            .outerjoin(Applicant, Document.applicant_id == Applicant.id)
            .filter(Applicant.id.is_(None))
            .count()
        )
        print(f"  Orphan documents: {orphans}")

        # Check for orphan messages
        orphan_msgs = (
            db.query(Message)
            .outerjoin(Applicant, Message.applicant_id == Applicant.id)
            .filter(Applicant.id.is_(None))
            .count()
        )
        print(f"  Orphan messages: {orphan_msgs}")

        if orphans == 0 and orphan_msgs == 0:
            print("[OK] No integrity issues found.")
        else:
            print("[WARN] Orphan records detected. Run data cleanup.")
    finally:
        db.close()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "db-stats"
    commands = {
        "cleanup-notifications": cleanup_notifications,
        "db-stats": db_stats,
        "check-integrity": check_integrity,
    }
    fn = commands.get(command)
    if fn:
        fn()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)
