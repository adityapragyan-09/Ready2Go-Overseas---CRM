"""
Ready2Go CRM — Enterprise Duplicate Detection Service

Architecture: Normalizer → Detector → Policy Engine → Result Builder
Supports configurable policies, metrics, structured metadata, and idempotency.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead_inquiry import LeadInquiry

logger = logging.getLogger(__name__)


# ── Enums ───────────────────────────────────

class DuplicatePolicy(str, Enum):
    REJECT = "REJECT"
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    MERGE = "MERGE"


class DuplicateCode(str, Enum):
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_ALREADY_EXISTS = "LEAD_ALREADY_EXISTS"
    REQUEST_ALREADY_PROCESSED = "REQUEST_ALREADY_PROCESSED"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"


class DuplicateReason(str, Enum):
    EMAIL_MATCH = "EMAIL_MATCH"
    PHONE_MATCH = "PHONE_MATCH"
    EMAIL_PHONE_MATCH = "EMAIL_PHONE_MATCH"
    REQUEST_ID_MATCH = "REQUEST_ID_MATCH"


# ── Metrics ─────────────────────────────────

@dataclass
class DuplicateMetrics:
    total_checks: int = 0
    email_matches: int = 0
    phone_matches: int = 0
    idempotent_replays: int = 0
    flagged_duplicates: int = 0
    allowed_duplicates: int = 0
    rejected_duplicates: int = 0

    def increment_email_match(self) -> None:
        self.email_matches += 1
        self.total_checks += 1

    def increment_phone_match(self) -> None:
        self.phone_matches += 1
        self.total_checks += 1

    def increment_idempotent(self) -> None:
        self.idempotent_replays += 1
        self.total_checks += 1

    def increment_flagged(self) -> None:
        self.flagged_duplicates += 1
        self.total_checks += 1

    def increment_allowed(self) -> None:
        self.allowed_duplicates += 1
        self.total_checks += 1

    def increment_rejected(self) -> None:
        self.rejected_duplicates += 1
        self.total_checks += 1

    def to_dict(self) -> dict:
        return {
            "total_checks": self.total_checks,
            "email_matches": self.email_matches,
            "phone_matches": self.phone_matches,
            "idempotent_replays": self.idempotent_replays,
            "flagged_duplicates": self.flagged_duplicates,
            "allowed_duplicates": self.allowed_duplicates,
            "rejected_duplicates": self.rejected_duplicates,
        }


# Singleton metrics instance (reset on app restart, suitable for single-worker deployments)
_metrics = DuplicateMetrics()


def get_metrics() -> DuplicateMetrics:
    """Return the global duplicate detection metrics instance."""
    return _metrics


# ── Structured Result ───────────────────────

@dataclass
class DuplicateResult:
    code: DuplicateCode
    is_duplicate: bool = False
    matched_lead: Optional[LeadInquiry] = None
    reason: DuplicateReason | None = None
    reason_detail: str | None = None
    matched_fields: list[str] = field(default_factory=list)
    matched_lead_id: int | None = None
    matched_request_id: str | None = None
    policy: DuplicatePolicy = DuplicatePolicy.REJECT
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.matched_lead:
            self.matched_lead_id = self.matched_lead.id
            self.matched_request_id = self.matched_lead.request_id

    def to_log_dict(self) -> dict:
        return {
            "code": self.code.value,
            "is_duplicate": self.is_duplicate,
            "reason": self.reason.value if self.reason else None,
            "reason_detail": self.reason_detail,
            "matched_fields": self.matched_fields,
            "matched_lead_id": self.matched_lead_id,
            "matched_request_id": self.matched_request_id,
            "policy": self.policy.value,
            "timestamp": self.timestamp,
        }


# ── Normalizer ──────────────────────────────

def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    cleaned = cleaned.lstrip("+")
    return cleaned


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def normalize_incoming(data: dict) -> dict:
    result = dict(data)
    if "email" in result:
        result["email"] = normalize_email(result["email"])
    if "phone" in result:
        result["phone"] = normalize_phone(result["phone"])
    if "full_name" in result:
        result["full_name"] = normalize_name(result["full_name"])
    return result


# ── Detector ────────────────────────────────

def _check_idempotency(db: Session, request_id: str | None) -> tuple[Optional[LeadInquiry], DuplicateReason | None]:
    if not request_id or not settings.ENABLE_IDEMPOTENCY:
        return None, None
    lead = db.query(LeadInquiry).filter(LeadInquiry.request_id == request_id).first()
    if lead:
        return lead, DuplicateReason.REQUEST_ID_MATCH
    return None, None


def _check_email(db: Session, email: str | None) -> tuple[Optional[LeadInquiry], DuplicateReason | None]:
    if not email:
        return None, None
    normalized = normalize_email(email)
    if not normalized:
        return None, None
    lead = (
        db.query(LeadInquiry)
        .filter(LeadInquiry.normalized_email == normalized)
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )
    if lead:
        return lead, DuplicateReason.EMAIL_MATCH
    return None, None


def _check_phone(db: Session, phone: str | None) -> tuple[Optional[LeadInquiry], DuplicateReason | None]:
    if not phone:
        return None, None
    normalized = normalize_phone(phone)
    if not normalized:
        return None, None
    lead = (
        db.query(LeadInquiry)
        .filter(LeadInquiry.normalized_phone == normalized)
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )
    if lead:
        return lead, DuplicateReason.PHONE_MATCH
    return None, None


def _check_email_phone(db: Session, email: str | None, phone: str | None) -> tuple[Optional[LeadInquiry], DuplicateReason | None]:
    norm_email = normalize_email(email) if email else None
    norm_phone = normalize_phone(phone) if phone else None
    if not norm_email and not norm_phone:
        return None, None
    conditions = []
    if norm_email:
        conditions.append(LeadInquiry.normalized_email == norm_email)
    if norm_phone:
        conditions.append(LeadInquiry.normalized_phone == norm_phone)
    if not conditions:
        return None, None
    lead = (
        db.query(LeadInquiry)
        .filter(or_(*conditions))
        .order_by(LeadInquiry.created_at.desc())
        .first()
    )
    if lead:
        return lead, DuplicateReason.EMAIL_PHONE_MATCH
    return None, None


# ── Policy Engine ───────────────────────────

def _resolve_policy() -> DuplicatePolicy:
    return DuplicatePolicy(settings.DUPLICATE_POLICY)


def _evaluate(result: DuplicateResult, metrics: DuplicateMetrics) -> DuplicateResult:
    """Apply policy decision to the duplicate result."""
    if not result.is_duplicate:
        return result

    if result.policy == DuplicatePolicy.REJECT:
        metrics.increment_rejected()
    elif result.policy == DuplicatePolicy.FLAG:
        metrics.increment_flagged()
    elif result.policy == DuplicatePolicy.ALLOW:
        metrics.increment_allowed()
    elif result.policy == DuplicatePolicy.MERGE:
        metrics.increment_flagged()

    return result


# ── Public API ──────────────────────────────

def detect_duplicate(
    db: Session,
    email: str | None,
    phone: str | None,
    request_id: str | None = None,
    policy: DuplicatePolicy | None = None,
) -> DuplicateResult:
    """
    Enterprise duplicate detection with policy evaluation.

    Priority: request_id → email → phone → email+phone. Returns DuplicateResult.
    """
    if not settings.ENABLE_DUPLICATE_CHECK:
        return DuplicateResult(code=DuplicateCode.LEAD_CREATED, policy=policy or _resolve_policy())

    policy = policy or _resolve_policy()

    # 1 — Idempotency
    lead, reason = _check_idempotency(db, request_id)
    if lead and reason:
        _metrics.increment_idempotent()
        return _evaluate(DuplicateResult(
            code=DuplicateCode.REQUEST_ALREADY_PROCESSED,
            is_duplicate=True,
            matched_lead=lead,
            reason=reason,
            reason_detail=f"Request {request_id} already processed as {lead.lead_number}.",
            matched_fields=["request_id"],
            policy=policy,
        ), _metrics)

    # 2 — Email
    lead, reason = _check_email(db, email)
    if lead and reason:
        _metrics.increment_email_match()
        return _evaluate(DuplicateResult(
            code=DuplicateCode.LEAD_ALREADY_EXISTS,
            is_duplicate=True,
            matched_lead=lead,
            reason=reason,
            reason_detail=f"Lead with email {email} already exists as {lead.lead_number}.",
            matched_fields=["email"],
            policy=policy,
        ), _metrics)

    # 3 — Phone
    lead, reason = _check_phone(db, phone)
    if lead and reason:
        _metrics.increment_phone_match()
        return _evaluate(DuplicateResult(
            code=DuplicateCode.LEAD_ALREADY_EXISTS,
            is_duplicate=True,
            matched_lead=lead,
            reason=reason,
            reason_detail=f"Lead with phone {phone} already exists as {lead.lead_number}.",
            matched_fields=["phone"],
            policy=policy,
        ), _metrics)

    # 4 — Email + Phone
    lead, reason = _check_email_phone(db, email, phone)
    if lead and reason:
        _metrics.increment_email_match()
        return _evaluate(DuplicateResult(
            code=DuplicateCode.LEAD_ALREADY_EXISTS,
            is_duplicate=True,
            matched_lead=lead,
            reason=reason,
            reason_detail=f"Lead with same contact info already exists as {lead.lead_number}.",
            matched_fields=["email", "phone"],
            policy=policy,
        ), _metrics)

    return DuplicateResult(code=DuplicateCode.LEAD_CREATED, policy=policy)
