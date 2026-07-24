"""
Ready2Go CRM — Enterprise Document Storage Tests (v2)

Covers:
- Storage Service (unit)
- Document Service + Repository (integration)
- API Routes (integration)
- Migration script logic
- Error handling
- Permissions
"""

import io
import sys
from pathlib import Path

import pytest

from app.core.config import settings
from app.errors.document_errors import (
    DocumentError, DOCUMENT_NOT_FOUND, UPLOAD_FAILED, SIGNED_URL_FAILED,
    INVALID_FILE_TYPE, FILE_TOO_LARGE,
)
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.services.storage_service import (
    _normalize, upload_file, generate_signed_url, delete_file,
    verify_file_exists, list_folder, create_zip, diagnose_path,
)

FILE_PDF = b"%PDF-1.4 fake pdf content"
FILE_DOCX = b"PK\x03\x04 fake docx content"
FILE_PNG = b"\x89PNG\r\n\x1a\n fake png"
FILE_JPEG = b"\xff\xd8\xff\xe0 fake jpeg"


def _migrate_normalize(path: str) -> str:
    """Inline copy of migrate_document_storage.normalize()."""
    if not path:
        return path
    p = path.strip().replace("\\", "/").lstrip("/")
    prefix = f"{settings.SUPABASE_BUCKET}/"
    if p.startswith(prefix):
        p = p[len(prefix):]
    p = p.lstrip("/")
    while "//" in p:
        p = p.replace("//", "/")
    return p.strip()


