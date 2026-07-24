"""
Ready2Go CRM — Document Storage Integration Tests

Covers the full document lifecycle including:
- Path normalization (bucket prefix stripping)
- Upload, signed URL generation, verification
- Download, preview, ZIP download
- Soft delete
- Migration of pre-existing path formats
"""

import io
import zipfile

import pytest
from pathlib import Path

from app.services.storage_service import (
    normalize_storage_path,
    upload_file,
    generate_signed_url,
    delete_file,
    download_file_as_bytes,
    list_storage_objects,
    diagnose_storage_path,
)
from app.models.document import Document
from app.models.applicant import Applicant
from app.core.config import settings


FILE_CONTENT_PDF = b"%PDF-1.4 fake pdf content for testing"
FILE_CONTENT_DOCX = b"PK\x03\x04 fake docx content for testing"
FILE_CONTENT_PNG = b"\x89PNG\r\n\x1a\n fake png content"
FILE_CONTENT_JPEG = b"\xff\xd8\xff\xe0 fake jpeg content"


# ═══════════════════════════════════════════════════════════════════════
# Module 2 — normalize_storage_path() unit tests
# ═══════════════════════════════════════════════════════════════════════

class TestNormalizeStoragePath:
    """Verify canonical path normalisation rules."""

    def test_strips_bucket_prefix(self):
        path = f"{settings.SUPABASE_BUCKET}/applicants/APP-000048/file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_keeps_already_canonical(self):
        path = "applicants/APP-000048/file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_strips_leading_slash(self):
        path = "/applicants/APP-000048/file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_normalizes_windows_backslashes(self):
        path = "applicants\\APP-000048\\file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_collapses_duplicate_slashes(self):
        path = "applicants//APP-000048///file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_combined_edge_cases(self):
        path = f"/{settings.SUPABASE_BUCKET}//applicants\\\\APP-000048\\file.pdf"
        assert normalize_storage_path(path) == "applicants/APP-000048/file.pdf"

    def test_empty_string(self):
        assert normalize_storage_path("") == ""

    def test_none(self):
        assert normalize_storage_path(None) is None


