"""
Ready2Go CRM — FastAPI Application Entry Point

Creates the FastAPI app, registers routers, middleware,
and centralized exception handlers.

Run with:
    uvicorn main:app --reload --port 8000

Production:
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
"""

import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.applicants import router as applicants_router
from app.api.auth import router as auth_router
from app.api.employees import router as employees_router
from app.api.documents import router as documents_router
from app.api.progress import router as progress_router
from app.api.chat import router as chat_router
from app.api.notifications import router as notifications_router
from app.api.dashboard import router as dashboard_router
from app.api.activity_logs import router as activity_logs_router
from app.core.config import settings
from app.core.logging import logger
from app.middlewares.cors import setup_cors
from app.middlewares.security_headers import setup_security_headers
from app.middlewares.rate_limit import setup_rate_limiter
from app.utils.response import error_response

# ── Create FastAPI app ───────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    redirect_slashes=False,
)


# ── Startup: Auto-run database migrations ───────

@app.on_event("startup")
def run_database_migrations():
    """Execute Alembic migrations before the first request is handled.

    This ensures the database schema is always synchronized with the
    SQLAlchemy models, regardless of whether Render uses Docker (where
    startup.sh handles this) or Native Python runtime (where Render
    controls the start command directly).

    The subprocess runs 'alembic upgrade head' which applies ALL pending
    migrations in order. If the migration fails, the application logs the
    error but still starts — this allows the health check to report the
    database status via /ready.
    """
    try:
        logger.info("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.info("Migration stdout: %s", result.stdout.strip() if result.stdout else "(none)")
        if result.returncode != 0:
            logger.error("Migration stderr: %s", result.stderr.strip() if result.stderr else "(none)")
            logger.error("Migration failed with exit code %d", result.returncode)
        else:
            logger.info("Database migrations completed successfully.")
    except Exception as exc:
        logger.error("Migration command failed to execute: %s", exc)


# ── Request ID Middleware ───────────────────────

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Assign a unique request_id to every request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ── Middleware ───────────────────────────────────

setup_cors(app)
setup_security_headers(app)
setup_rate_limiter(app)

# ── Ensure upload directory exists ───────────────

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
# In production, uploads MUST be served via signed URLs — avoid mounting
if settings.ENVIRONMENT != "production":
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Register API routers ────────────────────────

app.include_router(auth_router, prefix=f"{settings.API_PREFIX}/auth", tags=["Auth"])
app.include_router(employees_router, prefix=f"{settings.API_PREFIX}/employees", tags=["Employees"])
app.include_router(applicants_router, prefix=f"{settings.API_PREFIX}/applicants", tags=["Applicants"])
app.include_router(documents_router, prefix=f"{settings.API_PREFIX}/documents", tags=["Documents"])
app.include_router(progress_router, prefix=f"{settings.API_PREFIX}/progress", tags=["Progress"])
app.include_router(chat_router, prefix=f"{settings.API_PREFIX}/chat", tags=["Chat"])
app.include_router(notifications_router, prefix=f"{settings.API_PREFIX}/notifications", tags=["Notifications"])
app.include_router(dashboard_router, prefix=f"{settings.API_PREFIX}/dashboard", tags=["Dashboard"])
app.include_router(activity_logs_router, prefix=f"{settings.API_PREFIX}/activity-logs", tags=["Activity Logs"])

# ── Health / Liveness / Readiness ────────────────

@app.get("/health", tags=["Infrastructure"])
def health_check():
    """Basic health check — returns app status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ready", tags=["Infrastructure"])
def readiness_check():
    """
    Readiness probe.
    Confirms that the application can establish a database connection.
    """
    from app.db.session import SessionLocal

    db = None

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception:
        logger.exception("Readiness check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "database": "disconnected",
            },
        )
    finally:
        if db is not None:
            db.close()


@app.get("/live", tags=["Infrastructure"])
def liveness_check():
    """Liveness probe — process is alive."""
    return {"status": "alive"}


@app.get("/version", tags=["Infrastructure"])
def version_info():
    """Version and build information."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ── Centralized Exception Handlers ───────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standard envelope."""
    request_id = getattr(request.state, "request_id", None)
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])

    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "endpoint": str(request.url.path),
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            "Validation failed.",
            errors=errors,
            request_id=request_id,
            error="VALIDATION_ERROR",
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPExceptions with standard envelope and appropriate error codes."""
    request_id = getattr(request.state, "request_id", None)

    # Map HTTP status codes to machine-readable error codes
    error_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    }
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "endpoint": str(request.url.path),
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            exc.detail,
            request_id=request_id,
            error=error_code,
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions — never exposes stack traces."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "endpoint": str(request.url.path),
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            "Internal server error.",
            request_id=request_id,
            error="INTERNAL_ERROR",
        ),
    )
