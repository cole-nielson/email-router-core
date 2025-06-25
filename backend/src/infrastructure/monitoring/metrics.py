"""
Monitoring and metrics collection service.
📊 Provides comprehensive system metrics for monitoring and alerting.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Optional, TypedDict

logger = logging.getLogger(__name__)


class ClientMetric(TypedDict, total=False):
    requests: int
    successful: int
    failed: int
    last_activity: Optional[datetime]
    emails_processed: int


class MetricsCollector:
    """
    Comprehensive metrics collection for API monitoring.

    Collects and provides metrics for:
    - Request rates and response times
    - Error rates and status codes
    - System health and performance
    - Business metrics and usage patterns
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.start_time = time.time()
        self._lock = threading.Lock()

        # Request metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: deque[float] = deque(maxlen=1000)  # Last 1000 response times

        # Status code tracking
        self.status_codes: defaultdict[int, int] = defaultdict(int)

        # Endpoint metrics
        self.endpoint_metrics: defaultdict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "avg_response_time": 0.0,
                "total_response_time": 0.0,
            }
        )

        # Client metrics
        self.client_metrics: defaultdict[str, ClientMetric] = defaultdict(
            lambda: {"requests": 0, "successful": 0, "failed": 0, "last_activity": None}
        )

        # Health check metrics
        self.health_checks = 0
        self.last_health_check: Optional[datetime] = None

        # Business metrics
        self.emails_processed = 0
        self.emails_classified = 0
        self.emails_routed = 0
        self.ai_requests = 0
        self.webhook_requests = 0

        # Time series data (last 24 hours in 5-minute buckets)
        self.time_series: Dict[str, deque] = {
            "requests": deque(maxlen=288),  # 24 hours * 12 (5-min buckets)
            "errors": deque(maxlen=288),
            "response_times": deque(maxlen=288),
            "timestamps": deque(maxlen=288),
        }

        # Initialize first time bucket
        self._init_time_series()

        logger.info("Metrics collector initialized")

    def _init_time_series(self) -> None:
        """Initialize time series data."""
        now = datetime.utcnow()
        # Round down to nearest 5-minute mark
        rounded_time = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)

        self.time_series["requests"].append(0)
        self.time_series["errors"].append(0)
        self.time_series["response_times"].append(0.0)
        self.time_series["timestamps"].append(rounded_time)
        self.current_bucket_start = rounded_time

    def record_request(
        self, endpoint: Optional[str] = None, client_id: Optional[str] = None
    ) -> None:
        """Record a new request."""
        with self._lock:
            self.total_requests += 1

            if endpoint:
                self.endpoint_metrics[endpoint]["requests"] += 1

            if client_id:
                self.client_metrics[client_id]["requests"] += 1
                self.client_metrics[client_id]["last_activity"] = datetime.utcnow()

            self._update_time_series("requests", 1)

    def record_successful_request(
        self, endpoint: Optional[str] = None, client_id: Optional[str] = None
    ) -> None:
        """Record a successful request."""
        with self._lock:
            self.successful_requests += 1

            if endpoint:
                self.endpoint_metrics[endpoint]["successful"] += 1

            if client_id:
                self.client_metrics[client_id]["successful"] += 1

    def record_failed_request(
        self, endpoint: Optional[str] = None, client_id: Optional[str] = None
    ) -> None:
        """Record a failed request."""
        with self._lock:
            self.failed_requests += 1

            if endpoint:
                self.endpoint_metrics[endpoint]["failed"] += 1

            if client_id:
                self.client_metrics[client_id]["failed"] += 1

            self._update_time_series("errors", 1)

    def record_response_time(self, response_time: float, endpoint: Optional[str] = None) -> None:
        """Record response time for a request."""
        with self._lock:
            self.response_times.append(response_time)

            if endpoint:
                metrics = self.endpoint_metrics[endpoint]
                metrics["total_response_time"] += response_time
                # Update average (simple moving average)
                total_requests = metrics["requests"]
                if total_requests > 0:
                    metrics["avg_response_time"] = metrics["total_response_time"] / total_requests

            self._update_time_series("response_times", response_time)

    def record_status_code(self, status_code: int) -> None:
        """Record HTTP status code."""
        with self._lock:
            self.status_codes[status_code] += 1

    def record_health_check(self) -> None:
        """Record a health check."""
        with self._lock:
            self.health_checks += 1
            self.last_health_check = datetime.utcnow()

    def record_email_processed(self, client_id: Optional[str] = None) -> None:
        """Record an email being processed."""
        with self._lock:
            self.emails_processed += 1
            if client_id:
                if "emails_processed" not in self.client_metrics[client_id]:
                    self.client_metrics[client_id]["emails_processed"] = 0
                self.client_metrics[client_id]["emails_processed"] += 1

    def record_email_classified(self, method: Optional[str] = None) -> None:
        """Record an email classification."""
        with self._lock:
            self.emails_classified += 1
            if method == "ai":
                self.ai_requests += 1

    def record_email_routed(self, category: Optional[str] = None) -> None:
        """Record an email being routed."""
        with self._lock:
            self.emails_routed += 1

    def record_webhook_request(self) -> None:
        """Record a webhook request."""
        with self._lock:
            self.webhook_requests += 1

    def _update_time_series(self, metric: str, value: float) -> None:
        """Update time series data."""
        now = datetime.utcnow()
        # Round down to nearest 5-minute mark
        rounded_time = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)

        # Check if we need a new bucket
        if rounded_time > self.current_bucket_start:
            # Add new bucket
            self.time_series["requests"].append(0)
            self.time_series["errors"].append(0)
            self.time_series["response_times"].append(0.0)
            self.time_series["timestamps"].append(rounded_time)
            self.current_bucket_start = rounded_time

        # Update current bucket
        if metric == "requests":
            if self.time_series["requests"]:
                self.time_series["requests"][-1] += value
        elif metric == "errors":
            if self.time_series["errors"]:
                self.time_series["errors"][-1] += value
        elif metric == "response_times":
            if self.time_series["response_times"]:
                # Update average response time for this bucket
                current_avg = self.time_series["response_times"][-1]
                current_count = (
                    self.time_series["requests"][-1] if self.time_series["requests"] else 1
                )
                self.time_series["response_times"][-1] = (
                    current_avg * (current_count - 1) + value
                ) / current_count

    def get_avg_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def get_requests_per_minute(self) -> float:
        """Get current requests per minute."""
        if len(self.response_times) < 2:
            return 0.0

        # Calculate based on last minute of data
        now = time.time()
        minute_ago = now - 60

        recent_requests = sum(1 for _ in self.response_times if _ > minute_ago)
        return recent_requests

    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics."""
        with self._lock:
            uptime_seconds = int(time.time() - self.start_time)

            return {
                "uptime_seconds": uptime_seconds,
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "avg_response_time_ms": self.get_avg_response_time() * 1000,
                "error_rate_percent": self.get_error_rate(),
                "requests_per_minute": self.get_requests_per_minute(),
                "health_checks": self.health_checks,
                "last_health_check": (
                    self.last_health_check.isoformat() if self.last_health_check else None
                ),
                "emails_processed": self.emails_processed,
                "emails_classified": self.emails_classified,
                "emails_routed": self.emails_routed,
                "ai_requests": self.ai_requests,
                "webhook_requests": self.webhook_requests,
            }

    def get_endpoint_metrics(self) -> Dict:
        """Get per-endpoint metrics."""
        with self._lock:
            return dict(self.endpoint_metrics)

    def get_client_metrics(self) -> Dict:
        """Get per-client metrics."""
        with self._lock:
            # Convert defaultdict to regular dict and format timestamps
            client_data = {}
            for client_id, metrics in self.client_metrics.items():
                client_data[client_id] = dict(metrics)
                last_activity = metrics["last_activity"]
                if last_activity:
                    client_data[client_id]["last_activity"] = last_activity.isoformat()
            return client_data

    def get_status_code_distribution(self) -> Dict:
        """Get HTTP status code distribution."""
        with self._lock:
            return dict(self.status_codes)

    def get_time_series_data(self, hours: int = 24) -> Dict:
        """Get time series data for specified hours."""
        with self._lock:
            # Calculate how many buckets we need (5-minute buckets)
            buckets_needed = min(hours * 12, len(self.time_series["timestamps"]))

            if buckets_needed == 0:
                return {
                    "timestamps": [],
                    "requests": [],
                    "errors": [],
                    "response_times": [],
                }

            # Get the last N buckets
            return {
                "timestamps": [
                    ts.isoformat() for ts in list(self.time_series["timestamps"])[-buckets_needed:]
                ],
                "requests": list(self.time_series["requests"])[-buckets_needed:],
                "errors": list(self.time_series["errors"])[-buckets_needed:],
                "response_times": list(self.time_series["response_times"])[-buckets_needed:],
            }

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        with self._lock:
            metrics = []

            # System metrics
            metrics.extend(
                [
                    "# HELP email_router_requests_total Total number of requests",
                    "# TYPE email_router_requests_total counter",
                    f"email_router_requests_total {self.total_requests}",
                    "",
                    "# HELP email_router_requests_successful_total Total number of successful requests",
                    "# TYPE email_router_requests_successful_total counter",
                    f"email_router_requests_successful_total {self.successful_requests}",
                    "",
                    "# HELP email_router_requests_failed_total Total number of failed requests",
                    "# TYPE email_router_requests_failed_total counter",
                    f"email_router_requests_failed_total {self.failed_requests}",
                    "",
                    "# HELP email_router_response_time_seconds Average response time",
                    "# TYPE email_router_response_time_seconds gauge",
                    f"email_router_response_time_seconds {self.get_avg_response_time()}",
                    "",
                    "# HELP email_router_error_rate_percent Error rate percentage",
                    "# TYPE email_router_error_rate_percent gauge",
                    f"email_router_error_rate_percent {self.get_error_rate()}",
                    "",
                    "# HELP email_router_uptime_seconds System uptime",
                    "# TYPE email_router_uptime_seconds gauge",
                    f"email_router_uptime_seconds {int(time.time() - self.start_time)}",
                ]
            )

            # Business metrics
            metrics.extend(
                [
                    "",
                    "# HELP email_router_emails_processed_total Total emails processed",
                    "# TYPE email_router_emails_processed_total counter",
                    f"email_router_emails_processed_total {self.emails_processed}",
                    "",
                    "# HELP email_router_emails_classified_total Total emails classified",
                    "# TYPE email_router_emails_classified_total counter",
                    f"email_router_emails_classified_total {self.emails_classified}",
                    "",
                    "# HELP email_router_ai_requests_total Total AI classification requests",
                    "# TYPE email_router_ai_requests_total counter",
                    f"email_router_ai_requests_total {self.ai_requests}",
                ]
            )

            # Status code metrics
            metrics.append("")
            metrics.append("# HELP email_router_http_requests_total HTTP requests by status code")
            metrics.append("# TYPE email_router_http_requests_total counter")
            for status_code, count in self.status_codes.items():
                metrics.append(
                    f'email_router_http_requests_total{{status_code="{status_code}"}} {count}'
                )

            return "\n".join(metrics)

    def get_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        with self._lock:
            scores = []

            # Error rate score (lower is better)
            error_rate = self.get_error_rate()
            if error_rate < 1:
                scores.append(100)
            elif error_rate < 5:
                scores.append(90)
            elif error_rate < 10:
                scores.append(70)
            elif error_rate < 20:
                scores.append(50)
            else:
                scores.append(20)

            # Response time score
            avg_response_time = self.get_avg_response_time()
            if avg_response_time < 0.1:  # < 100ms
                scores.append(100)
            elif avg_response_time < 0.5:  # < 500ms
                scores.append(90)
            elif avg_response_time < 1.0:  # < 1s
                scores.append(70)
            elif avg_response_time < 2.0:  # < 2s
                scores.append(50)
            else:
                scores.append(20)

            # Uptime score (assume good if we're running)
            scores.append(100)

            # Calculate weighted average
            return sum(scores) / len(scores) if scores else 0

    def reset_metrics(self) -> None:
        """Reset all metrics (for testing or maintenance)."""
        with self._lock:
            # Reset all metrics to initial state
            self.start_time = time.time()
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.response_times.clear()
            self.status_codes.clear()
            self.endpoint_metrics.clear()
            self.client_metrics.clear()
            self.health_checks = 0
            self.last_health_check = None
            self.emails_processed = 0
            self.emails_classified = 0
            self.emails_routed = 0
            self.ai_requests = 0
            self.webhook_requests = 0
            for key in self.time_series:
                self.time_series[key].clear()
            self._init_time_series()
            logger.info("Metrics reset")

    def get_summary(self) -> Dict:
        """Get a comprehensive metrics summary."""
        return {
            "system": self.get_system_metrics(),
            "endpoints": self.get_endpoint_metrics(),
            "clients": self.get_client_metrics(),
            "status_codes": self.get_status_code_distribution(),
            "time_series": self.get_time_series_data(1),  # Last 1 hour
            "health_score": self.get_health_score(),
        }
