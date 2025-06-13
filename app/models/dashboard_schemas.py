"""
Dashboard-specific data models for client metrics, activities, and real-time updates.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class MetricTrend(str, Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType(str, Enum):
    EMAIL_PROCESSED = "email_processed"
    CLASSIFICATION_COMPLETE = "classification_complete"
    ROUTING_EXECUTED = "routing_executed"
    INTEGRATION_SYNC = "integration_sync"
    ALERT_TRIGGERED = "alert_triggered"
    AUTOMATION_STARTED = "automation_started"
    AUTOMATION_COMPLETED = "automation_completed"


class SystemStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


# Dashboard Metrics Models
class DashboardMetrics(BaseModel):
    emails_processed_24h: int = Field(..., description="Total emails processed in last 24 hours")
    emails_processed_7d: int = Field(..., description="Total emails processed in last 7 days")
    classification_accuracy: float = Field(
        ..., ge=0, le=1, description="AI classification accuracy (0-1)"
    )
    average_response_time: float = Field(..., description="Average processing time in seconds")
    active_automations: int = Field(..., description="Number of currently active automations")
    successful_routes: int = Field(..., description="Successfully routed emails in 24h")
    failed_routes: int = Field(..., description="Failed routing attempts in 24h")
    uptime_hours: float = Field(..., description="System uptime in hours")


class MetricChange(BaseModel):
    trend: MetricTrend
    value: str = Field(..., description="Change value (e.g., '+12%', '-0.3s')")
    period: str = Field(default="24h", description="Time period for comparison")


class ProcessingActivity(BaseModel):
    id: str = Field(..., description="Unique activity identifier")
    type: ActivityType
    timestamp: datetime
    client_id: str
    title: str = Field(..., description="Human-readable activity title")
    description: str = Field(..., description="Detailed activity description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional activity data")
    success: bool = Field(default=True, description="Whether the activity was successful")
    duration_ms: Optional[int] = Field(None, description="Activity duration in milliseconds")


class SystemAlert(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    client_id: str
    severity: AlertSeverity
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Detailed alert message")
    timestamp: datetime
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationStatus(BaseModel):
    id: str = Field(..., description="Automation identifier")
    name: str = Field(..., description="Human-readable automation name")
    type: str = Field(..., description="Automation type (e.g., 'email_processing', 'lead_scoring')")
    status: SystemStatus
    last_run: Optional[datetime] = None
    success_rate: float = Field(..., ge=0, le=1, description="Success rate (0-1)")
    total_executions: int = Field(default=0)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class IntegrationHealth(BaseModel):
    id: str = Field(..., description="Integration identifier")
    name: str = Field(..., description="Integration name (e.g., 'Salesforce', 'Slack')")
    type: str = Field(..., description="Integration type")
    status: SystemStatus
    last_sync: Optional[datetime] = None
    sync_frequency: str = Field(..., description="How often sync occurs")
    error_count: int = Field(default=0, description="Errors in last 24h")
    response_time_ms: Optional[int] = None


class DashboardAnalytics(BaseModel):
    email_volume_chart: List[Dict[str, Union[str, int]]] = Field(
        default_factory=list, description="Time series data for email volume"
    )
    classification_breakdown: Dict[str, int] = Field(
        default_factory=dict, description="Email categories and counts"
    )
    performance_trends: List[Dict[str, Union[str, float]]] = Field(
        default_factory=list, description="Performance metrics over time"
    )
    top_routing_destinations: List[Dict[str, Union[str, int]]] = Field(
        default_factory=list, description="Most common routing destinations"
    )


class ClientInfo(BaseModel):
    id: str = Field(..., description="Client identifier")
    name: str = Field(..., description="Client display name")
    industry: str = Field(..., description="Client industry")
    primary_domain: str = Field(..., description="Primary email domain")
    total_domains: int = Field(..., description="Number of configured domains")
    created_at: Optional[datetime] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


# API Response Models
class DashboardResponse(BaseModel):
    client: ClientInfo
    metrics: DashboardMetrics
    activities: List[ProcessingActivity]
    alerts: List[SystemAlert]
    automations: List[AutomationStatus]
    integrations: List[IntegrationHealth]
    analytics: Optional[DashboardAnalytics] = None
    last_updated: datetime


class MetricsResponse(BaseModel):
    metrics: DashboardMetrics
    changes: Dict[str, MetricChange] = Field(
        default_factory=dict, description="Metric changes compared to previous period"
    )
    timestamp: datetime


class ActivityFeedResponse(BaseModel):
    activities: List[ProcessingActivity]
    total_count: int
    has_more: bool = Field(default=False)
    timestamp: datetime


class AlertsResponse(BaseModel):
    alerts: List[SystemAlert]
    unread_count: int
    critical_count: int
    timestamp: datetime


# WebSocket Message Models
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type identifier")
    client_id: str = Field(..., description="Target client ID")
    data: Any = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricUpdateMessage(WebSocketMessage):
    type: Literal["metric_update"] = "metric_update"
    data: DashboardMetrics


class ActivityUpdateMessage(WebSocketMessage):
    type: Literal["activity_feed"] = "activity_feed"
    data: ProcessingActivity


class AlertUpdateMessage(WebSocketMessage):
    type: Literal["system_alert"] = "system_alert"
    data: SystemAlert


class ClientUpdateMessage(WebSocketMessage):
    type: Literal["client_update"] = "client_update"
    data: ClientInfo
