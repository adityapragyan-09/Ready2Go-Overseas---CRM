"""
Ready2Go CRM — Authentication Smoke Tests

Exercises the login and token-validation flow with a focus on
error-path behaviour:
    - Missing or invalid fields → 422
    - Wrong credentials          → 401
    - Missing / bad token        → 401

Endpoints under test:
    POST /api/v1/auth/login
    GET  /api/v1/auth/me
"""

import pytest


class TestLogin:
    """POST /api/v1/auth/login — Credential validation."""

    def test_missing_fields_returns_422(self, client):
        """Sending an empty JSON body should trigger Pydantic validation."""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        """Sending only an email should still be rejected."""
        response = client.post(
            "/api/v1/auth/login", json={"email": "admin@example.com"}
        )
        assert response.status_code == 422

    def test_invalid_credentials_returns_401(self, client):
        """Wrong email/password combination must return 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "wrong-password",
            },
        )
        assert response.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        """Email that does not exist in the database must return 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "does-not-exist@example.com",
                "password": "testpass123",
            },
        )
        assert response.status_code == 401

    def test_deactivated_user_returns_401(self, client, deactivated_user):
        """An account that has been deactivated must not be allowed to log in."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": deactivated_user.email,
                "password": "testpass123",
            },
        )
        assert response.status_code == 401


class TestMe:
    """GET /api/v1/auth/me — Current-user profile."""

    def test_without_token_returns_401(self, client):
        """No Authorization header → 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_with_invalid_token_returns_401(self, client):
        """Garbage bearer token → 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert response.status_code == 401

    def test_with_empty_bearer_returns_401(self, client):
        """Header with 'Bearer ' but no actual token → 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401
