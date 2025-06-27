"""
Dashboard API Router - Endpoints for client dashboard data and real-time updates.
"""

import logging
from datetime import datetime
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from application.middleware.auth import DualAuthUser, require_dual_auth
from core.dashboard.service import DashboardService, get_dashboard_service
from core.models.dashboard import (
    ActivityFeedResponse,
    AlertsResponse,
    AutomationStatus,
    ClientInfo,
    DashboardMetrics,
    DashboardResponse,
    IntegrationHealth,
    MetricsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Analytics router for trend analysis endpoints
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get("/trends", tags=["Analytics"])
async def get_dashboard_trends(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Query(..., description="Client identifier"),
    timeframe: str = Query(default="24h", description="Time range (1h, 6h, 12h, 24h, 7d, 30d)"),
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard trend analysis.

    Returns volume metrics, performance metrics, quality metrics, escalation metrics,
    and trends compared to the previous period. Provides data-driven insights for
    email routing performance and operational metrics.

    **Features:**
    - Volume analysis by category and time
    - Performance metrics with processing times and success rates
    - AI confidence distribution and quality metrics
    - Escalation patterns and analysis
    - Period-over-period trend comparisons
    - Fallback support when analytics unavailable
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        # Check if user has access to this client
        # TODO: Add client access validation based on user permissions

        # Get trend analysis from dashboard service
        trends = await dashboard_service.calculate_dashboard_trends(client_id, timeframe)

        return {
            "success": True,
            "data": trends,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "timeframe": timeframe,
        }

    except HTTPException:
        raise
    except AttributeError as e:
        # Handle case where trend analysis methods don't exist yet
        logger.warning(f"Trend analysis not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trend analysis feature is not yet available. Please ensure the analytics repository is properly configured.",
        )
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard trends for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard trends: {str(e)}",
        )


@analytics_router.get("/volume-patterns", tags=["Analytics"])
async def get_volume_patterns(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Query(..., description="Client identifier"),
    timeframe: str = Query(default="7d", description="Time range (1h, 6h, 12h, 24h, 7d, 30d)"),
) -> Dict[str, Any]:
    """
    Get email volume patterns for visualization.

    Returns hourly and daily volume patterns, peak hours analysis, and business hours
    vs after-hours volume distribution. Useful for understanding email traffic patterns
    and optimizing resource allocation.

    **Features:**
    - Hourly volume patterns (0-23 hours)
    - Daily volume trends over time period
    - Peak hour and quietest hour identification
    - Business hours vs after-hours analysis
    - Total volume statistics
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        # Get volume patterns from dashboard service
        patterns = await dashboard_service.get_volume_patterns(client_id, timeframe)

        return {
            "success": True,
            "data": patterns,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "timeframe": timeframe,
        }

    except HTTPException:
        raise
    except AttributeError as e:
        logger.warning(f"Volume patterns analysis not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Volume patterns analysis feature is not yet available. Please ensure the analytics repository is properly configured.",
        )
    except Exception as e:
        logger.error(f"❌ Failed to get volume patterns for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volume patterns: {str(e)}",
        )


@analytics_router.get("/sender-analytics", tags=["Analytics"])
async def get_sender_analytics(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Query(..., description="Client identifier"),
    timeframe: str = Query(default="7d", description="Time range (1h, 6h, 12h, 24h, 7d, 30d)"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of top domains to return"),
) -> Dict[str, Any]:
    """
    Get sender domain analytics and insights.

    Returns top sender domains by volume, domain diversity metrics, and concentration
    analysis. Helps identify email source patterns and potential security insights.

    **Features:**
    - Top sender domains with volume and percentage
    - Domain diversity and concentration metrics
    - Total unique domains count
    - Top domain share analysis
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        # Get sender analytics from dashboard service
        analytics = await dashboard_service.get_sender_analytics(client_id, timeframe, limit)

        return {
            "success": True,
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "timeframe": timeframe,
            "limit": limit,
        }

    except HTTPException:
        raise
    except AttributeError as e:
        logger.warning(f"Sender analytics not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Sender analytics feature is not yet available. Please ensure the analytics repository is properly configured.",
        )
    except Exception as e:
        logger.error(f"❌ Failed to get sender analytics for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sender analytics: {str(e)}",
        )


@analytics_router.get("/performance-insights", tags=["Analytics"])
async def get_performance_insights(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Query(..., description="Client identifier"),
    timeframe: str = Query(default="7d", description="Time range (1h, 6h, 12h, 24h, 7d, 30d)"),
) -> Dict[str, Any]:
    """
    Get detailed performance insights and recommendations.

    Returns processing performance analysis, quality metrics, escalation analysis,
    overall system grading (A-F), and actionable recommendations for improvement.

    **Features:**
    - Processing performance with average times and grading
    - Quality performance with confidence scores and error rates
    - Escalation performance analysis
    - Overall system grade (A+ to F)
    - Actionable recommendations for improvement
    - Performance trend indicators
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        # Get performance insights from dashboard service
        insights = await dashboard_service.get_performance_insights(client_id, timeframe)

        return {
            "success": True,
            "data": insights,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "timeframe": timeframe,
        }

    except HTTPException:
        raise
    except AttributeError as e:
        logger.warning(f"Performance insights not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Performance insights feature is not yet available. Please ensure the analytics repository is properly configured.",
        )
    except Exception as e:
        logger.error(f"❌ Failed to get performance insights for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance insights: {str(e)}",
        )


@router.get("/clients/{client_id}", response_model=ClientInfo, tags=["Dashboard"])
async def get_client_info(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get basic client information for dashboard header.

    Returns client name, industry, domain info, and basic settings.
    """
    try:
        client_info = await dashboard_service.get_client_info(client_id)
        return client_info

    except Exception as e:
        logger.error(f"❌ Failed to get client info for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client information: {str(e)}",
        )


@router.get("/clients/{client_id}/metrics", response_model=MetricsResponse, tags=["Dashboard"])
async def get_client_metrics(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
    timeframe: str = Query(default="24h", description="Time range (1h, 6h, 12h, 24h, 7d, 30d)"),
):
    """
    Get aggregated system metrics for client dashboard.

    Returns email volume, classification accuracy, response times, and system health metrics.
    Supports different timeframes for historical comparison.
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        metrics = await dashboard_service.get_system_metrics(client_id, timeframe)

        # Metric changes calculation would require historical data storage
        changes: Dict[str, Any] = {}  # Placeholder for period-over-period comparison

        return MetricsResponse(metrics=metrics, changes=changes, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get metrics for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}",
        )


@router.get(
    "/clients/{client_id}/activity", response_model=ActivityFeedResponse, tags=["Dashboard"]
)
async def get_client_activity(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of activities"),
    offset: int = Query(default=0, ge=0, description="Number of activities to skip"),
):
    """
    Get recent processing activities for client dashboard feed.

    Returns chronological list of email processing, routing, and automation activities.
    Supports pagination for loading historical data.
    """
    try:
        # Get activities (offset handling would be implemented in service layer)
        activities = await dashboard_service.get_recent_activities(client_id, limit + offset)

        # Apply pagination
        paginated_activities = activities[offset : offset + limit]

        return ActivityFeedResponse(
            activities=paginated_activities,
            total_count=len(activities),
            has_more=len(activities) > offset + limit,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"❌ Failed to get activities for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activities: {str(e)}",
        )


@router.get("/clients/{client_id}/alerts", response_model=AlertsResponse, tags=["Dashboard"])
async def get_client_alerts(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get current system alerts for client dashboard.

    Returns active alerts, warnings, and notifications with severity levels.
    Unresolved alerts are prioritized in the response.
    """
    try:
        alerts = await dashboard_service.get_alerts(client_id)

        # Calculate counts
        unread_count = len([a for a in alerts if not a.resolved])
        critical_count = len([a for a in alerts if a.severity == "critical" and not a.resolved])

        return AlertsResponse(
            alerts=alerts,
            unread_count=unread_count,
            critical_count=critical_count,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"❌ Failed to get alerts for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}",
        )


@router.post("/clients/{client_id}/alerts/{alert_id}/resolve", tags=["Dashboard"])
async def resolve_alert(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
    alert_id: str = Path(..., description="Alert identifier"),
):
    """
    Mark an alert as resolved.

    Updates alert status and records who resolved it and when.
    """
    try:
        resolved_by = current_user.email if current_user else "system"
        success = await dashboard_service.resolve_alert(client_id, alert_id, resolved_by)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found for client {client_id}",
            )

        return {"success": True, "message": "Alert resolved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}",
        )


