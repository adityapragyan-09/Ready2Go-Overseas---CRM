"""
Ready2Go CRM — Applicant Management Routes

Router: /api/v1/applicants (prefix set in main.py)
Access Level: Authenticated Users (JWT required)

Endpoints:
    POST   /        — Create a new applicant
    GET    /        — List applicants with filters, search, pagination
    GET    /{id}    — Retrieve a single applicant by ID
    PUT    /{id}    — Update an existing applicant
    DELETE /{id}    — Delete an applicant
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    ApplicantFilterParams,
    PaginationParams,
    get_current_user,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantListResponse,
    ApplicantResponse,
    ApplicantUpdate,
)
from app.services.applicant_service import (
    create_applicant,
    delete_applicant,
    get_applicant_by_id,
    list_applicants,
    update_applicant,
)
from app.utils.response import success_response

router = APIRouter()


# ── POST / ──────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_applicant_route(
    body: ApplicantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new applicant record.
    Requires a valid JWT token.
    """
    applicant = create_applicant(db, body, created_by=current_user.id)
    applicant_data = ApplicantResponse.model_validate(applicant).model_dump(by_alias=True)

    return success_response(
        message="Applicant created successfully.",
        data=applicant_data,
    )


# ── GET / ───────────────────────────────────

@router.get("/")
def list_applicants_route(
    filters: ApplicantFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    assigned_to: int | None = Query(default=None, description="Filter by assigned employee ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List applicants with optional filters, search, and pagination.
    Requires a valid JWT token.

    Query Parameters:
        visa_type       — Filter by visa type (student, visit, tourist, business)
        status          — Filter by application status
        country         — Filter by country (partial match)
        assigned_to     — Filter by assigned employee ID
        search          — Search across name, email, phone
        page            — Page number (default: 1)
        page_size       — Items per page (default: 20, max: 100)
    """
    result = list_applicants(
        db,
        visa_type=filters.visa_type,
        applicant_status=filters.status,
        country=filters.country,
        assigned_to=assigned_to,
        search=filters.search,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    list_data = ApplicantListResponse(
        applicants=[
            ApplicantResponse.model_validate(a) for a in result["applicants"]
        ],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    ).model_dump(by_alias=True)

    return success_response(
        message="Applicants retrieved successfully.",
        data=list_data,
    )


# ── GET /{id} ───────────────────────────────

@router.get("/{id}")
def get_applicant_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single applicant by ID.
    Requires a valid JWT token.
    """
    applicant = get_applicant_by_id(db, id)
    applicant_data = ApplicantResponse.model_validate(applicant).model_dump(by_alias=True)

    return success_response(
        message="Applicant retrieved successfully.",
        data=applicant_data,
    )


# ── PUT /{id} ───────────────────────────────

@router.put("/{id}")
def update_applicant_route(
    id: int,
    body: ApplicantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing applicant record.
    Only fields included in the request body will be updated.
    Requires a valid JWT token.
    """
    applicant = update_applicant(db, id, body)
    applicant_data = ApplicantResponse.model_validate(applicant).model_dump(by_alias=True)

    return success_response(
        message="Applicant updated successfully.",
        data=applicant_data,
    )


# ── DELETE /{id} ────────────────────────────

@router.delete("/{id}")
def delete_applicant_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an applicant record.
    Requires a valid JWT token.
    """
    applicant = delete_applicant(db, id, deleted_by=current_user.id)

    return success_response(
        message=f"Applicant '{applicant.full_name}' deleted successfully.",
    )
