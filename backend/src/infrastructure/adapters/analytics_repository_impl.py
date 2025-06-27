"""
SQLAlchemy Analytics Repository Implementation

Concrete implementation of the AnalyticsRepository interface using SQLAlchemy
for persistence to relational databases.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.ports.analytics_repository import AnalyticsError, AnalyticsRepository
from infrastructure.database.models import RoutingHistory

logger = logging.getLogger(__name__)


class SQLAlchemyAnalyticsRepository(AnalyticsRepository):
    """
    SQLAlchemy implementation of the AnalyticsRepository interface.

    Provides persistence for routing analytics data using SQLAlchemy ORM
    with comprehensive error handling and performance optimization.
    """

    def __init__(self, db_session: Session):
        """
        Initialize the repository with a database session.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    async def save_routing_decision(self, routing_data: Dict[str, Any]) -> None:
        """
        Save a routing decision to the database.

        Args:
            routing_data: Dictionary containing routing decision data

        Raises:
            AnalyticsError: If the routing decision cannot be saved
        """
        try:
            # Extract data with defaults
            email_data = routing_data.get("email_data", {})
            classification = routing_data.get("classification", {})
            routing_result = routing_data.get("routing_result", {})
            performance_metrics = routing_data.get("performance_metrics", {})
            metadata = routing_data.get("metadata", {})

            # Extract sender domain from email
            sender_email = email_data.get("sender", "")
            sender_domain = None
            if "@" in sender_email:
                sender_domain = sender_email.split("@")[1].lower()

            # Get current time info
            now = datetime.utcnow()
            day_of_week = now.strftime("%A")

            # Determine if during business hours (9 AM - 5 PM UTC for now)
            # TODO: Use client-specific timezone and business hours
            business_hours = 9 <= now.hour < 17

            # Create routing history record
            routing_history = RoutingHistory(
                # Email identification
                email_id=email_data.get("email_id"),
                message_id=email_data.get("message_id"),
                # Client context
                client_id=routing_data.get("client_id"),
                # Email details
                sender_email=sender_email,
                sender_domain=sender_domain,
                subject=email_data.get("subject", "")[:500],  # Truncate to field limit
                # Routing decision
                category=classification.get("category", "general"),
                primary_destination=routing_result.get("forward_to", ""),
                cc_destinations=routing_result.get("cc", []) if routing_result.get("cc") else None,
                # AI classification data
                confidence_level=classification.get("confidence"),
                ai_model=classification.get("ai_model"),
                classification_method=classification.get("method", "ai"),
                # Special handling
                special_handling=routing_result.get("special_handling"),
                escalated=routing_result.get("escalated", False),
                priority_level=routing_result.get("priority"),
                # Routing performance
                processing_time_ms=performance_metrics.get("total_time_ms"),
                classification_time_ms=performance_metrics.get("classification_time_ms"),
                routing_time_ms=performance_metrics.get("routing_time_ms"),
                # Business context
                business_hours=business_hours,
                day_of_week=day_of_week,
                # Routing metadata
                routing_version=routing_result.get("version"),
                fallback_used=routing_result.get("fallback_used", False),
                error_occurred=routing_data.get("error_occurred", False),
                error_details=routing_data.get("error_details"),
                # Additional metadata
                additional_metadata=metadata if metadata else None,
                # Timestamps
                routed_at=routing_data.get("routed_at", now),
            )

            # Save to database
            self.db_session.add(routing_history)
            self.db_session.commit()

            logger.debug(
                f"Saved routing decision for client {routing_data.get('client_id')} "
                f"with category {classification.get('category')}"
            )

        except SQLAlchemyError as e:
            self.db_session.rollback()
            error_msg = f"Failed to save routing decision: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e
        except Exception as e:
            self.db_session.rollback()
            error_msg = f"Unexpected error saving routing decision: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_routing_analytics(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve routing analytics data for a client.

        Args:
            client_id: Client identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            category: Optional category filter
            limit: Maximum number of records to return

        Returns:
            List of routing analytics records
        """
        try:
            query = self.db_session.query(RoutingHistory).filter(
                RoutingHistory.client_id == client_id
            )

            # Apply date filters
            if start_date:
                query = query.filter(RoutingHistory.routed_at >= start_date)
            if end_date:
                query = query.filter(RoutingHistory.routed_at <= end_date)
            if category:
                query = query.filter(RoutingHistory.category == category)

            # Order by most recent first and limit
            routing_records = query.order_by(desc(RoutingHistory.routed_at)).limit(limit).all()

            # Convert to dictionaries
            result = []
            for record in routing_records:
                result.append(
                    {
                        "id": record.id,
                        "email_id": record.email_id,
                        "message_id": record.message_id,
                        "sender_email": record.sender_email,
                        "sender_domain": record.sender_domain,
                        "subject": record.subject,
                        "category": record.category,
                        "primary_destination": record.primary_destination,
                        "cc_destinations": record.cc_destinations,
                        "confidence_level": record.confidence_level,
                        "ai_model": record.ai_model,
                        "classification_method": record.classification_method,
                        "special_handling": record.special_handling,
                        "escalated": record.escalated,
                        "priority_level": record.priority_level,
                        "processing_time_ms": record.processing_time_ms,
                        "classification_time_ms": record.classification_time_ms,
                        "routing_time_ms": record.routing_time_ms,
                        "business_hours": record.business_hours,
                        "day_of_week": record.day_of_week,
                        "routing_version": record.routing_version,
                        "fallback_used": record.fallback_used,
                        "error_occurred": record.error_occurred,
                        "error_details": record.error_details,
                        "metadata": record.additional_metadata,
                        "routed_at": record.routed_at.isoformat(),
                        "created_at": record.created_at.isoformat(),
                    }
                )

            return result

        except SQLAlchemyError as e:
            error_msg = f"Failed to retrieve routing analytics: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_routing_summary(
        self, client_id: str, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get routing summary statistics for a client.

        Args:
            client_id: Client identifier
            time_period_hours: Time period for analytics in hours

        Returns:
            Dictionary containing summary statistics
        """
        try:
            # Calculate time boundary
            start_time = datetime.utcnow() - timedelta(hours=time_period_hours)

            # Base query for the time period
            base_query = self.db_session.query(RoutingHistory).filter(
                and_(RoutingHistory.client_id == client_id, RoutingHistory.routed_at >= start_time)
            )

            # Total emails count
            total_emails = base_query.count()

            # Routing breakdown by category
            category_breakdown = {}
            category_stats = (
                base_query.with_entities(
                    RoutingHistory.category, func.count(RoutingHistory.id).label("count")
                )
                .group_by(RoutingHistory.category)
                .all()
            )

            for category, count in category_stats:
                category_breakdown[category] = count

            # Average confidence (exclude None values)
            avg_confidence_result = (
                base_query.filter(RoutingHistory.confidence_level.isnot(None))
                .with_entities(func.avg(RoutingHistory.confidence_level).label("avg_confidence"))
                .first()
            )
            avg_confidence = (
                float(avg_confidence_result.avg_confidence)
                if avg_confidence_result.avg_confidence
                else 0.0
            )

            # Escalations count
            escalations = base_query.filter(RoutingHistory.escalated).count()

            # Special handling count
            special_handling_count = base_query.filter(
                RoutingHistory.special_handling.isnot(None)
            ).count()

            # Error rate
            error_count = base_query.filter(RoutingHistory.error_occurred).count()
            error_rate = (error_count / total_emails * 100) if total_emails > 0 else 0.0

            # Fallback usage
            fallback_count = base_query.filter(RoutingHistory.fallback_used).count()
            fallback_rate = (fallback_count / total_emails * 100) if total_emails > 0 else 0.0

            return {
                "client_id": client_id,
                "time_period_hours": time_period_hours,
                "total_emails": total_emails,
                "routing_breakdown": category_breakdown,
                "avg_confidence": round(avg_confidence, 3),
                "escalations": escalations,
                "special_handling_count": special_handling_count,
                "error_rate": round(error_rate, 2),
                "fallback_rate": round(fallback_rate, 2),
            }

        except SQLAlchemyError as e:
            error_msg = f"Failed to get routing summary: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_performance_metrics(
        self, client_id: str, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get performance metrics for routing decisions.

        Args:
            client_id: Client identifier
            time_period_hours: Time period for metrics in hours

        Returns:
            Dictionary containing performance metrics
        """
        try:
            # Calculate time boundary
            start_time = datetime.utcnow() - timedelta(hours=time_period_hours)

            # Base query for the time period with non-null performance metrics
            perf_query = self.db_session.query(RoutingHistory).filter(
                and_(
                    RoutingHistory.client_id == client_id,
                    RoutingHistory.routed_at >= start_time,
                    RoutingHistory.processing_time_ms.isnot(None),
                )
            )

            # Calculate averages
            performance_stats = perf_query.with_entities(
                func.avg(RoutingHistory.processing_time_ms).label("avg_processing_time"),
                func.avg(RoutingHistory.classification_time_ms).label("avg_classification_time"),
                func.avg(RoutingHistory.routing_time_ms).label("avg_routing_time"),
                func.count(RoutingHistory.id).label("total_with_metrics"),
            ).first()

            avg_processing_time = (
                float(performance_stats.avg_processing_time)
                if performance_stats.avg_processing_time
                else 0.0
            )
            avg_classification_time = (
                float(performance_stats.avg_classification_time)
                if performance_stats.avg_classification_time
                else 0.0
            )
            avg_routing_time = (
                float(performance_stats.avg_routing_time)
                if performance_stats.avg_routing_time
                else 0.0
            )

            return {
                "client_id": client_id,
                "time_period_hours": time_period_hours,
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "avg_classification_time_ms": round(avg_classification_time, 2),
                "avg_routing_time_ms": round(avg_routing_time, 2),
                "records_with_metrics": performance_stats.total_with_metrics,
            }

        except SQLAlchemyError as e:
            error_msg = f"Failed to get performance metrics: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def health_check(self) -> bool:
        """
        Check if the analytics repository is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple query to test database connectivity
            self.db_session.execute("SELECT 1")
            return True
        except Exception:
            return False

    # =============================================================================
    # TREND ANALYSIS IMPLEMENTATION
    # =============================================================================

    async def get_routing_volume_by_category(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Get email routing volume grouped by category for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping category names to email counts
        """
        try:
            # Query volume by category using SQLAlchemy aggregation
            volume_stats = (
                self.db_session.query(
                    RoutingHistory.category, func.count(RoutingHistory.id).label("count")
                )
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                    )
                )
                .group_by(RoutingHistory.category)
                .all()
            )

            # Convert to dictionary
            volume_by_category = {}
            for category, count in volume_stats:
                volume_by_category[category] = count

            return volume_by_category

        except SQLAlchemyError as e:
            error_msg = f"Failed to get routing volume by category: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_average_processing_time(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Get average email processing time for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Average processing time in milliseconds
        """
        try:
            # Query average processing time with null filtering
            avg_result = (
                self.db_session.query(func.avg(RoutingHistory.processing_time_ms).label("avg_time"))
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                        RoutingHistory.processing_time_ms.isnot(None),
                    )
                )
                .first()
            )

            return float(avg_result.avg_time) if avg_result.avg_time else 0.0

        except SQLAlchemyError as e:
            error_msg = f"Failed to get average processing time: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_error_rate(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Get error rate percentage for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Error rate as percentage (0.0 to 100.0)
        """
        try:
            # Base query for the time period
            base_query = self.db_session.query(RoutingHistory).filter(
                and_(
                    RoutingHistory.client_id == client_id,
                    RoutingHistory.routed_at >= start_date,
                    RoutingHistory.routed_at <= end_date,
                )
            )

            # Count total and error emails
            total_emails = base_query.count()
            error_emails = base_query.filter(RoutingHistory.error_occurred).count()

            # Calculate error rate percentage
            error_rate = (error_emails / total_emails * 100) if total_emails > 0 else 0.0
            return round(error_rate, 2)

        except SQLAlchemyError as e:
            error_msg = f"Failed to get error rate: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_confidence_distribution(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Get distribution of AI confidence levels for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping confidence ranges to counts
        """
        try:
            # Query all confidence levels within the period
            confidence_records = (
                self.db_session.query(RoutingHistory.confidence_level)
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                        RoutingHistory.confidence_level.isnot(None),
                    )
                )
                .all()
            )

            # Categorize confidence levels and count
            distribution = {
                "very_high": 0,  # >= 0.9
                "high": 0,  # 0.7-0.89
                "medium": 0,  # 0.5-0.69
                "low": 0,  # 0.3-0.49
                "very_low": 0,  # < 0.3
            }

            for (confidence,) in confidence_records:
                if confidence >= 0.9:
                    distribution["very_high"] += 1
                elif confidence >= 0.7:
                    distribution["high"] += 1
                elif confidence >= 0.5:
                    distribution["medium"] += 1
                elif confidence >= 0.3:
                    distribution["low"] += 1
                else:
                    distribution["very_low"] += 1

            return distribution

        except SQLAlchemyError as e:
            error_msg = f"Failed to get confidence distribution: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_hourly_volume_pattern(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[int, int]:
        """
        Get email volume by hour of day for pattern analysis.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping hour (0-23) to email counts
        """
        try:
            # Extract hour and count using SQLAlchemy func.extract
            hourly_stats = (
                self.db_session.query(
                    func.extract("hour", RoutingHistory.routed_at).label("hour"),
                    func.count(RoutingHistory.id).label("count"),
                )
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                    )
                )
                .group_by(func.extract("hour", RoutingHistory.routed_at))
                .all()
            )

            # Initialize all hours with 0, then fill in actual data
            hourly_pattern = {hour: 0 for hour in range(24)}
            for hour, count in hourly_stats:
                hourly_pattern[int(hour)] = count

            return hourly_pattern

        except SQLAlchemyError as e:
            error_msg = f"Failed to get hourly volume pattern: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_daily_volume_trend(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Get daily email volume for trend analysis.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to email counts
        """
        try:
            # Extract date and count using SQLAlchemy func.date
            daily_stats = (
                self.db_session.query(
                    func.date(RoutingHistory.routed_at).label("date"),
                    func.count(RoutingHistory.id).label("count"),
                )
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                    )
                )
                .group_by(func.date(RoutingHistory.routed_at))
                .order_by(func.date(RoutingHistory.routed_at))
                .all()
            )

            # Convert to dictionary with string dates
            daily_trend = {}
            for date_obj, count in daily_stats:
                # Handle SQLite returning string dates vs other DBs returning date objects
                if isinstance(date_obj, str):
                    date_str = date_obj  # SQLite already returns YYYY-MM-DD format
                else:
                    date_str = date_obj.strftime("%Y-%m-%d")  # Other databases
                daily_trend[date_str] = count

            return daily_trend

        except SQLAlchemyError as e:
            error_msg = f"Failed to get daily volume trend: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_top_sender_domains(
        self, client_id: str, start_date: datetime, end_date: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top sender domains by email volume.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period
            limit: Maximum number of domains to return

        Returns:
            List of dictionaries with domain info
        """
        try:
            # Query sender domains with counts
            domain_stats = (
                self.db_session.query(
                    RoutingHistory.sender_domain, func.count(RoutingHistory.id).label("count")
                )
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                        RoutingHistory.sender_domain.isnot(None),
                    )
                )
                .group_by(RoutingHistory.sender_domain)
                .order_by(desc(func.count(RoutingHistory.id)))
                .limit(limit)
                .all()
            )

            # Get total count for percentage calculation
            total_count = (
                self.db_session.query(func.count(RoutingHistory.id))
                .filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                        RoutingHistory.sender_domain.isnot(None),
                    )
                )
                .scalar()
            )

            # Build result with percentages
            top_domains = []
            for domain, count in domain_stats:
                percentage = (count / total_count * 100) if total_count > 0 else 0.0
                top_domains.append(
                    {"domain": domain, "count": count, "percentage": round(percentage, 1)}
                )

            return top_domains

        except SQLAlchemyError as e:
            error_msg = f"Failed to get top sender domains: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_escalation_metrics(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get escalation statistics and patterns.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary containing escalation metrics
        """
        try:
            # Base query for the period
            base_query = self.db_session.query(RoutingHistory).filter(
                and_(
                    RoutingHistory.client_id == client_id,
                    RoutingHistory.routed_at >= start_date,
                    RoutingHistory.routed_at <= end_date,
                )
            )

            # Total emails and escalations
            total_emails = base_query.count()
            total_escalations = base_query.filter(RoutingHistory.escalated).count()

            # Escalation rate
            escalation_rate = (total_escalations / total_emails * 100) if total_emails > 0 else 0.0

            # Escalations by category
            escalations_by_category = {}
            category_escalation_stats = (
                base_query.filter(RoutingHistory.escalated)
                .with_entities(
                    RoutingHistory.category, func.count(RoutingHistory.id).label("count")
                )
                .group_by(RoutingHistory.category)
                .all()
            )
            for category, count in category_escalation_stats:
                escalations_by_category[category] = count

            # Escalations by priority
            escalations_by_priority = {}
            priority_escalation_stats = (
                base_query.filter(RoutingHistory.escalated)
                .with_entities(
                    RoutingHistory.priority_level, func.count(RoutingHistory.id).label("count")
                )
                .group_by(RoutingHistory.priority_level)
                .all()
            )
            for priority, count in priority_escalation_stats:
                if priority:  # Skip None values
                    escalations_by_priority[priority] = count

            return {
                "total_escalations": total_escalations,
                "escalation_rate": round(escalation_rate, 2),
                "by_category": escalations_by_category,
                "by_priority": escalations_by_priority,
            }

        except SQLAlchemyError as e:
            error_msg = f"Failed to get escalation metrics: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e

    async def get_period_comparison(
        self,
        client_id: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> Dict[str, Any]:
        """
        Compare metrics between two time periods for trend analysis.

        Args:
            client_id: Client identifier
            current_start: Start of current period
            current_end: End of current period
            previous_start: Start of previous period
            previous_end: End of previous period

        Returns:
            Dictionary containing period comparison with change calculations
        """
        try:
            # Helper function to get period metrics
            def get_period_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
                period_query = self.db_session.query(RoutingHistory).filter(
                    and_(
                        RoutingHistory.client_id == client_id,
                        RoutingHistory.routed_at >= start_date,
                        RoutingHistory.routed_at <= end_date,
                    )
                )

                # Total emails
                total_emails = period_query.count()

                # Average processing time
                avg_time_result = (
                    period_query.filter(RoutingHistory.processing_time_ms.isnot(None))
                    .with_entities(func.avg(RoutingHistory.processing_time_ms))
                    .scalar()
                )
                avg_processing_time = float(avg_time_result) if avg_time_result else 0.0

                # Error rate
                error_count = period_query.filter(RoutingHistory.error_occurred).count()
                error_rate = (error_count / total_emails * 100) if total_emails > 0 else 0.0

                # Escalation rate
                escalation_count = period_query.filter(RoutingHistory.escalated).count()
                escalation_rate = (
                    (escalation_count / total_emails * 100) if total_emails > 0 else 0.0
                )

                return {
                    "total_emails": total_emails,
                    "avg_processing_time": round(avg_processing_time, 1),
                    "error_rate": round(error_rate, 2),
                    "escalation_rate": round(escalation_rate, 2),
                }

            # Get metrics for both periods
            current_metrics = get_period_metrics(current_start, current_end)
            previous_metrics = get_period_metrics(previous_start, previous_end)

            # Calculate changes
            changes = {}
            for metric in current_metrics.keys():
                current_val = current_metrics[metric]
                previous_val = previous_metrics[metric]

                # Calculate absolute and percentage change
                absolute_change = current_val - previous_val
                percentage_change = (
                    (absolute_change / previous_val * 100) if previous_val != 0 else 0.0
                )

                changes[metric] = {
                    "value": round(absolute_change, 2),
                    "percentage": round(percentage_change, 1),
                }

            return {
                "current_period": current_metrics,
                "previous_period": previous_metrics,
                "changes": changes,
            }

        except SQLAlchemyError as e:
            error_msg = f"Failed to get period comparison: {e}"
            logger.error(error_msg)
            raise AnalyticsError(error_msg) from e
