"""
Production security configuration and hardening utilities.
Implements security best practices for production deployment.
"""
import os
import secrets
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Production security configuration and utilities."""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = "60/minute"
    API_RATE_LIMIT = "300/minute"
    AUTH_RATE_LIMIT = "10/minute"
    WEBHOOK_RATE_LIMIT = "1000/minute"
    
    # Session security
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
    SESSION_TIMEOUT_MINUTES = 60
    MAX_CONCURRENT_SESSIONS = 5
    
    # API Key security
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "er_"  # email-router prefix
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Content validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_EMAIL_SIZE = 25 * 1024 * 1024    # 25MB (Mailgun limit)
    MAX_JSON_PAYLOAD = 1024 * 1024       # 1MB
    
    # Logging and monitoring
    LOG_SECURITY_EVENTS = True
    LOG_FAILED_ATTEMPTS = True
    ALERT_THRESHOLD_FAILED_LOGINS = 5
    ALERT_THRESHOLD_TIMESPAN_MINUTES = 15
    
    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, List[str]]:
        """
        Validate password against security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters long")
        
        if cls.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if cls.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if cls.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if cls.PASSWORD_REQUIRE_SPECIAL and not any(c in cls.PASSWORD_SPECIAL_CHARS for c in password):
            errors.append(f"Password must contain at least one special character: {cls.PASSWORD_SPECIAL_CHARS}")
        
        # Check for common weak passwords
        weak_patterns = ['password', '123456', 'admin', 'user', 'test']
        if any(pattern in password.lower() for pattern in weak_patterns):
            errors.append("Password contains common weak patterns")
        
        return len(errors) == 0, errors
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Hex-encoded secure token
        """
        return secrets.token_hex(length)
    
    @classmethod
    def generate_api_key(cls) -> str:
        """
        Generate secure API key with prefix.
        
        Returns:
            Formatted API key with prefix
        """
        token = cls.generate_secure_token(cls.API_KEY_LENGTH)
        return f"{cls.API_KEY_PREFIX}{token}"
    
    @classmethod
    def hash_api_key(cls, api_key: str) -> str:
        """
        Hash API key for secure storage.
        
        Args:
            api_key: Raw API key
            
        Returns:
            SHA-256 hash of API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @classmethod
    def validate_api_key_format(cls, api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        if not api_key.startswith(cls.API_KEY_PREFIX):
            return False
        
        # Remove prefix and check length
        token_part = api_key[len(cls.API_KEY_PREFIX):]
        expected_length = cls.API_KEY_LENGTH * 2  # Hex encoding doubles length
        
        return len(token_part) == expected_length and all(c in '0123456789abcdef' for c in token_part.lower())
    
    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Extract client IP address from request, handling proxies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (from load balancers/proxies)
        forwarded_ips = [
            request.headers.get("X-Forwarded-For"),
            request.headers.get("X-Real-IP"),
            request.headers.get("CF-Connecting-IP"),  # Cloudflare
        ]
        
        for ip_header in forwarded_ips:
            if ip_header:
                # Take first IP from comma-separated list
                return ip_header.split(',')[0].strip()
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    @classmethod
    def is_suspicious_request(cls, request) -> tuple[bool, str]:
        """
        Check if request exhibits suspicious characteristics.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (is_suspicious, reason)
        """
        # Check for suspicious headers
        suspicious_headers = [
            "X-Forwarded-Host",
            "X-Originating-IP", 
            "X-Remote-IP",
            "X-Injection-Test"
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                return True, f"Suspicious header detected: {header}"
        
        # Check user agent
        user_agent = request.headers.get("User-Agent", "").lower()
        suspicious_agents = ["sqlmap", "nikto", "dirb", "nmap", "masscan"]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                return True, f"Suspicious user agent: {agent}"
        
        # Check for SQL injection patterns in query params
        query_params = str(request.url.query).lower()
        sql_patterns = ["'", "union", "select", "drop", "insert", "delete", "script", "<script"]
        
        for pattern in sql_patterns:
            if pattern in query_params:
                return True, f"Potential injection attempt in query: {pattern}"
        
        return False, ""
    
    @classmethod
    def log_security_event(cls, event_type: str, details: Dict, ip_address: str = None, user_id: str = None):
        """
        Log security-related events for monitoring and alerting.
        
        Args:
            event_type: Type of security event
            details: Event details dictionary
            ip_address: Client IP address
            user_id: User ID if applicable
        """
        if not cls.LOG_SECURITY_EVENTS:
            return
        
        security_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "ip_address": ip_address,
            "user_id": user_id,
            "severity": cls._get_event_severity(event_type)
        }
        
        logger.warning(f"SECURITY_EVENT: {security_log}")
        
        # In production, send to SIEM/monitoring system
        # self._send_to_monitoring_system(security_log)
    
    @classmethod
    def _get_event_severity(cls, event_type: str) -> str:
        """Get severity level for security event type."""
        high_severity = [
            "authentication_failure",
            "suspicious_request",
            "injection_attempt",
            "brute_force_attempt",
            "unauthorized_access"
        ]
        
        medium_severity = [
            "rate_limit_exceeded",
            "invalid_api_key",
            "session_timeout",
            "password_reset_request"
        ]
        
        if event_type in high_severity:
            return "HIGH"
        elif event_type in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"


# Security middleware helpers
def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return SecurityConfig.SECURITY_HEADERS


def validate_request_size(content_length: Optional[int]) -> bool:
    """Validate request size against limits."""
    if content_length is None:
        return True  # No content-length header
    
    return content_length <= SecurityConfig.MAX_REQUEST_SIZE


def generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return f"req_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"


# Environment-specific security configurations
def get_production_security_config() -> Dict[str, any]:
    """Get production-specific security configuration."""
    return {
        "debug": False,
        "testing": False,
        "log_level": "WARNING",
        "cors_origins": [
            "https://emailrouter.ai",
            "https://*.emailrouter.ai"
        ],
        "trusted_hosts": [
            "emailrouter.ai", 
            "*.emailrouter.ai",
            "*.run.app"  # Google Cloud Run
        ],
        "rate_limits": {
            "default": SecurityConfig.DEFAULT_RATE_LIMIT,
            "api": SecurityConfig.API_RATE_LIMIT,
            "auth": SecurityConfig.AUTH_RATE_LIMIT,
            "webhook": SecurityConfig.WEBHOOK_RATE_LIMIT
        },
        "session_config": {
            "secure": True,
            "httponly": True,
            "samesite": "strict",
            "max_age": SecurityConfig.SESSION_TIMEOUT_MINUTES * 60
        },
        "jwt_config": {
            "algorithm": "HS256",
            "access_token_expire_minutes": SecurityConfig.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": SecurityConfig.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        }
    }


def get_development_security_config() -> Dict[str, any]:
    """Get development-specific security configuration."""
    config = get_production_security_config()
    
    # Relaxed settings for development
    config.update({
        "debug": True,
        "log_level": "INFO",
        "cors_origins": [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ],
        "trusted_hosts": ["*"],  # Allow all hosts in development
        "session_config": {
            "secure": False,  # Allow HTTP cookies in development
            "httponly": True,
            "samesite": "lax",
            "max_age": SecurityConfig.SESSION_TIMEOUT_MINUTES * 60
        }
    })
    
    return config