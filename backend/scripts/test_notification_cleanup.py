"""
Ready2Go CRM — Test Suite for Notification Reset & Cleanup

1. Seeds 84 notification records (mix of read/unread, different modules & users).
2. Runs batched deletion with automatic retry logic.
3. Tests retry logic on simulated cold start / rate limit errors.
4. Verifies:
   - Notification table record count == 0
   - Inbox page display empty state (total_count == 0, items == [])
   - Unread notification count == 0
   - Orphaned notification references == 0
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.user import User
from app.services import notification_service
from scripts.reset_notifications import reset_notifications_db, retry_with_backoff


def seed_notifications(count: int = 84):
    """Seed `count` notification records in the database."""
    db = SessionLocal()
    try:
        # Create a test user if none exists
        user = db.query(User).first()
        user_id = user.id if user else None

        # Clean existing notifications first
        db.query(Notification).delete()
        db.commit()

        modules = ["applicant", "assignment", "employee", "document", "chat", "authentication"]
        notifs = []
        for i in range(1, count + 1):
            is_read = (i % 2 == 0)
            module = modules[i % len(modules)]
            notif = Notification(
                notification_code=f"NOT-{i:06d}",
                title=f"Test Notification #{i}",
                message=f"Detailed message payload for notification #{i}",
                type="info" if i % 2 == 0 else "warning",
                module=module,
                priority="medium" if i % 3 == 0 else "high",
                recipient_user_id=user_id if i % 4 != 0 else None,
                created_by=user_id,
                reference_type="lead" if i % 2 == 0 else "document",
                reference_id=i,
                is_read=is_read,
            )
            notifs.append(notif)

        db.bulk_save_objects(notifs)
        db.commit()

        seeded_count = db.query(Notification).count()
        print(f"[OK] Seeded {seeded_count} notification records.")
        return seeded_count
    finally:
        db.close()


def test_retry_mechanism():
    """Test retry_with_backoff function under simulated failure conditions."""
    attempts = 0

    def flaky_op():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            class Mock503Error(Exception):
                status_code = 503
            raise Mock503Error("Simulated 503 Cold Start")
        return "SUCCESS"

    result = retry_with_backoff(flaky_op, max_retries=5, initial_delay=0.1, backoff_factor=1.5)
    assert result == "SUCCESS", "Retry mechanism failed to succeed after transient errors"
    assert attempts == 3, f"Expected 3 attempts, got {attempts}"
    print("[OK] Retry mechanism passed simulation test.")


def main():
    print("==================================================")
    print("      Testing Notification Cleanup & Verification ")
    print("==================================================")

    # 1. Seed 84 notifications
    seeded = seed_notifications(84)
    assert seeded == 84, f"Seeding failed: expected 84, got {seeded}"

    # 2. Test retry utility
    test_retry_mechanism()

    # 3. Perform batched reset (batch_size=25)
    deleted, remaining, validation = reset_notifications_db(batch_size=25)

    print("\n--------------------------------------------------")
    print(f"Total deleted:   {deleted}")
    print(f"Remaining count: {remaining}")
    print("Validation Output:")
    for k, v in validation.items():
        print(f"  {k}: {v}")

    # 4. Strict assertions
    assert deleted == 84, f"Expected 84 deleted, got {deleted}"
    assert remaining == 0, f"Expected 0 remaining, got {remaining}"
    assert validation["notifications_table_count"] == 0, "Table count is not 0"
    assert validation["inbox_empty_state"] is True, "Inbox empty state check failed"
    assert validation["unread_count"] == 0, "Unread count is not 0"
    assert validation["orphaned_references_count"] == 0, "Orphaned references exist"
    assert validation["all_checks_passed"] is True, "Not all validation checks passed"

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    main()
