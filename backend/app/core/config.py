"""
Ready2Go CRM — Application Configuration

Loads ALL configuration from environment variables via pydantic-settings.
No secrets are hardcoded anywhere in this file.

Usage:
    from app.core.config import settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Application ──────────────────────────────
    APP_NAME: str = "Ready2Go CRM"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Branding & Formats
    COMPANY_NAME: str = "Ready2Go Overseas"
    DATE_FORMAT: str = "%Y-%m-%d"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # Feature Flags
    ENABLE_SOFT_DELETE: bool = True

    # ── Security ─────────────────────────────────
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM

    @property
    def JWT_EXPIRE_MINUTES(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    # ── Database — Supabase PostgreSQL ───────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # ── CORS ─────────────────────────────────────
    FRONTEND_URL: str

    # ── Document Management ──────────────────────
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "ready2go-documents"
    CRM_API_KEY: str | None = None
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 500
    UPLOAD_TIMEOUT_SECONDS: int = 600
    SIGNED_URL_EXPIRY_MINUTES: int = 60
    ALLOWED_DOCUMENT_TYPES: str = "pdf,jpg,jpeg,png,doc,docx"

    @property
    def ALLOWED_DOCUMENT_TYPES_LIST(self) -> list[str]:
        return [x.strip().lower() for x in self.ALLOWED_DOCUMENT_TYPES.split(",") if x.strip()]

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def ALLOWED_DOCUMENT_TYPES_SET(self) -> set[str]:
        return {f".{ext}" for ext in self.ALLOWED_DOCUMENT_TYPES_LIST}

    # ── Pagination ───────────────────────────────
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    # ── Search ───────────────────────────────────
    MAX_SEARCH_RESULTS: int = 100


settings = Settings()

# Runtime safety checks: validate required secrets on startup.
if settings.ENVIRONMENT.lower() == "production":
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production environment")
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY must be provided in production environment")
    if not settings.FRONTEND_URL:
        raise RuntimeError("FRONTEND_URL must be configured for CORS in production")
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise RuntimeError("Supabase credentials (SUPABASE_URL, SUPABASE_KEY) must be provided in production")
    if not settings.SUPABASE_URL.startswith("https://"):
        raise RuntimeError("SUPABASE_URL must be a valid HTTPS URL")
    if not settings.SUPABASE_KEY.startswith("ey"):
        raise RuntimeError("SUPABASE_KEY appears invalid — should be a JWT token starting with 'ey'")
    if settings.DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("SQLite is not supported in production. Use a PostgreSQL-compatible database URL.")

if not settings.SECRET_KEY or not settings.JWT_SECRET_KEY:
    raise RuntimeError("SECRET_KEY and JWT_SECRET_KEY must both be configured in .env")
