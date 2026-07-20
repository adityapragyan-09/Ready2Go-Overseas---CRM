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

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
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
from app.services.notification_service import create_notification
from app.utils.response import success_response

router = APIRouter()


def _serialize_lead(lead) -> dict:
    """Convert LeadInquiry ORM object to response dict with employee name."""
    data = LeadInquiryResponse.model_validate(lead).model_dump()
    if lead.assigned_employee:
        data["assigned_employee_name"] = lead.assigned_employee.name
    return data


# ── POST / ──────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_lead_route(
    body: LeadInquiryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new lead inquiry.
    Requires JWT authentication.
    Generates automatic notification on creation.
    """
    lead = service.create_lead(
        db,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        visa_type=body.visa_type,
        preferred_country=body.preferred_country,
        message=body.message,
        source=body.source,
        assigned_employee_id=body.assigned_employee_id,
        created_by=current_user.id,
    )

    # Create notification for new lead
    try:
        create_notification(
            db,
            title="New Website Inquiry",
            message=f"Lead inquiry from {lead.full_name} for {lead.preferred_country or 'unspecified country'}.",
            type="info",
            module="applicant",
            priority="medium",
            recipient_user_id=current_user.id,
            created_by=current_user.id,
            reference_type="lead",
            reference_id=lead.id,
        )
    except Exception:
        pass  # Non-fatal

    return success_response(
        message="Lead inquiry created successfully.",
        data=_serialize_lead(lead),
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
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        leads=leads_data,
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
    lead = service.change_lead_status(db, id, body.status)
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
    lead = service.assign_employee(db, id, body.employee_id)
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
