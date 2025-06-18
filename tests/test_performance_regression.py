"""
Performance regression tests for the core email processing pipeline.
🚀 Tests performance characteristics to catch regressions in response times and throughput.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from app.services.ai_classifier import get_ai_classifier
from app.services.client_manager import ClientManager, get_client_manager
from app.services.email_service import EmailService, get_email_service
from app.services.routing_engine import get_routing_engine

# import psutil  # Not available in this environment
# import os


class TestPerformanceBenchmarks:
    """Performance benchmarks for core services."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.test_email_data = {
            "from": "customer@example.com",
            "to": "support@colenielson.dev",
            "subject": "Performance test email",
            "body_text": "This is a performance test email with some content to process.",
            "stripped_text": "This is a performance test email with some content to process.",
        }

        self.test_classification = {
            "category": "support",
            "confidence": 0.92,
            "reasoning": "Performance test classification",
        }

    def test_client_identification_performance(self):
        """Test client identification performance."""

        client_manager = get_client_manager()

        # Test single identification performance
        start_time = time.time()

        for _ in range(100):
            result = client_manager.identify_client_by_email("support@colenielson.dev")
            assert result.is_successful

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100

        # Should average under 5ms per identification (including caching benefits)
        assert (
            avg_time < 0.005
        ), f"Client identification too slow: {avg_time:.4f}s avg (should be <0.005s)"

        print(f"✅ Client identification: {avg_time:.4f}s avg for 100 operations")

    def test_config_loading_performance(self):
        """Test configuration loading performance."""

        client_manager = get_client_manager()

        # Test config loading performance (should benefit from caching)
        start_time = time.time()

        for _ in range(50):
            config = client_manager.get_client_config("client-001-cole-nielson")
            assert config.client.id == "client-001-cole-nielson"

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50

        # Should average under 10ms per config load (with caching)
        assert avg_time < 0.01, f"Config loading too slow: {avg_time:.4f}s avg (should be <0.01s)"

        print(f"✅ Config loading: {avg_time:.4f}s avg for 50 operations")

    @pytest.mark.asyncio
    async def test_ai_classification_mock_performance(self):
        """Test AI classification performance with mocked AI service."""

        classifier = get_ai_classifier()

        # Mock AI service for consistent timing
        with patch.object(classifier, "_call_ai_service") as mock_ai:
            mock_ai.return_value = self.test_classification

            # Test classification performance
            times = []

            for _ in range(20):
                start_time = time.time()

                result = await classifier.classify_email(
                    self.test_email_data, "client-001-cole-nielson"
                )

                end_time = time.time()
                times.append(end_time - start_time)

                assert result["category"] == "support"

            avg_time = statistics.mean(times)
            max_time = max(times)

            # Should average under 50ms per classification (excluding actual AI call)
            assert (
                avg_time < 0.05
            ), f"AI classification too slow: {avg_time:.4f}s avg (should be <0.05s)"
            assert (
                max_time < 0.1
            ), f"AI classification max time too slow: {max_time:.4f}s (should be <0.1s)"

            print(
                f"✅ AI classification (mocked): {avg_time:.4f}s avg, {max_time:.4f}s max for 20 operations"
            )

    @pytest.mark.asyncio
    async def test_email_generation_performance(self):
        """Test email content generation performance."""

        email_service = get_email_service()

        # Mock AI service calls
        with patch.object(email_service, "_call_ai_service") as mock_ai:
            mock_ai.return_value = "Thank you for contacting us. We'll respond within 4 hours."

            # Test customer acknowledgment generation
            ack_times = []

            for _ in range(15):
                start_time = time.time()

                acknowledgment = await email_service.generate_customer_acknowledgment(
                    self.test_email_data, self.test_classification, "client-001-cole-nielson"
                )

                end_time = time.time()
                ack_times.append(end_time - start_time)

                assert isinstance(acknowledgment, str)
                assert len(acknowledgment) > 0

            # Test team analysis generation
            analysis_times = []

            for _ in range(15):
                start_time = time.time()

                analysis = await email_service.generate_team_analysis(
                    self.test_email_data, self.test_classification, "client-001-cole-nielson"
                )

                end_time = time.time()
                analysis_times.append(end_time - start_time)

                assert isinstance(analysis, str)
                assert len(analysis) > 0

            ack_avg = statistics.mean(ack_times)
            analysis_avg = statistics.mean(analysis_times)

            # Should average under 30ms per generation (excluding AI call)
            assert ack_avg < 0.03, f"Acknowledgment generation too slow: {ack_avg:.4f}s avg"
            assert analysis_avg < 0.03, f"Analysis generation too slow: {analysis_avg:.4f}s avg"

            print(
                f"✅ Email generation: {ack_avg:.4f}s acknowledgment, {analysis_avg:.4f}s analysis avg"
            )

    def test_routing_engine_performance(self):
        """Test routing engine performance."""

        routing_engine = get_routing_engine()

        # Test routing performance
        times = []

        for _ in range(100):
            start_time = time.time()

            result = routing_engine.route_email(
                "client-001-cole-nielson", self.test_classification, self.test_email_data
            )

            end_time = time.time()
            times.append(end_time - start_time)

            assert "primary_destination" in result

        avg_time = statistics.mean(times)
        max_time = max(times)

        # Should average under 5ms per routing decision
        assert avg_time < 0.005, f"Routing too slow: {avg_time:.4f}s avg (should be <0.005s)"
        assert max_time < 0.02, f"Routing max time too slow: {max_time:.4f}s (should be <0.02s)"

        print(f"✅ Routing engine: {avg_time:.4f}s avg, {max_time:.4f}s max for 100 operations")


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""

    def setup_method(self):
        """Set up concurrency test fixtures."""
        self.test_email_data = {
            "from": "customer@example.com",
            "to": "support@colenielson.dev",
            "subject": "Concurrent test email",
            "body_text": "This is a concurrent test email.",
        }

    def test_concurrent_client_identification(self):
        """Test client identification under concurrent load."""

        client_manager = get_client_manager()

        def identify_client():
            start_time = time.time()
            result = client_manager.identify_client_by_email("support@colenielson.dev")
            end_time = time.time()
            return end_time - start_time, result.is_successful

        # Test with multiple threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()

            # Submit 50 concurrent identification requests
            futures = [executor.submit(identify_client) for _ in range(50)]
            results = [future.result() for future in futures]

            end_time = time.time()
            total_time = end_time - start_time

        # Analyze results
        times, successes = zip(*results)
        avg_time = statistics.mean(times)
        max_time = max(times)
        success_rate = sum(successes) / len(successes)

        # Performance requirements under load
        assert avg_time < 0.01, f"Concurrent identification too slow: {avg_time:.4f}s avg"
        assert max_time < 0.05, f"Concurrent identification max too slow: {max_time:.4f}s"
        assert success_rate == 1.0, f"Some identifications failed: {success_rate:.2f} success rate"
        assert total_time < 2.0, f"Total concurrent time too slow: {total_time:.2f}s"

        print(
            f"✅ Concurrent identification: {avg_time:.4f}s avg, {total_time:.2f}s total for 50 ops"
        )

    def test_concurrent_config_loading(self):
        """Test config loading under concurrent access."""

        client_manager = get_client_manager()

        def load_config():
            start_time = time.time()
            config = client_manager.get_client_config("client-001-cole-nielson")
            end_time = time.time()
            return end_time - start_time, config.client.name

        # Test with multiple threads
        with ThreadPoolExecutor(max_workers=8) as executor:
            start_time = time.time()

            # Submit 40 concurrent config loading requests
            futures = [executor.submit(load_config) for _ in range(40)]
            results = [future.result() for future in futures]

            end_time = time.time()
            total_time = end_time - start_time

        # Analyze results
        times, names = zip(*results)
        avg_time = statistics.mean(times)
        max_time = max(times)

        # All names should be consistent
        unique_names = set(names)
        assert len(unique_names) == 1, f"Inconsistent config results: {unique_names}"

        # Performance requirements
        assert avg_time < 0.015, f"Concurrent config loading too slow: {avg_time:.4f}s avg"
        assert max_time < 0.05, f"Concurrent config loading max too slow: {max_time:.4f}s"
        assert total_time < 1.5, f"Total concurrent config time too slow: {total_time:.2f}s"

        print(
            f"✅ Concurrent config loading: {avg_time:.4f}s avg, {total_time:.2f}s total for 40 ops"
        )

    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self):
        """Test concurrent async operations performance."""

        email_service = get_email_service()

        async def generate_content(request_id):
            with patch.object(email_service, "_call_ai_service") as mock_ai:
                mock_ai.return_value = f"Response for request {request_id}"

                start_time = time.time()

                result = await email_service.generate_customer_acknowledgment(
                    self.test_email_data,
                    {"category": "support", "confidence": 0.9},
                    "client-001-cole-nielson",
                )

                end_time = time.time()
                return end_time - start_time, result

        # Run 20 concurrent async operations
        start_time = time.time()

        tasks = [generate_content(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        times, responses = zip(*results)
        avg_time = statistics.mean(times)
        max_time = max(times)

        # All responses should be valid
        assert all(isinstance(r, str) and len(r) > 0 for r in responses)

        # Performance requirements for async operations
        assert avg_time < 0.05, f"Concurrent async ops too slow: {avg_time:.4f}s avg"
        assert max_time < 0.1, f"Concurrent async ops max too slow: {max_time:.4f}s"
        assert total_time < 2.0, f"Total concurrent async time too slow: {total_time:.2f}s"

        print(f"✅ Concurrent async ops: {avg_time:.4f}s avg, {total_time:.2f}s total for 20 ops")


class TestMemoryPerformance:
    """Test memory usage and performance characteristics."""

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during operations."""

        # Skip memory testing if psutil not available
        pytest.skip("Memory testing requires psutil which is not available")

    def test_cache_memory_efficiency(self):
        """Test that caching is memory efficient."""

        email_service = EmailService(ClientManager())

        # Fill caches with test data
        for i in range(100):
            email_service._template_cache[f"template-{i}"] = f"Template content {i}" * 10
            email_service._branding_cache[f"client-{i}"] = {
                "color": f"#color{i}",
                "name": f"Company {i}",
                "logo": f"https://example.com/logo{i}.png",
            }

        # Check cache sizes are reasonable
        template_cache_size = len(str(email_service._template_cache))
        branding_cache_size = len(str(email_service._branding_cache))

        # Caches should not be excessively large
        assert template_cache_size < 50000, f"Template cache too large: {template_cache_size} chars"
        assert branding_cache_size < 20000, f"Branding cache too large: {branding_cache_size} chars"

        # Test cache clearing efficiency
        email_service.clear_cache()

        assert len(email_service._template_cache) == 0
        assert len(email_service._branding_cache) == 0

        print(
            f"✅ Cache efficiency: Template={template_cache_size}, Branding={branding_cache_size} chars"
        )


class TestPerformanceRegression:
    """Test for performance regressions in core operations."""

    def test_baseline_performance_metrics(self):
        """Establish baseline performance metrics for regression testing."""

        # These metrics should be updated when legitimate performance improvements are made
        performance_baselines = {
            "client_identification": 0.008,  # 8ms max (allow for variation)
            "config_loading": 0.015,  # 15ms max
            "routing_decision": 0.025,  # 25ms max (includes timezone processing)
            "template_injection": 0.002,  # 2ms max
            "context_preparation": 0.015,  # 15ms max
        }

        client_manager = get_client_manager()
        email_service = get_email_service()
        routing_engine = get_routing_engine()

        # Test client identification
        start_time = time.time()
        result = client_manager.identify_client_by_email("support@colenielson.dev")
        client_id_time = time.time() - start_time

        # Test config loading
        start_time = time.time()
        config = client_manager.get_client_config("client-001-cole-nielson")
        config_time = time.time() - start_time

        # Test routing decision
        classification = {"category": "support", "confidence": 0.9}
        email_data = {"from": "test@example.com", "to": "support@colenielson.dev"}

        start_time = time.time()
        routing_result = routing_engine.route_email(
            "client-001-cole-nielson", classification, email_data
        )
        routing_time = time.time() - start_time

        # Test template injection
        template = "Hello {{client.name}}, your {{email.subject}} was received"
        context = {"client": {"name": "Test"}, "email": {"subject": "test email"}}

        start_time = time.time()
        injected = email_service._inject_template_variables(template, context)
        injection_time = time.time() - start_time

        # Test context preparation
        start_time = time.time()
        context = email_service._prepare_template_context("client-001-cole-nielson", email_data)
        context_time = time.time() - start_time

        # Check against baselines
        actual_metrics = {
            "client_identification": client_id_time,
            "config_loading": config_time,
            "routing_decision": routing_time,
            "template_injection": injection_time,
            "context_preparation": context_time,
        }

        print("Performance metrics:")
        for metric, actual_time in actual_metrics.items():
            baseline = performance_baselines[metric]
            status = "✅" if actual_time <= baseline else "❌"
            print(f"  {status} {metric}: {actual_time:.4f}s (baseline: {baseline:.4f}s)")

            # Assert against baseline
            assert (
                actual_time <= baseline
            ), f"{metric} regression: {actual_time:.4f}s > {baseline:.4f}s baseline"

        print("✅ All performance metrics within baseline thresholds")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
