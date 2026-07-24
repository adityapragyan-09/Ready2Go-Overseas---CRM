"""
Ready2Go CRM — Enterprise Document Error Codes

Standardized error codes and exception classes for the document management
module.  Every error is a structured JSON object with a machine-readable
``code`` and a human-readable ``message``.
"""

from typing import Any


class DocumentError(Exception):
    """Base exception for all document-module errors."""

    def __init__(self, code: str, message: str, status_code: int = 400, detail: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "detail": self.detail,
        }


# ── Error codes ──────────────────────────────────────────────────────

DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
UPLOAD_FAILED = "UPLOAD_FAILED"
DELETE_FAILED = "DELETE_FAILED"
SIGNED_URL_FAILED = "SIGNED_URL_FAILED"
OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
INVALID_STORAGE_PATH = "INVALID_STORAGE_PATH"
INVALID_BUCKET = "INVALID_BUCKET"
BUCKET_UNAVAILABLE = "BUCKET_UNAVAILABLE"
DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
ZIP_FAILED = "ZIP_FAILED"
INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
FILE_TOO_LARGE = "FILE_TOO_LARGE"
VERIFICATION_FAILED = "VERIFICATION_FAILED"
STORAGE_AUTH_FAILED = "STORAGE_AUTH_FAILED"
STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
RESTORE_FAILED = "RESTORE_FAILED"


# ── Factory functions ────────────────────────────────────────────────

def doc_not_found(doc_id: int) -> DocumentError:
    return DocumentError(DOCUMENT_NOT_FOUND, f"Document {doc_id} not found.", 404)


def upload_failed(reason: str = "") -> DocumentError:
    msg = f"File upload failed.{' ' + reason if reason else ''}"
    return DocumentError(UPLOAD_FAILED, msg, 500)


def object_not_found(path: str) -> DocumentError:
    return DocumentError(OBJECT_NOT_FOUND, f"Storage object not found: {path}", 404)


def signed_url_failed(path: str = "") -> DocumentError:
    msg = f"Failed to generate signed URL.{' Path: ' + path if path else ''}"
    return DocumentError(SIGNED_URL_FAILED, msg, 502)


def storage_unavailable() -> DocumentError:
    return DocumentError(STORAGE_UNAVAILABLE, "Storage service is currently unavailable.", 502)
