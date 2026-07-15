"""
Ready2Go CRM — Security Utilities

Provides:
    Password hashing  — hash_password(), verify_password()
    JWT management     — create_access_token(), decode_access_token()

Uses passlib (bcrypt) for passwords and PyJWT for tokens.
"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ── JWT Tokens ───────────────────────────────────

def create_access_token(
    subject: str | int,
    role: str,
    name: str,
) -> str:
    """
    Create a JWT access token with standard claims.

    Args:
        subject: User ID (stored as 'sub' claim).
        role: User role ('admin' or 'employee').
        name: User display name.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject),
        "role": role,
        "name": name,
        "iat": now,
        "exp": expire,
        "iss": settings.APP_NAME,
        "aud": settings.APP_NAME,
        "type": "access",
        "jti": str(subject) + "_" + str(int(now.timestamp())),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


import logging

logger = logging.getLogger(__name__)

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )

        if payload.get("type") != "access":
            return None

        return payload

    except Exception as e:
        logger.exception(f"JWT decode failed: {e}")
        return None
