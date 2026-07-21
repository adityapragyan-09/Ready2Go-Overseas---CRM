"""
Ready2Go CRM — FastAPI Dependencies

Reusable dependency functions injected via Depends():
    get_current_user  — Decode JWT, fetch user from DB, return User object.
    require_admin     — Same as above, but raises 403 if role != 'admin'.

Usage:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)):
        ...

    @router.get("/admin-panel")
    def admin_panel(user: User = Depends(require_admin)):
        ...
"""

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import CallerType
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


class PaginationParams:
    """Standard pagination query parameters dependency."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(
            default=settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="Items per page",
        ),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


class ApplicantFilterParams:
    """Standard applicant filtering query parameters dependency."""

    def __init__(
        self,
        visa_type: str | None = Query(default=None, description="Filter by visa type"),
        status: str | None = Query(default=None, description="Filter by application status"),
        country: str | None = Query(default=None, description="Filter by applicant country"),
        search: str | None = Query(default=None, description="General search term (names, email, contact)"),
    ):
        self.visa_type = visa_type
        self.status = status
        self.country = country
        self.search = search



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer token and return the authenticated User.
    Raises 401 if the token is missing, expired, or invalid.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated.",
        )

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user has the 'admin' role.
    Raises 403 if the user is not an admin.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


from dataclasses import dataclass


@dataclass
class LeadIdentity:
    """Represents the identity of the caller for lead creation."""
    caller_type: CallerType
    user_id: int | None = None
    user: User | None = None


async def resolve_lead_identity(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> LeadIdentity:
    """
    Unified authentication for lead inquiry creation.

    Supports two auth methods:
    1. JWT Bearer token (CRM users)
    2. CRM API Key (Website integration)

    Returns a LeadIdentity with the caller context.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
        )

    token = authorization.replace("Bearer ", "")

    # Try JWT first (CRM user)
    if settings.CRM_API_KEY and token == settings.CRM_API_KEY:
        return LeadIdentity(caller_type=CallerType.WEBSITE)

    # JWT authentication
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated.",
        )

    return LeadIdentity(caller_type=CallerType.CRM_USER, user_id=user.id, user=user)
