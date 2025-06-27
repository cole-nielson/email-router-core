"""
Dashboard Service - Aggregates data from email processing and client configurations
to provide comprehensive dashboard metrics and analytics.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.ports.analytics_repository import AnalyticsRepository
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

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        client_manager: ClientManager,
        analytics_repository: Optional[AnalyticsRepository] = None,
    ):
        self.config_provider = config_provider
        self.client_manager = client_manager
        self.analytics_repository = analytics_repository

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

    # =============================================================================
    # TREND ANALYSIS METHODS
    # =============================================================================

    async def calculate_dashboard_trends(
        self, client_id: str, timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive dashboard trends using analytics data.

        Args:
            client_id: Client identifier
            timeframe: Time period for analysis (1h, 6h, 12h, 24h, 7d, 30d)

        Returns:
            Dictionary containing comprehensive trend analysis
        """
        if not self.analytics_repository:
            logger.warning("Analytics repository not available, using fallback data")
            return self._get_fallback_trends(client_id, timeframe)

        try:
            # Calculate time periods
            end_date = datetime.utcnow()
            hours = self._get_timeframe_hours(timeframe)
            start_date = end_date - timedelta(hours=hours)

            # Calculate previous period for comparison
            previous_end = start_date
            previous_start = previous_end - timedelta(hours=hours)

            # Get analytics data in parallel
            volume_by_category = await self.analytics_repository.get_routing_volume_by_category(
                client_id, start_date, end_date
            )

            avg_processing_time = await self.analytics_repository.get_average_processing_time(
                client_id, start_date, end_date
            )

            error_rate = await self.analytics_repository.get_error_rate(
                client_id, start_date, end_date
            )

            confidence_distribution = await self.analytics_repository.get_confidence_distribution(
                client_id, start_date, end_date
            )

            escalation_metrics = await self.analytics_repository.get_escalation_metrics(
                client_id, start_date, end_date
            )

            # Get period comparison for trend indicators
            period_comparison = await self.analytics_repository.get_period_comparison(
                client_id, start_date, end_date, previous_start, previous_end
            )

            # Calculate total emails and success metrics
            total_emails = sum(volume_by_category.values())
            success_rate = 100.0 - error_rate

            return {
                "timeframe": timeframe,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "hours": hours,
                },
                "volume_metrics": {
                    "total_emails": total_emails,
                    "by_category": volume_by_category,
                    "daily_average": round(total_emails / max(hours / 24, 1), 1),
                },
                "performance_metrics": {
                    "avg_processing_time_ms": round(avg_processing_time, 1),
                    "success_rate": round(success_rate, 2),
                    "error_rate": round(error_rate, 2),
                },
                "quality_metrics": {
                    "confidence_distribution": confidence_distribution,
                    "high_confidence_rate": round(
                        (
                            confidence_distribution.get("very_high", 0)
                            + confidence_distribution.get("high", 0)
                        )
                        / max(total_emails, 1)
                        * 100,
                        2,
                    ),
                },
                "escalation_metrics": escalation_metrics,
                "trends": {
                    "vs_previous_period": period_comparison.get("changes", {}),
                    "total_emails_change": period_comparison.get("changes", {}).get(
                        "total_emails", {}
                    ),
                    "performance_change": period_comparison.get("changes", {}).get(
                        "avg_processing_time", {}
                    ),
                    "error_rate_change": period_comparison.get("changes", {}).get("error_rate", {}),
                },
            }

        except Exception as e:
            logger.error(f"Failed to calculate dashboard trends for {client_id}: {e}")
            return self._get_fallback_trends(client_id, timeframe)

    async def get_volume_patterns(self, client_id: str, timeframe: str = "7d") -> Dict[str, Any]:
        """
        Get email volume patterns for visualization.

        Args:
            client_id: Client identifier
            timeframe: Time period for pattern analysis

        Returns:
            Dictionary containing volume patterns and trends
        """
        if not self.analytics_repository:
            return self._get_fallback_patterns(client_id)

        try:
            end_date = datetime.utcnow()
            hours = self._get_timeframe_hours(timeframe)
            start_date = end_date - timedelta(hours=hours)

            # Get hourly and daily patterns
            hourly_pattern = await self.analytics_repository.get_hourly_volume_pattern(
                client_id, start_date, end_date
            )

            daily_trend = await self.analytics_repository.get_daily_volume_trend(
                client_id, start_date, end_date
            )

            # Analyze patterns
            peak_hour = max(hourly_pattern.items(), key=lambda x: x[1])[0] if hourly_pattern else 9
            quietest_hour = (
                min(hourly_pattern.items(), key=lambda x: x[1])[0] if hourly_pattern else 2
            )

            # Calculate business hours vs after hours
            business_hours_volume = sum(hourly_pattern.get(h, 0) for h in range(9, 17))
            after_hours_volume = sum(
                hourly_pattern.get(h, 0) for h in list(range(0, 9)) + list(range(17, 24))
            )
            total_volume = business_hours_volume + after_hours_volume

            business_hours_percentage = (
                (business_hours_volume / total_volume * 100) if total_volume > 0 else 0
            )

            return {
                "timeframe": timeframe,
                "hourly_pattern": hourly_pattern,
                "daily_trend": daily_trend,
                "insights": {
                    "peak_hour": peak_hour,
                    "quietest_hour": quietest_hour,
                    "business_hours_percentage": round(business_hours_percentage, 1),
                    "after_hours_percentage": round(100 - business_hours_percentage, 1),
                    "total_volume": total_volume,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get volume patterns for {client_id}: {e}")
            return self._get_fallback_patterns(client_id)

    async def get_sender_analytics(
        self, client_id: str, timeframe: str = "7d", limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get sender domain analytics and insights.

        Args:
            client_id: Client identifier
            timeframe: Time period for analysis
            limit: Number of top domains to return

        Returns:
            Dictionary containing sender analytics
        """
        if not self.analytics_repository:
            return self._get_fallback_sender_analytics(client_id)

        try:
            end_date = datetime.utcnow()
            hours = self._get_timeframe_hours(timeframe)
            start_date = end_date - timedelta(hours=hours)

            # Get top sender domains
            top_domains = await self.analytics_repository.get_top_sender_domains(
                client_id, start_date, end_date, limit
            )

            # Calculate insights
            total_senders = len(top_domains)
            if top_domains:
                top_domain_percentage = top_domains[0]["percentage"]
                concentration_score = sum(domain["percentage"] for domain in top_domains[:3])
            else:
                top_domain_percentage = 0
                concentration_score = 0

            return {
                "timeframe": timeframe,
                "top_domains": top_domains,
                "insights": {
                    "total_unique_domains": total_senders,
                    "top_domain_share": round(top_domain_percentage, 1),
                    "top_3_concentration": round(concentration_score, 1),
                    "diversity_score": round(100 - concentration_score, 1),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get sender analytics for {client_id}: {e}")
            return self._get_fallback_sender_analytics(client_id)

    async def get_performance_insights(
        self, client_id: str, timeframe: str = "7d"
    ) -> Dict[str, Any]:
        """
        Get detailed performance insights and recommendations.

        Args:
            client_id: Client identifier
            timeframe: Time period for analysis

        Returns:
            Dictionary containing performance insights
        """
        if not self.analytics_repository:
            return self._get_fallback_performance_insights(client_id)

        try:
            end_date = datetime.utcnow()
            hours = self._get_timeframe_hours(timeframe)
            start_date = end_date - timedelta(hours=hours)

            # Get performance metrics
            avg_processing_time = await self.analytics_repository.get_average_processing_time(
                client_id, start_date, end_date
            )

            error_rate = await self.analytics_repository.get_error_rate(
                client_id, start_date, end_date
            )

            confidence_distribution = await self.analytics_repository.get_confidence_distribution(
                client_id, start_date, end_date
            )

            escalation_metrics = await self.analytics_repository.get_escalation_metrics(
                client_id, start_date, end_date
            )

            # Calculate performance scores and insights
            total_emails = sum(confidence_distribution.values())
            high_confidence_emails = confidence_distribution.get(
                "very_high", 0
            ) + confidence_distribution.get("high", 0)
            confidence_score = (
                (high_confidence_emails / total_emails * 100) if total_emails > 0 else 0
            )

            # Performance rating (A-F scale)
            performance_grade = self._calculate_performance_grade(
                avg_processing_time,
                error_rate,
                confidence_score,
                escalation_metrics["escalation_rate"],
            )

            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                avg_processing_time,
                error_rate,
                confidence_score,
                escalation_metrics["escalation_rate"],
            )

            return {
                "timeframe": timeframe,
                "processing_performance": {
                    "avg_time_ms": round(avg_processing_time, 1),
                    "grade": performance_grade,
                    "benchmark": "< 3000ms excellent, < 5000ms good, > 5000ms needs improvement",
                },
                "quality_performance": {
                    "confidence_score": round(confidence_score, 1),
                    "error_rate": round(error_rate, 2),
                    "success_rate": round(100 - error_rate, 2),
                },
                "escalation_performance": escalation_metrics,
                "overall_grade": performance_grade,
                "recommendations": recommendations,
                "insights": {
                    "total_emails_analyzed": total_emails,
                    "performance_trend": "stable",  # Could be calculated from period comparison
                    "strongest_metric": self._identify_strongest_metric(
                        avg_processing_time, error_rate, confidence_score
                    ),
                    "improvement_area": self._identify_improvement_area(
                        avg_processing_time, error_rate, confidence_score
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get performance insights for {client_id}: {e}")
            return self._get_fallback_performance_insights(client_id)

    # =============================================================================
    # HELPER METHODS FOR TREND ANALYSIS
    # =============================================================================

    def _get_timeframe_hours(self, timeframe: str) -> int:
        """Convert timeframe string to hours."""
        timeframe_hours = {
            "1h": 1,
            "6h": 6,
            "12h": 12,
            "24h": 24,
            "7d": 168,  # 7 * 24
            "30d": 720,  # 30 * 24
        }
        return timeframe_hours.get(timeframe, 24)

    def _calculate_performance_grade(
        self, avg_time: float, error_rate: float, confidence_score: float, escalation_rate: float
    ) -> str:
        """Calculate overall performance grade A-F."""
        # Scoring algorithm based on multiple metrics
        time_score = (
            100 if avg_time < 2000 else (90 if avg_time < 3000 else (80 if avg_time < 5000 else 60))
        )
        error_score = (
            100
            if error_rate < 0.5
            else (90 if error_rate < 1.0 else (80 if error_rate < 2.0 else 60))
        )
        confidence_score_normalized = min(confidence_score, 100)
        escalation_score = (
            100
            if escalation_rate < 1.0
            else (90 if escalation_rate < 2.0 else (80 if escalation_rate < 5.0 else 60))
        )

        # Weighted average
        overall_score = (
            time_score * 0.3
            + error_score * 0.3
            + confidence_score_normalized * 0.3
            + escalation_score * 0.1
        )

        if overall_score >= 95:
            return "A+"
        elif overall_score >= 90:
            return "A"
        elif overall_score >= 85:
            return "B+"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 75:
            return "C+"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 65:
            return "D"
        else:
            return "F"

    def _generate_performance_recommendations(
        self, avg_time: float, error_rate: float, confidence_score: float, escalation_rate: float
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if avg_time > 5000:
            recommendations.append(
                "Consider optimizing AI model configuration or processing pipeline to reduce response times"
            )
        elif avg_time > 3000:
            recommendations.append(
                "Monitor processing times during peak hours and consider scaling resources"
            )

        if error_rate > 2.0:
            recommendations.append(
                "Investigate and address high error rate - check logs for common failure patterns"
            )
        elif error_rate > 1.0:
            recommendations.append(
                "Review error handling and consider implementing additional retry logic"
            )

        if confidence_score < 70:
            recommendations.append(
                "Review AI classification prompts and training data to improve confidence scores"
            )
        elif confidence_score < 85:
            recommendations.append(
                "Fine-tune classification categories to better match incoming email patterns"
            )

        if escalation_rate > 5.0:
            recommendations.append(
                "Review escalation rules - high escalation rate may indicate routing issues"
            )
        elif escalation_rate > 2.0:
            recommendations.append(
                "Monitor escalation patterns to identify optimization opportunities"
            )

        if not recommendations:
            recommendations.append(
                "System is performing well - maintain current configuration and monitor trends"
            )

        return recommendations

    def _identify_strongest_metric(
        self, avg_time: float, error_rate: float, confidence_score: float
    ) -> str:
        """Identify the strongest performing metric."""
        scores: Dict[str, float] = {}

        if avg_time < 2000:
            scores["processing_speed"] = 95.0
        elif avg_time < 3000:
            scores["processing_speed"] = 85.0
        else:
            scores["processing_speed"] = 70.0

        if error_rate < 0.5:
            scores["reliability"] = 95.0
        elif error_rate < 1.0:
            scores["reliability"] = 85.0
        else:
            scores["reliability"] = 70.0

        scores["ai_confidence"] = min(confidence_score, 95.0)

        return max(scores, key=lambda k: scores[k])

    def _identify_improvement_area(
        self, avg_time: float, error_rate: float, confidence_score: float
    ) -> str:
        """Identify the area most needing improvement."""
        scores: Dict[str, float] = {}

        if avg_time > 5000:
            scores["processing_speed"] = 40.0
        elif avg_time > 3000:
            scores["processing_speed"] = 70.0
        else:
            scores["processing_speed"] = 90.0

        if error_rate > 2.0:
            scores["reliability"] = 40.0
        elif error_rate > 1.0:
            scores["reliability"] = 70.0
        else:
            scores["reliability"] = 90.0

        scores["ai_confidence"] = min(confidence_score, 95.0)

        return min(scores, key=lambda k: scores[k])

    # Fallback methods for when analytics repository is not available
    def _get_fallback_trends(self, client_id: str, timeframe: str) -> Dict[str, Any]:
        """Provide fallback trend data when analytics repository is unavailable."""
        return {
            "timeframe": timeframe,
            "period": {"start": "", "end": "", "hours": self._get_timeframe_hours(timeframe)},
            "volume_metrics": {"total_emails": 0, "by_category": {}, "daily_average": 0},
            "performance_metrics": {
                "avg_processing_time_ms": 0,
                "success_rate": 0,
                "error_rate": 0,
            },
            "quality_metrics": {"confidence_distribution": {}, "high_confidence_rate": 0},
            "escalation_metrics": {
                "total_escalations": 0,
                "escalation_rate": 0,
                "by_category": {},
                "by_priority": {},
            },
            "trends": {
                "vs_previous_period": {},
                "total_emails_change": {},
                "performance_change": {},
                "error_rate_change": {},
            },
            "note": "Analytics repository unavailable - using fallback data",
        }

    def _get_fallback_patterns(self, client_id: str) -> Dict[str, Any]:
        """Provide fallback pattern data."""
        return {
            "timeframe": "7d",
            "hourly_pattern": {hour: 0 for hour in range(24)},
            "daily_trend": {},
            "insights": {
                "peak_hour": 9,
                "quietest_hour": 2,
                "business_hours_percentage": 0,
                "after_hours_percentage": 0,
                "total_volume": 0,
            },
            "note": "Analytics repository unavailable - using fallback data",
        }

    def _get_fallback_sender_analytics(self, client_id: str) -> Dict[str, Any]:
        """Provide fallback sender analytics."""
        return {
            "timeframe": "7d",
            "top_domains": [],
            "insights": {
                "total_unique_domains": 0,
                "top_domain_share": 0,
                "top_3_concentration": 0,
                "diversity_score": 0,
            },
            "note": "Analytics repository unavailable - using fallback data",
        }

    def _get_fallback_performance_insights(self, client_id: str) -> Dict[str, Any]:
        """Provide fallback performance insights."""
        return {
            "timeframe": "7d",
            "processing_performance": {
                "avg_time_ms": 0,
                "grade": "N/A",
                "benchmark": "Analytics unavailable",
            },
            "quality_performance": {"confidence_score": 0, "error_rate": 0, "success_rate": 0},
            "escalation_performance": {
                "total_escalations": 0,
                "escalation_rate": 0,
                "by_category": {},
                "by_priority": {},
            },
            "overall_grade": "N/A",
            "recommendations": [
                "Analytics repository unavailable - enable analytics for detailed insights"
            ],
            "insights": {
                "total_emails_analyzed": 0,
                "performance_trend": "unknown",
                "strongest_metric": "unknown",
                "improvement_area": "unknown",
            },
            "note": "Analytics repository unavailable - using fallback data",
        }

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
        from application.dependencies.repositories import get_analytics_repository
        from infrastructure.database.connection import get_database_session

        config_provider = get_config_provider()
        client_manager = get_client_manager()

        # Try to get analytics repository, but continue without it if unavailable
        analytics_repository = None
        try:
            db_session = next(get_database_session())
            analytics_repository = get_analytics_repository(db_session)
            logger.info("✅ Analytics repository initialized for dashboard service")
        except Exception as e:
            logger.warning(f"⚠️ Analytics repository unavailable for dashboard: {e}")
            # Dashboard will use fallback data

        _dashboard_service = DashboardService(config_provider, client_manager, analytics_repository)

    return _dashboard_service
