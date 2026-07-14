"""
Ready2Go CRM — Database Initialization Script

Directly creates all database tables for local SQLite development
and marks the Alembic migration history as fully upgraded.
"""

from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base

# Import all models so they are registered with the Base metadata
from app.models.user import User
from app.models.applicant import Applicant
from app.models.document import Document
from app.models.message import Message
from app.models.notification import Notification
from app.models.progress import ProgressHistory
from app.models.activity_log import ActivityLog

def init_database():
    print("Initializing local SQLite database...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
    
    # Mark the latest migration version in the database
    latest_revision = "7b6f8779f472"
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{latest_revision}')"))
        print(f"Database version marked as {latest_revision} in alembic_version table.")

if __name__ == "__main__":
    init_database()
