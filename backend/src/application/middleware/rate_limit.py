"""
Rate limiting middleware for API requests.
🚦 Implements token bucket algorithm with configurable limits per client/IP.
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient
        """
        now = time.time()

        # Add tokens based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def remaining_tokens(self) -> int:
        """Get number of remaining tokens."""
        now = time.time()
        elapsed = now - self.last_update
        return min(self.capacity, self.tokens + elapsed * self.refill_rate)


class RateLimitStorage:
    """In-memory storage for rate limiting data."""

    def __init__(self):
        """Initialize rate limit storage."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Dict[str, datetime] = {}

        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def get_bucket(self, key: str, capacity: int, refill_rate: float) -> TokenBucket:
        """Get or create token bucket for key."""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(capacity, refill_rate)
        return self.buckets[key]

    def record_request(self, key: str):
        """Record request timestamp for analytics."""
        self.request_history[key].append(time.time())

    def get_request_rate(self, key: str, window_seconds: int = 60) -> float:
        """Get requests per second for key in time window."""
        now = time.time()
        cutoff = now - window_seconds

        # Remove old requests
        while self.request_history[key] and self.request_history[key][0] < cutoff:
            self.request_history[key].popleft()

        return len(self.request_history[key]) / window_seconds

    def block_ip(self, ip: str, duration_seconds: int = 3600):
        """Block IP for specified duration."""
        self.blocked_ips[ip] = datetime.utcnow() + timedelta(seconds=duration_seconds)
        logger.warning(f"Blocked IP {ip} for {duration_seconds} seconds")

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if ip in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        return False

    def cleanup(self):
        """Clean up old data to prevent memory leaks."""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove old buckets that haven't been used recently
        cutoff = now - 3600  # 1 hour
        old_buckets = [key for key, bucket in self.buckets.items() if bucket.last_update < cutoff]

        for key in old_buckets:
            del self.buckets[key]

        # Clean up expired blocked IPs
        expired_ips = [ip for ip, expiry in self.blocked_ips.items() if datetime.utcnow() >= expiry]

        for ip in expired_ips:
            del self.blocked_ips[ip]

        self.last_cleanup = now

        if old_buckets or expired_ips:
            logger.info(
                f"Cleaned up {len(old_buckets)} old rate limit buckets and {len(expired_ips)} expired IP blocks"
            )


# Global storage instance
storage = RateLimitStorage()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with configurable limits.

    Features:
    - Per-IP and per-API-key rate limiting
    - Token bucket algorithm for smooth rate limiting
    - Automatic IP blocking for excessive requests
    - Burst protection with separate limits
    """

    def __init__(self, app, calls_per_minute: int = None, burst_limit: int = None):
        """
        Initialize rate limiter middleware.

        Args:
            app: FastAPI application
            calls_per_minute: Sustained rate limit (from config if None)
            burst_limit: Burst rate limit per 10 seconds (default: calls_per_minute/6)
        """
        super().__init__(app)

        # Load rate limits from unified configuration
        try:
            from ..core import get_app_config

            config = get_app_config()

            self.calls_per_minute = calls_per_minute or config.security.api_rate_limit_per_minute
            self.burst_limit = burst_limit or max(
                10, self.calls_per_minute // 6
            )  # 1/6 of per-minute limit

        except Exception:
            # Fallback to provided values or defaults
            self.calls_per_minute = calls_per_minute or 60
            self.burst_limit = burst_limit or 10

        self.refill_rate = self.calls_per_minute / 60.0  # tokens per second

        logger.info(
            f"Rate limiter initialized: {self.calls_per_minute} req/min, {self.burst_limit} burst"
        )

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        try:
            # Cleanup old data periodically
            storage.cleanup()

            # Get client identifier
            client_id = self._get_client_identifier(request)
            client_ip = self._get_client_ip(request)

            # Check if IP is blocked
            if storage.is_blocked(client_ip):
                return self._rate_limit_response(
                    message="IP temporarily blocked due to excessive requests",
                    retry_after=3600,
                )

            # Check rate limits
            rate_limit_result = self._check_rate_limits(client_id, client_ip)

            if not rate_limit_result["allowed"]:
                # Block IP if too many violations
                violation_rate = storage.get_request_rate(
                    f"violations:{client_ip}", 300
                )  # 5 min window
                if violation_rate > 10:  # More than 10 violations in 5 minutes
                    storage.block_ip(client_ip, 3600)  # Block for 1 hour

                return self._rate_limit_response(
                    message=rate_limit_result["message"],
                    retry_after=rate_limit_result["retry_after"],
                )

            # Record successful request
            storage.record_request(client_id)
            storage.record_request(f"ip:{client_ip}")

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            self._add_rate_limit_headers(response, client_id)

            return response

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Don't block requests due to rate limiter errors
            return await call_next(request)

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"

        # Try bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return f"token:{token[:16]}"  # Use first 16 chars for privacy

        # Fall back to IP
        return f"ip:{self._get_client_ip(request)}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (load balancers, proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _check_rate_limits(self, client_id: str, client_ip: str) -> Dict:
        """Check both sustained and burst rate limits."""
        # Check sustained rate limit (per minute)
        sustained_bucket = storage.get_bucket(
            f"sustained:{client_id}", self.calls_per_minute, self.refill_rate
        )

        # Check burst rate limit (per 10 seconds)
        burst_bucket = storage.get_bucket(
            f"burst:{client_id}",
            self.burst_limit,
            self.burst_limit / 10.0,  # refill in 10 seconds
        )

        # Try to consume from both buckets
        if not sustained_bucket.consume():
            storage.record_request(f"violations:{client_ip}")
            return {
                "allowed": False,
                "message": f"Rate limit exceeded: {self.calls_per_minute} requests per minute",
                "retry_after": 60,
            }

        if not burst_bucket.consume():
            # Refund the sustained token since burst failed
            sustained_bucket.tokens += 1
            storage.record_request(f"violations:{client_ip}")
            return {
                "allowed": False,
                "message": f"Burst limit exceeded: {self.burst_limit} requests per 10 seconds",
                "retry_after": 10,
            }

        return {"allowed": True}

    def _add_rate_limit_headers(self, response: Response, client_id: str):
        """Add rate limiting headers to response."""
        try:
            sustained_bucket = storage.buckets.get(f"sustained:{client_id}")
            burst_bucket = storage.buckets.get(f"burst:{client_id}")

            if sustained_bucket:
                response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(
                    int(sustained_bucket.remaining_tokens())
                )
                response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

            if burst_bucket:
                response.headers["X-RateLimit-Burst-Limit"] = str(self.burst_limit)
                response.headers["X-RateLimit-Burst-Remaining"] = str(
                    int(burst_bucket.remaining_tokens())
                )
        except Exception as e:
            logger.warning(f"Failed to add rate limit headers: {e}")

    def _rate_limit_response(self, message: str, retry_after: int) -> JSONResponse:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": True,
                "status_code": 429,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after), "X-RateLimit-Error": "true"},
        )


