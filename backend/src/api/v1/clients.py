"""
API v1 Router for client management and system operations.
🔌 Comprehensive REST API endpoints for multi-tenant management.
"""

import logging
import time
from datetime import datetime
from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ...models.schemas import (
    APIStatusResponse,
    ClientListResponse,
    ClientSummary,
    DomainResolutionResult,
    SystemMetrics,
)
from ...security.authentication.middleware import DualAuthUser, require_dual_auth
from ...services.client_manager import ClientManager, get_client_manager
from ...services.monitoring import MetricsCollector
from ...utils.domain_resolver import normalize_domain

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize metrics collector for this module
metrics = MetricsCollector()


@router.get("/status", response_model=APIStatusResponse, tags=["System Status"])
async def get_api_status(client_manager: Annotated[ClientManager, Depends(get_client_manager)]):
    """
    Get comprehensive API status and system information.

    Provides detailed information about:
    - API version and operational status
    - System uptime and performance metrics
    - Client configuration statistics
    - Feature availability and health scores

    This endpoint is useful for monitoring dashboards and health checks.
    """
    try:
        # Get system metrics
        system_metrics = metrics.get_system_metrics()

        # Get client information
        available_clients = client_manager.get_available_clients()

        # Calculate total domains
        total_domains = 0
        valid_clients = 0

        for client_id in available_clients:
            try:
                domains = client_manager.get_client_domains(client_id)
                total_domains += len(domains)

                if client_manager.validate_client_setup(client_id):
                    valid_clients += 1
            except Exception as e:
                logger.warning(f"Failed to get info for client {client_id}: {e}")

        # Calculate health score
        health_score = (valid_clients / len(available_clients) * 100) if available_clients else 100

        # Get enabled features
        features_enabled = [
            "multi_tenant_client_management",
            "ai_powered_classification",
            "smart_routing_engine",
            "personalized_responses",
            "advanced_domain_resolution",
            "rate_limiting",
            "dual_authentication",
            "comprehensive_monitoring",
            "webhook_processing",
        ]

        # Component status
        component_status = {
            "api_server": "healthy",
            "client_manager": "healthy" if valid_clients == len(available_clients) else "degraded",
            "domain_resolver": "healthy",
            "rate_limiter": "healthy",
            "metrics_collector": "healthy",
            "webhook_processor": "healthy",
        }

        # Create system metrics object
        metrics_obj = SystemMetrics(
            total_requests=system_metrics["total_requests"],
            successful_requests=system_metrics["successful_requests"],
            failed_requests=system_metrics["failed_requests"],
            avg_response_time_ms=system_metrics["avg_response_time_ms"],
            requests_per_minute=system_metrics.get("requests_per_minute", 0),
            error_rate=system_metrics["error_rate_percent"],
            uptime_seconds=system_metrics["uptime_seconds"],
        )

        return APIStatusResponse(
            api_version="2.0.0",
            status="operational",
            timestamp=datetime.utcnow(),
            uptime_seconds=system_metrics["uptime_seconds"],
            total_clients=len(available_clients),
            total_domains=total_domains,
            health_score=health_score,
            features_enabled=features_enabled,
            metrics=metrics_obj,
            component_status=component_status,
        )

    except Exception as e:
        logger.error(f"Failed to get API status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API status",
        )


