"""
Ready2Go CRM — Auth Schemas

Request and response schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login request body."""
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    """POST /api/v1/auth/change-password request body."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Token + user data returned after successful login."""
    token: str
    user: dict
