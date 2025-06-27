"""
End-to-end integration tests for trend analysis functionality.

Tests the complete workflow from analytics repository through dashboard service
to ensure proper integration and data flow.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.dashboard.service import DashboardService
from infrastructure.adapters.analytics_repository_impl import SQLAlchemyAnalyticsRepository
from infrastructure.database.models import Base, RoutingHistory


class TestTrendAnalysisEndToEnd:
    """End-to-end tests for trend analysis functionality."""

    @pytest.fixture(scope="function")
    def e2e_db_session(self):
        """Create isolated database session for E2E testing."""
        # Create in-memory database for testing
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()

    @pytest.fixture
    def analytics_repository(self, e2e_db_session):
        """Create real analytics repository with test database."""
        return SQLAlchemyAnalyticsRepository(e2e_db_session)

    @pytest.fixture
    def dashboard_service(self, analytics_repository):
        """Create dashboard service with real analytics repository."""
        from unittest.mock import MagicMock

        mock_config_provider = MagicMock()
        mock_client_manager = MagicMock()
        mock_client_manager.get_available_clients.return_value = ["test-client-001"]

        return DashboardService(
            config_provider=mock_config_provider,
            client_manager=mock_client_manager,
            analytics_repository=analytics_repository,
        )

    @pytest.fixture
    def sample_routing_data(self, e2e_db_session):
        """Create sample routing history data for testing."""
        client_id = "test-client-001"
        now = datetime.utcnow()

        # Create diverse routing history data over the past 7 days
        routing_records = []

        # Day 1: High volume, good performance
        base_time = now - timedelta(days=6)
        for hour in range(9, 18):  # Business hours
            for i in range(5):  # 5 emails per hour
                record = RoutingHistory(
                    client_id=client_id,
                    sender_email=f"user{i}@example.com",
                    sender_domain="example.com",
                    subject=f"Test email {i}",
                    category="support" if i < 3 else "billing" if i < 4 else "sales",
                    primary_destination="team@client.com",
                    confidence_level=0.85 + (i * 0.03),  # Good confidence
                    ai_model="claude-3-5-sonnet",
                    classification_method="ai",
                    escalated=i == 4,  # One escalation per hour
                    processing_time_ms=2000 + (i * 200),  # Good processing times
                    classification_time_ms=1500 + (i * 100),
                    routing_time_ms=500 + (i * 50),
                    business_hours=True,
                    day_of_week=base_time.strftime("%A"),
                    error_occurred=False,
                    fallback_used=False,
                    routed_at=base_time.replace(hour=hour, minute=i * 10),
                    created_at=base_time.replace(hour=hour, minute=i * 10),
                )
                routing_records.append(record)

        # Day 2: Lower volume, some errors
        base_time = now - timedelta(days=5)
        for hour in range(10, 16):  # Shorter business day
            for i in range(3):  # 3 emails per hour
                record = RoutingHistory(
                    client_id=client_id,
                    sender_email=f"customer{i}@partner.com",
                    sender_domain="partner.com",
                    subject=f"Partner email {i}",
                    category="general" if i < 2 else "support",
                    primary_destination="team@client.com",
                    confidence_level=0.75 + (i * 0.05),  # Lower confidence
                    ai_model="claude-3-5-sonnet",
                    classification_method="ai",
                    escalated=i == 2,
                    processing_time_ms=3000 + (i * 500),  # Slower processing
                    classification_time_ms=2000 + (i * 200),
                    routing_time_ms=1000 + (i * 100),
                    business_hours=True,
                    day_of_week=base_time.strftime("%A"),
                    error_occurred=i == 2,  # Some errors
                    fallback_used=i == 2,
                    routed_at=base_time.replace(hour=hour, minute=i * 15),
                    created_at=base_time.replace(hour=hour, minute=i * 15),
                )
                routing_records.append(record)

        # Day 3: After-hours activity
        base_time = now - timedelta(days=4)
        for hour in [20, 21, 22]:  # Evening hours
            for i in range(2):  # 2 emails per hour
                record = RoutingHistory(
                    client_id=client_id,
                    sender_email=f"urgent{i}@client.com",
                    sender_domain="client.com",
                    subject=f"Urgent request {i}",
                    category="support",
                    primary_destination="oncall@client.com",
                    confidence_level=0.90 + (i * 0.02),  # High confidence for urgent
                    ai_model="claude-3-5-sonnet",
                    classification_method="ai",
                    escalated=True,  # All after-hours are escalated
                    priority_level="urgent",
                    processing_time_ms=1800 + (i * 100),  # Fast urgent processing
                    classification_time_ms=1200 + (i * 50),
                    routing_time_ms=600 + (i * 25),
                    business_hours=False,
                    day_of_week=base_time.strftime("%A"),
                    error_occurred=False,
                    fallback_used=False,
                    routed_at=base_time.replace(hour=hour, minute=i * 20),
                    created_at=base_time.replace(hour=hour, minute=i * 20),
                )
                routing_records.append(record)

        # Add all records to database
        for record in routing_records:
            e2e_db_session.add(record)
        e2e_db_session.commit()

        return {
            "total_records": len(routing_records),
            "client_id": client_id,
            "date_range": {"start": now - timedelta(days=6), "end": now},
        }

    @pytest.mark.asyncio
    async def test_complete_trend_analysis_workflow(self, dashboard_service, sample_routing_data):
        """Test complete trend analysis workflow with real data."""
        client_id = sample_routing_data["client_id"]

        # Test 1: Calculate dashboard trends
        trends = await dashboard_service.calculate_dashboard_trends(client_id, "7d")

        # Verify structure and data presence
        assert "volume_metrics" in trends
        assert "performance_metrics" in trends
        assert "quality_metrics" in trends
        assert "escalation_metrics" in trends
        assert "trends" in trends

        # Verify volume metrics show real data
        volume = trends["volume_metrics"]
        assert volume["total_emails"] > 0
        assert len(volume["by_category"]) > 0
        assert "support" in volume["by_category"]  # Should have support emails

        # Verify performance metrics are calculated
        performance = trends["performance_metrics"]
        assert performance["avg_processing_time_ms"] > 0
        assert 0 <= performance["error_rate"] <= 100
        assert 0 <= performance["success_rate"] <= 100

        # Verify quality metrics
        quality = trends["quality_metrics"]
        assert len(quality["confidence_distribution"]) > 0
        assert 0 <= quality["high_confidence_rate"] <= 100

        print(f"✅ Dashboard trends calculated: {volume['total_emails']} emails processed")

    @pytest.mark.asyncio
    async def test_volume_patterns_analysis(self, dashboard_service, sample_routing_data):
        """Test volume pattern analysis with real data."""
        client_id = sample_routing_data["client_id"]

        patterns = await dashboard_service.get_volume_patterns(client_id, "7d")

        # Verify structure
        assert "hourly_pattern" in patterns
        assert "daily_trend" in patterns
        assert "insights" in patterns

        # Verify hourly pattern shows business hours activity
        hourly = patterns["hourly_pattern"]
        business_hours_volume = sum(hourly.get(h, 0) for h in range(9, 18))
        after_hours_volume = sum(hourly.get(h, 0) for h in list(range(0, 9)) + list(range(18, 24)))

        assert business_hours_volume > 0  # Should have business hours activity

        # Verify insights
        insights = patterns["insights"]
        assert "peak_hour" in insights
        assert "business_hours_percentage" in insights
        assert insights["total_volume"] > 0

        print(
            f"✅ Volume patterns analyzed: Peak hour {insights['peak_hour']}, {insights['business_hours_percentage']}% during business hours"
        )

    @pytest.mark.asyncio
    async def test_sender_analytics_with_real_data(self, dashboard_service, sample_routing_data):
        """Test sender analytics with real domain data."""
        client_id = sample_routing_data["client_id"]

        sender_analytics = await dashboard_service.get_sender_analytics(client_id, "7d")

        # Verify structure
        assert "top_domains" in sender_analytics
        assert "insights" in sender_analytics

        # Verify top domains
        top_domains = sender_analytics["top_domains"]
        assert len(top_domains) > 0

        # Should have example.com, partner.com, client.com from test data
        domain_names = [domain["domain"] for domain in top_domains]
        assert "example.com" in domain_names

        # Verify insights
        insights = sender_analytics["insights"]
        assert insights["total_unique_domains"] >= 3  # At least 3 domains in test data
        assert 0 <= insights["diversity_score"] <= 100

        print(
            f"✅ Sender analytics calculated: {len(top_domains)} domains, diversity score {insights['diversity_score']}"
        )

    @pytest.mark.asyncio
    async def test_performance_insights_integration(self, dashboard_service, sample_routing_data):
        """Test performance insights with real performance data."""
        client_id = sample_routing_data["client_id"]

        insights = await dashboard_service.get_performance_insights(client_id, "7d")

        # Verify structure
        assert "processing_performance" in insights
        assert "quality_performance" in insights
        assert "escalation_performance" in insights
        assert "overall_grade" in insights
        assert "recommendations" in insights

        # Verify processing performance
        processing = insights["processing_performance"]
        assert processing["avg_time_ms"] > 0
        assert processing["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

        # Verify quality performance
        quality = insights["quality_performance"]
        assert 0 <= quality["confidence_score"] <= 100
        assert 0 <= quality["error_rate"] <= 100

        # Verify escalation performance
        escalation = insights["escalation_performance"]
        assert escalation["total_escalations"] > 0  # Test data includes escalations
        assert escalation["escalation_rate"] > 0

        # Verify recommendations are generated
        recommendations = insights["recommendations"]
        assert isinstance(recommendations, list)

        print(
            f"✅ Performance insights generated: Grade {insights['overall_grade']}, {len(recommendations)} recommendations"
        )

    @pytest.mark.asyncio
    async def test_analytics_repository_methods_directly(
        self, analytics_repository, sample_routing_data
    ):
        """Test analytics repository methods directly to ensure data flow."""
        client_id = sample_routing_data["client_id"]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Test volume by category
        volume_by_category = await analytics_repository.get_routing_volume_by_category(
            client_id, start_date, end_date
        )
        assert len(volume_by_category) > 0
        assert "support" in volume_by_category

        # Test average processing time
        avg_time = await analytics_repository.get_average_processing_time(
            client_id, start_date, end_date
        )
        assert avg_time > 0

        # Test error rate
        error_rate = await analytics_repository.get_error_rate(client_id, start_date, end_date)
        assert 0 <= error_rate <= 100

        # Test confidence distribution
        confidence_dist = await analytics_repository.get_confidence_distribution(
            client_id, start_date, end_date
        )
        assert len(confidence_dist) > 0

        # Test hourly volume pattern
        hourly_pattern = await analytics_repository.get_hourly_volume_pattern(
            client_id, start_date, end_date
        )
        assert len(hourly_pattern) > 0

        # Test escalation metrics
        escalation_metrics = await analytics_repository.get_escalation_metrics(
            client_id, start_date, end_date
        )
        assert escalation_metrics["total_escalations"] > 0

        print(
            f"✅ Analytics repository methods validated: {sum(volume_by_category.values())} total emails"
        )

    @pytest.mark.asyncio
    async def test_period_comparison_functionality(self, analytics_repository, sample_routing_data):
        """Test period comparison calculations."""
        client_id = sample_routing_data["client_id"]
        end_date = datetime.utcnow()
        current_start = end_date - timedelta(days=3)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=3)

        comparison = await analytics_repository.get_period_comparison(
            client_id, current_start, end_date, previous_start, previous_end
        )

        # Verify structure
        assert "current_period" in comparison
        assert "previous_period" in comparison
        assert "changes" in comparison

        # Verify period data
        current = comparison["current_period"]
        previous = comparison["previous_period"]

        assert "total_emails" in current
        assert "avg_processing_time" in current
        assert "error_rate" in current
        assert "escalation_rate" in current

        # Verify changes calculation
        changes = comparison["changes"]
        if current["total_emails"] > 0 and previous["total_emails"] > 0:
            assert "total_emails" in changes
            email_change = changes["total_emails"]
            assert "value" in email_change
            assert "percentage" in email_change

        print(
            f"✅ Period comparison calculated: Current {current['total_emails']} vs Previous {previous['total_emails']} emails"
        )

    @pytest.mark.asyncio
    async def test_empty_data_handling(self, dashboard_service):
        """Test handling of client with no data."""
        # Test with non-existent client
        empty_client_id = "non-existent-client"

        trends = await dashboard_service.calculate_dashboard_trends(empty_client_id, "24h")

        # Should handle gracefully with zero data
        assert trends["volume_metrics"]["total_emails"] == 0
        assert trends["performance_metrics"]["avg_processing_time_ms"] == 0.0
        assert trends["performance_metrics"]["error_rate"] == 0.0

        print("✅ Empty data handling verified")

    @pytest.mark.asyncio
    async def test_different_timeframes(self, dashboard_service, sample_routing_data):
        """Test different timeframe calculations."""
        client_id = sample_routing_data["client_id"]

        timeframes = ["1h", "24h", "7d", "30d"]

        for timeframe in timeframes:
            trends = await dashboard_service.calculate_dashboard_trends(client_id, timeframe)

            assert trends["timeframe"] == timeframe
            assert "period" in trends
            assert "hours" in trends["period"]

            # Verify timeframe affects period calculation
            expected_hours = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
            assert trends["period"]["hours"] == expected_hours[timeframe]

        print(f"✅ All timeframes tested: {', '.join(timeframes)}")
