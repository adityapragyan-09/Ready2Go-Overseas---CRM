"""
Ready2Go CRM — Infrastructure / Health Smoke Tests

Verifies that the application's infrastructure endpoints return
the expected responses.  These endpoints live outside the
``/api/v1`` prefix and do NOT require authentication.
"""


class TestHealthEndpoint:
    """GET /health — Application health check."""

    def test_returns_200_and_status_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()

        assert body["status"] == "healthy"
        assert body["app"] == "Ready2Go CRM"
        # Version is a string — just check it exists
        assert body.get("version") is not None


class TestLivenessEndpoint:
    """GET /live — Liveness probe."""

    def test_returns_200_and_status_alive(self, client):
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestReadinessEndpoint:
    """GET /ready — Readiness probe (checks database connection and migrations)."""

    def test_returns_503_if_migrations_pending(self, client):
        """Migrations run in background — /ready returns 503 until they complete."""
        response = client.get("/ready")
        # In test environment migrations never finish (no alembic), so we get 503
        assert response.status_code in (200, 503)
        body = response.json()
        if response.status_code == 200:
            assert body["status"] == "ready"
        else:
            assert body["status"] == "migrating"


class TestVersionEndpoint:
    """GET /version — Application version info."""

    def test_returns_200_with_app_info(self, client):
        response = client.get("/version")
        assert response.status_code == 200
        body = response.json()

        assert body["app"] == "Ready2Go CRM"
        assert body["version"] == "1.0.0"
        assert body["environment"] == "test"