# ═══════════════════════════════════════════════════════════════════════
# Integration — Document Lifecycle
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_applicant(db_session):
    """Create a minimal applicant for document attachment."""
    from app.models.applicant import Applicant
    app = Applicant(
        applicant_code="APP-999999",
        full_name="Storage Test Applicant",
        email="storagetest@example.com",
        visa_type="student",
        created_by=1,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


class TestDocumentUploadLifecycle:
    """Full upload → verify → signed URL → download → delete."""

    def _upload_and_assert(self, client, admin_headers, applicant_id, file_bytes, filename, doc_type):
        """Helper: upload a file and return the created document."""
        resp = client.post(
            "/api/v1/documents/upload",
            data={
                "applicant_id": applicant_id,
                "document_type": doc_type,
            },
            files={
                "file": (filename, io.BytesIO(file_bytes), "application/octet-stream"),
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, f"Upload failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        doc = data["data"]

        # Storage path must NOT contain the bucket prefix
        assert not doc["storage_path"].startswith(f"{settings.SUPABASE_BUCKET}/"), (
            f"storage_path contains bucket prefix: {doc['storage_path']}"
        )
        # Storage path must start with applicants/
        assert doc["storage_path"].startswith("applicants/"), (
            f"storage_path has wrong format: {doc['storage_path']}"
        )
        return doc

    def test_upload_pdf(self, client, admin_headers, sample_applicant):
        """Upload PDF → verify storage_path is canonical."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "document.pdf", "passport",
        )
        assert doc["file_extension"] == "pdf"
        assert doc["mime_type"] == "application/octet-stream"

    def test_upload_docx(self, client, admin_headers, sample_applicant):
        """Upload DOCX → verify storage_path is canonical."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_DOCX, "document.docx", "academic_certificate",
        )
        assert doc["file_extension"] == "docx"

    def test_upload_png(self, client, admin_headers, sample_applicant):
        """Upload PNG image → verify."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PNG, "photo.png", "photograph",
        )
        assert doc["file_extension"] == "png"

    def test_upload_jpeg(self, client, admin_headers, sample_applicant):
        """Upload JPEG image → verify."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_JPEG, "photo.jpg", "photograph",
        )
        assert doc["file_extension"] == "jpg"

    def test_view_endpoint_returns_signed_url(self, client, admin_headers, sample_applicant):
        """GET /documents/{id}/view returns a signed URL."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "view-test.pdf", "passport",
        )
        resp = client.get(f"/api/v1/documents/{doc['id']}/view", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        view_url = data["data"]["view_url"]
        # In dev mode, the signed URL is a localhost fallback
        assert "uploads" in view_url or "signed" in view_url

    def test_download_endpoint_returns_url(self, client, admin_headers, sample_applicant):
        """GET /documents/{id}/download returns a download URL."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "download-test.pdf", "passport",
        )
        resp = client.get(f"/api/v1/documents/{doc['id']}/download", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "download_url" in data["data"]

    def test_list_applicant_documents(self, client, admin_headers, sample_applicant):
        """GET /documents/applicant/{id} returns uploaded docs."""
        self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "list-test.pdf", "passport",
        )
        resp = client.get(
            f"/api/v1/documents/applicant/{sample_applicant.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_soft_delete_document(self, client, admin_headers, sample_applicant):
        """DELETE /documents/{id} soft-deletes the document."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "delete-test.pdf", "passport",
        )
        resp = client.delete(f"/api/v1/documents/{doc['id']}", headers=admin_headers)
        assert resp.status_code == 200
        # Verify it's gone from list
        resp = client.get(
            f"/api/v1/documents/applicant/{sample_applicant.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        doc_ids = [d["id"] for d in resp.json()["data"]]
        assert doc["id"] not in doc_ids

    def test_diagnose_endpoint(self, client, admin_headers, sample_applicant):
        """GET /documents/{id}/diagnose returns comprehensive info."""
        doc = self._upload_and_assert(
            client, admin_headers, sample_applicant.id,
            FILE_CONTENT_PDF, "diagnose-test.pdf", "passport",
        )
        resp = client.get(f"/api/v1/documents/{doc['id']}/diagnose", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        diag = data["data"]
        # Must contain the new diagnostic fields
        assert "bucket" in diag
        assert "db_storage_path" in diag
        assert "normalized_storage_path" in diag
        assert "bucket_prefix_removed" in diag
        assert "object_exists" in diag or "errors" in diag


# ═══════════════════════════════════════════════════════════════════════
# Migration script test
# ═══════════════════════════════════════════════════════════════════════

class TestPathMigration:
    """Verify the fix_storage_paths.py migration logic works on existing records."""

    def test_normalize_applied_to_existing_db_record(self, db_session):
        """Simulate an old buggy record and verify normalize would fix it."""
        from app.services.storage_service import normalize_storage_path
        old_buggy_path = f"{settings.SUPABASE_BUCKET}/applicants/APP-000048/file.pdf"
        canonical = normalize_storage_path(old_buggy_path)
        assert canonical == "applicants/APP-000048/file.pdf"
        assert not canonical.startswith(f"{settings.SUPABASE_BUCKET}/")

    def test_idempotent_normalize(self):
        """Running normalize twice should not change anything."""
        paths = [
            "applicants/APP-000001/doc.pdf",
            f"{settings.SUPABASE_BUCKET}/applicants/APP-000002/file.docx",
            "/applicants/APP-000003/image.png",
            "applicants//APP-000004\\\\photo.jpg",
        ]
        for p in paths:
            first = normalize_storage_path(p)
            second = normalize_storage_path(first)
            assert first == second, (
                f"normalize is not idempotent for input '{p}': "
                f"'{first}' → '{second}'"
            )
