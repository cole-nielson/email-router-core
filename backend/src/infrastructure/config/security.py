"""
Security Configuration using Unified Config System
🔧 Centralized security configuration leveraging the Phase 2 unified config.
"""

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityConfig(BaseModel):
    """
    Centralized security configuration that integrates with the unified config system.

    This replaces the scattered security settings from the old security_config.py
    and integrates with the Phase 2 unified configuration system.
    """

    # Password requirements
    min_password_length: int = Field(default=12, ge=8, le=128)
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    password_special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Rate limiting (per minute)
    default_rate_limit: int = Field(default=60, ge=10, le=1000)
    api_rate_limit: int = Field(default=300, ge=50, le=5000)
    auth_rate_limit: int = Field(default=10, ge=5, le=50)
    webhook_rate_limit: int = Field(default=1000, ge=100, le=10000)

    # Session security
    session_timeout_minutes: int = Field(default=60, ge=15, le=480)
    max_concurrent_sessions: int = Field(default=5, ge=1, le=20)

    # API Key security
    api_key_length: int = Field(default=32, ge=16, le=64)
    api_key_prefix: str = "er_"

    # Security headers
    security_headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    )

    # Content validation (in bytes)
    max_request_size: int = Field(default=10 * 1024 * 1024, ge=1024)  # 10MB
    max_email_size: int = Field(default=25 * 1024 * 1024, ge=1024)  # 25MB
    max_json_payload: int = Field(default=1024 * 1024, ge=1024)  # 1MB

    # Security monitoring
    log_security_events: bool = True
    log_failed_attempts: bool = True
    alert_threshold_failed_logins: int = Field(default=5, ge=3, le=20)
    alert_threshold_timespan_minutes: int = Field(default=15, ge=5, le=60)

    # Threat detection
    enable_threat_detection: bool = True
    suspicious_patterns: List[str] = Field(
        default_factory=lambda: [
            "script",
            "alert",
            "javascript:",
            "data:",
            "../",
            "..\\",
            "/etc/passwd",
            "/etc/shadow",
            "union select",
            "drop table",
            "insert into",
        ]
    )

    @classmethod
    def from_unified_config(cls, unified_config) -> "SecurityConfig":
        """
        Create SecurityConfig from unified configuration system.

        Args:
            unified_config: AppConfig instance from unified config system

        Returns:
            SecurityConfig instance with values from unified config
        """
        try:
            # Extract security settings from unified config
            security_section = unified_config.security

            return cls(
                # Password requirements from unified config
                min_password_length=security_section.password_min_length,
                password_require_uppercase=security_section.require_password_complexity,
                password_require_lowercase=security_section.require_password_complexity,
                password_require_digits=security_section.require_password_complexity,
                password_require_special=security_section.require_password_complexity,
                # Rate limiting from unified config
                default_rate_limit=security_section.rate_limit_per_minute,
                api_rate_limit=security_section.api_rate_limit_per_minute,
                auth_rate_limit=max(10, security_section.rate_limit_per_minute // 6),
                webhook_rate_limit=security_section.api_rate_limit_per_minute * 3,
                # Session security from unified config
                session_timeout_minutes=security_section.session_timeout_minutes,
                max_concurrent_sessions=security_section.max_sessions_per_user,
                # Security monitoring from unified config
                alert_threshold_failed_logins=security_section.max_login_attempts,
                alert_threshold_timespan_minutes=security_section.lockout_duration_minutes,
                # CORS and security settings
                enable_threat_detection=True,  # Always enabled in production
            )

        except Exception as e:
            logger.warning(f"Failed to load from unified config, using defaults: {e}")
            return cls()  # Return with default values

    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """
        Validate password against security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if len(password) < self.min_password_length:
            errors.append(f"Password must be at least {self.min_password_length} characters long")

        if self.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if self.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if self.password_require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if self.password_require_special:
            if not any(c in self.password_special_chars for c in password):
                errors.append(
                    f"Password must contain at least one special character: {self.password_special_chars}"
                )

        return len(errors) == 0, errors

    def get_rate_limit_for_endpoint(self, endpoint_path: str) -> int:
        """
        Get rate limit for specific endpoint.

        Args:
            endpoint_path: API endpoint path

        Returns:
            Rate limit per minute
        """
        if endpoint_path.startswith("/auth/"):
            return self.auth_rate_limit
        elif endpoint_path.startswith("/webhooks/"):
            return self.webhook_rate_limit
        elif endpoint_path.startswith("/api/"):
            return self.api_rate_limit
        else:
            return self.default_rate_limit

    def is_request_size_valid(self, size: int, endpoint_path: str = "") -> bool:
        """
        Validate request size against limits.

        Args:
            size: Request size in bytes
            endpoint_path: API endpoint path for specific limits

        Returns:
            True if size is within limits
        """
        if endpoint_path.startswith("/webhooks/mailgun/"):
            # Email webhooks can be larger
            return size <= self.max_email_size
        elif endpoint_path.startswith("/api/"):
            # API endpoints have JSON payload limits
            return size <= self.max_json_payload
        else:
            # Default request size limit
            return size <= self.max_request_size

    def get_security_headers(self, environment: str = "production") -> Dict[str, str]:
        """
        Get security headers for response.

        Args:
            environment: Application environment

        Returns:
            Dictionary of security headers
        """
        headers = self.security_headers.copy()

        # Adjust headers based on environment
        if environment == "development":
            # Relax CSP for development
            headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'"

        return headers


# Global security config instance (will be initialized by SecurityManager)
_security_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """
    Get the global security configuration instance.

    Returns:
        SecurityConfig instance
    """
    global _security_config

    if _security_config is None:
        try:
            # Import unified config and create security config
            from core import get_app_config

            unified_config = get_app_config()
            _security_config = SecurityConfig.from_unified_config(unified_config)

            logger.info("Security configuration loaded from unified config system")

        except Exception as e:
            logger.warning(f"Failed to load unified config, using default security config: {e}")
            _security_config = SecurityConfig()

    return _security_config


def reload_security_config() -> None:
    """Force reload of security configuration."""
    global _security_config
    _security_config = None
    get_security_config()
