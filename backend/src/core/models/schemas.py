"""
Pydantic models for API request/response schemas.
🔧 Enhanced schemas for SaaS API management and monitoring.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Enhanced health check response with detailed metrics."""

    status: str = Field(..., description="Overall system health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: Optional[int] = Field(None, description="System uptime in seconds")
    response_time_ms: Optional[int] = Field(None, description="Health check response time")
    components: Dict[str, str] = Field(..., description="Individual component health status")


class APIInfo(BaseModel):
    """Comprehensive API information and navigation."""

    name: str = Field(..., description="API service name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    status: str = Field(..., description="API operational status")
    timestamp: datetime = Field(..., description="Response timestamp")
    endpoints: Dict[str, str] = Field(..., description="Available API endpoints")
    features: List[str] = Field(..., description="Available features")
    rate_limits: Dict[str, str] = Field(..., description="Rate limiting information")


class APIKeyInfo(BaseModel):
    """API key information."""

    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    client_id: str = Field(..., description="Associated client ID")
    permissions: List[str] = Field(..., description="API key permissions")
    rate_limit: int = Field(..., description="Requests per minute limit")
    created_at: datetime = Field(..., description="Key creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(..., description="Whether key is active")


class ClientSummary(BaseModel):
    """Client configuration summary."""

    client_id: str = Field(..., description="Client identifier")
    name: str = Field(..., description="Client name")
    industry: str = Field(..., description="Client industry")
    status: str = Field(..., description="Client status")
    domains: List[str] = Field(..., description="Associated domains")
    primary_domain: str = Field(..., description="Primary domain")
    routing_categories: List[str] = Field(..., description="Available routing categories")
    total_domains: int = Field(..., description="Total number of domains")
    settings: Dict[str, bool] = Field(..., description="Client settings")
    created_at: Optional[datetime] = Field(None, description="Client creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")


class ClientListResponse(BaseModel):
    """Response for client listing."""

    total: int = Field(..., description="Total number of clients")
    clients: List[ClientSummary] = Field(..., description="Client summaries")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")


class SystemMetrics(BaseModel):
    """System performance metrics."""

    total_requests: int = Field(..., description="Total requests processed")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    avg_response_time_ms: float = Field(..., description="Average response time")
    requests_per_minute: float = Field(..., description="Current request rate")
    error_rate: float = Field(..., description="Error rate percentage")
    uptime_seconds: int = Field(..., description="System uptime")


class EmailClassificationRequest(BaseModel):
    """Email classification request."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    sender: Optional[str] = Field(None, description="Sender email address")
    recipient: Optional[str] = Field(None, description="Recipient email address")
    client_id: Optional[str] = Field(None, description="Client identifier")


class EmailClassificationResponse(BaseModel):
    """Email classification response with enhanced metadata."""

    category: str = Field(..., description="Classified email category")
    confidence: float = Field(..., description="Classification confidence score")
    reasoning: str = Field(..., description="AI reasoning for classification")
    suggested_actions: List[str] = Field(..., description="Recommended actions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    client_id: Optional[str] = Field(None, description="Client identifier")
    method: str = Field(..., description="Classification method used")
    timestamp: datetime = Field(..., description="Classification timestamp")


class RoutingResult(BaseModel):
    """Email routing result."""

    category: str = Field(..., description="Email category")
    destination: str = Field(..., description="Routing destination")
    confidence: float = Field(..., description="Routing confidence")
    method: str = Field(..., description="Routing method")
    special_handling: List[str] = Field(default=[], description="Special handling flags")
    escalated: bool = Field(default=False, description="Whether email was escalated")
    business_hours: bool = Field(..., description="Routed during business hours")


class WebhookResponse(BaseModel):
    """Enhanced webhook response."""

    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    client_id: Optional[str] = Field(None, description="Identified client")
    processing_id: Optional[str] = Field(None, description="Processing identifier")
    timestamp: datetime = Field(..., description="Processing timestamp")


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: bool = Field(True, description="Error flag")
    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="Error timestamp")
    path: str = Field(..., description="Request path")
    method: str = Field(..., description="HTTP method")
    request_id: Optional[str] = Field(None, description="Request identifier")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class RateLimitInfo(BaseModel):
    """Rate limiting information."""

    limit: int = Field(..., description="Requests per minute limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Rate limit reset time")
    retry_after: Optional[int] = Field(None, description="Seconds until retry")


class DomainResolutionResult(BaseModel):
    """Domain resolution result."""

    domain: str = Field(..., description="Input domain")
    client_id: Optional[str] = Field(None, description="Resolved client ID")
    confidence: float = Field(..., description="Resolution confidence")
    method: str = Field(..., description="Resolution method")
    domain_used: str = Field(..., description="Domain used for matching")
    is_successful: bool = Field(..., description="Whether resolution was successful")
    similar_clients: Optional[List[Dict[str, Any]]] = Field(
        None, description="Similar clients if no exact match"
    )


class APIStatusResponse(BaseModel):
    """Comprehensive API status response."""

    api_version: str = Field(..., description="API version")
    status: str = Field(..., description="API status")
    timestamp: datetime = Field(..., description="Status timestamp")
    uptime_seconds: int = Field(..., description="API uptime")
    total_clients: int = Field(..., description="Total configured clients")
    total_domains: int = Field(..., description="Total mapped domains")
    health_score: float = Field(..., description="Overall health score")
    features_enabled: List[str] = Field(..., description="Enabled features")
    metrics: SystemMetrics = Field(..., description="System metrics")
    component_status: Dict[str, str] = Field(..., description="Component health status")