@router.get("/clients", response_model=ClientListResponse, tags=["Client Management"])
async def list_clients(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of clients to return"),
    offset: int = Query(default=0, ge=0, description="Number of clients to skip"),
    status_filter: Optional[str] = Query(default=None, description="Filter by client status"),
    industry_filter: Optional[str] = Query(default=None, description="Filter by industry"),
):
    """
    List all configured clients with pagination and filtering.

    Provides comprehensive client information including:
    - Basic client details (name, industry, status)
    - Domain configuration and mapping statistics
    - Routing categories and settings
    - Creation and update timestamps

    Supports filtering by status and industry for easier management.
    """
    try:
        available_clients = client_manager.get_available_clients()

        # Apply filters if specified
        filtered_clients = available_clients

        if status_filter:
            filtered_clients = [
                client_id
                for client_id in filtered_clients
                if _get_client_status(client_manager, client_id) == status_filter
            ]

        if industry_filter:
            filtered_clients = [
                client_id
                for client_id in filtered_clients
                if _get_client_industry(client_manager, client_id) == industry_filter
            ]

        # Apply pagination
        total_clients = len(filtered_clients)
        paginated_clients = filtered_clients[offset : offset + limit]

        # Get detailed client information
        client_summaries = []
        for client_id in paginated_clients:
            try:
                summary = client_manager.get_client_summary(client_id)

                client_summary = ClientSummary(
                    client_id=summary["client_id"],
                    name=summary["name"],
                    industry=summary["industry"],
                    status=summary["status"],
                    domains=summary["domains"],
                    primary_domain=summary["primary_domain"],
                    routing_categories=summary["routing_categories"],
                    total_domains=summary["total_domains"],
                    settings=summary["settings"],
                    created_at=None,  # Would come from database in production
                    updated_at=None,  # Would come from database in production
                )

                client_summaries.append(client_summary)

            except Exception as e:
                logger.warning(f"Failed to get summary for client {client_id}: {e}")
                # Create minimal summary for failed clients
                client_summaries.append(
                    ClientSummary(
                        client_id=client_id,
                        name="Error loading client",
                        industry="unknown",
                        status="error",
                        domains=[],
                        primary_domain="unknown",
                        routing_categories=[],
                        total_domains=0,
                        settings={},
                    )
                )

        # Pagination info
        pagination = {
            "total": total_clients,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_clients,
        }

        return ClientListResponse(
            total=total_clients, clients=client_summaries, pagination=pagination
        )

    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve client list",
        )


@router.get("/clients/{client_id}", response_model=ClientSummary, tags=["Client Management"])
async def get_client(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get detailed information about a specific client.

    Returns comprehensive client configuration including:
    - Complete domain mapping and variants
    - Routing rules and destination configuration
    - Branding and customization settings
    - Performance and usage statistics
    """
    try:
        # Check if client exists
        available_clients = client_manager.get_available_clients()
        if client_id not in available_clients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Client '{client_id}' not found"
            )

        # Check permissions (client-specific keys can only access their own data)
        if (
            current_user
            and current_user["client_id"] != "*"
            and current_user["client_id"] != client_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this client",
            )

        # Get client summary
        summary = client_manager.get_client_summary(client_id)

        return ClientSummary(
            client_id=summary["client_id"],
            name=summary["name"],
            industry=summary["industry"],
            status=summary["status"],
            domains=summary["domains"],
            primary_domain=summary["primary_domain"],
            routing_categories=summary["routing_categories"],
            total_domains=summary["total_domains"],
            settings=summary["settings"],
            created_at=None,  # Would come from database in production
            updated_at=None,  # Would come from database in production
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve client information",
        )


@router.post("/clients/{client_id}/validate", tags=["Client Management"])
async def validate_client(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Validate client configuration and setup.

    Performs comprehensive validation including:
    - Configuration file integrity
    - Domain mapping correctness
    - Routing rule completeness
    - Required field validation

    Returns detailed validation results and any issues found.
    """
    try:
        # Check if client exists
        available_clients = client_manager.get_available_clients()
        if client_id not in available_clients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Client '{client_id}' not found"
            )

        # Perform validation
        is_valid = client_manager.validate_client_setup(client_id)

        # Get validation details
        validation_results = {
            "client_id": client_id,
            "is_valid": is_valid,
            "timestamp": datetime.utcnow().isoformat(),
            "checks_performed": [],
            "issues_found": [],
            "warnings": [],
        }

        try:
            # Test client config loading
            client_manager.get_client_config(client_id)
            validation_results["checks_performed"].append("client_config_load")

            # Test routing rules loading
            routing_rules = client_manager.get_routing_rules(client_id)
            validation_results["checks_performed"].append("routing_rules_load")

            # Check domain configuration
            domains = client_manager.get_client_domains(client_id)
            if domains:
                validation_results["checks_performed"].append("domain_mapping")
            else:
                validation_results["issues_found"].append("No domains configured")

            # Check required routing categories
            required_categories = ["support", "billing", "sales", "general"]
            missing_categories = [
                cat for cat in required_categories if cat not in routing_rules.routing
            ]

            if missing_categories:
                validation_results["warnings"].extend(
                    [f"Missing routing rule for {cat}" for cat in missing_categories]
                )

            validation_results["summary"] = {
                "total_checks": len(validation_results["checks_performed"]),
                "issues_count": len(validation_results["issues_found"]),
                "warnings_count": len(validation_results["warnings"]),
                "domains_configured": len(domains),
                "routing_categories": len(routing_rules.routing),
            }

        except Exception as e:
            validation_results["issues_found"].append(f"Validation error: {str(e)}")

        return validation_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform client validation",
        )


