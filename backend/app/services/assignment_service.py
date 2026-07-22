"""
Ready2Go CRM — Assignment Request Service

Business logic for lead assignment requests, approval workflow, and direct assignment.
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment_request import AssignmentRequest
from app.models.lead_inquiry import LeadInquiry
from app.models.user import User

logger = logging.getLogger(__name__)


def create_request(db: Session, lead_id: int, employee_id: int, remarks: str | None = None) -> AssignmentRequest:
    """Create an assignment request from an employee for an unassigned lead."""
    lead = db.query(LeadInquiry).filter(LeadInquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    if lead.assigned_employee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead already has an assigned employee.")

    emp = db.query(User).filter(User.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    existing = db.query(AssignmentRequest).filter(
        AssignmentRequest.lead_id == lead_id,
        AssignmentRequest.employee_id == employee_id,
        AssignmentRequest.status == "PENDING",
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a pending request for this lead.")

    req = AssignmentRequest(lead_id=lead_id, employee_id=employee_id, remarks=remarks)
    db.add(req)
    try:
        db.commit()
        db.refresh(req)
    except Exception:
        db.rollback()
        logger.exception("Failed to create assignment request.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create request.")
    logger.info("Assignment request created: lead=%s employee=%s", lead_id, employee_id)
    return req


def list_requests(
    db: Session,
    status_filter: str | None = None,
    employee_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[AssignmentRequest]]:
    """List assignment requests with filters and pagination.

    Uses joinedload to prevent N+1 queries when serializers access
    employee and lead relationships.
    """
    query = db.query(AssignmentRequest).options(
        joinedload(AssignmentRequest.employee),
        joinedload(AssignmentRequest.lead),
    )
    if status_filter:
        query = query.filter(AssignmentRequest.status == status_filter.upper())
    if employee_id:
        query = query.filter(AssignmentRequest.employee_id == employee_id)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(AssignmentRequest.requested_at.desc()).offset(offset).limit(page_size).all()
    return total, items


def get_request(db: Session, request_id: int) -> AssignmentRequest:
    """Fetch a single assignment request."""
    req = db.query(AssignmentRequest).options(
        joinedload(AssignmentRequest.employee),
        joinedload(AssignmentRequest.lead),
    ).filter(AssignmentRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment request not found.")
    return req


def approve_request(db: Session, request_id: int, reviewer_id: int, remarks: str | None = None) -> AssignmentRequest:
    """Approve an assignment request and assign the lead to the employee."""
    req = get_request(db, request_id)
    if req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending.")

    req.status = "APPROVED"
    req.reviewed_by = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)
    if remarks:
        req.remarks = remarks

    lead = db.query(LeadInquiry).filter(LeadInquiry.id == req.lead_id).first()
    if lead:
        lead.assigned_employee_id = req.employee_id

    try:
        db.commit()
        db.refresh(req)
    except Exception:
        db.rollback()
        logger.exception("Failed to approve request %s.", request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve request.")
    logger.info("Assignment approved: request=%s lead=%s employee=%s", request_id, req.lead_id, req.employee_id)
    return req


def reject_request(db: Session, request_id: int, reviewer_id: int, remarks: str | None = None) -> AssignmentRequest:
    """Reject an assignment request."""
    req = get_request(db, request_id)
    if req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending.")

    req.status = "REJECTED"
    req.reviewed_by = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)
    if remarks:
        req.remarks = remarks

    try:
        db.commit()
        db.refresh(req)
    except Exception:
        db.rollback()
        logger.exception("Failed to reject request %s.", request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject request.")
    logger.info("Assignment rejected: request=%s lead=%s", request_id, req.lead_id)
    return req


def cancel_request(db: Session, request_id: int, user_id: int) -> AssignmentRequest:
    """Cancel a pending request (admin or the requesting employee)."""
    req = get_request(db, request_id)
    if req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled.")
    if req.employee_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another employee's request.")

    req.status = "CANCELLED"
    try:
        db.commit()
        db.refresh(req)
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel request %s.", request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel request.")
    return req


def direct_assign(db: Session, lead_id: int, employee_id: int | None, admin_id: int) -> LeadInquiry:
    """Admin directly assigns or unassigns a lead."""
    lead = db.query(LeadInquiry).filter(LeadInquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    old_employee_id = lead.assigned_employee_id
    lead.assigned_employee_id = employee_id

    try:
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        logger.exception("Failed to assign lead %s.", lead_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign lead.")
    logger.info("Lead %s assigned: employee=%s (was %s) by admin=%s", lead_id, employee_id, old_employee_id, admin_id)
    return lead
