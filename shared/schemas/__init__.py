"""
Shared Schemas Package
=' Pydantic models for API contracts shared between frontend and backend.
"""

from .api import *

__all__ = [
    # Health & Status
    "HealthResponse",
    "APIInfo",
    "SystemMetrics",
    "APIStatusResponse",
    # Errors & Rate Limiting
    "ErrorResponse",
    "RateLimitInfo",
    # Client Management
    "ClientSummary",
    "ClientListResponse",
    "DomainResolutionResult",
    # Email Processing
    "EmailClassificationRequest",
    "EmailClassificationResponse",
    "RoutingResult",
    "WebhookResponse",
    # API Keys
    "APIKeyInfo",
]
