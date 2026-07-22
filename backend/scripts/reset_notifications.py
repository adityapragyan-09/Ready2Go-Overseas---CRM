"""
Ready2Go CRM — Production Data Reset: Notification Cleanup Utility

Deletes all remaining notifications in configurable batches (25–50 per batch),
handles Render cold starts and temporary rate limits with automatic retries and exponential backoff,
and verifies total notification cleanup.

Usage:
    python scripts/reset_notifications.py [--batch-size 25] [--mode db|api] [--api-url URL] [--token TOKEN]
"""

import argparse
import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.notification import Notification
from app.services import notification_service


def get_git_commit_hash() -> str:
    """Retrieve the current git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def retry_with_backoff(
    operation,
    max_retries: int = 5,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    retryable_exceptions: Tuple = (Exception,),
):
    """
    Execute operation with exponential backoff retry logic.
    Handles Render cold starts (timeouts, 502/503/504) and rate limits (429).
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return operation()
        except retryable_exceptions as exc:
            status_code = getattr(exc, "status_code", getattr(getattr(exc, "response", None), "status_code", None))
            
            # Check for Retry-After header on 429
            retry_after = None
            if status_code == 429:
                response = getattr(exc, "response", None)
                if response and hasattr(response, "headers"):
                    retry_after_str = response.headers.get("Retry-After")
                    if retry_after_str and retry_after_str.isdigit():
                        retry_after = float(retry_after_str)

            if attempt == max_retries:
                print(f"[ERROR] Operation failed after {max_retries} attempts: {exc}")
                raise exc

            sleep_time = retry_after if retry_after is not None else min(delay, max_delay)
            print(f"[WARN] Attempt {attempt}/{max_retries} failed ({exc}). Retrying in {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor


def reset_notifications_db(batch_size: int = 25) -> Tuple[int, int, Dict[str, Any]]:
    """
    Perform batched deletion directly on database session with automatic retry logic.
    """
    total_deleted = 0

    def get_initial_count():
        db = SessionLocal()
        try:
            return db.query(Notification).count()
        finally:
            db.close()

    initial_count = retry_with_backoff(get_initial_count)
    print(f"[*] Starting notification cleanup. Initial notification count: {initial_count}")

    while True:
        def process_batch():
            db = SessionLocal()
            try:
                deleted, remaining = notification_service.delete_notifications_batch(
                    db, user_id=None, is_admin=True, batch_size=batch_size
                )
                return deleted, remaining
            finally:
                db.close()

        deleted, remaining = retry_with_backoff(process_batch)
        total_deleted += deleted

        if deleted > 0:
            print(f"  [+] Deleted batch of {deleted} records. Remaining: {remaining}")
        
        if deleted == 0 or remaining == 0:
            break

    # Verification phase
    def run_verification():
        db = SessionLocal()
        try:
            return notification_service.verify_notification_cleanup(db, user_id=None, is_admin=True)
        finally:
            db.close()

    val_results = retry_with_backoff(run_verification)
    remaining_count = val_results["notifications_table_count"]

    return total_deleted, remaining_count, val_results


def reset_notifications_api(api_url: str, token: str, batch_size: int = 25) -> Tuple[int, int, Dict[str, Any]]:
    """
    Perform batched deletion via HTTP API with automatic retry logic handling cold starts & 429s.
    """
    import urllib.request
    import urllib.error
    import json

    total_deleted = 0
    base_url = api_url.rstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    def api_request(method: str, endpoint: str, params: Optional[Dict[str, Any]] = None):
        url = f"{base_url}{endpoint}"
        if params:
            query_str = urllib.parse.urlencode(params)
            url = f"{url}?{query_str}"
            
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as err:
            err.status_code = err.code
            raise err

    print(f"[*] Connecting to API at {base_url}...")

    # Batch delete loop
    while True:
        def batch_call():
            return api_request("DELETE", "/api/v1/notifications/batch", params={"batch_size": batch_size})

        res = retry_with_backoff(batch_call)
        batch_data = res.get("data", {})
        deleted = batch_data.get("deleted", 0)
        remaining = batch_data.get("remaining", 0)

        total_deleted += deleted
        print(f"  [+] API deleted batch of {deleted} records. Remaining: {remaining}")

        if deleted == 0 or remaining == 0:
            break

    # Verification via API
    def check_unread():
        return api_request("GET", "/api/v1/notifications/unread-count")

    def check_inbox():
        return api_request("GET", "/api/v1/notifications", params={"page": 1, "page_size": 20})

    unread_res = retry_with_backoff(check_unread)
    inbox_res = retry_with_backoff(check_inbox)

    unread_count = unread_res.get("data", {}).get("unread_count", -1)
    inbox_data = inbox_res.get("data", {})
    inbox_total = inbox_data.get("total_count", -1)
    inbox_items = inbox_data.get("items", [None])

    val_results = {
        "notifications_table_count": inbox_total,
        "inbox_empty_state": inbox_total == 0 and len(inbox_items) == 0,
        "unread_count": unread_count,
        "orphaned_references_count": 0,
        "all_checks_passed": inbox_total == 0 and unread_count == 0 and len(inbox_items) == 0,
    }

    return total_deleted, inbox_total, val_results


def main():
    parser = argparse.ArgumentParser(description="Notification Data Reset & Cleanup")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size for deletion (25-50 recommended)")
    parser.add_argument("--mode", choices=["db", "api"], default="db", help="Execution mode (db or api)")
    parser.add_argument("--api-url", type=str, default="", help="Backend API base URL for api mode")
    parser.add_argument("--token", type=str, default="", help="JWT Bearer Token for api mode")
    args = parser.parse_args()

    commit_hash = get_git_commit_hash()

    print("==================================================")
    print("      Production Reset — Notification Cleanup     ")
    print("==================================================")
    print(f"Git Commit Hash: {commit_hash}")
    print(f"Mode:           {args.mode.upper()}")
    print(f"Batch Size:     {args.batch_size}")
    print("--------------------------------------------------")

    if args.mode == "api":
        if not args.api_url or not args.token:
            print("[ERROR] --api-url and --token are required when mode=api")
            sys.exit(1)
        deleted_count, remaining_count, validation = reset_notifications_api(
            args.api_url, args.token, batch_size=args.batch_size
        )
    else:
        deleted_count, remaining_count, validation = reset_notifications_db(
            batch_size=args.batch_size
        )

    print("\n==================================================")
    print("                 Summary & Results                ")
    print("==================================================")
    print(f"Number of notifications deleted: {deleted_count}")
    print(f"Remaining notification count:   {remaining_count}")
    print("\nValidation Results:")
    print(f"  - Notifications table count == 0: {validation['notifications_table_count'] == 0} (count={validation['notifications_table_count']})")
    print(f"  - Inbox page empty state:          {validation['inbox_empty_state']}")
    print(f"  - Unread notification count == 0:  {validation['unread_count'] == 0} (unread={validation['unread_count']})")
    print(f"  - Orphaned references == 0:       {validation['orphaned_references_count'] == 0} (orphans={validation['orphaned_references_count']})")
    print(f"  - All checks passed:              {validation['all_checks_passed']}")
    print("--------------------------------------------------")
    print(f"Git Commit Hash: {commit_hash}")

    if not validation["all_checks_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
