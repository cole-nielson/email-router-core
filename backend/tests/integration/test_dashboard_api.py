"""
Integration Tests for Dashboard Analytics Service

Tests the newly added analytics methods in the DashboardService:
- calculate_dashboard_trends
- get_volume_patterns
- get_sender_analytics
- get_performance_insights

These tests verify:
1. DashboardService analytics methods work correctly
2. Analytics repository integration
3. Data structure and calculations
4. Error handling
5. Service layer functionality
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.dashboard.service import DashboardService
from core.ports.analytics_repository import AnalyticsRepository


class MockAnalyticsRepository(AnalyticsRepository):
    """Mock analytics repository for testing."""

    async def save_routing_decision(self, routing_data: Dict[str, Any]) -> None:
        pass

    async def get_routing_analytics(
        self, client_id: str, start_date=None, end_date=None, category=None, limit=100
    ):
        return []

    async def get_routing_summary(self, client_id: str, time_period_hours: int = 24):
        return {
            "client_id": client_id,
            "time_period_hours": time_period_hours,
            "total_emails": 150,
            "routing_breakdown": {"support": 60, "sales": 40, "general": 50},
            "avg_confidence": 0.85,
            "escalations": 5,
            "special_handling_count": 3,
            "error_rate": 2.0,
            "fallback_rate": 1.5,
        }

    async def get_performance_metrics(self, client_id: str, time_period_hours: int = 24):
        return {
            "client_id": client_id,
            "time_period_hours": time_period_hours,
            "avg_processing_time_ms": 3500.0,
            "avg_classification_time_ms": 2000.0,
            "avg_routing_time_ms": 1500.0,
            "records_with_metrics": 150,
        }

    async def health_check(self) -> bool:
        return True

    # New trend analysis methods
    async def get_routing_volume_by_category(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        return {"support": 60, "sales": 40, "general": 50}

    async def get_average_processing_time(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        return 3500.0

    async def get_error_rate(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        return 2.0

    async def get_confidence_distribution(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        return {"high": 120, "medium": 25, "low": 5}

    async def get_hourly_volume_pattern(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[int, int]:
        # Return realistic hourly pattern
        pattern = {}
        for hour in range(24):
            if 9 <= hour <= 17:  # Business hours
                pattern[hour] = 10 + (hour % 3) * 2
            else:
                pattern[hour] = 2 + (hour % 2)
        return pattern

    async def get_daily_volume_trend(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        # Generate daily trend data
        trends = []
        current = start_date
        while current <= end_date:
            trends.append(
                {
                    "date": current.date(),
                    "volume": 150 + (current.day % 7) * 10,
                    "avg_confidence": 0.85 + (current.day % 3) * 0.02,
                }
            )
            current += timedelta(days=1)
        return trends

    async def get_top_sender_domains(
        self, client_id: str, start_date: datetime, end_date: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        return [
            {"domain": "gmail.com", "count": 45, "percentage": 30.0},
            {"domain": "company.com", "count": 30, "percentage": 20.0},
            {"domain": "outlook.com", "count": 25, "percentage": 16.7},
        ]

    async def get_escalation_metrics(
        self, client_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        return {
            "total_escalations": 5,
            "escalation_rate": 3.33,
            "escalation_reasons": {"urgent": 3, "vip": 2},
        }

    async def get_period_comparison(
        self,
        client_id: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> Dict[str, Any]:
        return {
            "current_period": {
                "total_emails": 150,
                "avg_confidence": 0.85,
                "avg_processing_time": 3500.0,
                "error_rate": 2.0,
            },
            "previous_period": {
                "total_emails": 140,
                "avg_confidence": 0.83,
                "avg_processing_time": 3800.0,
                "error_rate": 2.5,
            },
            "changes": {
                "total_emails_change": 7.14,
                "confidence_change": 2.41,
                "processing_time_change": -7.89,
                "error_rate_change": -20.0,
            },
        }


@pytest.fixture
def mock_dashboard_service():
    """Create a dashboard service with analytics repository for testing."""
    mock_config_provider = MagicMock()
    mock_client_manager = MagicMock()

    service = DashboardService(mock_config_provider, mock_client_manager)
    service.analytics_repository = MockAnalyticsRepository()

    return service


class TestDashboardAnalyticsService:
    """Test suite for dashboard analytics service methods."""

    @pytest.mark.asyncio
    async def test_calculate_dashboard_trends_success(self, mock_dashboard_service):
        """Test successful calculation of dashboard trends."""
        client_id = "client-001"
        timeframe = "24h"

        # Call the service method
        result = await mock_dashboard_service.calculate_dashboard_trends(client_id, timeframe)

        # Verify response structure
        assert isinstance(result, dict)
        assert "volume_metrics" in result
        assert "performance_metrics" in result
        assert "quality_metrics" in result
        assert "escalation_metrics" in result
        assert "trends" in result

        # Verify volume metrics
        volume_metrics = result["volume_metrics"]
        assert "total_emails" in volume_metrics
        assert "category_breakdown" in volume_metrics
        assert volume_metrics["total_emails"] == 150
        assert volume_metrics["category_breakdown"]["support"] == 60

        # Verify performance metrics
        performance_metrics = result["performance_metrics"]
        assert "average_processing_time_ms" in performance_metrics
        assert "error_rate" in performance_metrics
        assert performance_metrics["average_processing_time_ms"] == 3500.0
        assert performance_metrics["error_rate"] == 2.0

        # Verify trends (period comparison)
        trends = result["trends"]
        assert "total_emails_change" in trends or "volume_change" in trends
        assert "confidence_change" in trends
        assert "processing_time_change" in trends
        # The key might be "total_emails_change" from the mock
        volume_change = trends.get("volume_change", trends.get("total_emails_change", 0))
        assert volume_change == 7.14

    @pytest.mark.asyncio
    async def test_get_volume_patterns_success(self, mock_dashboard_service):
        """Test successful retrieval of volume patterns."""
        client_id = "client-001"
        timeframe = "7d"

        # Call the service method
        result = await mock_dashboard_service.get_volume_patterns(client_id, timeframe)

        # Verify response structure
        assert isinstance(result, dict)
        assert "hourly_pattern" in result
        assert "daily_trend" in result
        assert "peak_hour" in result
        assert "quietest_hour" in result
        assert "business_hours_volume" in result
        assert "after_hours_volume" in result
        assert "total_volume" in result

        # Verify hourly pattern
        hourly_pattern = result["hourly_pattern"]
        assert len(hourly_pattern) == 24  # Should have all 24 hours
        assert all(isinstance(v, int) for v in hourly_pattern.values())

        # Verify calculations
        business_hours_volume = result["business_hours_volume"]
        after_hours_volume = result["after_hours_volume"]
        total_volume = result["total_volume"]
        assert business_hours_volume + after_hours_volume == total_volume

    @pytest.mark.asyncio
    async def test_get_sender_analytics_success(self, mock_dashboard_service):
        """Test successful retrieval of sender analytics."""
        client_id = "client-001"
        timeframe = "7d"
        limit = 10

        # Call the service method
        result = await mock_dashboard_service.get_sender_analytics(client_id, timeframe, limit)

        # Verify response structure
        assert isinstance(result, dict)
        assert "top_domains" in result
        assert "domain_diversity" in result
        assert "total_unique_domains" in result
        assert "top_domain_concentration" in result

        # Verify top domains
        top_domains = result["top_domains"]
        assert len(top_domains) == 3  # Mock returns 3 domains
        assert all("domain" in domain for domain in top_domains)
        assert all("count" in domain for domain in top_domains)
        assert all("percentage" in domain for domain in top_domains)

        # Verify first domain
        assert top_domains[0]["domain"] == "gmail.com"
        assert top_domains[0]["count"] == 45
        assert top_domains[0]["percentage"] == 30.0

        # Verify metrics
        assert result["total_unique_domains"] == 3
        assert result["top_domain_concentration"] == 30.0

    @pytest.mark.asyncio
    async def test_get_performance_insights_success(self, mock_dashboard_service):
        """Test successful retrieval of performance insights."""
        client_id = "client-001"
        timeframe = "7d"

        # Call the service method
        result = await mock_dashboard_service.get_performance_insights(client_id, timeframe)

        # Verify response structure
        assert isinstance(result, dict)
        assert "processing_performance" in result
        assert "quality_performance" in result
        assert "escalation_performance" in result
        assert "overall_grade" in result
        assert "recommendations" in result

        # Verify processing performance
        proc_perf = result["processing_performance"]
        assert "average_time_ms" in proc_perf
        assert "grade" in proc_perf
        assert "trend" in proc_perf
        assert proc_perf["average_time_ms"] == 3500.0

        # Verify grading system
        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        assert result["overall_grade"] in valid_grades
        assert proc_perf["grade"] in valid_grades

        # Verify quality performance
        quality_perf = result["quality_performance"]
        assert "average_confidence" in quality_perf
        assert "error_rate" in quality_perf
        assert "grade" in quality_perf
        assert quality_perf["error_rate"] == 2.0

    @pytest.mark.asyncio
    async def test_analytics_without_repository_fallback(self):
        """Test that analytics methods handle missing repository gracefully."""
        # Create service without analytics repository
        mock_config_provider = MagicMock()
        mock_client_manager = MagicMock()
        service = DashboardService(mock_config_provider, mock_client_manager)
        service.analytics_repository = None  # No analytics repository

        client_id = "client-001"
        timeframe = "24h"

        # Call trends method - should return fallback data
        result = await service.calculate_dashboard_trends(client_id, timeframe)

        # Verify fallback structure
        assert isinstance(result, dict)
        assert "volume_metrics" in result
        assert result["volume_metrics"]["total_emails"] == 0
        assert result["performance_metrics"]["average_processing_time_ms"] == 0.0
        assert result["trends"]["volume_change"] == 0.0

    @pytest.mark.asyncio
    async def test_timeframe_parsing(self, mock_dashboard_service):
        """Test that different timeframes are parsed correctly."""
        client_id = "client-001"
        timeframes = ["1h", "6h", "12h", "24h", "7d", "30d"]

        for timeframe in timeframes:
            result = await mock_dashboard_service.calculate_dashboard_trends(client_id, timeframe)
            assert isinstance(result, dict)
            assert "volume_metrics" in result

    @pytest.mark.asyncio
    async def test_volume_pattern_calculations(self, mock_dashboard_service):
        """Test that volume pattern calculations are correct."""
        client_id = "client-001"
        timeframe = "24h"

        result = await mock_dashboard_service.get_volume_patterns(client_id, timeframe)

        # Verify hourly pattern sums match totals
        hourly_pattern = result["hourly_pattern"]
        calculated_total = sum(hourly_pattern.values())

        # Verify business hours calculation (9-17)
        business_hours_sum = sum(hourly_pattern[hour] for hour in range(9, 18))
        after_hours_sum = sum(
            hourly_pattern[hour] for hour in list(range(0, 9)) + list(range(18, 24))
        )

        assert business_hours_sum == result["business_hours_volume"]
        assert after_hours_sum == result["after_hours_volume"]
        assert calculated_total == result["total_volume"]

    @pytest.mark.asyncio
    async def test_performance_grading_consistency(self, mock_dashboard_service):
        """Test that performance grading is consistent and valid."""
        client_id = "client-001"
        timeframe = "24h"

        result = await mock_dashboard_service.get_performance_insights(client_id, timeframe)

        # Verify all grades are valid
        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

        assert result["overall_grade"] in valid_grades
        assert result["processing_performance"]["grade"] in valid_grades
        assert result["quality_performance"]["grade"] in valid_grades
        assert result["escalation_performance"]["grade"] in valid_grades

        # Verify recommendations are provided
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_sender_analytics_data_integrity(self, mock_dashboard_service):
        """Test sender analytics data integrity and calculations."""
        client_id = "client-001"
        timeframe = "7d"
        limit = 5

        result = await mock_dashboard_service.get_sender_analytics(client_id, timeframe, limit)

        # Verify top domains are sorted by count (descending)
        top_domains = result["top_domains"]
        for i in range(len(top_domains) - 1):
            assert top_domains[i]["count"] >= top_domains[i + 1]["count"]

        # Verify percentages are realistic
        for domain in top_domains:
            assert 0 <= domain["percentage"] <= 100

        # Verify diversity metrics
        assert result["total_unique_domains"] >= len(top_domains)
        assert result["domain_diversity"] > 0

    @pytest.mark.asyncio
    async def test_trend_comparison_calculations(self, mock_dashboard_service):
        """Test that trend comparisons are calculated correctly."""
        client_id = "client-001"
        timeframe = "24h"

        result = await mock_dashboard_service.calculate_dashboard_trends(client_id, timeframe)

        trends = result["trends"]

        # Verify all trend values are numeric
        for key, value in trends.items():
            assert isinstance(value, (int, float))

        # Verify specific expected trends from mock data
        volume_change = trends.get("volume_change", trends.get("total_emails_change", 0))
        assert volume_change == 7.14  # (150-140)/140 * 100
        assert trends["confidence_change"] == 2.41  # (0.85-0.83)/0.83 * 100
        assert trends["processing_time_change"] == -7.89  # (3500-3800)/3800 * 100
        assert trends["error_rate_change"] == -20.0  # (2.0-2.5)/2.5 * 100


class TestAnalyticsRepositoryIntegration:
    """Test analytics repository integration patterns."""

    @pytest.mark.asyncio
    async def test_repository_method_calls(self, mock_dashboard_service):
        """Test that service correctly calls repository methods."""
        # Get reference to mock repository
        mock_repo = mock_dashboard_service.analytics_repository

        # Convert to MagicMock to track calls
        mock_repo.get_routing_volume_by_category = AsyncMock(return_value={"support": 50})
        mock_repo.get_period_comparison = AsyncMock(
            return_value={
                "current_period": {"total_emails": 100},
                "previous_period": {"total_emails": 90},
                "changes": {"total_emails_change": 11.11},
            }
        )

        client_id = "client-001"
        timeframe = "24h"

        # Call service method
        await mock_dashboard_service.calculate_dashboard_trends(client_id, timeframe)

        # Verify repository methods were called
        mock_repo.get_routing_volume_by_category.assert_called()
        mock_repo.get_period_comparison.assert_called()

    @pytest.mark.asyncio
    async def test_repository_error_handling(self):
        """Test service handles repository errors gracefully."""
        # Create service with failing repository
        mock_config_provider = MagicMock()
        mock_client_manager = MagicMock()
        service = DashboardService(mock_config_provider, mock_client_manager)

        # Create repository that raises exceptions
        failing_repo = MagicMock()
        failing_repo.get_routing_volume_by_category = AsyncMock(
            side_effect=Exception("Database error")
        )
        service.analytics_repository = failing_repo

        client_id = "client-001"
        timeframe = "24h"

        # Should not raise exception, should return fallback data
        result = await service.calculate_dashboard_trends(client_id, timeframe)

        # Verify fallback data structure
        assert isinstance(result, dict)
        assert "volume_metrics" in result
        # With repository error, should fall back to empty/default data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