@router.post("/domain/resolve", response_model=DomainResolutionResult, tags=["Domain Resolution"])
async def resolve_domain(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    domain: str = Query(..., description="Domain to resolve"),
):
    """
    Resolve domain to client using advanced matching strategies.

    Uses multiple resolution strategies:
    - Exact domain matching
    - Subdomain hierarchy resolution
    - Fuzzy matching with confidence scoring
    - Similarity-based suggestions

    Returns detailed resolution results including confidence scores and methods used.
    """
    try:
        # Normalize domain
        normalized_domain = normalize_domain(domain)
        if not normalized_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid domain format"
            )

        # Perform domain resolution
        result = client_manager.identify_client_by_domain(normalized_domain)

        # Get similar clients if no exact match
        similar_clients = None
        if not result.is_successful:
            similar = client_manager.find_similar_clients(normalized_domain, limit=5)
            if similar:
                similar_clients = [
                    {"client_id": client_id, "similarity_score": score}
                    for client_id, score in similar
                ]

        return DomainResolutionResult(
            domain=domain,
            client_id=result.client_id,
            confidence=result.confidence,
            method=result.method,
            domain_used=result.domain_used,
            is_successful=result.is_successful,
            similar_clients=similar_clients,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve domain {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve domain"
        )


@router.get("/metrics/summary", tags=["System Metrics"])
async def get_metrics_summary(current_user: Annotated[DualAuthUser, Depends(require_dual_auth)]):
    """
    Get comprehensive system metrics summary.

    Provides detailed metrics including:
    - Request rates and response times
    - Error rates and status code distribution
    - Client usage statistics
    - Time series data for trending

    Requires admin permissions for full access.
    """
    try:
        # Check admin permissions for full metrics
        is_admin = current_user and "admin" in current_user.get("permissions", [])

        if not is_admin:
            # Return limited metrics for non-admin users
            return {
                "message": "Limited metrics access",
                "system_status": "operational",
                "total_requests": metrics.total_requests,
                "uptime_seconds": int(time.time() - metrics.start_time),
            }

        # Return full metrics for admin users
        return metrics.get_summary()

    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics"
        )


@router.post("/clients/{client_id}/refresh", tags=["Client Management"])
async def refresh_client_config(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Refresh client configuration from disk.

    Forces a reload of client configuration files and rebuilds
    internal caches. Useful after manual configuration changes.

    Requires write permissions.
    """
    try:
        # Check permissions
        if current_user and "write" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Write permissions required"
            )

        # Check if client exists
        available_clients = client_manager.get_available_clients()
        if client_id not in available_clients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Client '{client_id}' not found"
            )

        # Refresh client configuration
        client_manager.refresh_client(client_id)

        return {
            "message": f"Client '{client_id}' configuration refreshed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh client configuration",
        )


# Helper functions


def _get_client_status(client_manager: ClientManager, client_id: str) -> str:
    """Get client status."""
    try:
        config = client_manager.get_client_config(client_id)
        return config.client.status
    except Exception:
        return "error"


def _get_client_industry(client_manager: ClientManager, client_id: str) -> str:
    """Get client industry."""
    try:
        config = client_manager.get_client_config(client_id)
        return config.client.industry
    except Exception:
        return "unknown"
