"""
Unit tests for DashboardService trend calculation logic.

Tests the comprehensive trend analysis functionality with mock analytics data.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.clients.manager import ClientManager
from core.dashboard.service import DashboardService
from core.ports.analytics_repository import AnalyticsRepository
from core.ports.config_provider import ConfigurationProvider


class MockAnalyticsRepository:
    """Mock analytics repository for testing trend calculations."""

    def __init__(self):
        self.mock_data = self._setup_mock_data()

    def _setup_mock_data(self) -> Dict[str, Any]:
        """Set up comprehensive mock data for trend analysis."""
        return {
            "routing_volume_by_category": {"support": 45, "billing": 12, "sales": 8, "general": 23},
            "average_processing_time": 2500.5,
            "error_rate": 1.2,
            "confidence_distribution": {
                "very_high": 45,
                "high": 32,
                "medium": 18,
                "low": 5,
                "very_low": 2,
            },
            "hourly_volume_pattern": {
                9: 15,
                10: 23,
                11: 18,
                12: 12,
                13: 8,
                14: 31,
                15: 25,
                16: 20,
                17: 12,
            },
            "daily_volume_trend": {
                "2024-01-15": 45,
                "2024-01-16": 52,
                "2024-01-17": 38,
                "2024-01-18": 61,
                "2024-01-19": 47,
            },
            "top_sender_domains": [
                {"domain": "example.com", "count": 45, "percentage": 25.0},
                {"domain": "partner.com", "count": 30, "percentage": 16.7},
                {"domain": "client.com", "count": 25, "percentage": 13.9},
            ],
            "escalation_metrics": {
                "total_escalations": 12,
                "escalation_rate": 2.5,
                "by_category": {"support": 8, "billing": 4},
                "by_priority": {"urgent": 6, "high": 4, "medium": 2},
            },
            "period_comparison": {
                "current_period": {
                    "total_emails": 150,
                    "avg_processing_time": 2500.0,
                    "error_rate": 1.2,
                    "escalation_rate": 2.8,
                },
                "previous_period": {
                    "total_emails": 125,
                    "avg_processing_time": 2800.0,
                    "error_rate": 2.1,
                    "escalation_rate": 3.5,
                },
                "changes": {
                    "total_emails": {"value": 25, "percentage": 20.0},
                    "avg_processing_time": {"value": -300.0, "percentage": -10.7},
                    "error_rate": {"value": -0.9, "percentage": -42.9},
                    "escalation_rate": {"value": -0.7, "percentage": -20.0},
                },
            },
        }

    async def get_routing_volume_by_category(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        return self.mock_data["routing_volume_by_category"]

    async def get_average_processing_time(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        return self.mock_data["average_processing_time"]

    async def get_error_rate(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        return self.mock_data["error_rate"]

    async def get_confidence_distribution(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        return self.mock_data["confidence_distribution"]

    async def get_hourly_volume_pattern(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[int, int]:
        return self.mock_data["hourly_volume_pattern"]

    async def get_daily_volume_trend(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        return self.mock_data["daily_volume_trend"]

    async def get_top_sender_domains(
        self, client_id: str, start_date: datetime, end_date: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        return self.mock_data["top_sender_domains"]

    async def get_escalation_metrics(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        return self.mock_data["escalation_metrics"]

    async def get_period_comparison(
        self,
        client_id: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> Dict[str, Any]:
        return self.mock_data["period_comparison"]


@pytest.fixture
def mock_config_provider():
    """Mock configuration provider."""
    config_provider = MagicMock()
    return config_provider


@pytest.fixture
def mock_client_manager():
    """Mock client manager."""
    client_manager = MagicMock()
    client_manager.get_available_clients.return_value = ["test-client-001"]
    return client_manager


@pytest.fixture
def mock_analytics_repository():
    """Mock analytics repository with test data."""
    return MockAnalyticsRepository()


@pytest.fixture
def dashboard_service_with_analytics(
    mock_config_provider, mock_client_manager, mock_analytics_repository
):
    """Create DashboardService with analytics repository."""
    return DashboardService(
        config_provider=mock_config_provider,
        client_manager=mock_client_manager,
        analytics_repository=mock_analytics_repository,
    )


@pytest.fixture
def dashboard_service_without_analytics(mock_config_provider, mock_client_manager):
    """Create DashboardService without analytics repository for fallback testing."""
    return DashboardService(
        config_provider=mock_config_provider,
        client_manager=mock_client_manager,
        analytics_repository=None,
    )


class TestDashboardTrendAnalysis:
    """Test suite for dashboard trend analysis functionality."""

    @pytest.mark.asyncio
    async def test_calculate_dashboard_trends_with_analytics(
        self, dashboard_service_with_analytics
    ):
        """Test calculate_dashboard_trends with analytics repository available."""
        client_id = "test-client-001"
        timeframe = "24h"

        result = await dashboard_service_with_analytics.calculate_dashboard_trends(
            client_id, timeframe
        )

        # Verify structure
        assert "volume_metrics" in result
        assert "performance_metrics" in result
        assert "quality_metrics" in result
        assert "escalation_metrics" in result
        assert "trends" in result
        assert "timeframe" in result
        assert "period" in result

        # Verify volume metrics
        volume = result["volume_metrics"]
        assert "total_emails" in volume
        assert "by_category" in volume
        assert "daily_average" in volume
        assert volume["total_emails"] == 88  # sum of category volumes

        # Verify performance metrics
        performance = result["performance_metrics"]
        assert "avg_processing_time_ms" in performance
        assert "success_rate" in performance
        assert "error_rate" in performance
        assert performance["avg_processing_time_ms"] == 2500.5
        assert performance["error_rate"] == 1.2

        # Verify quality metrics
        quality = result["quality_metrics"]
        assert "confidence_distribution" in quality
        assert "high_confidence_rate" in quality

        # Verify escalation metrics
        escalation = result["escalation_metrics"]
        assert "total_escalations" in escalation
        assert "escalation_rate" in escalation
        assert escalation["total_escalations"] == 12

    @pytest.mark.asyncio
    async def test_calculate_dashboard_trends_fallback_mode(
        self, dashboard_service_without_analytics
    ):
        """Test calculate_dashboard_trends fallback when analytics repository unavailable."""
        client_id = "test-client-001"
        timeframe = "24h"

        result = await dashboard_service_without_analytics.calculate_dashboard_trends(
            client_id, timeframe
        )

        # Verify fallback structure
        assert "volume_metrics" in result
        assert "performance_metrics" in result
        assert "quality_metrics" in result
        assert "note" in result  # Instead of "source"

        # Verify fallback data
        volume = result["volume_metrics"]
        assert volume["total_emails"] == 0
        assert isinstance(volume["by_category"], dict)

    @pytest.mark.asyncio
    async def test_get_volume_patterns(self, dashboard_service_with_analytics):
        """Test volume pattern analysis."""
        client_id = "test-client-001"
        timeframe = "7d"

        result = await dashboard_service_with_analytics.get_volume_patterns(client_id, timeframe)

        # Verify structure
        assert "hourly_pattern" in result
        assert "daily_trend" in result
        assert "insights" in result
        assert "timeframe" in result

        # Verify hourly pattern
        hourly = result["hourly_pattern"]
        assert isinstance(hourly, dict)
        assert len(hourly) == 9  # Hours 9-17 from mock data

        # Verify insights
        insights = result["insights"]
        assert "peak_hour" in insights
        assert "quietest_hour" in insights
        assert "business_hours_percentage" in insights
        assert "after_hours_percentage" in insights
        assert "total_volume" in insights

        # Peak hour should be 14 (highest volume in mock data)
        assert insights["peak_hour"] == 14

    @pytest.mark.asyncio
    async def test_get_sender_analytics(self, dashboard_service_with_analytics):
        """Test sender domain analytics."""
        client_id = "test-client-001"
        timeframe = "30d"

        result = await dashboard_service_with_analytics.get_sender_analytics(client_id, timeframe)

        # Verify structure
        assert "top_domains" in result
        assert "insights" in result
        assert "timeframe" in result

        # Verify top domains
        top_domains = result["top_domains"]
        assert isinstance(top_domains, list)
        assert len(top_domains) == 3  # From mock data
        assert top_domains[0]["domain"] == "example.com"
        assert top_domains[0]["count"] == 45

        # Verify insights
        insights = result["insights"]
        assert "total_unique_domains" in insights
        assert "top_domain_share" in insights
        assert "top_3_concentration" in insights
        assert "diversity_score" in insights
        assert insights["total_unique_domains"] == 3

    @pytest.mark.asyncio
    async def test_get_performance_insights(self, dashboard_service_with_analytics):
        """Test performance insights generation."""
        client_id = "test-client-001"
        timeframe = "24h"

        result = await dashboard_service_with_analytics.get_performance_insights(
            client_id, timeframe
        )

        # Verify structure
        assert "processing_performance" in result
        assert "quality_performance" in result
        assert "escalation_performance" in result
        assert "overall_grade" in result
        assert "recommendations" in result
        assert "insights" in result
        assert "timeframe" in result

        # Verify processing performance
        processing = result["processing_performance"]
        assert "avg_time_ms" in processing
        assert "grade" in processing
        assert "benchmark" in processing
        assert processing["avg_time_ms"] == 2500.5

        # Verify quality performance
        quality = result["quality_performance"]
        assert "confidence_score" in quality
        assert "error_rate" in quality
        assert "success_rate" in quality
        assert quality["error_rate"] == 1.2

        # Verify escalation performance
        escalation = result["escalation_performance"]
        assert "total_escalations" in escalation
        assert "escalation_rate" in escalation
        assert escalation["escalation_rate"] == 2.5
        assert escalation["total_escalations"] == 12

        # Verify overall grade
        assert result["overall_grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

        # Verify recommendations
        recommendations = result["recommendations"]
        assert isinstance(recommendations, list)

        # Verify insights
        insights = result["insights"]
        assert "total_emails_analyzed" in insights
        assert "performance_trend" in insights
        assert "strongest_metric" in insights
        assert "improvement_area" in insights

    @pytest.mark.asyncio
    async def test_performance_grading_algorithm(self, dashboard_service_with_analytics):
        """Test the performance grading algorithm with different scenarios."""
        service = dashboard_service_with_analytics

        # Test excellent performance (should get A+ or A)
        grade_a = service._calculate_performance_grade(1500.0, 0.5, 85.0, 1.0)
        assert grade_a in ["A+", "A"]

        # Test poor performance (should get F)
        grade_f = service._calculate_performance_grade(8000.0, 15.0, 45.0, 8.0)
        assert grade_f == "F"

        # Test average performance (should get C+ or C)
        grade_c = service._calculate_performance_grade(3500.0, 3.0, 75.0, 3.5)
        assert grade_c in ["C+", "C", "B"]

    @pytest.mark.asyncio
    async def test_fallback_data_structure(self, dashboard_service_without_analytics):
        """Test that fallback data maintains consistent structure."""

        result = await dashboard_service_without_analytics.calculate_dashboard_trends(
            "test-client", "24h"
        )

        # Verify all required keys are present
        required_keys = [
            "volume_metrics",
            "performance_metrics",
            "quality_metrics",
            "escalation_metrics",
            "trends",
            "timeframe",
        ]

        for key in required_keys:
            assert key in result

        # Verify nested structure
        assert "total_emails" in result["volume_metrics"]
        assert "avg_processing_time_ms" in result["performance_metrics"]
        assert "error_rate" in result["performance_metrics"]
        assert "note" in result

    @pytest.mark.asyncio
    async def test_error_handling_in_trend_calculation(self, dashboard_service_with_analytics):
        """Test error handling when analytics repository fails."""

        # Create a service with a failing analytics repository
        failing_repo = AsyncMock()
        failing_repo.get_routing_volume_by_category.side_effect = Exception("Database error")

        service = DashboardService(
            config_provider=MagicMock(),
            client_manager=MagicMock(),
            analytics_repository=failing_repo,
        )

        # Should fall back gracefully when analytics fail
        result = await service.calculate_dashboard_trends("test-client", "24h")

        # Should return fallback data structure
        assert "note" in result
        assert "Analytics repository unavailable" in result["note"]
        assert "volume_metrics" in result

    @pytest.mark.asyncio
    async def test_timeframe_parsing(self, dashboard_service_with_analytics):
        """Test different timeframe formats are handled correctly."""
        service = dashboard_service_with_analytics

        # Test standard timeframes
        for timeframe in ["1h", "24h", "7d", "30d"]:
            result = await service.calculate_dashboard_trends("test-client", timeframe)
            assert result["timeframe"] == timeframe
            assert "period" in result

    @pytest.mark.asyncio
    async def test_empty_analytics_data_handling(self, dashboard_service_with_analytics):
        """Test handling when analytics return empty/zero data."""

        # Create analytics repo that returns empty data
        empty_repo = MockAnalyticsRepository()
        empty_repo.mock_data = {
            "routing_volume_by_category": {},
            "average_processing_time": 0.0,
            "error_rate": 0.0,
            "confidence_distribution": {},
            "hourly_volume_pattern": {},
            "daily_volume_trend": {},
            "top_sender_domains": [],
            "escalation_metrics": {
                "total_escalations": 0,
                "escalation_rate": 0.0,
                "by_category": {},
                "by_priority": {},
            },
            "period_comparison": {
                "current_period": {
                    "total_emails": 0,
                    "avg_processing_time": 0.0,
                    "error_rate": 0.0,
                    "escalation_rate": 0.0,
                },
                "previous_period": {
                    "total_emails": 0,
                    "avg_processing_time": 0.0,
                    "error_rate": 0.0,
                    "escalation_rate": 0.0,
                },
                "changes": {},
            },
        }

        service = DashboardService(
            config_provider=MagicMock(), client_manager=MagicMock(), analytics_repository=empty_repo
        )

        result = await service.calculate_dashboard_trends("test-client", "24h")

        # Should handle empty data gracefully
        assert result["volume_metrics"]["total_emails"] == 0
        assert result["performance_metrics"]["avg_processing_time_ms"] == 0.0
        assert result["performance_metrics"]["error_rate"] == 0.0
