"""Analytics Repository Interface.

This module defines the abstract interface for analytics data persistence,
following the Dependency Inversion Principle. The core business logic depends
on this abstraction rather than concrete implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class AnalyticsRepository(ABC):
    """Abstract interface for analytics data persistence.

    This interface defines the contract that any analytics repository
    must implement to be used by the core business logic layer.
    It abstracts away the details of how analytics data is stored,
    retrieved, and managed.
    """

    @abstractmethod
    async def save_routing_decision(self, routing_data: Dict[str, Any]) -> None:
        """Save a routing decision to the analytics store.

        Args:
            routing_data: Dictionary containing routing decision data including:
                - client_id: Client identifier
                - email_data: Original email information
                - classification: AI classification results
                - routing_result: Routing decision details
                - performance_metrics: Processing time data
                - metadata: Additional context data

        Raises:
            AnalyticsError: If the routing decision cannot be saved
        """
        pass

    @abstractmethod
    async def get_routing_analytics(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve routing analytics data for a client.

        Args:
            client_id: Client identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            category: Optional category filter (support, billing, etc.)
            limit: Maximum number of records to return

        Returns:
            List of routing analytics records

        Raises:
            AnalyticsError: If analytics data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_routing_summary(
        self, client_id: str, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get routing summary statistics for a client.

        Args:
            client_id: Client identifier
            time_period_hours: Time period for analytics in hours

        Returns:
            Dictionary containing summary statistics:
                - total_emails: Total number of emails processed
                - routing_breakdown: Count by category
                - avg_confidence: Average AI confidence score
                - escalations: Number of escalated emails
                - special_handling_count: Number with special handling
                - performance_metrics: Processing time statistics

        Raises:
            AnalyticsError: If summary data cannot be calculated
        """
        pass

    @abstractmethod
    async def get_performance_metrics(
        self, client_id: str, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for routing decisions.

        Args:
            client_id: Client identifier
            time_period_hours: Time period for metrics in hours

        Returns:
            Dictionary containing performance metrics:
                - avg_processing_time_ms: Average total processing time
                - avg_classification_time_ms: Average AI classification time
                - avg_routing_time_ms: Average routing decision time
                - error_rate: Percentage of failed routing decisions
                - fallback_rate: Percentage using fallback routing

        Raises:
            AnalyticsError: If performance metrics cannot be calculated
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the analytics repository is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        pass

    # =============================================================================
    # TREND ANALYSIS METHODS
    # =============================================================================

    @abstractmethod
    async def get_routing_volume_by_category(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """Get email routing volume grouped by category for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping category names to email counts:
                {"support": 45, "billing": 12, "sales": 8, "general": 23}

        Raises:
            AnalyticsError: If volume data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_average_processing_time(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Get average email processing time for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Average processing time in milliseconds

        Raises:
            AnalyticsError: If processing time data cannot be calculated
        """
        pass

    @abstractmethod
    async def get_error_rate(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Get error rate percentage for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Error rate as percentage (0.0 to 100.0)

        Raises:
            AnalyticsError: If error rate cannot be calculated
        """
        pass

    @abstractmethod
    async def get_confidence_distribution(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """Get distribution of AI confidence levels for a time period.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping confidence ranges to counts:
                {"very_high": 45, "high": 32, "medium": 18, "low": 5, "very_low": 2}

        Raises:
            AnalyticsError: If confidence distribution cannot be calculated
        """
        pass

    @abstractmethod
    async def get_hourly_volume_pattern(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[int, int]:
        """Get email volume by hour of day for pattern analysis.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping hour (0-23) to email counts:
                {9: 15, 10: 23, 11: 18, 14: 31, ...}

        Raises:
            AnalyticsError: If hourly pattern data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_daily_volume_trend(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """Get daily email volume for trend analysis.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to email counts:
                {"2024-01-15": 45, "2024-01-16": 52, "2024-01-17": 38}

        Raises:
            AnalyticsError: If daily trend data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_top_sender_domains(
        self, client_id: str, start_date: datetime, end_date: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top sender domains by email volume.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period
            limit: Maximum number of domains to return

        Returns:
            List of dictionaries with domain info:
                [{"domain": "example.com", "count": 45, "percentage": 12.5}, ...]

        Raises:
            AnalyticsError: If sender domain data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_escalation_metrics(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get escalation statistics and patterns.

        Args:
            client_id: Client identifier
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary containing escalation metrics:
                {
                    "total_escalations": 12,
                    "escalation_rate": 2.5,
                    "by_category": {"support": 8, "billing": 4},
                    "by_priority": {"urgent": 6, "high": 4, "medium": 2}
                }

        Raises:
            AnalyticsError: If escalation metrics cannot be calculated
        """
        pass

    @abstractmethod
    async def get_period_comparison(
        self,
        client_id: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> Dict[str, Any]:
        """Compare metrics between two time periods for trend analysis.

        Args:
            client_id: Client identifier
            current_start: Start of current period
            current_end: End of current period
            previous_start: Start of previous period
            previous_end: End of previous period

        Returns:
            Dictionary containing period comparison:
                {
                    "current_period": {
                        "total_emails": 150,
                        "avg_processing_time": 2500.0,
                        "error_rate": 1.2,
                        "escalation_rate": 2.8
                    },
                    "previous_period": {
                        "total_emails": 125,
                        "avg_processing_time": 2800.0,
                        "error_rate": 2.1,
                        "escalation_rate": 3.5
                    },
                    "changes": {
                        "total_emails": {"value": 25, "percentage": 20.0},
                        "avg_processing_time": {"value": -300.0, "percentage": -10.7},
                        "error_rate": {"value": -0.9, "percentage": -42.9},
                        "escalation_rate": {"value": -0.7, "percentage": -20.0}
                    }
                }

        Raises:
            AnalyticsError: If period comparison cannot be calculated
        """
        pass


class AnalyticsError(Exception):
    """Exception raised for analytics repository errors."""

    pass
