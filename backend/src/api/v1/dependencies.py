"""
API Dependencies for v1 endpoints.
🔧 Reusable dependency functions for pagination, sorting, and filtering.
"""

from typing import Optional

from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    offset: int = Field(ge=0, description="Number of items to skip")
    limit: int = Field(ge=1, le=1000, description="Maximum number of items to return")
    sort_by: str = Field(description="Field to sort by")
    sort_order: str = Field(description="Sort order (asc or desc)")


class UserFilterParams(BaseModel):
    """Filter parameters for user list endpoints."""

    search: Optional[str] = Field(None, description="Search term for username, email, or full name")
    role: Optional[str] = Field(None, description="Filter by user role")
    status: Optional[str] = Field(None, description="Filter by user status")
    client_id: Optional[str] = Field(None, description="Filter by client ID")


def common_pagination_parameters(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of items to return (max 1000)"
    ),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query(
        "desc", regex="^(asc|desc)$", description="Sort order: 'asc' or 'desc'"
    ),
) -> PaginationParams:
    """
    Common pagination parameters dependency for list endpoints.

    Args:
        offset: Number of items to skip (default: 0)
        limit: Maximum number of items to return (default: 100, max: 1000)
        sort_by: Field to sort by (default: "created_at")
        sort_order: Sort order - "asc" or "desc" (default: "desc")

    Returns:
        PaginationParams object with validated parameters
    """
    return PaginationParams(offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order)


def user_filter_parameters(
    search: Optional[str] = Query(
        None,
        min_length=1,
        max_length=255,
        description="Search users by username, email, or full name",
    ),
    role: Optional[str] = Query(
        None, regex="^(super_admin|client_admin|client_user)$", description="Filter by user role"
    ),
    status: Optional[str] = Query(
        None, regex="^(active|inactive|locked)$", description="Filter by user status"
    ),
    client_id: Optional[str] = Query(
        None, min_length=1, max_length=255, description="Filter by client ID"
    ),
) -> UserFilterParams:
    """
    User-specific filter parameters dependency.

    Args:
        search: Search term for username, email, or full name
        role: Filter by user role (super_admin, client_admin, client_user)
        status: Filter by user status (active, inactive, locked)
        client_id: Filter by client ID

    Returns:
        UserFilterParams object with validated filter parameters
    """
    return UserFilterParams(search=search, role=role, status=status, client_id=client_id)


# Common sort field validation for different entities
VALID_USER_SORT_FIELDS = {
    "created_at",
    "updated_at",
    "username",
    "email",
    "full_name",
    "role",
    "status",
    "last_login_at",
    "client_id",
}


def validate_user_sort_field(sort_by: str) -> str:
    """
    Validate that the sort field is allowed for user endpoints.

    Args:
        sort_by: The field name to sort by

    Returns:
        The validated sort field name

    Raises:
        ValueError: If the sort field is not allowed
    """
    if sort_by not in VALID_USER_SORT_FIELDS:
        raise ValueError(
            f"Invalid sort field '{sort_by}'. Allowed fields: {', '.join(sorted(VALID_USER_SORT_FIELDS))}"
        )
    return sort_by


def user_pagination_parameters(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of items to return (max 1000)"
    ),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query(
        "desc", regex="^(asc|desc)$", description="Sort order: 'asc' or 'desc'"
    ),
) -> PaginationParams:
    """
    User-specific pagination parameters with validated sort fields.

    Args:
        offset: Number of items to skip (default: 0)
        limit: Maximum number of items to return (default: 100, max: 1000)
        sort_by: Field to sort by (default: "created_at")
        sort_order: Sort order - "asc" or "desc" (default: "desc")

    Returns:
        PaginationParams object with validated parameters

    Raises:
        ValueError: If sort_by field is not valid for users
    """
    # Validate sort field for users
    validated_sort_by = validate_user_sort_field(sort_by)

    return PaginationParams(
        offset=offset, limit=limit, sort_by=validated_sort_by, sort_order=sort_order
    )
