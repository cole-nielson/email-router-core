"""
Dynamic email routing engine using client-specific rules.
📤 Multi-tenant email routing with escalation and special rules.
"""

import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pytz

from infrastructure.config.schema import ClientConfig

from ..clients.manager import ClientManager
from ..ports.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Multi-tenant email routing engine.

    Routes emails to appropriate team members based on client-specific
    rules, escalation policies, and business hours.
    """

    def __init__(
        self,
        client_manager: ClientManager,
        analytics_repository: Optional[AnalyticsRepository] = None,
    ):
        """
        Initialize routing engine.

        Args:
            client_manager: ClientManager instance for client operations
            analytics_repository: Optional analytics repository for capturing routing data
        """
        self.client_manager = client_manager
        self.analytics_repository = analytics_repository

    def route_email(
        self,
        client_id: str,
        classification: Dict[str, Any],
        email_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route email to appropriate team member.

        Args:
            client_id: Client identifier
            classification: Email classification result
            email_data: Optional email data for context

        Returns:
            Routing decision with destination, escalation info, etc.
        """
        start_time = datetime.utcnow()
        routing_start = None

        try:
            client_config = self.client_manager.get_client_config(client_id)
            if not client_config:
                raise ValueError("Could not load client configuration")

            category = classification.get("category", "general")
            confidence = classification.get("confidence", 0.5)

            # Start routing timing
            routing_start = datetime.utcnow()

            # Check for immediate escalation triggers
            escalation_result = self._check_immediate_escalation(
                client_id, classification, email_data, client_config
            )
            if escalation_result:
                logger.info(
                    f"🚨 Immediate escalation triggered for {client_id}: {escalation_result['reason']}"
                )
                return escalation_result

            # Get primary routing destination
            primary_destination = self._get_primary_destination(client_config, category)

            if not primary_destination:
                # Try backup routing
                backup_destination = self._get_backup_destination(
                    client_config, category
                )
                if backup_destination:
                    logger.warning(
                        f"Using backup routing for {category} -> {backup_destination}"
                    )
                    primary_destination = backup_destination
                else:
                    # Final fallback to general
                    primary_destination = self._get_primary_destination(
                        client_config, "general"
                    )
                    if not primary_destination:
                        logger.error(
                            f"No routing destination found for {client_id}, using primary contact"
                        )
                        primary_destination = client_config.contacts.primary_contact

            # Check business hours and route accordingly
            final_destination = self._apply_business_hours_routing(
                client_id, primary_destination, client_config
            )

            # Determine escalation schedule
            escalation_schedule = self._get_escalation_schedule(
                client_id, category, client_config, classification
            )

            # Build routing result
            routing_result = {
                "client_id": client_id,
                "category": category,
                "primary_destination": final_destination,
                "backup_destinations": self._get_backup_destinations(
                    client_config, category
                ),
                "escalation_schedule": escalation_schedule,
                "business_hours_applied": final_destination != primary_destination,
                "confidence_level": self._get_confidence_level(confidence),
                "special_handling": self._get_special_handling(
                    client_id, email_data, client_config
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Capture analytics data
            self._capture_routing_analytics(
                client_id=client_id,
                email_data=email_data or {},
                classification=classification,
                routing_result=routing_result,
                start_time=start_time,
                routing_start=routing_start,
            )

            logger.info(
                f"📍 Routed {category} email for {client_id} to {final_destination}"
            )
            return routing_result

        except Exception as e:
            logger.error(f"Routing failed for {client_id}: {e}")
            return self._get_fallback_routing(client_id, classification)

    def _check_immediate_escalation(
        self,
        client_id: str,
        classification: Dict[str, Any],
        email_data: Optional[Dict[str, Any]],
        client_config: ClientConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if email should be immediately escalated.

        Args:
            client_id: Client identifier
            classification: Email classification result
            email_data: Email data for context checks
            client_config: The client's configuration object.

        Returns:
            Escalation routing if triggered, None otherwise
        """
        # This method now needs to be adapted to use ClientConfig directly
        # For now, we'll bypass this check as it requires more info on escalation rules in new schema
        return None

    def _get_primary_destination(
        self, client_config: ClientConfig, category: str
    ) -> Optional[str]:
        """
        Get primary routing destination for category.

        Args:
            client_config: Client configuration object
            category: Email category

        Returns:
            Primary destination email if found
        """
        for rule in client_config.routing:
            if rule.category == category and rule.enabled:
                return str(rule.email) if rule.email else None
        return None

    def _get_backup_destination(
        self, client_config: ClientConfig, category: str
    ) -> Optional[str]:
        """
        Get backup routing destination for category.

        Args:
            client_config: Client configuration object
            category: Email category

        Returns:
            Backup destination email if found
        """
        for rule in client_config.routing:
            if rule.category == category and rule.enabled:
                return str(rule.backup_email) if rule.backup_email else None
        return None

    def _get_backup_destinations(
        self, client_config: ClientConfig, category: str
    ) -> List[str]:
        """
        Get list of backup destinations for category.

        Args:
            client_config: Client configuration object
            category: Email category

        Returns:
            List of backup destination emails
        """
        backups = []

        # Add backup routing destination
        backup = self._get_backup_destination(client_config, category)
        if backup:
            backups.append(backup)

        # Add general routing as ultimate backup
        general_dest = self._get_primary_destination(client_config, "general")
        if general_dest and general_dest not in backups:
            backups.append(general_dest)

        return backups

    def _apply_business_hours_routing(
        self,
        client_id: str,
        primary_destination: str,
        client_config: ClientConfig,
    ) -> str:
        """
        Apply business hours routing rules.

        Args:
            client_id: Client identifier
            primary_destination: Primary routing destination
            client_config: Client configuration

        Returns:
            Final destination after business hours consideration
        """
        try:
            if self._is_business_hours(client_config):
                # During business hours, use primary destination
                return primary_destination

            # This logic needs to be updated based on the new `special_rules` in ClientConfig
            # Bypassing for now
            return primary_destination

        except Exception as e:
            logger.warning(
                f"Failed to apply business hours routing for {client_id}: {e}"
            )
            return primary_destination

    def _is_business_hours(self, client_config: ClientConfig) -> bool:
        """
        Check if current time is within business hours.

        Args:
            client_config: Client configuration

        Returns:
            True if within business hours, False otherwise
        """
        try:
            client_tz = pytz.timezone(client_config.timezone)
            now = datetime.now(client_tz)

            business_hours_config = client_config.sla.business_hours
            if not business_hours_config:
                return True  # Default to always on if not configured

            workdays = business_hours_config.get("weekdays", {})
            start_time_str = workdays.get("start", "00:00")
            end_time_str = workdays.get("end", "23:59")

            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)

            # A simple check for now, can be expanded for specific workdays
            if now.weekday() < 5:  # Monday to Friday
                return start_time <= now.time() <= end_time

            return False

        except Exception as e:
            logger.warning(f"Failed to check business hours: {e}")
            return True  # Default to business hours if check fails

    def _get_escalation_schedule(
        self,
        client_id: str,
        category: str,
        client_config: ClientConfig,
        classification: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Get escalation schedule for category.

        Args:
            client_id: Client identifier
            category: Email category
            client_config: Client configuration object
            classification: Classification result

        Returns:
            List of escalation steps with timing and destinations
        """
        escalation_schedule: List[Dict[str, Any]] = []

        try:
            if (
                not client_config.sla.escalation_enabled
                or not client_config.sla.escalation_rules
            ):
                return escalation_schedule

            for i, rule in enumerate(client_config.sla.escalation_rules):
                # This needs more robust logic based on rule.trigger_type, etc.
                # For now, let's assume all rules apply and have a time trigger
                if rule.trigger_type == "time":
                    escalation_schedule.append(
                        {
                            "step": i + 1,
                            "hours_after": rule.trigger_value,
                            "escalate_to": rule.target_email,
                            "escalation_time": self._calculate_escalation_time(
                                rule.trigger_value
                            ),
                            "category": category,
                        }
                    )
        except Exception as e:
            logger.warning(f"Failed to get escalation schedule for {client_id}: {e}")

        return escalation_schedule

    def _calculate_escalation_time(self, hours_after: int) -> str:
        """
        Calculate escalation time from now.

        Args:
            hours_after: Hours after initial email

        Returns:
            ISO timestamp for escalation time
        """
        escalation_time = datetime.utcnow() + timedelta(hours=hours_after)
        return escalation_time.isoformat()

    def _get_confidence_level(self, confidence: float) -> str:
        """
        Get confidence level category.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence level string
        """
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.3:
            return "low"
        else:
            return "very_low"

    def _get_special_handling(
        self,
        client_id: str,
        email_data: Optional[Dict[str, Any]],
        client_config: ClientConfig,
    ) -> List[str]:
        """
        Get special handling flags for email.

        Args:
            client_id: Client identifier
            email_data: Email data
            client_config: Client configuration object

        Returns:
            List of special handling flags
        """
        flags: List[str] = []

        try:
            if not email_data:
                return flags

            # This logic needs to be updated to match new config structure for VIPs etc.
            # Bypassing for now.

            # Check for urgent keywords in subject/body
            subject = email_data.get("subject", "").lower()
            body = (
                email_data.get("stripped_text") or email_data.get("body_text", "")
            ).lower()
            text = f"{subject} {body}"

            urgent_keywords = ["urgent", "emergency", "critical", "asap", "immediate"]
            if any(keyword in text for keyword in urgent_keywords):
                flags.append("urgent_keywords")

            # Check for complaint indicators
            complaint_keywords = [
                "complaint",
                "dissatisfied",
                "unhappy",
                "terrible",
                "awful",
                "worst",
            ]
            if any(keyword in text for keyword in complaint_keywords):
                flags.append("complaint_indicators")

        except Exception as e:
            logger.warning(f"Failed to get special handling for {client_id}: {e}")

        return flags

    def _get_fallback_routing(
        self, client_id: str, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get fallback routing when normal routing fails.

        Args:
            client_id: Client identifier
            classification: Classification result

        Returns:
            Fallback routing result
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            if client_config is not None and client_config.contacts is not None:
                primary_contact = client_config.contacts.primary_contact
            else:
                primary_contact = "admin@example.com"

            return {
                "client_id": client_id,
                "category": classification.get("category", "general"),
                "primary_destination": primary_contact,
                "backup_destinations": (
                    [client_config.contacts.escalation_contact]
                    if client_config is not None and client_config.contacts is not None
                    else []
                ),
                "escalation_schedule": [],
                "business_hours_applied": False,
                "confidence_level": "unknown",
                "special_handling": ["fallback_routing"],
                "error": "Normal routing failed, using fallback",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Fallback routing failed for {client_id}: {e}")
            return {
                "client_id": client_id,
                "category": classification.get("category", "general"),
                "primary_destination": "admin@example.com",  # Hard fallback
                "backup_destinations": [],
                "escalation_schedule": [],
                "business_hours_applied": False,
                "confidence_level": "unknown",
                "special_handling": ["hard_fallback"],
                "error": "All routing methods failed",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _capture_routing_analytics(
        self,
        client_id: str,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        routing_result: Dict[str, Any],
        start_time: datetime,
        routing_start: Optional[datetime],
    ) -> None:
        """
        Capture routing analytics data for analysis.

        Args:
            client_id: Client identifier
            email_data: Original email data
            classification: AI classification results
            routing_result: Routing decision details
            start_time: When processing started
            routing_start: When routing logic started
        """
        if not self.analytics_repository:
            # Analytics not enabled, skip capture
            return

        try:
            end_time = datetime.utcnow()

            # Calculate performance metrics
            total_time_ms = int((end_time - start_time).total_seconds() * 1000)
            routing_time_ms = None
            if routing_start:
                routing_time_ms = int((end_time - routing_start).total_seconds() * 1000)

            # Get classification timing if available
            classification_time_ms = classification.get("processing_time_ms")

            # Build analytics data structure
            analytics_data = {
                "client_id": client_id,
                "email_data": {
                    "sender": email_data.get("sender", ""),
                    "subject": email_data.get("subject", ""),
                    "message_id": email_data.get("message_id"),
                    "email_id": email_data.get("email_id"),
                },
                "classification": classification,
                "routing_result": {
                    "category": routing_result.get("category"),
                    "forward_to": routing_result.get("primary_destination"),
                    "cc": routing_result.get("backup_destinations"),
                    "special_handling": routing_result.get("special_handling"),
                    "escalated": routing_result.get("escalation_schedule") is not None,
                    "priority": routing_result.get("confidence_level"),
                    "fallback_used": routing_result.get("fallback_used", False),
                    "version": "1.0",  # Routing engine version
                },
                "performance_metrics": {
                    "total_time_ms": total_time_ms,
                    "classification_time_ms": classification_time_ms,
                    "routing_time_ms": routing_time_ms,
                },
                "metadata": {
                    "business_hours_applied": routing_result.get(
                        "business_hours_applied", False
                    ),
                    "confidence_level": routing_result.get("confidence_level"),
                    "timestamp": routing_result.get("timestamp"),
                },
                "routed_at": end_time,
                "error_occurred": False,
            }

            # Capture the analytics asynchronously (fire and forget)
            try:
                import asyncio

                # Try to run async method in background
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule the task
                    loop.create_task(
                        self.analytics_repository.save_routing_decision(analytics_data)
                    )
                else:
                    # Run sync
                    asyncio.run(
                        self.analytics_repository.save_routing_decision(analytics_data)
                    )
            except Exception as async_error:
                logger.warning(
                    f"Failed to capture routing analytics asynchronously: {async_error}"
                )
                # Could implement a queue-based fallback here

        except Exception as e:
            logger.warning(f"Failed to capture routing analytics for {client_id}: {e}")
            # Don't let analytics failure affect the main routing flow

    def get_routing_analytics(
        self, client_id: str, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get routing analytics for a client.

        Args:
            client_id: Client identifier
            time_period_hours: Time period for analytics

        Returns:
            Routing analytics data
        """
        # Analytics implementation placeholder - would require database models for tracking
        # routing decisions, escalations, response times, etc.
        return {
            "client_id": client_id,
            "time_period_hours": time_period_hours,
            "total_emails": 0,
            "routing_breakdown": {},
            "escalations": 0,
            "avg_confidence": 0.0,
            "special_handling_count": 0,
        }


_routing_engine_instance: Optional[RoutingEngine] = None


def get_routing_engine() -> RoutingEngine:
    """Dependency injection function for RoutingEngine."""
    global _routing_engine_instance
    if _routing_engine_instance is None:
        from ..clients.manager import get_client_manager

        client_manager = get_client_manager()

        # Try to get analytics repository, but don't fail if not available
        analytics_repository = None
        try:
            from infrastructure.adapters.analytics_repository_impl import (
                SQLAlchemyAnalyticsRepository,
            )
            from infrastructure.database.connection import get_database_session

            db_session = get_database_session()
            analytics_repository = SQLAlchemyAnalyticsRepository(next(db_session))
        except Exception as e:
            logger.warning(f"Analytics repository not available: {e}")
            # Continue without analytics - it's optional

        _routing_engine_instance = RoutingEngine(client_manager, analytics_repository)
    return _routing_engine_instance
