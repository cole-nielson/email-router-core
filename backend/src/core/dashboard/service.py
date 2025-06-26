"""
Dashboard Service - Aggregates data from email processing and client configurations
to provide comprehensive dashboard metrics and analytics.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from core.ports.config_provider import ConfigurationProvider

from ..clients.manager import ClientManager
from ..models.dashboard import (
    ActivityType,
    AlertSeverity,
    AutomationStatus,
    ClientInfo,
    DashboardMetrics,
    IntegrationHealth,
    ProcessingActivity,
    SystemAlert,
    SystemStatus,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Core service for dashboard data aggregation and metrics generation.
    """

    def __init__(self, config_provider: ConfigurationProvider, client_manager: ClientManager):
        self.config_provider = config_provider
        self.client_manager = client_manager

        # In-memory storage for demo (would be replaced with database in production)
        self._activities_cache: Dict[str, List[ProcessingActivity]] = defaultdict(list)
        self._alerts_cache: Dict[str, List[SystemAlert]] = defaultdict(list)
        self._metrics_cache: Dict[str, Dict] = {}
        self._automation_status: Dict[str, List[AutomationStatus]] = defaultdict(list)
        self._integration_status: Dict[str, List[IntegrationHealth]] = defaultdict(list)

        # Initialize demo data
        self._initialize_demo_data()

    def _initialize_demo_data(self):
        """Initialize demo data for development purposes."""
        try:
            available_clients = self.client_manager.get_available_clients()

            for client_id in available_clients:
                # Initialize metrics
                self._calculate_real_metrics(client_id)

                # Initialize empty activities - real activities will be added during email processing
                self._activities_cache[client_id] = []

                # Initialize alerts
                self._generate_demo_alerts(client_id)

                # Initialize automations
                self._generate_demo_automations(client_id)

                # Initialize integrations
                self._generate_demo_integrations(client_id)

            logger.info(f"✅ Initialized demo data for {len(available_clients)} clients")

        except Exception as e:
            logger.error(f"❌ Failed to initialize demo data: {e}")

    async def get_client_info(self, client_id: str) -> ClientInfo:
        """Get basic client information."""
        try:
            client_summary = await self.client_manager.get_client_summary(client_id)

            return ClientInfo(
                id=client_id,
                name=client_summary.get("name", "Unknown Client"),
                industry=client_summary.get("industry", "Unknown"),
                primary_domain=client_summary.get("primary_domain", "unknown.com"),
                total_domains=client_summary.get("total_domains", 0),
                created_at=datetime.utcnow() - timedelta(days=30),  # Demo value
                settings=client_summary.get("settings", {}),
            )

        except Exception as e:
            logger.error(f"❌ Failed to get client info for {client_id}: {e}")
            raise

    async def get_system_metrics(self, client_id: str, timeframe: str = "24h") -> DashboardMetrics:
        """Get aggregated system metrics for a client."""
        try:
            # Get cached metrics or calculate real ones
            if client_id not in self._metrics_cache:
                self._calculate_real_metrics(client_id)

            base_metrics = self._metrics_cache[client_id]

            # Adjust metrics based on timeframe
            multiplier = self._get_timeframe_multiplier(timeframe)

            return DashboardMetrics(
                emails_processed_24h=int(base_metrics["emails_24h"] * multiplier),
                emails_processed_7d=int(base_metrics["emails_7d"] * multiplier),
                classification_accuracy=base_metrics["accuracy"],
                average_response_time=base_metrics["response_time"],
                active_automations=base_metrics["automations"],
                successful_routes=int(base_metrics["successful_routes"] * multiplier),
                failed_routes=int(base_metrics["failed_routes"] * multiplier),
                uptime_hours=base_metrics["uptime_hours"],
            )

        except Exception as e:
            logger.error(f"❌ Failed to get metrics for {client_id}: {e}")
            # Return default metrics on error
            return DashboardMetrics(
                emails_processed_24h=0,
                emails_processed_7d=0,
                classification_accuracy=0.0,
                average_response_time=0.0,
                active_automations=0,
                successful_routes=0,
                failed_routes=0,
                uptime_hours=0.0,
            )

    async def get_recent_activities(
        self, client_id: str, limit: int = 50
    ) -> List[ProcessingActivity]:
        """Get recent processing activities for a client."""
        try:
            activities = self._activities_cache.get(client_id, [])

            # Sort by timestamp (newest first) and limit
            sorted_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)
            return sorted_activities[:limit]

        except Exception as e:
            logger.error(f"❌ Failed to get activities for {client_id}: {e}")
            return []

    async def get_alerts(self, client_id: str) -> List[SystemAlert]:
        """Get current alerts for a client."""
        try:
            alerts = self._alerts_cache.get(client_id, [])

            # Sort by timestamp (newest first) and return unresolved first
            sorted_alerts = sorted(alerts, key=lambda x: (x.resolved, -x.timestamp.timestamp()))
            return sorted_alerts

        except Exception as e:
            logger.error(f"❌ Failed to get alerts for {client_id}: {e}")
            return []

    async def get_automations(self, client_id: str) -> List[AutomationStatus]:
        """Get automation status for a client."""
        try:
            return self._automation_status.get(client_id, [])

        except Exception as e:
            logger.error(f"❌ Failed to get automations for {client_id}: {e}")
            return []

    async def get_integrations(self, client_id: str) -> List[IntegrationHealth]:
        """Get integration health status for a client."""
        try:
            return self._integration_status.get(client_id, [])

        except Exception as e:
            logger.error(f"❌ Failed to get integrations for {client_id}: {e}")
            return []

    async def resolve_alert(self, client_id: str, alert_id: str, resolved_by: str) -> bool:
        """Mark an alert as resolved."""
        try:
            alerts = self._alerts_cache.get(client_id, [])

            for alert in alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    alert.resolved_by = resolved_by
                    logger.info(f"✅ Alert {alert_id} resolved by {resolved_by}")
                    return True

            logger.warning(f"⚠️ Alert {alert_id} not found for client {client_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to resolve alert {alert_id}: {e}")
            return False

    async def record_email_processed(self, client_id: str, email_data: Dict[str, Any]):
        """Record a new email processing activity."""
        try:
            # Map stage to activity type and generate appropriate title/description
            stage = email_data.get("stage", "email_processed")
            activity_type, title, description = self._get_activity_details(stage, email_data)

            activity = ProcessingActivity(
                id=str(uuid.uuid4()),
                type=activity_type,
                timestamp=datetime.utcnow(),
                client_id=client_id,
                title=title,
                description=description,
                metadata=email_data,
                success=email_data.get("success", True),
                duration_ms=email_data.get("processing_time_ms"),
            )

            # Add to activities cache
            self._activities_cache[client_id].append(activity)

            # Keep only last 1000 activities per client
            self._activities_cache[client_id] = self._activities_cache[client_id][-1000:]

            # Update metrics
            self._update_metrics_cache(client_id, activity)

            logger.debug(f"📧 Recorded email processing activity for {client_id}")
            return activity

        except Exception as e:
            logger.error(f"❌ Failed to record email activity: {e}")
            return None

    def _get_activity_details(self, stage: str, email_data: Dict[str, Any]) -> tuple:
        """Map processing stage to activity type and generate title/description."""
        sender = email_data.get("sender", "unknown")
        subject = email_data.get("subject", "No Subject")
        category = email_data.get("category", "general")
        routing_destination = email_data.get("routing_destination", "unknown")
        success = email_data.get("success", True)

        stage_mapping = {
            "email_received": (
                ActivityType.EMAIL_PROCESSED,
                f"📧 Email received from {sender}",
                f"New email: {subject}",
            ),
            "classification_complete": (
                ActivityType.CLASSIFICATION_COMPLETE,
                f"🤖 Email classified as {category}",
                f"AI classified '{subject}' with {email_data.get('confidence', 0):.1%} confidence",
            ),
            "routing_complete": (
                ActivityType.ROUTING_EXECUTED,
                f"📍 Email routed to {category}",
                f"Routed '{subject}' to {routing_destination}",
            ),
            "delivery_complete": (
                ActivityType.EMAIL_PROCESSED,
                "✅ Email processing complete" if success else "❌ Email processing failed",
                f"Completed processing '{subject}' in {email_data.get('processing_time_ms', 0)}ms",
            ),
            "processing_error": (
                ActivityType.EMAIL_PROCESSED,
                f"❌ Processing failed for email from {sender}",
                f"Error processing '{subject}': {email_data.get('error_message', 'Unknown error')}",
            ),
        }

        return stage_mapping.get(
            stage, (ActivityType.EMAIL_PROCESSED, f"Email from {sender}", f"Processed: {subject}")
        )

    def _calculate_real_metrics(self, client_id: str):
        """Calculate real metrics from actual email processing activities."""
        now = datetime.utcnow()

        # Get activities for this client
        activities = self._activities_cache.get(client_id, [])

        # Calculate time-based counts
        emails_24h = 0
        emails_7d = 0
        successful_routes = 0
        failed_routes = 0
        total_processing_time = 0
        processing_count = 0
        classification_attempts = 0
        successful_classifications = 0

        for activity in activities:
            # Calculate age in hours
            hours_ago = (now - activity.timestamp).total_seconds() / 3600

            # Count emails processed
            if activity.type in [
                ActivityType.EMAIL_PROCESSED
            ] and "email_received" in activity.metadata.get("stage", ""):
                if hours_ago <= 24:
                    emails_24h += 1
                if hours_ago <= 168:  # 7 days * 24 hours
                    emails_7d += 1

            # Count routing success/failures
            if activity.type == ActivityType.ROUTING_EXECUTED:
                if activity.success:
                    successful_routes += 1
                else:
                    failed_routes += 1

            # Calculate processing times
            if (
                activity.type == ActivityType.EMAIL_PROCESSED
                and activity.metadata.get("stage") == "delivery_complete"
                and activity.duration_ms
            ):
                total_processing_time += activity.duration_ms
                processing_count += 1

            # Calculate classification accuracy
            if activity.type == ActivityType.CLASSIFICATION_COMPLETE:
                classification_attempts += 1
                if activity.success and activity.metadata.get("confidence", 0) > 0.7:
                    successful_classifications += 1

        # Calculate derived metrics
        avg_response_time = (
            (total_processing_time / processing_count / 1000) if processing_count > 0 else 3.5
        )
        classification_accuracy = (
            (successful_classifications / classification_attempts)
            if classification_attempts > 0
            else 0.9
        )

        # Set default values if no real data yet
        if emails_24h == 0 and len(activities) == 0:
            # New client with no activity - use minimal realistic values
            self._metrics_cache[client_id] = {
                "emails_24h": 0,
                "emails_7d": 0,
                "accuracy": 0.90,
                "response_time": 3.5,
                "automations": 6,  # Number of configured automations
                "successful_routes": 0,
                "failed_routes": 0,
                "uptime_hours": 24.0,  # System has been running
            }
        else:
            # Use calculated real metrics
            self._metrics_cache[client_id] = {
                "emails_24h": emails_24h,
                "emails_7d": emails_7d,
                "accuracy": classification_accuracy,
                "response_time": avg_response_time,
                "automations": 6,  # Static for now - could be calculated from automation config
                "successful_routes": successful_routes,
                "failed_routes": failed_routes,
                "uptime_hours": 24.0,  # Could be calculated from first activity timestamp
            }

    def _generate_demo_activities(self, client_id: str):
        """Generate demo activities for development."""
        import random

        activities = []
        now = datetime.utcnow()

        activity_types = [
            (ActivityType.EMAIL_PROCESSED, "Processed email from"),
            (ActivityType.CLASSIFICATION_COMPLETE, "AI classified email as"),
            (ActivityType.ROUTING_EXECUTED, "Routed email to"),
            (ActivityType.INTEGRATION_SYNC, "Synced with"),
            (ActivityType.AUTOMATION_STARTED, "Started automation"),
        ]

        senders = ["john@company.com", "support@vendor.com", "info@partner.org", "hello@startup.io"]
        categories = ["Support", "Sales", "General", "Marketing", "Technical"]
        destinations = ["support-team", "sales-team", "general-inbox", "technical-support"]

        for i in range(20):
            activity_type, prefix = random.choice(activity_types)

            # Generate realistic activity data
            if activity_type == ActivityType.EMAIL_PROCESSED:
                sender = random.choice(senders)
                title = f"{prefix} {sender}"
                description = f"Successfully processed and classified email from {sender}"
            elif activity_type == ActivityType.CLASSIFICATION_COMPLETE:
                category = random.choice(categories)
                title = f"{prefix} {category}"
                description = f"AI classified email with {random.randint(85, 98)}% confidence"
            elif activity_type == ActivityType.ROUTING_EXECUTED:
                destination = random.choice(destinations)
                title = f"{prefix} {destination}"
                description = f"Email successfully routed to {destination}"
            else:
                title = f"{prefix} system component"
                description = "Automation task completed successfully"

            activity = ProcessingActivity(
                id=str(uuid.uuid4()),
                type=activity_type,
                timestamp=now - timedelta(minutes=random.randint(1, 1440)),  # Last 24 hours
                client_id=client_id,
                title=title,
                description=description,
                metadata={"demo": True},
                success=random.choice([True, True, True, False]),  # 75% success rate
                duration_ms=random.randint(1500, 8000),
            )

            activities.append(activity)

        self._activities_cache[client_id] = activities

    def _generate_demo_alerts(self, client_id: str):
        """Generate demo alerts for development."""
        import random

        alerts = []
        now = datetime.utcnow()

        alert_templates = [
            (AlertSeverity.LOW, "Processing Delay", "Email processing is taking longer than usual"),
            (
                AlertSeverity.MEDIUM,
                "Classification Confidence Low",
                "Recent emails have lower AI confidence scores",
            ),
            (
                AlertSeverity.HIGH,
                "Integration Timeout",
                "External system integration experiencing timeouts",
            ),
            (AlertSeverity.CRITICAL, "System Overload", "Processing queue is backing up"),
        ]

        # Generate 0-3 alerts per client
        for _ in range(random.randint(0, 3)):
            severity, title, message = random.choice(alert_templates)

            alert = SystemAlert(
                id=str(uuid.uuid4()),
                client_id=client_id,
                severity=severity,
                title=title,
                message=message,
                timestamp=now - timedelta(minutes=random.randint(1, 720)),
                resolved=(
                    random.choice([True, False]) if severity != AlertSeverity.CRITICAL else False
                ),
                metadata={"demo": True},
            )

            alerts.append(alert)

        self._alerts_cache[client_id] = alerts

    def _generate_demo_automations(self, client_id: str):
        """Generate demo automation status for development."""
        import random

        automations = [
            AutomationStatus(
                id="email-processor",
                name="Email Processing",
                type="email_processing",
                status=SystemStatus.HEALTHY,
                last_run=datetime.utcnow() - timedelta(minutes=random.randint(1, 30)),
                success_rate=random.uniform(0.92, 0.99),
                total_executions=random.randint(100, 500),
                configuration={"model": "claude-3-5-sonnet", "confidence_threshold": 0.8},
            ),
            AutomationStatus(
                id="lead-qualifier",
                name="Lead Qualification",
                type="lead_scoring",
                status=SystemStatus.HEALTHY,
                last_run=datetime.utcnow() - timedelta(hours=random.randint(1, 6)),
                success_rate=random.uniform(0.88, 0.96),
                total_executions=random.randint(50, 200),
                configuration={"scoring_model": "b2b_services", "threshold": 75},
            ),
            AutomationStatus(
                id="support-escalator",
                name="Support Escalation",
                type="support_automation",
                status=random.choice([SystemStatus.HEALTHY, SystemStatus.WARNING]),
                last_run=datetime.utcnow() - timedelta(minutes=random.randint(5, 60)),
                success_rate=random.uniform(0.85, 0.94),
                total_executions=random.randint(20, 100),
                configuration={"escalation_rules": "priority_based", "after_hours": True},
            ),
        ]

        self._automation_status[client_id] = automations

    def _generate_demo_integrations(self, client_id: str):
        """Generate demo integration health for development."""
        import random

        integrations = [
            IntegrationHealth(
                id="mailgun",
                name="Mailgun",
                type="email_service",
                status=SystemStatus.HEALTHY,
                last_sync=datetime.utcnow() - timedelta(minutes=random.randint(1, 10)),
                sync_frequency="real-time",
                error_count=0,
                response_time_ms=random.randint(200, 800),
            ),
            IntegrationHealth(
                id="slack",
                name="Slack",
                type="communication",
                status=SystemStatus.HEALTHY,
                last_sync=datetime.utcnow() - timedelta(minutes=random.randint(1, 15)),
                sync_frequency="instant",
                error_count=random.randint(0, 2),
                response_time_ms=random.randint(300, 1200),
            ),
            IntegrationHealth(
                id="salesforce",
                name="Salesforce",
                type="crm",
                status=random.choice([SystemStatus.HEALTHY, SystemStatus.WARNING]),
                last_sync=datetime.utcnow() - timedelta(minutes=random.randint(5, 30)),
                sync_frequency="5 minutes",
                error_count=random.randint(0, 3),
                response_time_ms=random.randint(800, 2500),
            ),
        ]

        self._integration_status[client_id] = integrations

    def _update_metrics_cache(self, client_id: str, activity: ProcessingActivity):
        """Update metrics cache based on new activity by recalculating from all activities."""
        # Instead of incrementing, recalculate metrics to ensure accuracy
        self._calculate_real_metrics(client_id)

    def _get_timeframe_multiplier(self, timeframe: str) -> float:
        """Get multiplier for different timeframes."""
        multipliers = {
            "1h": 1 / 24,
            "6h": 6 / 24,
            "12h": 12 / 24,
            "24h": 1.0,
            "7d": 7.0,
            "30d": 30.0,
        }
        return multipliers.get(timeframe, 1.0)


# Global dashboard service instance
_dashboard_service = None


def get_dashboard_service() -> DashboardService:
    """Get or create dashboard service instance."""
    global _dashboard_service

    if _dashboard_service is None:
        from application.dependencies.config import get_client_manager, get_config_provider

        config_provider = get_config_provider()
        client_manager = get_client_manager()
        _dashboard_service = DashboardService(config_provider, client_manager)

    return _dashboard_service
