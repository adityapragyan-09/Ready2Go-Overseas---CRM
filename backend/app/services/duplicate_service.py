"""
Ready2Go CRM — Duplicate Detection Service

Enterprise duplicate detection for lead inquiries.
Supports configurable policies and request idempotency.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead_inquiry import LeadInquiry

logger = logging.getLogger(__name__)


class DuplicatePolicy(str, Enum):
    """Configurable duplicate handling policies."""
    REJECT = "REJECT"
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    MERGE = "MERGE"  # Placeholder for future implementation


class DuplicateCode(str, Enum):
    """Structured response codes for duplicate detection."""
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_ALREADY_EXISTS = "LEAD_ALREADY_EXISTS"
    REQUEST_ALREADY_PROCESSED = "REQUEST_ALREADY_PROCESSED"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"


@dataclass
class DuplicateResult:
    """Structured result from duplicate detection."""
    code: DuplicateCode
    is_duplicate: bool = False
    matched_lead: LeadInquiry | None = None
    reason: str | None = None
    policy: DuplicatePolicy = DuplicatePolicy.REJECT


def normalize_email(email: str | None) -> str | None:
    """Normalize email: lowercase + strip."""
    if not email:
        return None
    return email.strip().lower()


def normalize_phone(phone: str | None) -> str | None:
    """Normalize phone: strip spaces, hyphens, brackets, leading +."""
    if not phone:
        return None
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    cleaned = cleaned.lstrip("+")
    return cleaned


def normalize_name(name: str) -> str:
    """Normalize name: trim + collapse repeated spaces."""
    return re.sub(r"\s+", " ", name.strip())


def check_request_idempotency(db: Session, request_id: str) -> LeadInquiry | None:
    """Check if a request_id has already been processed."""
    if not request_id or not settings.ENABLE_IDEMPOTENCY:
        return None
    return db.query(LeadInquiry).filter(LeadInquiry.request_id == request_id).first()


def check_duplicate_email(db: Session, email: str | None) -> LeadInquiry | None:
    """Search for existing lead by normalized email."""
    normalized = normalize_email(email)
    if not normalized:
        return None
    return (
        db.query(LeadInquiry)
        .filter(LeadInquiry.email == normalized)
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )


def check_duplicate_phone(db: Session, phone: str | None) -> LeadInquiry | None:
    """Search for existing lead by normalized phone."""
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    return (
        db.query(LeadInquiry)
        .filter(LeadInquiry.phone == normalized)
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )


def check_duplicate_email_phone(db: Session, email: str | None, phone: str | None) -> LeadInquiry | None:
    """Search for existing lead by email AND phone combination."""
    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)
    if not norm_email and not norm_phone:
        return None
    conditions = []
    if norm_email:
        conditions.append(LeadInquiry.email == norm_email)
    if norm_phone:
        conditions.append(LeadInquiry.phone == norm_phone)
    if not conditions:
        return None
    return (
        db.query(LeadInquiry)
        .filter(or_(*conditions))
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )


def normalize_incoming(data: dict) -> dict:
    """Normalize incoming lead data for duplicate checking."""
    result = dict(data)
    if "email" in result:
        result["email"] = normalize_email(result["email"])
    if "phone" in result:
        result["phone"] = normalize_phone(result["phone"])
    if "full_name" in result:
        result["full_name"] = normalize_name(result["full_name"])
    return result


def detect_duplicate(
    db: Session,
    email: str | None,
    phone: str | None,
    request_id: str | None = None,
    policy: DuplicatePolicy | None = None,
) -> DuplicateResult:
    """
    Enterprise duplicate detection with configurable policy.

    Priority:
    1. Request idempotency (same request_id)
    2. Email match (normalized)
    3. Phone match (normalized)
    4. Email + Phone combination

    Returns structured DuplicateResult with code, matched lead, and reason.
    """
    if not settings.ENABLE_DUPLICATE_CHECK:
        return DuplicateResult(code=DuplicateCode.LEAD_CREATED, policy=policy or DuplicatePolicy.REJECT)

    policy = policy or DuplicatePolicy(settings.DUPLICATE_POLICY)

    # Priority 1: Request idempotency
    if request_id:
        existing = check_request_idempotency(db, request_id)
        if existing:
            logger.info("Idempotency match: request_id=%s lead=%s", request_id, existing.lead_number)
            return DuplicateResult(
                code=DuplicateCode.REQUEST_ALREADY_PROCESSED,
                is_duplicate=True,
                matched_lead=existing,
                reason=f"Request {request_id} already processed as {existing.lead_number}.",
                policy=policy,
            )

    # Priority 2: Email match
    if email:
        existing = check_duplicate_email(db, email)
        if existing:
            logger.info("Duplicate email: email=%s matched=%s", email, existing.lead_number)
            return DuplicateResult(
                code=DuplicateCode.LEAD_ALREADY_EXISTS,
                is_duplicate=True,
                matched_lead=existing,
                reason=f"Lead with email {email} already exists as {existing.lead_number}.",
                policy=policy,
            )

    # Priority 3: Phone match
    if phone:
        existing = check_duplicate_phone(db, phone)
        if existing:
            logger.info("Duplicate phone: phone=%s matched=%s", phone, existing.lead_number)
            return DuplicateResult(
                code=DuplicateCode.LEAD_ALREADY_EXISTS,
                is_duplicate=True,
                matched_lead=existing,
                reason=f"Lead with phone {phone} already exists as {existing.lead_number}.",
                policy=policy,
            )

    # Priority 4: Email + Phone combo
    if email or phone:
        existing = check_duplicate_email_phone(db, email, phone)
        if existing:
            logger.info("Duplicate email+phone: email=%s phone=%s matched=%s", email, phone, existing.lead_number)
            return DuplicateResult(
                code=DuplicateCode.LEAD_ALREADY_EXISTS,
                is_duplicate=True,
                matched_lead=existing,
                reason=f"Lead with same contact info already exists as {existing.lead_number}.",
                policy=policy,
            )

    return DuplicateResult(code=DuplicateCode.LEAD_CREATED, policy=policy)
