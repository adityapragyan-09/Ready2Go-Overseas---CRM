from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply security headers to every HTTP response.

    Headers applied:
        - Strict-Transport-Security (HSTS)
        - X-Content-Type-Options (nosniff)
        - X-Frame-Options (DENY)
        - Referrer-Policy
        - Permissions-Policy
        - Content-Security-Policy
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

        # CSP: restrictive in production, relaxed in development for hot-reload
        if settings.ENVIRONMENT == "production":
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
            )
        else:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' http://localhost:* ws://localhost:*;",
            )
        return response


def setup_security_headers(app: ASGIApp) -> None:
    """Register the SecurityHeadersMiddleware on the FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
