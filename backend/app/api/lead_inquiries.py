"""
Ready2Go CRM — Lead Inquiry Routes

Router: /api/v1/lead-inquiries
Access Level: Authenticated Users (JWT required)

Endpoints:
    POST   /                          — Create a new lead inquiry
    GET    /                          — List leads with filters, search, pagination
    GET    /{id}                      — Get a single lead by ID
    PUT    /{id}                      — Update a lead
    DELETE /{id}                      — Delete a lead
    PATCH  /{id}/status               — Update lead status
    PATCH  /{id}/assign               — Assign lead to employee
    POST   /{id}/convert              — Convert lead to applicant (stub - 501)
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import LeadIdentity, get_current_user, resolve_lead_identity
from app.core.enums import CallerType
from app.db.session import get_db
import logging

logger = logging.getLogger(__name__)
from app.models.user import User
from app.schemas.lead_inquiry import (
    LeadInquiryAssign,
    LeadInquiryCreate,
    LeadInquiryListResponse,
    LeadInquiryResponse,
    LeadInquiryStatusUpdate,
    LeadInquiryUpdate,
)
from app.services import lead_inquiry_service as service
from app.services.duplicate_service import (
    DuplicateCode,
    DuplicatePolicy,
    detect_duplicate,
    normalize_incoming,
)
from app.services.lead_activity_service import get_activities, log_activity
from app.services.notification_service import create_notification
from app.utils.response import error_response, success_response

router = APIRouter()


def _serialize_lead(lead) -> dict:
    """Convert LeadInquiry ORM object to response dict with employee name."""
    data = LeadInquiryResponse.model_validate(lead).model_dump()
    if lead.assigned_employee:
        data["assigned_employee_name"] = lead.assigned_employee.name
    data["request_id"] = lead.request_id
    return data


# ── POST / ──────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_lead_route(
    body: LeadInquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
    identity: LeadIdentity = Depends(resolve_lead_identity),
):
    """
    Create a new lead inquiry with enterprise duplicate detection.

    Authentication:
    - CRM Users: JWT Bearer token
    - Website: CRM_API_KEY as Bearer token

    Duplicate detection:
    - Request idempotency (same request_id → return existing)
    - Email match (normalized)
    - Phone match (normalized)
    - Email + Phone combination

    Configurable policies: REJECT, ALLOW, FLAG, MERGE (placeholder)
    """
    # Normalize incoming data
    normalized = normalize_incoming(body.model_dump())

    # Enterprise duplicate detection
    dup_result = detect_duplicate(
        db,
        email=normalized.get("email"),
        phone=normalized.get("phone"),
        request_id=body.request_id,
    )

    # Handle idempotency: same request_id → return existing record
    if dup_result.code == DuplicateCode.REQUEST_ALREADY_PROCESSED:
        log_activity(
            db, lead_id=dup_result.matched_lead.id, action="DUPLICATE_IGNORED",
            description=f"Duplicate ignored: {dup_result.reason_detail or 'request_id already processed'}.",
            created_by=identity.user_id,
        )
        return success_response(
            message=dup_result.reason_detail or "Request already processed.",
            data=_serialize_lead(dup_result.matched_lead),
        )

    # Handle REJECT policy: existing lead with same email/phone
    if dup_result.code == DuplicateCode.LEAD_ALREADY_EXISTS and dup_result.policy == DuplicatePolicy.REJECT:
        log_activity(
            db, lead_id=dup_result.matched_lead.id, action="DUPLICATE_REJECTED",
            description=dup_result.reason_detail or f"Duplicate: {dup_result.reason.value if dup_result.reason else 'unknown'}",
            created_by=identity.user_id,
        )
        return success_response(
            message=dup_result.reason_detail or "Lead already exists.",
            data=_serialize_lead(dup_result.matched_lead),
        )

    # Create the lead
    lead = service.create_lead(
        db,
        full_name=normalized.get("full_name", body.full_name),
        email=normalized.get("email"),
        phone=normalized.get("phone"),
        visa_type=body.visa_type,
        preferred_country=body.preferred_country,
        message=body.message,
        source=body.source or "Website",
        request_id=body.request_id,
        assigned_employee_id=body.assigned_employee_id,
        created_by=identity.user_id,
    )

    # Log duplicate information if FLAG policy
    if dup_result.code == DuplicateCode.POTENTIAL_DUPLICATE or (
        dup_result.code == DuplicateCode.LEAD_ALREADY_EXISTS and dup_result.policy == DuplicatePolicy.FLAG
    ):
        log_activity(
            db, lead_id=lead.id, action="POTENTIAL_DUPLICATE",
            description=dup_result.reason_detail or f"Potential duplicate: {dup_result.reason.value if dup_result.reason else 'unknown'}.",
            created_by=identity.user_id,
        )
        if dup_result.matched_lead:
            logger.info(
                "FLAG policy: lead %s created but matches %s via %s",
                lead.lead_number, dup_result.matched_lead.lead_number,
                dup_result.reason.value if dup_result.reason else "unknown",
            )

    # Notifications only for CRM users
    if identity.caller_type == CallerType.CRM_USER and identity.user_id:
        try:
            create_notification(
                db,
                title="New Inquiry",
                message=f"Lead inquiry from {lead.full_name} for {lead.preferred_country or 'unspecified country'}.",
                type="info",
                module="applicant",
                priority="medium",
                recipient_user_id=identity.user_id,
                created_by=identity.user_id,
                reference_type="lead",
                reference_id=lead.id,
            )
        except Exception:
            pass  # Non-fatal

    logger.info(
        "Lead created [caller=%s request_id=%s lead_number=%s source=%s code=%s ip=%s]",
        identity.caller_type.value, body.request_id, lead.lead_number, body.source,
        dup_result.code.value,
        request.client.host if request.client else "unknown",
    )

    response_data = _serialize_lead(lead)

    return success_response(
        message="Lead inquiry created successfully.",
        data=response_data,
    )


# ── GET / ───────────────────────────────────

@router.get("")
def list_leads_route(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None, alias="status"),
    source: str | None = Query(default=None, alias="source"),
    assigned_to: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List lead inquiries with search, filters, pagination, and sorting.
    Requires JWT authentication.
    """
    total, items, total_pages = service.get_leads(
        db,
        search=search,
        status_filter=status,
        source_filter=source,
        employee_id=assigned_to,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    leads_data = [_serialize_lead(lead) for lead in items]
    list_data = LeadInquiryListResponse(
        items=leads_data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    ).model_dump()

    return success_response(
        message="Lead inquiries retrieved successfully.",
        data=list_data,
    )


# ── GET /{id} ───────────────────────────────

@router.get("/{id}")
def get_lead_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single lead inquiry by ID."""
    lead = service.get_lead(db, id)
    return success_response(
        message="Lead inquiry retrieved successfully.",
        data=_serialize_lead(lead),
    )


# ── PUT /{id} ───────────────────────────────

@router.put("/{id}")
def update_lead_route(
    id: int,
    body: LeadInquiryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing lead inquiry."""
    update_data = body.model_dump(exclude_unset=True)
    lead = service.update_lead(db, id, update_data, updated_by=current_user.id)
    return success_response(
        message="Lead inquiry updated successfully.",
        data=_serialize_lead(lead),
    )


# ── DELETE /{id} ────────────────────────────

@router.delete("/{id}")
def delete_lead_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a lead inquiry permanently."""
    result = service.delete_lead(db, id)
    return success_response(
        message=f"Lead inquiry '{result['lead_number']}' deleted successfully.",
    )


# ── PATCH /{id}/status ─────────────────────

@router.patch("/{id}/status")
def update_lead_status_route(
    id: int,
    body: LeadInquiryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the status of a lead inquiry."""
    lead = service.change_lead_status(db, id, body.status, changed_by=current_user.id)
    return success_response(
        message=f"Lead status updated to '{lead.status}'.",
        data=_serialize_lead(lead),
    )


# ── PATCH /{id}/assign ─────────────────────

@router.patch("/{id}/assign")
def assign_lead_route(
    id: int,
    body: LeadInquiryAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a lead inquiry to an employee."""
    lead = service.assign_employee(db, id, body.employee_id, assigned_by=current_user.id)
    assigned_name = lead.assigned_employee.name if lead.assigned_employee else "Unknown"
    return success_response(
        message=f"Lead assigned to {assigned_name}.",
        data=_serialize_lead(lead),
    )


# ── POST /{id}/convert ─────────────────────

@router.post("/{id}/convert")
def convert_lead_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert a lead to an applicant. (Stub — returns 501)"""
    return service.convert_to_applicant(db, id)


# ── GET /{id}/activities ──────────────────

@router.get("/{id}/activities")
def get_lead_activities_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve timeline of activities for a lead inquiry."""
    activities = get_activities(db, id)
    activity_data = [
        {
            "id": a.id,
            "action": a.action,
            "description": a.description,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "created_by_name": a.creator.name if a.creator else None,
            "created_at": a.created_at,
        }
        for a in activities
    ]
    return success_response(
        message="Lead activities retrieved successfully.",
        data=activity_data,
    )
