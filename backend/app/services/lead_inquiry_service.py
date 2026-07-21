"""
Ready2Go CRM — Lead Inquiry Service

Business logic for lead inquiry management.
"""

import logging
import math

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.constants.lead_inquiry import NEW as STATUS_NEW
from app.models.lead_inquiry import LeadInquiry
from app.models.user import User
from app.services.duplicate_service import normalize_email, normalize_phone

logger = logging.getLogger(__name__)

_CODE_PREFIX = "LEAD"


def _generate_lead_number(db: Session) -> str:
    """Generate sequential unique lead number (LEAD-000001 format)."""
    max_id = db.query(func.max(LeadInquiry.id)).scalar()
    next_num = (max_id or 0) + 1
    return f"{_CODE_PREFIX}-{next_num:06d}"


def check_duplicate(
    db: Session,
    email: str | None = None,
    phone: str | None = None,
    full_name: str | None = None,
) -> list[LeadInquiry]:
    """
    Detect potential duplicate leads by email or phone.
    Returns list of existing leads that match.
    """
    if not email and not phone:
        return []
    conditions = []
    if email:
        conditions.append(LeadInquiry.email == email.lower())
    if phone:
        conditions.append(LeadInquiry.phone == phone)
    if not conditions:
        return []
    return db.query(LeadInquiry).filter(or_(*conditions)).order_by(LeadInquiry.created_at.desc()).limit(5).all()


def create_lead(
    db: Session,
    *,
    full_name: str,
    email: str | None = None,
    phone: str | None = None,
    visa_type: str = "student",
    preferred_country: str | None = None,
    message: str | None = None,
    source: str = "WEBSITE",
    request_id: str | None = None,
    assigned_employee_id: int | None = None,
    created_by: int | None = None,
) -> LeadInquiry:
    """
    Create a new lead inquiry.
    Auto-generates lead_number and UUID.
    Accepts optional request_id from website integration.
    """
    # Check duplicates
    duplicates = check_duplicate(db, email=email, phone=phone)
    if duplicates:
        logger.info("Duplicate lead detected: email=%s phone=%s matches=%d request_id=%s", email, phone, len(duplicates), request_id)

    lead_number = _generate_lead_number(db)

    lead = LeadInquiry(
        lead_number=lead_number,
        request_id=request_id,
        full_name=full_name,
        email=email.lower() if email else None,
        phone=phone,
        normalized_email=normalize_email(email),
        normalized_phone=normalize_phone(phone),
        visa_type=visa_type,
        preferred_country=preferred_country,
        message=message,
        source=source.upper(),
        status=STATUS_NEW,
        assigned_employee_id=assigned_employee_id,
        created_by=created_by,
    )

    try:
        db.add(lead)
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        logger.exception("Failed to create lead inquiry.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead inquiry.",
        )

    # Log creation activity
    from app.services.lead_activity_service import log_activity
    log_activity(
        db, lead_id=lead.id, action="CREATED",
        description=f"Lead created from {source}",
        created_by=created_by,
    )

    logger.info("Lead inquiry created: %s (%s)", lead.lead_number, lead.full_name)
    return lead


def get_leads(
    db: Session,
    *,
    search: str | None = None,
    status_filter: str | None = None,
    source_filter: str | None = None,
    employee_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[int, list[LeadInquiry]]:
    """Retrieve filtered, paginated, sorted list of leads."""
    query = db.query(LeadInquiry)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                LeadInquiry.lead_number.ilike(search_term),
                LeadInquiry.full_name.ilike(search_term),
                LeadInquiry.email.ilike(search_term),
                LeadInquiry.phone.ilike(search_term),
            )
        )

    if status_filter:
        query = query.filter(LeadInquiry.status == status_filter.upper())

    if source_filter:
        query = query.filter(LeadInquiry.source == source_filter.upper())

    if employee_id:
        query = query.filter(LeadInquiry.assigned_employee_id == employee_id)

    total = query.count()

    # Sorting
    sort_column = getattr(LeadInquiry, sort_by, LeadInquiry.created_at)
    order_fn = sort_column.desc if sort_order == "desc" else sort_column.asc
    query = query.order_by(order_fn())

    # Pagination
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return total, items, total_pages


def get_lead(db: Session, lead_id: int) -> LeadInquiry:
    """Fetch a single lead by ID or raise 404."""
    lead = db.query(LeadInquiry).filter(LeadInquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead inquiry not found.",
        )
    return lead


def update_lead(db: Session, lead_id: int, update_data: dict, updated_by: int | None = None) -> LeadInquiry:
    """Partially update a lead inquiry."""
    lead = get_lead(db, lead_id)

    for field, value in update_data.items():
        if value is not None:
            setattr(lead, field, value)

    lead.updated_by = updated_by

    try:
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        logger.exception("Failed to update lead inquiry %s.", lead_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead inquiry.",
        )

    return lead


def delete_lead(db: Session, lead_id: int) -> dict:
    """Permanently delete a lead inquiry."""
    lead = get_lead(db, lead_id)
    name = lead.full_name
    lead_number = lead.lead_number

    try:
        db.delete(lead)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete lead inquiry %s.", lead_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lead inquiry.",
        )

    logger.info("Lead inquiry deleted: %s (%s)", lead_number, name)
    return {"full_name": name, "lead_number": lead_number}


def change_lead_status(db: Session, lead_id: int, new_status: str, changed_by: int | None = None) -> LeadInquiry:
    """Update the status of a lead inquiry."""
    from app.services.lead_activity_service import log_activity

    lead = get_lead(db, lead_id)
    old_status = lead.status
    lead.status = new_status.upper()

    try:
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        logger.exception("Failed to update lead status %s.", lead_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead status.",
        )

    log_activity(
        db, lead_id=lead_id, action="STATUS_CHANGED",
        description=f"Status changed from {old_status} to {new_status.upper()}",
        old_value=old_status, new_value=new_status.upper(),
        created_by=changed_by,
    )

    return lead


def assign_employee(db: Session, lead_id: int, employee_id: int, assigned_by: int | None = None) -> LeadInquiry:
    """Assign a lead to an employee."""
    from app.services.lead_activity_service import log_activity

    emp = db.query(User).filter(User.id == employee_id).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        )

    lead = get_lead(db, lead_id)
    lead.assigned_employee_id = employee_id

    try:
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        logger.exception("Failed to assign lead %s.", lead_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign lead.",
        )

    log_activity(
        db, lead_id=lead_id, action="ASSIGNED",
        description=f"Assigned to {emp.name}",
        new_value=emp.name,
        created_by=assigned_by,
    )

    return lead


def convert_to_applicant(db: Session, lead_id: int) -> dict:
    """
    Convert a lead to an applicant. (Stub — returns 501)
    Full implementation in Phase 2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Lead-to-applicant conversion will be implemented in Phase 2.",
    )
