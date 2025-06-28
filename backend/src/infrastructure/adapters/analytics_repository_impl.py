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
                cc_destinations=(
                    routing_result.get("cc", []) if routing_result.get("cc") else None
                ),
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
                classification_time_ms=performance_metrics.get(
                    "classification_time_ms"
                ),
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
            routing_records = (
                query.order_by(desc(RoutingHistory.routed_at)).limit(limit).all()
            )

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
                and_(
                    RoutingHistory.client_id == client_id,
                    RoutingHistory.routed_at >= start_time,
                )
            )

            # Total emails count
            total_emails = base_query.count()

            # Routing breakdown by category
            category_breakdown = {}
            category_stats = (
                base_query.with_entities(
                    RoutingHistory.category,
                    func.count(RoutingHistory.id).label("count"),
                )
                .group_by(RoutingHistory.category)
                .all()
            )

            for category, count in category_stats:
                category_breakdown[category] = count

            # Average confidence (exclude None values)
            avg_confidence_result = (
                base_query.filter(RoutingHistory.confidence_level.isnot(None))
                .with_entities(
                    func.avg(RoutingHistory.confidence_level).label("avg_confidence")
                )
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
            fallback_rate = (
                (fallback_count / total_emails * 100) if total_emails > 0 else 0.0
            )

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
                func.avg(RoutingHistory.processing_time_ms).label(
                    "avg_processing_time"
                ),
                func.avg(RoutingHistory.classification_time_ms).label(
                    "avg_classification_time"
                ),
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
