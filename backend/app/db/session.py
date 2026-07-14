"""
Ready2Go CRM — Database Session Management

Provides:
    engine       — SQLAlchemy engine connected to Supabase PostgreSQL
    SessionLocal — Session factory for creating DB sessions
    get_db()     — FastAPI dependency that yields a session per request
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

if settings.DATABASE_URL.startswith("sqlite"):

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )

else:

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        connect_args={
            "sslmode": "require",
        },
        future=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()