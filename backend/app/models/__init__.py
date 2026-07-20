"""
Ready2Go CRM — Model Registry

All models are imported here so that Alembic's autogenerate
can detect them via Base.metadata.

Import this module in alembic/env.py:
    from app.models import *  # noqa
"""

from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.applicant import Applicant  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.progress import ProgressHistory  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.lead_inquiry import LeadInquiry  # noqa: F401
