"""
Ready2Go CRM — Application Status Constants

All valid lifecycle stages for an applicant's visa application.
"""

INQUIRY = "inquiry"
DOCUMENTS_PENDING = "documents_pending"
DOCUMENTS_SUBMITTED = "documents_submitted"
APPLICATION_PROCESSING = "application_processing"
UNDER_REVIEW = "under_review"
INTERVIEW_SCHEDULED = "interview_scheduled"
VISA_APPROVED = "visa_approved"
VISA_REJECTED = "visa_rejected"
APPROVED = "approved"
VISA_ISSUED = "visa_issued"
REJECTED = "rejected"
CANCELLED = "cancelled"
COMPLETED = "completed"

# For validation checks
ALL_STATUSES = (
    INQUIRY,
    DOCUMENTS_PENDING,
    DOCUMENTS_SUBMITTED,
    APPLICATION_PROCESSING,
    UNDER_REVIEW,
    INTERVIEW_SCHEDULED,
    VISA_APPROVED,
    VISA_REJECTED,
    APPROVED,
    VISA_ISSUED,
    REJECTED,
    CANCELLED,
    COMPLETED,
)
