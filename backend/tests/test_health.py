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
    """GET /ready — Readiness probe (checks database connection)."""

    def test_returns_200_when_db_connected(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        body = response.json()

        assert body["status"] == "ready"
        assert body["database"] == "connected"


class TestVersionEndpoint:
    """GET /version — Application version info."""

    def test_returns_200_with_app_info(self, client):
        response = client.get("/version")
        assert response.status_code == 200
        body = response.json()

        assert body["app"] == "Ready2Go CRM"
        assert body["version"] == "1.0.0"
        assert body["environment"] == "test"