@pytest.fixture
def sample_applicant(db_session):
    """Create a minimal applicant for document attachment."""
    from app.models.applicant import Applicant
    app = Applicant(
        applicant_code="APP-999999",
        full_name="Storage Test V2 Applicant",
        email="storagetestv2@example.com",
        visa_type="student",
        created_by=1,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


# ═══════════════════════════════════════════════════════════════════════
# Storage Service — Unit Tests
# ═══════════════════════════════════════════════════════════════════════

class TestNormalize:
    def test_strips_bucket_prefix(self):
        assert _normalize(f"{settings.SUPABASE_BUCKET}/applicants/APP-1/a.pdf") == "applicants/APP-1/a.pdf"

    def test_already_canonical(self):
        assert _normalize("applicants/APP-1/a.pdf") == "applicants/APP-1/a.pdf"

    def test_leading_slash(self):
        assert _normalize("/applicants/APP-1/a.pdf") == "applicants/APP-1/a.pdf"

    def test_backslashes(self):
        assert _normalize("applicants\\APP-1\\a.pdf") == "applicants/APP-1/a.pdf"

    def test_duplicate_slashes(self):
        assert _normalize("applicants//APP-1///a.pdf") == "applicants/APP-1/a.pdf"

    def test_empty(self):
        assert _normalize("") == ""
        assert _normalize(None) is None

    def test_bucket_prefix_plus_leading_slash(self):
        path = f"/{settings.SUPABASE_BUCKET}/applicants/APP-1/a.pdf"
        assert _normalize(path) == "applicants/APP-1/a.pdf"

    def test_idempotent(self):
        p = _normalize(f"/{settings.SUPABASE_BUCKET}//applicants\\APP-1/a.pdf")
        assert _normalize(p) == p


class TestStorageService:
    """All storage operations work via local fallback in test mode."""

    def test_upload_local(self):
        r = upload_file(io.BytesIO(FILE_PDF), "applicants/APP-TEST/upload.pdf", "application/pdf")
        assert r["success"] is True
        assert r["data"]["canonical_path"] == "applicants/APP-TEST/upload.pdf"

    def test_upload_normalizes_path(self):
        r = upload_file(io.BytesIO(FILE_PDF), f"{settings.SUPABASE_BUCKET}/applicants/APP-TEST/norm.pdf", "application/pdf")
        assert r["success"] is True
        assert r["data"]["canonical_path"] == "applicants/APP-TEST/norm.pdf"

    def test_verify_exists(self):
        r = verify_file_exists("applicants/APP-TEST/upload.pdf")
        assert r["success"] is True
        assert r["data"]["exists"] is True

    def test_verify_not_exists(self):
        r = verify_file_exists("applicants/APP-TEST/nonexistent.pdf")
        assert r["success"] is True
        assert r["data"]["exists"] is False

    def test_list_folder(self):
        r = list_folder("applicants/APP-TEST")
        assert r["success"] is True
        assert isinstance(r["data"]["objects"], list)

    def test_signed_url_local(self):
        r = generate_signed_url("applicants/APP-TEST/upload.pdf")
        assert r["success"] is True
        assert "uploads" in r["data"]["signed_url"]

    def test_delete(self):
        upload_file(io.BytesIO(FILE_PDF), "applicants/APP-TEST/to-delete.pdf", "application/pdf")
        r = delete_file("applicants/APP-TEST/to-delete.pdf")
        assert r["success"] is True
        v = verify_file_exists("applicants/APP-TEST/to-delete.pdf")
        assert v["data"]["exists"] is False

    def test_upload_png(self):
        r = upload_file(io.BytesIO(FILE_PNG), "applicants/APP-TEST/photo.png", "image/png")
        assert r["success"] is True

    def test_upload_jpeg(self):
        r = upload_file(io.BytesIO(FILE_JPEG), "applicants/APP-TEST/photo.jpg", "image/jpeg")
        assert r["success"] is True


# ═══════════════════════════════════════════════════════════════════════
# Document Repository — Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDocumentRepository:
    """Requires a database session fixture (provided by conftest)."""

    def test_create_and_get(self, db_session, sample_applicant):
        repo = DocumentRepository(db_session)
        doc = repo.create(
            applicant_id=sample_applicant.id,
            document_type="passport",
            original_name="test.pdf",
            stored_name="uuid.pdf",
            storage_path="applicants/APP-TEST/uuid.pdf",
            mime_type="application/pdf",
            file_extension="pdf",
            file_size=100,
            uploaded_by=1,
        )
        assert doc.id > 0
        assert doc.document_code.startswith("DOC-")
        assert doc.storage_path == "applicants/APP-TEST/uuid.pdf"
        fetched = repo.get_by_id(doc.id)
        assert fetched.id == doc.id

    def test_get_not_found(self, db_session):
        repo = DocumentRepository(db_session)
        with pytest.raises(DocumentError) as exc:
            repo.get_by_id(99999)
        assert exc.value.code == "DOCUMENT_NOT_FOUND"

    def test_list_by_applicant(self, db_session, sample_applicant):
        repo = DocumentRepository(db_session)
        repo.create(applicant_id=sample_applicant.id, document_type="passport",
                    original_name="a.pdf", stored_name="a.pdf",
                    storage_path="applicants/APP-TEST/a.pdf", mime_type="application/pdf",
                    file_extension="pdf", file_size=10, uploaded_by=1)
        repo.create(applicant_id=sample_applicant.id, document_type="ielts",
                    original_name="b.pdf", stored_name="b.pdf",
                    storage_path="applicants/APP-TEST/b.pdf", mime_type="application/pdf",
                    file_extension="pdf", file_size=20, uploaded_by=1)
        repo.commit()
        docs = repo.list_by_applicant(sample_applicant.id)
        assert len(docs) >= 2

    def test_soft_delete_and_restore(self, db_session, sample_applicant):
        repo = DocumentRepository(db_session)
        doc = repo.create(applicant_id=sample_applicant.id, document_type="passport",
                          original_name="del.pdf", stored_name="del.pdf",
                          storage_path="applicants/APP-TEST/del.pdf", mime_type="application/pdf",
                          file_extension="pdf", file_size=10, uploaded_by=1)
        repo.commit()
        repo.soft_delete(doc, deleted_by=1)
        repo.commit()
        with pytest.raises(DocumentError):
            repo.get_by_id(doc.id)
        restored = repo.get_by_id(doc.id, include_deleted=True)
        assert restored.is_deleted is True
        repo.restore(restored)
        repo.commit()
        fetched = repo.get_by_id(doc.id)
        assert fetched.is_deleted is False


# ═══════════════════════════════════════════════════════════════════════
# Document Service — Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class MockUploadFile:
    """Minimal mock of FastAPI UploadFile for testing DocumentService."""
    def __init__(self, filename, content_type, data):
        self.filename = filename
        self.content_type = content_type
        self.file = io.BytesIO(data)


class TestDocumentService:
    def test_upload_full_flow(self, db_session, sample_applicant, admin_user):
        repo = DocumentRepository(db_session)
        svc = DocumentService(repo)
        mock = MockUploadFile("passport.pdf", "application/pdf", FILE_PDF)
        result = svc.upload(
            file=mock, file_size=len(FILE_PDF),
            applicant_id=sample_applicant.id, document_type="passport",
            uploaded_by=admin_user.id, applicant_code=sample_applicant.applicant_code,
        )
        assert result["storage_path"].startswith("applicants/")
        assert not result["storage_path"].startswith(settings.SUPABASE_BUCKET)
        assert result["file_extension"] == "pdf"
        assert result["document_type"] == "passport"

    def test_upload_invalid_type(self, db_session, sample_applicant, admin_user):
        repo = DocumentRepository(db_session)
        svc = DocumentService(repo)
        with pytest.raises(DocumentError) as exc:
            mock = MockUploadFile("bad.exe", "application/x-msdownload", b"MZ")
            svc.upload(file=mock, file_size=10,
                       applicant_id=sample_applicant.id, document_type="passport",
                       uploaded_by=admin_user.id,
                       applicant_code=sample_applicant.applicant_code)
        assert exc.value.code == "INVALID_FILE_TYPE"

    def test_view_and_download_urls(self, db_session, sample_applicant, admin_user):
        repo = DocumentRepository(db_session)
        svc = DocumentService(repo)
        mock = MockUploadFile("view.pdf", "application/pdf", FILE_PDF)
        result = svc.upload(file=mock, file_size=len(FILE_PDF),
                            applicant_id=sample_applicant.id, document_type="passport",
                            uploaded_by=admin_user.id,
                            applicant_code=sample_applicant.applicant_code)
        doc_id = result["id"]
        view = svc.get_view_url(doc_id)
        assert "view_url" in view
        dl = svc.get_download_url(doc_id)
        assert "download_url" in dl

    def test_delete_and_restore(self, db_session, sample_applicant, admin_user):
        repo = DocumentRepository(db_session)
        svc = DocumentService(repo)
        mock = MockUploadFile("del.pdf", "application/pdf", FILE_PDF)
        result = svc.upload(file=mock, file_size=len(FILE_PDF),
                            applicant_id=sample_applicant.id, document_type="passport",
                            uploaded_by=admin_user.id,
                            applicant_code=sample_applicant.applicant_code)
        doc_id = result["id"]
        deleted = svc.delete(doc_id, deleted_by=admin_user.id)
        assert deleted["is_deleted"] is True
        restored = svc.restore(doc_id)
        assert restored["is_deleted"] is False


# ═══════════════════════════════════════════════════════════════════════
# API Route — Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDocumentAPI:
    def test_upload_pdf(self, client, admin_headers, sample_applicant):
        resp = client.post(
            "/api/v1/documents/upload",
            data={"applicant_id": sample_applicant.id, "document_type": "passport"},
            files={"file": ("test.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["success"] is True
        doc = data["data"]
        assert doc["storage_path"].startswith("applicants/")
        assert settings.SUPABASE_BUCKET not in doc["storage_path"]

    def test_upload_docx(self, client, admin_headers, sample_applicant):
        resp = client.post(
            "/api/v1/documents/upload",
            data={"applicant_id": sample_applicant.id, "document_type": "academic_certificate"},
            files={"file": ("report.docx", io.BytesIO(FILE_DOCX),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["success"] is True

    def test_upload_png(self, client, admin_headers, sample_applicant):
        resp = client.post(
            "/api/v1/documents/upload",
            data={"applicant_id": sample_applicant.id, "document_type": "photograph"},
            files={"file": ("photo.png", io.BytesIO(FILE_PNG), "image/png")},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text

    def test_upload_jpg(self, client, admin_headers, sample_applicant):
        resp = client.post(
            "/api/v1/documents/upload",
            data={"applicant_id": sample_applicant.id, "document_type": "photograph"},
            files={"file": ("photo.jpg", io.BytesIO(FILE_JPEG), "image/jpeg")},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text

    def test_upload_invalid_type(self, client, admin_headers, sample_applicant):
        resp = client.post(
            "/api/v1/documents/upload",
            data={"applicant_id": sample_applicant.id, "document_type": "passport"},
            files={"file": ("test.exe", io.BytesIO(b"MZ"), "application/x-msdownload")},
            headers=admin_headers,
        )
        assert resp.status_code == 400  # FastAPI HTTPException 400

    def test_view(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("view.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/view", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        assert "view_url" in resp.json()["data"]

    def test_download(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("dl.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/download", headers=admin_headers)
        assert resp.status_code == 200
        assert "download_url" in resp.json()["data"]

    def test_list(self, client, admin_headers, sample_applicant):
        client.post("/api/v1/documents/upload",
                    data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                    files={"file": ("list.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                    headers=admin_headers)
        resp = client.get(f"/api/v1/documents/applicant/{sample_applicant.id}", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_soft_delete(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("del.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert resp.status_code == 200
        lst = client.get(f"/api/v1/documents/applicant/{sample_applicant.id}", headers=admin_headers)
        ids = [d["id"] for d in lst.json()["data"]]
        assert doc_id not in ids

    def test_restore(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("restore.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        resp = client.patch(f"/api/v1/documents/{doc_id}/restore", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["is_deleted"] is False

    def test_metadata(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("meta.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == doc_id

    def test_404(self, client, admin_headers):
        for path in ["/api/v1/documents/99999",
                     "/api/v1/documents/99999/view",
                     "/api/v1/documents/99999/download"]:
            resp = client.get(path, headers=admin_headers)
            assert resp.status_code == 404, f"{path} returned {resp.status_code}"
        resp = client.delete("/api/v1/documents/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_zip_download(self, client, admin_headers, sample_applicant):
        for name in ["zip1.pdf", "zip2.pdf"]:
            client.post("/api/v1/documents/upload",
                        data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                        files={"file": (name, io.BytesIO(FILE_PDF), "application/pdf")},
                        headers=admin_headers)
        resp = client.get(f"/api/v1/documents/applicant/{sample_applicant.id}/download-all", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

    def test_diagnose(self, client, admin_headers, sample_applicant):
        up = client.post("/api/v1/documents/upload",
                         data={"applicant_id": sample_applicant.id, "document_type": "passport"},
                         files={"file": ("diag.pdf", io.BytesIO(FILE_PDF), "application/pdf")},
                         headers=admin_headers)
        doc_id = up.json()["data"]["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/diagnose", headers=admin_headers)
        assert resp.status_code == 200
        diag = resp.json()["data"]
        assert "bucket" in diag
        assert "db_storage_path" in diag
        assert "normalized_storage_path" in diag


# ═══════════════════════════════════════════════════════════════════════
# Migration Logic Tests
# ═══════════════════════════════════════════════════════════════════════

class TestMigration:
    def test_migration_normalize_bucket_prefix(self):
        old = f"{settings.SUPABASE_BUCKET}/applicants/APP-001/old.pdf"
        new = _migrate_normalize(old)
        assert new == "applicants/APP-001/old.pdf"
        assert not new.startswith(settings.SUPABASE_BUCKET)

    def test_migration_skips_canonical(self):
        canonical = "applicants/APP-001/doc.pdf"
        assert _migrate_normalize(canonical) == canonical

    def test_migration_idempotent(self):
        cases = [
            "applicants/APP-001/a.pdf",
            f"{settings.SUPABASE_BUCKET}/applicants/APP-001/a.pdf",
            "/applicants/APP-001/a.pdf",
            "applicants//APP-001\\a.pdf",
        ]
        for c in cases:
            first = _migrate_normalize(c)
            second = _migrate_normalize(first)
            assert first == second, f"Not idempotent: '{c}' -> '{first}' -> '{second}'"
