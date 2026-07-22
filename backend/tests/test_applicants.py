"""
Ready2Go CRM — Applicant CRUD Smoke Tests

Basic smoke tests for the applicants resource.  These verify that
the endpoint wiring (auth guards, response shapes, 404 handling)
is in place — they do NOT attempt exhaustive CRUD coverage.

Endpoints under test:
    POST   /api/v1/applicants
    GET    /api/v1/applicants
    GET    /api/v1/applicants/{id}
"""

import pytest


class TestCreateApplicant:
    """POST /api/v1/applicants — Create a new applicant."""

    def test_requires_authentication(self, client):
        """Without a valid JWT the endpoint must return 401."""
        response = client.post(
            "/api/v1/applicants",
            json={"full_name": "Test Applicant", "visa_type": "student"},
        )
        assert response.status_code == 401


class TestListApplicants:
    """GET /api/v1/applicants — Paginated applicant listing."""

    def test_requires_authentication(self, client):
        """Without a valid JWT the endpoint must return 401."""
        response = client.get("/api/v1/applicants")
        assert response.status_code == 401

    def test_returns_paginated_response(self, client, employee_headers):
        """A successful response must contain pagination metadata."""
        response = client.get(
            "/api/v1/applicants", headers=employee_headers
        )
        assert response.status_code == 200
        body = response.json()

        # The envelope structure
        assert body["success"] is True
        assert "data" in body

        # Paginated list shape
        data = body["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_respects_page_query_param(self, client, employee_headers):
        """Passing ``?page=2`` must be accepted (even if empty)."""
        response = client.get(
            "/api/v1/applicants?page=2", headers=employee_headers
        )
        assert response.status_code == 200

    def test_respects_page_size_query_param(self, client, employee_headers):
        """Passing ``?page_size=5`` must be accepted."""
        response = client.get(
            "/api/v1/applicants?page_size=5", headers=employee_headers
        )
        assert response.status_code == 200


class TestGetApplicant:
    """GET /api/v1/applicants/{id} — Single applicant retrieval."""

    def test_requires_authentication(self, client):
        """Without a valid JWT the endpoint must return 401."""
        response = client.get("/api/v1/applicants/1")
        assert response.status_code == 401

    def test_returns_404_for_missing_applicant(self, client, employee_headers):
        """A non-existent applicant ID must return 404."""
        response = client.get(
            "/api/v1/applicants/99999", headers=employee_headers
        )
        assert response.status_code == 404
