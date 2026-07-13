"""
Ready2Go CRM — Database Seeding Script

Creates the initial admin user in the Supabase database.
Run with:
    python seed_admin.py
"""

import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def seed_admin():
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        admin_email = "admin@ready2gooverseas.com"
        existing_user = db.query(User).filter(User.email == admin_email).first()
        
        if existing_user:
            print(f"User {admin_email} already exists. Skipping seeding.")
            return

        print(f"Creating admin user {admin_email}...")
        admin = User(
            name="System Admin",
            email=admin_email,
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
