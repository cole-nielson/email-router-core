"""
Central Security Manager for Email Router
🔐 Coordinates all security operations and provides unified security interface.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status

from .auth_context import AuthenticationType, SecurityContext
from .config import SecurityConfig

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Central security manager that coordinates authentication, authorization, and security policies.

    This class serves as the main entry point for all security operations,
    replacing the scattered security logic across multiple middleware and services.
    """

    def __init__(self, config: SecurityConfig):
        """
        Initialize security manager with configuration.

        Args:
            config: Security configuration instance
        """
        self.config = config
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._blocked_ips: Dict[str, datetime] = {}
        self._security_events: List[Dict[str, Any]] = []

    # =========================================================================
    # REQUEST SECURITY PROCESSING
    # =========================================================================

    def create_security_context(self, request: Request) -> SecurityContext:
        """
        Create security context from request.

        Args:
            request: FastAPI request object

        Returns:
            SecurityContext with request metadata
        """
        return SecurityContext.create_unauthenticated(
            request_id=self.generate_request_id(),
            ip_address=self._extract_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )

    def authenticate_request(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """
        Authenticate request and update security context.

        Args:
            request: FastAPI request object
            security_context: Current security context

        Returns:
            Updated security context with authentication state
        """
        # Check if IP is blocked
        client_ip = security_context.ip_address
        if client_ip and self.is_ip_blocked(client_ip):
            self.log_security_event(
                "blocked_ip_attempt", {"ip": client_ip, "path": str(request.url.path)}, client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP temporarily blocked due to security violations",
            )

        # Skip authentication for public endpoints
        if security_context.can_access_endpoint(str(request.url.path), request.method):
            return security_context

        # Try authentication methods based on endpoint preferences
        auth_strategy = self._get_auth_strategy(str(request.url.path))

        if auth_strategy == "jwt_preferred":
            # Try JWT first, then API key
            jwt_context = self._try_jwt_authentication(request, security_context)
            if jwt_context.is_authenticated:
                return jwt_context
            return self._try_api_key_authentication(request, security_context)

        elif auth_strategy == "api_key_preferred":
            # Try API key first, then JWT
            api_context = self._try_api_key_authentication(request, security_context)
            if api_context.is_authenticated:
                return api_context
            return self._try_jwt_authentication(request, security_context)

        elif auth_strategy == "jwt_only":
            # JWT only for sensitive endpoints
            return self._try_jwt_authentication(request, security_context)

        else:
            # Default: try both with JWT preferred
            jwt_context = self._try_jwt_authentication(request, security_context)
            if jwt_context.is_authenticated:
                return jwt_context
            return self._try_api_key_authentication(request, security_context)

    def validate_request_security(self, request: Request) -> None:
        """
        Validate request against security policies.

        Args:
            request: FastAPI request object

        Raises:
            HTTPException: If request violates security policies
        """
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.config.max_request_size:
                    self.log_security_event(
                        "request_too_large",
                        {"size": size, "limit": self.config.max_request_size},
                        self._extract_client_ip(request),
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large",
                    )
            except ValueError:
                pass  # Invalid content-length header

        # Check for suspicious patterns
        self._check_suspicious_request(request)

    # =========================================================================
    # AUTHENTICATION METHODS
    # =========================================================================

    def _try_jwt_authentication(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """Try JWT authentication."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return security_context

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Import here to avoid circular imports
            from ...database.connection import get_database_session
            from ...services.auth_service import get_auth_service

            # Validate JWT token
            db = get_database_session()
            try:
                auth_service = get_auth_service(db)
                user = auth_service.get_current_user(token)

                if user:
                    return SecurityContext.create_from_jwt_user(
                        user=user,
                        token=token,
                        request_id=security_context.request_id,
                        ip_address=security_context.ip_address,
                        user_agent=security_context.user_agent,
                    )
            finally:
                db.close()

        except Exception as e:
            logger.debug(f"JWT authentication failed: {e}")

        return security_context

    def _try_api_key_authentication(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """Try API key authentication."""
        try:
            api_key = self._extract_api_key(request)
            if not api_key:
                return security_context

            # Simple API key validation (would be enhanced with proper key management)
            client_id = self._extract_client_from_api_key(api_key)
            if client_id:
                # Standard API key permissions
                permissions = [
                    "webhooks:write",
                    "client:read",
                    "system:monitor",
                ]

                return SecurityContext.create_from_api_key(
                    client_id=client_id,
                    api_key_id="webhook_key",
                    permissions=permissions,
                    token=api_key,
                    request_id=security_context.request_id,
                    ip_address=security_context.ip_address,
                    user_agent=security_context.user_agent,
                )

        except Exception as e:
            logger.debug(f"API key authentication failed: {e}")

        return security_context

    # =========================================================================
    # AUTHORIZATION METHODS
    # =========================================================================

    def check_permission(
        self,
        security_context: SecurityContext,
        permission: str,
        target_client_id: Optional[str] = None,
    ) -> bool:
        """
        Check if security context has specific permission.

        Args:
            security_context: Current security context
            permission: Permission to check
            target_client_id: Target client for scoped permissions

        Returns:
            True if permission is granted
        """
        return security_context.has_permission(permission, target_client_id)

    def require_permission(
        self,
        security_context: SecurityContext,
        permission: str,
        target_client_id: Optional[str] = None,
    ) -> None:
        """
        Require specific permission or raise HTTPException.

        Args:
            security_context: Current security context
            permission: Required permission
            target_client_id: Target client for scoped permissions

        Raises:
            HTTPException: If permission is denied
        """
        if not self.check_permission(security_context, permission, target_client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission}"
            )

    def require_role(self, security_context: SecurityContext, required_roles: List[str]) -> None:
        """
        Require specific role or raise HTTPException.

        Args:
            security_context: Current security context
            required_roles: List of acceptable roles

        Raises:
            HTTPException: If role requirement is not met
        """
        if not security_context.has_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role requirement not met. Required: {required_roles}",
            )

    def require_client_access(self, security_context: SecurityContext, client_id: str) -> None:
        """
        Require access to specific client or raise HTTPException.

        Args:
            security_context: Current security context
            client_id: Required client ID

        Raises:
            HTTPException: If client access is denied
        """
        if not security_context.has_client_access(client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied to client {client_id}"
            )

    # =========================================================================
    # SECURITY MONITORING
    # =========================================================================

    def log_security_event(
        self, event_type: str, details: Dict[str, Any], ip_address: Optional[str] = None
    ) -> None:
        """
        Log security event for monitoring and analysis.

        Args:
            event_type: Type of security event
            details: Event details
            ip_address: Source IP address
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "ip_address": ip_address,
        }

        self._security_events.append(event)
        logger.warning(f"Security event [{event_type}]: {details}")

        # Track failed attempts for IP blocking
        if event_type in ["invalid_token", "invalid_api_key", "permission_denied"]:
            self._track_failed_attempt(ip_address)

    def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if IP address is currently blocked.

        Args:
            ip_address: IP address to check

        Returns:
            True if IP is blocked
        """
        if ip_address in self._blocked_ips:
            unblock_time = self._blocked_ips[ip_address]
            if datetime.utcnow() < unblock_time:
                return True
            else:
                # Remove expired block
                del self._blocked_ips[ip_address]

        return False

    def _track_failed_attempt(self, ip_address: Optional[str]) -> None:
        """Track failed authentication attempts."""
        if not ip_address:
            return

        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.config.alert_threshold_timespan_minutes)

        # Initialize or clean up old attempts
        if ip_address not in self._failed_attempts:
            self._failed_attempts[ip_address] = []

        # Remove old attempts
        self._failed_attempts[ip_address] = [
            attempt for attempt in self._failed_attempts[ip_address] if attempt > cutoff
        ]

        # Add current attempt
        self._failed_attempts[ip_address].append(now)

        # Check if should block IP
        if len(self._failed_attempts[ip_address]) >= self.config.alert_threshold_failed_logins:
            block_until = now + timedelta(hours=1)  # Block for 1 hour
            self._blocked_ips[ip_address] = block_until

            self.log_security_event(
                "ip_blocked",
                {
                    "ip": ip_address,
                    "failed_attempts": len(self._failed_attempts[ip_address]),
                    "blocked_until": block_until.isoformat(),
                },
                ip_address,
            )

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def generate_request_id(self) -> str:
        """Generate unique request ID."""
        return f"req_{secrets.token_urlsafe(16)}"

    def _extract_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP from request."""
        # Check forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else None

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request."""
        # Try X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Try Authorization header with Bearer scheme for API keys
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer sk-"):
            return auth_header[7:]  # Remove "Bearer " prefix

        return None

    def _extract_client_from_api_key(self, api_key: str) -> Optional[str]:
        """Extract client ID from API key format."""
        # Simple client mapping (would be enhanced with proper key management)
        if api_key.startswith("sk-") and len(api_key) > 10:
            parts = api_key.split("-")
            if len(parts) >= 3:
                client_part = parts[1]
                client_mapping = {
                    "client001": "client-001-cole-nielson",
                    "dev": "client-001-cole-nielson",  # For development
                    "test": "test-client",
                    "demo": "demo-client",
                }
                return client_mapping.get(client_part)

        return None

    def _get_auth_strategy(self, path: str) -> str:
        """Determine authentication strategy for endpoint."""
        if path.startswith("/webhooks/"):
            return "api_key_preferred"
        elif path.startswith("/api/v2/"):
            return "jwt_only"
        elif path.startswith("/auth/"):
            return "public"
        else:
            return "jwt_preferred"

    def _check_suspicious_request(self, request: Request) -> None:
        """Check for suspicious request patterns."""
        # Basic suspicious pattern detection
        suspicious_patterns = [
            "script",
            "alert",
            "javascript:",
            "data:",
            "../",
            "..\\",
            "/etc/passwd",
            "/etc/shadow",
        ]

        path = str(request.url.path).lower()
        for pattern in suspicious_patterns:
            if pattern in path:
                self.log_security_event(
                    "suspicious_request",
                    {"pattern": pattern, "path": path},
                    self._extract_client_ip(request),
                )
                break
