"""
Ready2Go CRM — Core Enums

Strongly typed enumerations used across the application.
"""

from enum import Enum


class CallerType(str, Enum):
    """Identifies the origin of an API request.

    Used by LeadIdentity to distinguish between different
    authentication paths without string literals.
    """
    WEBSITE = "website"
    CRM_USER = "crm_user"