@router.get(
    "/clients/{client_id}/automations", response_model=list[AutomationStatus], tags=["Dashboard"]
)
async def get_client_automations(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get automation status for client dashboard.

    Returns list of configured automations with their current status,
    performance metrics, and configuration details.
    """
    try:
        automations = await dashboard_service.get_automations(client_id)
        return automations

    except Exception as e:
        logger.error(f"❌ Failed to get automations for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve automations: {str(e)}",
        )


@router.get(
    "/clients/{client_id}/integrations", response_model=list[IntegrationHealth], tags=["Dashboard"]
)
async def get_client_integrations(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get integration health status for client dashboard.

    Returns status of all external system integrations including
    connection health, sync status, and error rates.
    """
    try:
        integrations = await dashboard_service.get_integrations(client_id)
        return integrations

    except Exception as e:
        logger.error(f"❌ Failed to get integrations for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integrations: {str(e)}",
        )


@router.get("/clients/{client_id}/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
async def get_dashboard_data(
    current_user: Annotated[DualAuthUser, Depends(require_dual_auth)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    client_id: str = Path(..., description="Client identifier"),
):
    """
    Get comprehensive dashboard data in a single request.

    Returns all dashboard components: metrics, activities, alerts,
    automations, and integrations. Useful for initial dashboard load.
    """
    try:
        # Load all dashboard data in parallel
        import asyncio

        client_info_task = dashboard_service.get_client_info(client_id)
        metrics_task = dashboard_service.get_system_metrics(client_id)
        activities_task = dashboard_service.get_recent_activities(client_id, 15)
        alerts_task = dashboard_service.get_alerts(client_id)
        automations_task = dashboard_service.get_automations(client_id)
        integrations_task = dashboard_service.get_integrations(client_id)

        # Wait for all tasks to complete
        results = await asyncio.gather(
            client_info_task,
            metrics_task,
            activities_task,
            alerts_task,
            automations_task,
            integrations_task,
            return_exceptions=True,
        )

        # Check for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Dashboard data task {i} failed: {result}")

        client_info = results[0] if not isinstance(results[0], Exception) else None
        metrics = (
            results[1]
            if not isinstance(results[1], Exception)
            else DashboardMetrics(
                emails_processed_24h=0,
                emails_processed_7d=0,
                classification_accuracy=0.0,
                average_response_time=0.0,
                active_automations=0,
                successful_routes=0,
                failed_routes=0,
                uptime_hours=0.0,
            )
        )
        activities = results[2] if not isinstance(results[2], Exception) else []
        alerts = results[3] if not isinstance(results[3], Exception) else []
        automations = results[4] if not isinstance(results[4], Exception) else []
        integrations = results[5] if not isinstance(results[5], Exception) else []

        if client_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Client {client_id} not found"
            )

        return DashboardResponse(
            client=client_info,
            metrics=metrics,
            activities=activities,
            alerts=alerts,
            automations=automations,
            integrations=integrations,
            analytics=None,  # Analytics feature requires advanced data aggregation
            last_updated=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard data for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}",
        )


# Include analytics router in the main router
router.include_router(analytics_router)
