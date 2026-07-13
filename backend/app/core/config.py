"""
Ready2Go CRM — Application Configuration

Loads ALL configuration from environment variables via pydantic-settings.
No secrets are hardcoded anywhere in this file.

Usage:
    from app.core.config import settings
    print(settings.DATABASE_URL)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── App ──────────────────────────────────────
    APP_NAME: str = "Ready2Go CRM"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ── Database — Supabase PostgreSQL ───────────
    DATABASE_URL: str

    # ── JWT ──────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ─────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    # ── File Uploads ─────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 16


settings = Settings()
