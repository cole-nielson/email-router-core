"""
Threat Detection Middleware
🛡️ Monitors requests for security threats and suspicious activity.
"""

import logging
import time
from typing import Callable, Dict, List
from urllib.parse import unquote

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_security_config

logger = logging.getLogger(__name__)


class ThreatDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that monitors requests for security threats.

    This middleware provides basic threat detection including:
    - Suspicious request patterns
    - Potential injection attacks
    - Unusual request sizes
    - Rate limiting violations
    """

    def __init__(self, app, enable_detection: bool = True):
        """
        Initialize threat detection middleware.

        Args:
            app: FastAPI application
            enable_detection: Whether to enable threat detection
        """
        super().__init__(app)
        self.enable_detection = enable_detection
        self.security_config = get_security_config()

        # Threat detection state
        self._suspicious_ips: Dict[str, List[float]] = {}
        self._blocked_ips: Dict[str, float] = {}

        logger.info(f"Threat detection middleware initialized (enabled: {enable_detection})")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Monitor request for threats and process.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If threat is detected
        """
        if not self.enable_detection:
            return await call_next(request)

        start_time = time.time()
        client_ip = self._get_client_ip(request)

        try:
            # Check if IP is blocked
            if self._is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="IP temporarily blocked due to suspicious activity",
                )

            # Perform threat detection checks
            self._check_request_threats(request, client_ip)

            # Process request
            response = await call_next(request)

            # Monitor response for additional threats
            self._monitor_response(request, response, client_ip, start_time)

            return response

        except HTTPException:
            # Re-raise HTTP exceptions
            self._record_suspicious_activity(client_ip, "http_exception")
            raise

        except Exception as e:
            # Log unexpected errors as potential threats
            logger.error(f"Threat detection middleware error: {e}")
            self._record_suspicious_activity(client_ip, "middleware_error")
            raise

    def _check_request_threats(self, request: Request, client_ip: str) -> None:
        """
        Check request for various threat patterns.

        Args:
            request: FastAPI request object
            client_ip: Client IP address

        Raises:
            HTTPException: If threat is detected
        """
        # Check suspicious patterns in URL
        self._check_url_threats(request, client_ip)

        # Check request headers for threats
        self._check_header_threats(request, client_ip)

        # Check request size
        self._check_request_size(request, client_ip)

        # Check user agent
        self._check_user_agent(request, client_ip)

    def _check_url_threats(self, request: Request, client_ip: str) -> None:
        """Check URL for suspicious patterns."""
        url_path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()
        full_url = f"{url_path}?{query_string}"

        # Decode URL to catch encoded attacks
        try:
            decoded_url = unquote(full_url)
        except Exception:
            decoded_url = full_url

        # Check against suspicious patterns
        for pattern in self.security_config.suspicious_patterns:
            if pattern in decoded_url:
                logger.warning(f"Suspicious pattern detected in URL: {pattern} from {client_ip}")
                self._record_suspicious_activity(client_ip, f"suspicious_pattern:{pattern}")

                # Block certain high-risk patterns immediately
                if pattern in ["../", "union select", "drop table"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Malicious request detected",
                    )

    def _check_header_threats(self, request: Request, client_ip: str) -> None:
        """Check request headers for threats."""
        # Check for suspicious user agents
        user_agent = request.headers.get("User-Agent", "").lower()
        suspicious_ua_patterns = [
            "sqlmap",
            "nmap",
            "nikto",
            "burpsuite",
            "masscan",
            "python-requests",
            "curl",
            "wget",  # May be legitimate but worth monitoring
        ]

        for pattern in suspicious_ua_patterns:
            if pattern in user_agent:
                logger.info(f"Suspicious user agent from {client_ip}: {user_agent}")
                self._record_suspicious_activity(client_ip, f"suspicious_ua:{pattern}")

        # Check for header injection attempts
        for header, value in request.headers.items():
            if any(char in value for char in ["\n", "\r", "\0"]):
                logger.warning(f"Header injection attempt from {client_ip}: {header}")
                self._record_suspicious_activity(client_ip, "header_injection")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request headers",
                )

    def _check_request_size(self, request: Request, client_ip: str) -> None:
        """Check request size for abuse."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if not self.security_config.is_request_size_valid(size, str(request.url.path)):
                    logger.warning(f"Request too large from {client_ip}: {size} bytes")
                    self._record_suspicious_activity(client_ip, "large_request")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large",
                    )
            except ValueError:
                # Invalid content-length header
                logger.warning(f"Invalid content-length header from {client_ip}")
                self._record_suspicious_activity(client_ip, "invalid_content_length")

    def _check_user_agent(self, request: Request, client_ip: str) -> None:
        """Check user agent for suspicious patterns."""
        user_agent = request.headers.get("User-Agent", "")

        # Missing user agent (might be automated)
        if not user_agent:
            logger.debug(f"Missing user agent from {client_ip}")
            # Don't block, but record for monitoring
            self._record_suspicious_activity(client_ip, "missing_user_agent", severity="low")

        # Extremely long user agent (potential buffer overflow attempt)
        elif len(user_agent) > 1000:
            logger.warning(f"Excessively long user agent from {client_ip}")
            self._record_suspicious_activity(client_ip, "long_user_agent")

    def _monitor_response(
        self, request: Request, response: Response, client_ip: str, start_time: float
    ) -> None:
        """Monitor response for additional threat indicators."""
        # Check response time (potential DoS indicators)
        response_time = time.time() - start_time
        if response_time > 10.0:  # 10 seconds
            logger.warning(f"Slow response ({response_time:.2f}s) for {client_ip}")
            self._record_suspicious_activity(client_ip, "slow_response", severity="low")

        # Monitor error responses
        if response.status_code >= 400:
            self._record_suspicious_activity(
                client_ip, f"error_{response.status_code}", severity="low"
            )

    def _record_suspicious_activity(
        self, client_ip: str, activity_type: str, severity: str = "medium"
    ) -> None:
        """
        Record suspicious activity for IP monitoring.

        Args:
            client_ip: Client IP address
            activity_type: Type of suspicious activity
            severity: Severity level (low, medium, high)
        """
        if not client_ip:
            return

        current_time = time.time()

        # Initialize tracking for new IPs
        if client_ip not in self._suspicious_ips:
            self._suspicious_ips[client_ip] = []

        # Add activity with timestamp
        self._suspicious_ips[client_ip].append(current_time)

        # Clean old activities (older than 1 hour)
        cutoff_time = current_time - 3600
        self._suspicious_ips[client_ip] = [
            t for t in self._suspicious_ips[client_ip] if t > cutoff_time
        ]

        # Check if IP should be blocked
        activity_count = len(self._suspicious_ips[client_ip])

        # Block thresholds based on severity
        block_threshold = {
            "low": 20,  # 20 low-severity events in 1 hour
            "medium": 10,  # 10 medium-severity events in 1 hour
            "high": 3,  # 3 high-severity events in 1 hour
        }.get(severity, 10)

        if activity_count >= block_threshold:
            # Block IP for 1 hour
            self._blocked_ips[client_ip] = current_time + 3600
            logger.warning(
                f"IP {client_ip} blocked for suspicious activity: "
                f"{activity_count} {severity} events"
            )

    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked."""
        if not client_ip or client_ip not in self._blocked_ips:
            return False

        # Check if block has expired
        if time.time() > self._blocked_ips[client_ip]:
            del self._blocked_ips[client_ip]
            return False

        return True

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"
