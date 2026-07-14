"""
Ready2Go CRM — Admin User Creator

Usage:
    python scripts/create_admin.py

Creates the initial admin user in the database.
Requires .env with DATABASE_URL configured.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ready2gooverseas.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator")


def create_admin():
    """Create the first admin user if none exists."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print(f"[SKIP] Admin user already exists: {ADMIN_EMAIL}")
            return existing

        admin = User(
            employee_code="ADMIN-000001",
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[OK] Admin user created: {ADMIN_EMAIL}")
        print(f"[INFO] Change the default password immediately after first login.")
        return admin
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