def get_rate_limit_info(client_identifier: str) -> Dict:
    """Get current rate limit status for a client."""
    try:
        sustained_bucket = storage.buckets.get(f"sustained:{client_identifier}")
        burst_bucket = storage.buckets.get(f"burst:{client_identifier}")

        return {
            "sustained": {
                "limit": 60,  # calls per minute
                "remaining": (int(sustained_bucket.remaining_tokens()) if sustained_bucket else 60),
                "reset_time": datetime.utcnow() + timedelta(minutes=1),
            },
            "burst": {
                "limit": 10,  # calls per 10 seconds
                "remaining": (int(burst_bucket.remaining_tokens()) if burst_bucket else 10),
                "reset_time": datetime.utcnow() + timedelta(seconds=10),
            },
            "request_rate": storage.get_request_rate(client_identifier),
            "is_blocked": (
                storage.is_blocked(client_identifier.replace("ip:", ""))
                if "ip:" in client_identifier
                else False
            ),
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit info: {e}")
        return {
            "sustained": {
                "limit": 60,
                "remaining": 60,
                "reset_time": datetime.utcnow(),
            },
            "burst": {"limit": 10, "remaining": 10, "reset_time": datetime.utcnow()},
            "request_rate": 0.0,
            "is_blocked": False,
        }
