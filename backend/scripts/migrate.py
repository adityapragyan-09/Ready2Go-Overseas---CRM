"""
Ready2Go CRM — Database Migration Runner

Usage:
    python scripts/migrate.py [revision]

Runs Alembic migrations. Default: upgrade to head.
Pass a specific revision to migrate to that version.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alembic.config import Config
from alembic import command


def run_migrations(revision: str = "head"):
    """Execute Alembic database migrations."""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(os.path.dirname(__file__), "..", "alembic"),
    )
    print(f"[MIGRATE] Running migration to: {revision}")
    command.upgrade(alembic_cfg, revision)
    print(f"[OK] Migration to {revision} completed.")


if __name__ == "__main__":
    revision = sys.argv[1] if len(sys.argv) > 1 else "head"
    run_migrations(revision)
