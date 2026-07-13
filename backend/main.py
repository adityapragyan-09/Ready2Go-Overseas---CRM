"""
Ready2Go CRM — FastAPI Application Entry Point

Creates the FastAPI app, registers routers, middleware,
and centralized exception handlers.

Run with:
    uvicorn main:app --reload --port 8000

Production:
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.employees import router as employees_router
from app.core.config import settings
from app.middlewares.cors import setup_cors
from app.utils.response import error_response

# ── Create FastAPI app ───────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware ───────────────────────────────────

setup_cors(app)

# ── Ensure upload directory exists ───────────────

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ── Register API routers ────────────────────────

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(employees_router, prefix="/api/v1/employees", tags=["Employees"])

# Future routers (uncomment as modules are built):
# app.include_router(applicants_router,    prefix="/api/v1/applicants",    tags=["Applicants"])
# app.include_router(documents_router,     prefix="/api/v1/documents",     tags=["Documents"])
# app.include_router(employees_router,     prefix="/api/v1/employees",     tags=["Employees"])
# app.include_router(messages_router,      prefix="/api/v1/messages",      tags=["Messages"])
# app.include_router(dashboard_router,     prefix="/api/v1/dashboard",     tags=["Dashboard"])
# app.include_router(activity_logs_router, prefix="/api/v1/activity-logs", tags=["Activity Logs"])
# app.include_router(progress_router,      prefix="/api/v1/progress",      tags=["Progress"])


# ── Health check ─────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint for Render monitoring."""
    return {"status": "healthy", "app": settings.APP_NAME}


# ── Centralized Exception Handlers ───────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standard envelope."""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response("Validation failed.", errors=errors),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPExceptions with standard envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.detail),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response("Internal server error."),
    )
