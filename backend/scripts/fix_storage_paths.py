"""
Ready2Go CRM — Fix Storage Paths Migration Script

Reads every row from the ``documents`` table and normalizes the
``storage_path`` column so it never includes the bucket name prefix.

Supabase Storage sometimes returns the upload ``Key`` field with the
bucket name prefixed (e.g. ``ready2go-documents/applicants/…``).  Early
versions of the upload pipeline saved this raw value verbatim, which
causes signed URL generation to fail because the path is double-nested.

This script strips the bucket prefix from any affected records.

Run from the project root:
    python -m backend.scripts.fix_storage_paths

It is idempotent — running it twice will not modify already-correct rows.
"""

import logging
import os
import sys

# Allow running as `python -m backend.scripts.fix_storage_paths`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("fix_storage_paths")

BUCKET_PREFIX = f"{settings.SUPABASE_BUCKET}/"


def normalize(path: str) -> str:
    """Return the canonical storage path (bucket prefix stripped)."""
    if not path:
        return path
    path = path.strip()
    # In case there are mixed separators from older bugs
    path = path.replace("\\", "/")
    path = path.lstrip("/")
    while "//" in path:
        path = path.replace("//", "/")
    if path.startswith(BUCKET_PREFIX):
        path = path[len(BUCKET_PREFIX):]
    return path.strip()


def main():
    db = SessionLocal()
    try:
        total = db.query(Document).count()
        logger.info("Total documents in database: %d", total)

        # ── Phase 1: find affected records ────────────────────────────
        all_docs = db.query(Document).order_by(Document.id).all()
        corrected = 0
        skipped = 0
        failed = 0

        for doc in all_docs:
            old_path = doc.storage_path
            new_path = normalize(old_path)

            if old_path == new_path:
                # Already canonical — nothing to do
                skipped += 1
                continue

            # Path changed — update
            try:
                doc.storage_path = new_path
                db.flush()
                logger.info(
                    "UPDATED doc id=%d code=%s: '%s' → '%s'",
                    doc.id, doc.document_code, old_path, new_path,
                )
                corrected += 1
            except Exception:
                logger.exception(
                    "FAILED to update doc id=%d (path='%s')",
                    doc.id, old_path,
                )
                db.rollback()
                failed += 1
                continue

        # ── Commit all changes ────────────────────────────────────────
        if corrected > 0:
            db.commit()
            logger.info("Committed %d path corrections.", corrected)
        else:
            logger.info("No corrections needed — all paths already canonical.")

        # ── Summary ────────────────────────────────────────────────────
        logger.info("=" * 50)
        logger.info("STORAGE PATH MIGRATION COMPLETE")
        logger.info("  Total scanned:  %d", total)
        logger.info("  Updated:        %d", corrected)
        logger.info("  Skipped:        %d", skipped)
        logger.info("  Failed:         %d", failed)
        logger.info("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
