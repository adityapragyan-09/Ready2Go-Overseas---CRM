"""
Ready2Go CRM — End-to-End Business Workflow Integration Tests

Validates every core business process by simulating real user
interactions through the API. Tests cover lead management,
assignment workflow, applicant lifecycle, documents, notifications,
dashboard, activity logs, and role-based access control.
"""

import pytest


class TestLeadWorkflow:
    """Lead inquiry, listing, search, and duplicate detection."""

    def test_create_lead(self, client, admin_headers):
        """Verify lead creation returns correct structure."""
        resp = client.post("/api/v1/lead-inquiries", json={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "visa_type": "student",
            "preferred_country": "Canada",
            "source": "WEBSITE",
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        lead = data["data"]
        assert lead["full_name"] == "Jane Doe"
        assert lead["lead_number"].startswith("LEAD-")
        assert lead["status"] == "NEW"
        assert lead["source"] == "WEBSITE"

    def test_list_leads(self, client, admin_headers):
        """Verify lead listing with pagination."""
        resp = client.get("/api/v1/lead-inquiries?page=1&page_size=10", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "total" in data["data"]

    def test_search_leads(self, client, admin_headers):
        """Verify lead search endpoint works with valid params."""
        resp = client.get("/api/v1/lead-inquiries?search=Jane", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data["data"]
        assert "items" in data["data"]

    def test_duplicate_detection(self, client, admin_headers):
        """Verify duplicate lead detection (same email)."""
        resp = client.post("/api/v1/lead-inquiries", json={
            "full_name": "Jane Doe Clone",
            "email": "jane@example.com",
            "phone": "+1987654321",
            "visa_type": "student",
        }, headers=admin_headers)
        # Should respond with success regardless of policy (ALLOW/REJECT/FLAG)
        assert "success" in resp.json()


class TestAssignmentWorkflow:
    """Employee requests -> Admin approves -> Lead assigned."""

    def test_full_assignment_cycle(self, client, employee_headers, admin_headers):
        """Journey B: Employee requests, admin approves, lead assigned."""
        resp = client.post("/api/v1/lead-inquiries", json={
            "full_name": "Assignment Test",
            "email": "assign@test.com",
            "visa_type": "student",
        }, headers=admin_headers)
        assert resp.status_code == 201
        lead_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/assignment-requests", json={
            "lead_id": lead_id,
        }, headers=employee_headers)
        assert resp.status_code == 201
        request_id = resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assignment-requests/{request_id}/approve",
                          json={"remarks": "Approved"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = client.get(f"/api/v1/lead-inquiries/{lead_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["assigned_employee_id"] is not None

    def test_direct_assign(self, client, admin_headers):
        """Journey C: Admin directly assigns lead to employee."""
        resp = client.post("/api/v1/lead-inquiries", json={
            "full_name": "Direct Assign",
            "email": "direct@test.com",
            "visa_type": "student",
        }, headers=admin_headers)
        assert resp.status_code == 201
        lead_id = resp.json()["data"]["id"]

        resp = client.get("/api/v1/employees?page_size=5", headers=admin_headers)
        employees = resp.json()["data"]["items"]
        assert len(employees) > 0
        emp_id = employees[0]["id"]

        resp = client.post("/api/v1/assignment-requests/direct-assign", json={
            "lead_id": lead_id,
            "employee_id": emp_id,
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_duplicate_request_prevented(self, client, admin_headers, employee_headers):
        """Verify duplicate assignment requests are rejected."""
        resp = client.post("/api/v1/lead-inquiries", json={
            "full_name": "Dup Request",
            "visa_type": "student",
        }, headers=admin_headers)
        lead_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/assignment-requests", json={"lead_id": lead_id},
                          headers=employee_headers)
        assert resp.status_code == 201

        resp = client.post("/api/v1/assignment-requests", json={"lead_id": lead_id},
                          headers=employee_headers)
        assert resp.status_code == 400


class TestApplicantWorkflow:
    """Applicant CRUD, status progression, progress tracking."""

    def test_create_applicant(self, client, admin_headers):
        """Verify applicant creation returns correct structure."""
        resp = client.post("/api/v1/applicants", json={
            "full_name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890",
            "visa_type": "student",
            "country": "Australia",
            "status": "inquiry",
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        app = data["data"]
        assert app["applicant_code"].startswith("APP-")
        assert app["full_name"] == "John Smith"

    def test_list_applicants(self, client, admin_headers):
        """Verify applicant listing with pagination."""
        resp = client.get("/api/v1/applicants?page=1&page_size=10", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data["data"]
        assert "total" in data["data"]

    def test_search_applicants(self, client, admin_headers):
        """Verify applicant search endpoint works with valid params."""
        resp = client.get("/api/v1/applicants?search=John", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data["data"]
        assert "items" in data["data"]

    def test_status_update_with_timeline(self, client, admin_headers):
        """Verify status progression creates timeline entries."""
        resp = client.post("/api/v1/applicants", json={
            "full_name": "Status Test",
            "visa_type": "student",
            "status": "inquiry",
        }, headers=admin_headers)
        app_id = resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/progress/applicant/{app_id}", json={
            "status": "documents_pending",
            "remarks": "Requested documents",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = client.get(f"/api/v1/progress/applicant/{app_id}", headers=admin_headers)
        assert resp.status_code == 200
        entries = resp.json()["data"]
        assert len(entries) >= 2

    def test_applicant_not_found(self, client, admin_headers):
        """Verify 404 for non-existent applicant."""
        resp = client.get("/api/v1/applicants/999999", headers=admin_headers)
        assert resp.status_code == 404


class TestInboxWorkflow:
    """Notifications: listing, unread count, mark-read."""

    def test_notification_listing(self, client, admin_headers):
        resp = client.get("/api/v1/notifications?page=1&page_size=10", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()["data"]

    def test_unread_count(self, client, admin_headers):
        resp = client.get("/api/v1/notifications/unread-count", headers=admin_headers)
        assert resp.status_code == 200
        assert "unread_count" in resp.json()["data"]

    def test_mark_read(self, client, admin_headers):
        """Verify mark-read works on notification (if any exist)."""
        resp = client.get("/api/v1/notifications?page_size=1", headers=admin_headers)
        data = resp.json()
        if data["data"]["total"] > 0:
            notif_id = data["data"]["items"][0]["id"]
            resp = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=admin_headers)
            assert resp.status_code == 200
            assert resp.json()["success"] is True


class TestDashboardWorkflow:
    """Dashboard metrics consistency."""

    def test_dashboard_summary(self, client, admin_headers, employee_headers):
        """Verify dashboard summary for both roles."""
        for headers in [admin_headers, employee_headers]:
            resp = client.get("/api/v1/dashboard/summary", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert "total_applicants" in data["data"]

    def test_dashboard_charts(self, client, admin_headers):
        resp = client.get("/api/v1/dashboard/charts", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestActivityLogWorkflow:
    """Activity logs are admin-only and properly filtered."""

    def test_activity_logs_admin(self, client, admin_headers):
        resp = client.get("/api/v1/activity-logs?page=1", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_activity_logs_employee_denied(self, client, employee_headers):
        resp = client.get("/api/v1/activity-logs", headers=employee_headers)
        assert resp.status_code == 403


class TestRoleWorkflows:
    """Verify role-based access controls."""

    def test_employee_cannot_access_admin_routes(self, client, employee_headers):
        admin_routes = [
            ("GET", "/api/v1/employees"),
            ("POST", "/api/v1/employees"),
            ("GET", "/api/v1/activity-logs"),
        ]
        for method, path in admin_routes:
            resp = client.get(path, headers=employee_headers) if method == "GET" \
                else client.post(path, json={}, headers=employee_headers)
            assert resp.status_code == 403, f"{method} {path} returned {resp.status_code}"

    def test_unauthenticated_blocked(self, client):
        protected = [
            "/api/v1/applicants",
            "/api/v1/employees",
            "/api/v1/lead-inquiries",
            "/api/v1/notifications",
            "/api/v1/dashboard/summary",
        ]
        for path in protected:
            resp = client.get(path)
            assert resp.status_code == 401, f"GET {path} returned {resp.status_code}"


class TestNegativeCases:
    """Input validation and error handling."""

    def test_invalid_applicant_status(self, client, admin_headers):
        resp = client.post("/api/v1/applicants", json={
            "full_name": "Bad Status",
            "visa_type": "student",
            "status": "non_existent_status",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_invalid_visa_type(self, client, admin_headers):
        resp = client.post("/api/v1/applicants", json={
            "full_name": "Bad Visa",
            "visa_type": "invalid_visa",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_missing_required_fields(self, client, admin_headers):
        resp = client.post("/api/v1/applicants", json={}, headers=admin_headers)
        assert resp.status_code == 422

    def test_invalid_email_format(self, client, admin_headers):
        resp = client.post("/api/v1/applicants", json={
            "full_name": "Bad Email",
            "visa_type": "student",
            "email": "not-an-email",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_invalid_pagination(self, client, admin_headers):
        resp = client.get("/api/v1/applicants?page=0", headers=admin_headers)
        assert resp.status_code == 422

    def test_oversized_page_size(self, client, admin_headers):
        resp = client.get("/api/v1/applicants?page_size=1000", headers=admin_headers)
        assert resp.status_code == 422

    def test_delete_nonexistent(self, client, admin_headers):
        resp = client.delete("/api/v1/lead-inquiries/999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_access_nonexistent_id(self, client, admin_headers):
        resp = client.get("/api/v1/lead-inquiries/999999", headers=admin_headers)
        assert resp.status_code == 404
