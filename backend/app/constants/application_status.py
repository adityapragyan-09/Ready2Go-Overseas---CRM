"""
Ready2Go CRM — Application Status Constants
"""

INQUIRY = "inquiry"
DOCUMENTS_PENDING = "documents_pending"
DOCUMENTS_SUBMITTED = "documents_submitted"
UNDER_REVIEW = "under_review"
APPROVED = "approved"
VISA_ISSUED = "visa_issued"
REJECTED = "rejected"
CANCELLED = "cancelled"

# For patterns or validation checks
ALL_STATUSES = (
    INQUIRY,
    DOCUMENTS_PENDING,
    DOCUMENTS_SUBMITTED,
    UNDER_REVIEW,
    APPROVED,
    VISA_ISSUED,
    REJECTED,
    CANCELLED,
)
