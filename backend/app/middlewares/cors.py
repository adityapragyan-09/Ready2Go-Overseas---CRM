"""
Ready2Go CRM — CORS Middleware Setup

Configures Cross-Origin Resource Sharing for the FastAPI app.
Whitelists only the configured frontend URL. In production, only
the actual deployment origin is allowed.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Request-ID",
    "X-CSRF-Token",
]


def setup_cors(app: FastAPI) -> None:
    """Add CORS middleware to the FastAPI application with restricted methods/headers."""
    allowed_origins = [settings.FRONTEND_URL]
    if settings.ENVIRONMENT == "development":
        allowed_origins.extend(["http://localhost:5173", "http://localhost:3000"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
    )
