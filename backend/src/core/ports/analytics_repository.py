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


class AnalyticsError(Exception):
    """Exception raised for analytics repository errors."""

    pass
