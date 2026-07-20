"""
Ready2Go CRM — Lead Activity Service

Tracks every action on lead inquiries for the timeline.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.lead_activity import LeadActivity

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    *,
    lead_id: int,
    action: str,
    description: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    created_by: int | None = None,
) -> LeadActivity:
    """Create a timeline entry for a lead inquiry action."""
    entry = LeadActivity(
        lead_id=lead_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
        created_by=created_by,
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
    except Exception:
        db.rollback()
        logger.exception("Failed to log activity for lead %s", lead_id)
    return entry


def get_activities(db: Session, lead_id: int, limit: int = 50) -> list[LeadActivity]:
    """Retrieve timeline entries for a lead inquiry."""
    return (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
        .limit(limit)
        .all()
    )
