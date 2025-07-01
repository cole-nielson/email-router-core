"""
Shared API Contract Types
🌐 Common TypeScript-compatible type definitions for API contracts.
This file bridges Python backend types and TypeScript frontend types.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

# =============================================================================
# API VERSIONING AND METADATA
# =============================================================================


class APIVersion(str, Enum):
    """API version identifiers."""

    V1 = "v1"
    V2 = "v2"


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class APIEndpoint(BaseModel):
    """API endpoint definition."""

    path: str = Field(..., description="Endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    version: APIVersion = Field(..., description="API version")
    description: str = Field(..., description="Endpoint description")
    requires_auth: bool = Field(..., description="Whether endpoint requires authentication")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")


# =============================================================================
# COMMON API RESPONSE PATTERNS
# =============================================================================


class APIResponse(BaseModel):
    """Base API response structure."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class PaginatedResponse(BaseModel):
    """Paginated response structure."""

    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class DataResponse(APIResponse):
    """API response with data payload."""

    data: Any = Field(..., description="Response data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ListResponse(APIResponse):
    """API response for list operations."""

    data: List[Any] = Field(..., description="List of items")
    pagination: Optional[PaginatedResponse] = Field(None, description="Pagination information")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    sort: Optional[Dict[str, Any]] = Field(None, description="Applied sorting")


# =============================================================================
# STATUS AND HEALTH CHECK TYPES
# =============================================================================


class ComponentStatus(str, Enum):
    """Component health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceStatus(str, Enum):
    """Overall service status."""

    OPERATIONAL = "operational"
    DEGRADED_PERFORMANCE = "degraded_performance"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    MAINTENANCE = "maintenance"


class HealthCheckResult(BaseModel):
    """Health check result for a component."""

    component: str = Field(..., description="Component name")
    status: ComponentStatus = Field(..., description="Component status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    message: Optional[str] = Field(None, description="Status message")
    last_check: datetime = Field(..., description="Last check timestamp")


# =============================================================================
# VALIDATION AND ERROR TYPES
# =============================================================================


class ValidationError(BaseModel):
    """Field validation error."""

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    value: Optional[Any] = Field(None, description="Invalid value")


class APIError(BaseModel):
    """Structured API error response."""

    error_type: str = Field(..., description="Error type")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    validation_errors: Optional[List[ValidationError]] = Field(
        None, description="Validation errors"
    )
    help_url: Optional[str] = Field(None, description="Documentation URL")


# =============================================================================
# FILTERING AND SORTING TYPES
# =============================================================================


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class SortCriteria(BaseModel):
    """Sort criteria."""

    field: str = Field(..., description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


class FilterOperator(str, Enum):
    """Filter operators."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"


class FilterCriteria(BaseModel):
    """Filter criteria."""

    field: str = Field(..., description="Field to filter")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")


class QueryParams(BaseModel):
    """Common query parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort: Optional[List[SortCriteria]] = Field(None, description="Sort criteria")
    filters: Optional[List[FilterCriteria]] = Field(None, description="Filter criteria")
    search: Optional[str] = Field(None, description="Search query")


# =============================================================================
# WEBHOOK AND EVENT TYPES
# =============================================================================


class WebhookEventType(str, Enum):
    """Webhook event types."""

    EMAIL_RECEIVED = "email.received"
    EMAIL_CLASSIFIED = "email.classified"
    EMAIL_ROUTED = "email.routed"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_FAILED = "email.failed"
    CLIENT_CREATED = "client.created"
    CLIENT_UPDATED = "client.updated"
    CLIENT_DELETED = "client.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"


class WebhookEvent(BaseModel):
    """Webhook event structure."""

    id: str = Field(..., description="Event ID")
    type: WebhookEventType = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    source: str = Field(..., description="Event source")
    data: Dict[str, Any] = Field(..., description="Event data")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    user_id: Optional[int] = Field(None, description="Associated user ID")


# =============================================================================
# CONFIGURATION TYPES
# =============================================================================


class ConfigScope(str, Enum):
    """Configuration scope levels."""

    GLOBAL = "global"
    CLIENT = "client"
    USER = "user"


class ConfigValueType(str, Enum):
    """Configuration value types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    OBJECT = "object"


class ConfigItem(BaseModel):
    """Configuration item definition."""

    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    type: ConfigValueType = Field(..., description="Value type")
    scope: ConfigScope = Field(..., description="Configuration scope")
    description: str = Field(..., description="Configuration description")
    is_required: bool = Field(..., description="Whether configuration is required")
    is_sensitive: bool = Field(default=False, description="Whether value is sensitive")
    default_value: Optional[Any] = Field(None, description="Default value")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


# =============================================================================
# MONITORING AND METRICS TYPES
# =============================================================================


class MetricType(str, Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricValue(BaseModel):
    """Metric value with metadata."""

    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    value: Union[int, float] = Field(..., description="Metric value")
    timestamp: datetime = Field(..., description="Metric timestamp")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")
    unit: Optional[str] = Field(None, description="Metric unit")


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[int, float] = Field(..., description="Data point value")


class TimeSeries(BaseModel):
    """Time series data."""

    name: str = Field(..., description="Series name")
    points: List[TimeSeriesPoint] = Field(..., description="Data points")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Series metadata")


# =============================================================================
# EXPORT TYPES FOR FRONTEND CONSUMPTION
# =============================================================================

# These are the primary types that should be used in frontend applications
__all__ = [
    # API Structure
    "APIVersion",
    "HTTPMethod",
    "APIEndpoint",
    # Response Patterns
    "APIResponse",
    "DataResponse",
    "ListResponse",
    "PaginatedResponse",
    # Status Types
    "ComponentStatus",
    "ServiceStatus",
    "HealthCheckResult",
    # Error Types
    "ValidationError",
    "APIError",
    # Query Types
    "SortOrder",
    "SortCriteria",
    "FilterOperator",
    "FilterCriteria",
    "QueryParams",
    # Event Types
    "WebhookEventType",
    "WebhookEvent",
    # Config Types
    "ConfigScope",
    "ConfigValueType",
    "ConfigItem",
    # Metric Types
    "MetricType",
    "MetricValue",
    "TimeSeriesPoint",
    "TimeSeries",
]
