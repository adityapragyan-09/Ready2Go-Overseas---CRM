"""
Ready2Go CRM — Enterprise Document Storage Migration (v2)

Idempotent migration script that normalises all ``documents.storage_path``
values to the canonical form ``applicants/APP-XXXX/file.pdf``.

Run:
    python -m backend.scripts.migrate_document_storage

Or from the repo root:
    cd backend && python -m scripts.migrate_document_storage
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_document_storage")

BUCKET = settings.SUPABASE_BUCKET


def normalize(path: str) -> str:
    """Strip bucket prefix and normalise separators."""
    if not path:
        return path
    p = path.strip().replace("\\", "/").lstrip("/")
    prefix = f"{BUCKET}/"
    if p.startswith(prefix):
        logger.info("  stripping bucket prefix from '%s'", p[:120])
        p = p[len(prefix):]
    p = p.lstrip("/")
    while "//" in p:
        p = p.replace("//", "/")
    return p.strip()


def main():
    db = SessionLocal()
    try:
        total = db.query(Document).count()
        logger.info("Scanned %d documents", total)

        updated = 0
        skipped = 0
        failed = 0

        for doc in db.query(Document).order_by(Document.id).all():
            old_path = doc.storage_path
            new_path = normalize(old_path)

            if old_path == new_path:
                skipped += 1
                continue

            try:
                doc.storage_path = new_path
                db.flush()
                logger.info("  [OK] id=%d code=%s: '%s' -> '%s'", doc.id, doc.document_code, old_path, new_path)
                updated += 1
            except Exception as exc:
                logger.exception("  [FAIL] id=%d: %s", doc.id, exc)
                db.rollback()
                failed += 1

        if updated > 0:
            db.commit()
            logger.info("Committed %d updates", updated)
        else:
            logger.info("No updates needed")

        logger.info("=" * 50)
        logger.info("MIGRATION COMPLETE")
        logger.info("  Scanned: %d", total)
        logger.info("  Updated: %d", updated)
        logger.info("  Skipped: %d", skipped)
        logger.info("  Failed:  %d", failed)
        logger.info("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
