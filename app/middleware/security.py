"""
Security middleware for production hardening.
Implements security headers, request validation, and threat detection.
"""
import logging
import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.security_config import (
    SecurityConfig, 
    get_security_headers,
    validate_request_size,
    generate_request_id
)

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for request validation and threat detection.
    
    Features:
    - Security headers injection
    - Request size validation  
    - Suspicious request detection
    - Request ID generation
    - Security event logging
    """
    
    def __init__(self, app, enable_threat_detection: bool = True):
        super().__init__(app)
        self.enable_threat_detection = enable_threat_detection
        self.security_headers = get_security_headers()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks."""
        start_time = time.time()
        
        # Generate unique request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        try:
            # Pre-flight security checks
            await self._validate_request(request)
            
            # Process request
            response = await call_next(request)
            
            # Post-processing security enhancements
            self._add_security_headers(response)
            self._add_request_metadata(response, request_id, start_time)
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            # Log unexpected errors and return safe response
            SecurityConfig.log_security_event(
                "middleware_error", 
                {"error": str(e), "path": str(request.url.path), "method": request.method},
                SecurityConfig.get_client_ip(request)
            )
            
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": True,
                    "message": "Request processing failed",
                    "request_id": request_id
                }
            )
    
    async def _validate_request(self, request: Request) -> None:
        """Perform pre-flight request validation."""
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if not validate_request_size(size):
                    SecurityConfig.log_security_event(
                        "request_too_large",
                        {"size": size, "limit": SecurityConfig.MAX_REQUEST_SIZE},
                        SecurityConfig.get_client_ip(request)
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large"
                    )
            except ValueError:
                # Invalid content-length header
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content-length header"
                )
        
        # Threat detection
        if self.enable_threat_detection:
            await self._detect_threats(request)
    
    async def _detect_threats(self, request: Request) -> None:
        """Detect and block suspicious requests."""
        is_suspicious, reason = SecurityConfig.is_suspicious_request(request)
        
        if is_suspicious:
            client_ip = SecurityConfig.get_client_ip(request)
            
            SecurityConfig.log_security_event(
                "suspicious_request",
                {
                    "reason": reason,
                    "path": str(request.url.path),
                    "method": request.method,
                    "user_agent": request.headers.get("User-Agent", ""),
                    "query_params": str(request.url.query)
                },
                client_ip
            )
            
            # Block the request
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request blocked for security reasons"
            )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value
    
    def _add_request_metadata(self, response: Response, request_id: str, start_time: float) -> None:
        """Add request metadata headers."""
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{(time.time() - start_time):.3f}s"
        response.headers["X-Content-Type-Options"] = "nosniff"


class RateLimitingSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting with security-focused features.
    
    Features:
    - IP-based rate limiting
    - Endpoint-specific limits
    - Burst protection
    - Security event logging
    """
    
    def __init__(self, app, default_limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.request_counts = {}  # In production, use Redis
        self.blocked_ips = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting with security monitoring."""
        client_ip = SecurityConfig.get_client_ip(request)
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if self._is_ip_blocked(client_ip, current_time):
            SecurityConfig.log_security_event(
                "rate_limit_blocked",
                {"blocked_until": self.blocked_ips[client_ip]},
                client_ip
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. IP temporarily blocked."
            )
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time, request):
            # Log security event
            SecurityConfig.log_security_event(
                "rate_limit_exceeded",
                {
                    "limit": self.default_limit,
                    "window": self.window_seconds,
                    "path": str(request.url.path),
                    "method": request.method
                },
                client_ip
            )
            
            # Apply temporary block for repeated violations
            self._apply_temporary_block(client_ip, current_time)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {self.window_seconds} seconds."
            )
        
        # Update request count
        self._update_request_count(client_ip, current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip, current_time)
        
        return response
    
    def _is_ip_blocked(self, ip: str, current_time: float) -> bool:
        """Check if IP is temporarily blocked."""
        if ip not in self.blocked_ips:
            return False
        
        # Remove expired blocks
        if current_time > self.blocked_ips[ip]:
            del self.blocked_ips[ip]
            return False
        
        return True
    
    def _is_rate_limited(self, ip: str, current_time: float, request: Request) -> bool:
        """Check if request should be rate limited."""
        window_start = current_time - self.window_seconds
        
        if ip not in self.request_counts:
            return False
        
        # Clean old requests
        self.request_counts[ip] = [
            req_time for req_time in self.request_counts[ip] 
            if req_time > window_start
        ]
        
        # Get endpoint-specific limit
        limit = self._get_endpoint_limit(request)
        
        return len(self.request_counts[ip]) >= limit
    
    def _get_endpoint_limit(self, request: Request) -> int:
        """Get rate limit for specific endpoint."""
        path = request.url.path
        
        # Endpoint-specific limits
        if path.startswith("/auth/"):
            return 10  # Stricter limit for auth endpoints
        elif path.startswith("/webhooks/"):
            return 1000  # Higher limit for webhooks
        elif path.startswith("/api/"):
            return 300  # API endpoints
        
        return self.default_limit
    
    def _update_request_count(self, ip: str, current_time: float) -> None:
        """Update request count for IP."""
        if ip not in self.request_counts:
            self.request_counts[ip] = []
        
        self.request_counts[ip].append(current_time)
    
    def _apply_temporary_block(self, ip: str, current_time: float) -> None:
        """Apply temporary block for repeated violations."""
        # Block for 5 minutes
        block_duration = 300
        self.blocked_ips[ip] = current_time + block_duration
    
    def _add_rate_limit_headers(self, response: Response, ip: str, current_time: float) -> None:
        """Add rate limiting headers to response."""
        window_start = current_time - self.window_seconds
        
        if ip in self.request_counts:
            # Clean old requests for accurate count
            self.request_counts[ip] = [
                req_time for req_time in self.request_counts[ip] 
                if req_time > window_start
            ]
            
            remaining = max(0, self.default_limit - len(self.request_counts[ip]))
            response.headers["X-RateLimit-Limit"] = str(self.default_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(window_start + self.window_seconds))


# Middleware factory functions
def create_security_middleware(enable_threat_detection: bool = True):
    """Create security middleware with configuration."""
    def middleware_factory(app):
        return SecurityMiddleware(app, enable_threat_detection)
    return middleware_factory


def create_rate_limiting_middleware(default_limit: int = 60, window_seconds: int = 60):
    """Create rate limiting middleware with configuration.""" 
    def middleware_factory(app):
        return RateLimitingSecurityMiddleware(app, default_limit, window_seconds)
    return middleware_factory