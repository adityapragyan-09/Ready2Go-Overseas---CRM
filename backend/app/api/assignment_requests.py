"""
Ready2Go CRM — Assignment Request Routes

Router: /api/v1/assignment-requests
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.assignment_request import (
    AssignmentRequestCreate,
    AssignmentRequestResponse,
    AssignmentRequestReview,
)
from app.services import assignment_service as service
from app.services.lead_activity_service import log_activity as log_lead_activity
from app.services.notification_service import create_notification
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize(req) -> dict:
    data = AssignmentRequestResponse.model_validate(req).model_dump()
    if req.employee:
        data["employee_name"] = req.employee.name
        data["employee_email"] = req.employee.email
    if req.lead:
        data["lead_number"] = req.lead.lead_number
        data["lead_name"] = req.lead.full_name
    return data


# ── POST / — Create request ─────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_request_route(
    body: AssignmentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee requests assignment of an unassigned lead."""
    req = service.create_request(db, body.lead_id, current_user.id, body.remarks)

    log_lead_activity(db, lead_id=body.lead_id, action="ASSIGNMENT_REQUESTED",
                      description=f"Assignment requested by {current_user.name}.",
                      created_by=current_user.id)

    # Notify admin
    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()
    for admin in admins:
        try:
            create_notification(db, title="New Assignment Request",
                                message=f"{current_user.name} requested assignment of lead #{body.lead_id}.",
                                type="info", module="applicant", priority="medium",
                                recipient_user_id=admin.id, created_by=current_user.id,
                                reference_type="lead", reference_id=body.lead_id)
        except Exception:
            pass

    return success_response(message="Assignment request submitted.", data=_serialize(req))


# ── GET / — List requests ──────────────────

@router.get("")
def list_requests_route(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List assignment requests. Admin sees all; employees see their own."""
    emp_id = None if current_user.role == "admin" else current_user.id
    total, items = service.list_requests(db, status_filter=status, employee_id=emp_id, page=page, page_size=page_size)
    return success_response(message="Requests retrieved.", data={
        "total": total, "page": page, "page_size": page_size,
        "items": [_serialize(r) for r in items],
    })


# ── GET /{id} — Get request ────────────────

@router.get("/{id}")
def get_request_route(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = service.get_request(db, id)
    return success_response(message="Request retrieved.", data=_serialize(req))


# ── PATCH /{id}/approve — Approve ──────────

@router.patch("/{id}/approve")
def approve_request_route(
    id: int,
    body: AssignmentRequestReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    req = service.approve_request(db, id, admin.id, body.remarks)

    log_lead_activity(db, lead_id=req.lead_id, action="ASSIGNMENT_APPROVED",
                      description=f"Assignment approved by {admin.name}.",
                      created_by=admin.id)

    try:
        create_notification(db, title="Assignment Approved",
                            message=f"Your request for lead #{req.lead_id} has been approved.",
                            type="success", module="applicant", priority="high",
                            recipient_user_id=req.employee_id, created_by=admin.id,
                            reference_type="lead", reference_id=req.lead_id)
    except Exception:
        pass

    return success_response(message="Request approved.", data=_serialize(req))


# ── PATCH /{id}/reject ─────────────────────

@router.patch("/{id}/reject")
def reject_request_route(
    id: int,
    body: AssignmentRequestReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    req = service.reject_request(db, id, admin.id, body.remarks)

    log_lead_activity(db, lead_id=req.lead_id, action="ASSIGNMENT_REJECTED",
                      description=f"Assignment rejected by {admin.name}.",
                      created_by=admin.id)

    try:
        create_notification(db, title="Assignment Rejected",
                            message=f"Your request for lead #{req.lead_id} has been rejected.",
                            type="warning", module="applicant", priority="medium",
                            recipient_user_id=req.employee_id, created_by=admin.id,
                            reference_type="lead", reference_id=req.lead_id)
    except Exception:
        pass

    return success_response(message="Request rejected.", data=_serialize(req))


# ── DELETE /{id} — Cancel ──────────────────

@router.delete("/{id}")
def cancel_request_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending request (the requester or admin)."""
    if current_user.role == "admin":
        req = service.get_request(db, id)
        if req.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending.")
        req.status = "CANCELLED"
        try:
            db.commit()
            db.refresh(req)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel.")
    else:
        req = service.cancel_request(db, id, current_user.id)

    log_lead_activity(db, lead_id=req.lead_id, action="ASSIGNMENT_CANCELLED",
                      description="Assignment request cancelled.", created_by=current_user.id)

    return success_response(message="Request cancelled.", data=_serialize(req))


# ── POST /direct-assign — Admin direct assign ─

@router.post("/direct-assign")
def direct_assign_route(
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin directly assigns (or unassigns) a lead to an employee."""
    lead_id = body.get("lead_id")
    employee_id = body.get("employee_id")
    if not lead_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_id is required.")

    lead = service.direct_assign(db, lead_id, employee_id, admin.id)
    emp_name = "Unassigned"
    if employee_id:
        emp = db.query(User).filter(User.id == employee_id).first()
        if emp:
            emp_name = emp.name

    log_lead_activity(db, lead_id=lead_id, action="LEAD_ASSIGNED",
                      description=f"Lead assigned to {emp_name} by {admin.name}.",
                      created_by=admin.id)

    return success_response(message=f"Lead assigned to {emp_name}.", data={
        "lead_id": lead.id, "assigned_employee_id": lead.assigned_employee_id,
    })
