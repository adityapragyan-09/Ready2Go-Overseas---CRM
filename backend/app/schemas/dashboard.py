"""
Ready2Go CRM — Dashboard & Analytics Schemas
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    total_applicants: int
    student_visa: int
    visit_visa: int
    tourist_visa: int
    business_visa: int
    applications_processing: int
    documents_pending: int
    documents_uploaded: int
    visa_approved: int
    visa_rejected: int
    completed_applications: int
    total_employees: int
    active_employees: int
    inactive_employees: int
    todays_logins: int
    unread_notifications: int


class KeyValueMetric(BaseModel):
    label: str
    value: Any


class ApplicantAnalytics(BaseModel):
    by_country: List[KeyValueMetric]
    by_visa_type: List[KeyValueMetric]
    by_status: List[KeyValueMetric]
    monthly_registrations: List[KeyValueMetric]
    yearly_registrations: List[KeyValueMetric]


class DocumentItem(BaseModel):
    document_code: str
    original_file_name: str
    file_size: int
    applicant_name: str


class DocumentAnalytics(BaseModel):
    documents_uploaded: int
    pending_documents: int
    by_type: List[KeyValueMetric]
    storage_usage: int
    largest_documents: List[DocumentItem]


class ProgressAnalytics(BaseModel):
    status_distribution: List[KeyValueMetric]
    average_completion_time: Optional[float] = None
    current_pipeline: List[KeyValueMetric]


class ChatAnalytics(BaseModel):
    messages_today: int
    system_messages: int
    employee_messages: int


class NotificationAnalytics(BaseModel):
    unread_notifications: int
    notifications_today: int
    notifications_by_module: List[KeyValueMetric]


class DashboardChartsResponse(BaseModel):
    applicant_analytics: ApplicantAnalytics
    document_analytics: DocumentAnalytics
    progress_analytics: ProgressAnalytics
    chat_analytics: ChatAnalytics
    notification_analytics: NotificationAnalytics


class RecentApplicant(BaseModel):
    id: int
    full_name: str
    visa_type: str
    status: str
    created_at: datetime


class RecentDocument(BaseModel):
    id: int
    original_file_name: str
    document_type: str
    uploaded_at: datetime
    applicant_name: str


class RecentStatusUpdate(BaseModel):
    id: int
    current_status: str
    previous_status: Optional[str] = None
    remarks: str
    updated_at: datetime
    applicant_name: str
    updater_name: str


class RecentChatMessage(BaseModel):
    id: int
    content: str
    sender_name: str
    applicant_name: str
    created_at: datetime


class RecentEmployee(BaseModel):
    id: int
    name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime


class RecentNotification(BaseModel):
    id: int
    title: str
    message: str
    type: str
    created_at: datetime


class QuickActionsMetadata(BaseModel):
    create_applicant: bool
    upload_document: bool
    create_employee: bool
    update_progress: bool


class DashboardRecentResponse(BaseModel):
    recent_applicants: List[RecentApplicant]
    recent_documents: List[RecentDocument]
    recent_status_updates: List[RecentStatusUpdate]
    recent_chat_messages: List[RecentChatMessage]
    recent_employees: List[RecentEmployee]
    recent_notifications: List[RecentNotification]
    quick_actions: QuickActionsMetadata


class DashboardEmployeeResponse(BaseModel):
    employee_id: int
    name: str
    role: str
    applicants_assigned: int
    completed_cases: int
    pending_cases: int
    documents_pending: int
    documents_uploaded: int
    average_processing_time: Optional[float] = None
    latest_login: Optional[datetime] = None
    latest_logout: Optional[datetime] = None


class DashboardSystemResponse(BaseModel):
    total_db_size_bytes: int
    sqlite_version: str
    system_uptime_seconds: Optional[float] = None
    active_user_sessions: int
    total_queries_logged: int
