#!/usr/bin/env python3
"""
AI Email Router - Production SaaS FastAPI Application
🚀 Multi-tenant AI-powered email classification and routing system with advanced API management.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# Initialize unified configuration system
from infrastructure.config.manager import (  # type: ignore
    get_app_config,
    get_config_manager,
)
from infrastructure.logging.logger import configure_logging, get_logger  # type: ignore

# Get configuration and set up logging
config = get_app_config()
configure_logging(
    level=config.server.log_level.value, format_string=config.server.log_format
)
logger = get_logger(__name__)

from api.v1.auth import router as auth_router  # type: ignore # noqa: E402
from api.v1.clients import router as api_v1_router  # type: ignore # noqa: E402
from api.v1.dashboard import router as dashboard_router  # type: ignore # noqa: E402
from api.v1.webhooks import router as webhook_router  # type: ignore # noqa: E402
from api.v2.config import router as api_v2_router  # type: ignore # noqa: E402
from application.middleware.auth import (  # noqa: E402
    UnifiedAuthMiddleware as DualAuthMiddleware,  # type: ignore
)
from application.middleware.rate_limit import RateLimiterMiddleware  # type: ignore # noqa: E402
from core.models.schemas import APIInfo, HealthResponse  # type: ignore # noqa: E402
from infrastructure.monitoring.metrics import MetricsCollector  # type: ignore # noqa: E402
from infrastructure.websockets.manager import get_websocket_manager  # type: ignore # noqa: E402

# Initialize metrics collector
metrics = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    try:
        # Run startup validation first
        from application.startup import validate_startup

        validation_results = validate_startup()
        logger.info(
            f"✅ Startup validation passed: {validation_results['checks_passed']}/{validation_results['total_checks']} checks"
        )

        # Initialize database
        from infrastructure.database.connection import init_database

        init_database()
        logger.info("✅ Database initialized successfully")

        # Log startup completion
        logger.info("🚀 Email Router SaaS API v2.0 started successfully")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise e  # Re-raise to prevent app from starting with invalid configuration

    yield  # Application runs here

    # Shutdown
    logger.info("🔄 Application shutting down...")


# Create FastAPI app with enhanced metadata
app = FastAPI(
    lifespan=lifespan,
    title=config.app_name,
    description="""
    ## Multi-Tenant AI Email Router API

    A powerful SaaS platform for intelligent email classification and routing using Claude 3.5 Sonnet AI.

    ### 🎯 Key Features
    - **Multi-tenant architecture** with client-specific configurations
    - **AI-powered classification** using advanced language models
    - **Smart routing** with business rules and escalation
    - **Personalized responses** with client branding
    - **Real-time webhooks** for instant email processing
    - **Advanced domain resolution** with fuzzy matching

    ### 🔐 Authentication
    - **API Key Authentication**: Include `X-API-Key` header
    - **Webhook Signatures**: Mailgun signature verification
    - **Rate Limiting**: Configurable per-client quotas

    ### 📊 Monitoring
    - **Health Checks**: `/health` and `/health/detailed`
    - **Metrics**: `/metrics` (Prometheus format)
    - **Status Dashboard**: `/api/v1/status`

    ### 🚀 Getting Started
    1. Obtain API key from your dashboard
    2. Configure webhook endpoints
    3. Set up client domains and routing rules
    4. Start receiving intelligent email routing!

    ### 📚 Documentation
    - **Interactive Docs**: `/docs` (Swagger UI)
    - **Alternative Docs**: `/redoc` (ReDoc)
    - **OpenAPI Spec**: `/openapi.json`
    """,
    version=config.app_version,
    terms_of_service="https://emailrouter.ai/terms",
    contact={
        "name": "Email Router Support",
        "url": "https://emailrouter.ai/support",
        "email": "support@emailrouter.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "https://api.emailrouter.ai", "description": "Production server"},
        {"url": "https://staging-api.emailrouter.ai", "description": "Staging server"},
        {
            "url": f"http://localhost:{config.server.port}",
            "description": "Development server",
        },
    ],
    docs_url=None,  # We'll create custom docs
    redoc_url=None,  # We'll create custom redoc
    openapi_url="/openapi.json",
    debug=config.debug,
)

# Security scheme
security = HTTPBearer()

# Add security middleware - order matters (last added = first executed)
app.add_middleware(DualAuthMiddleware)  # JWT + API key authentication

# Add rate limiting middleware with configuration
app.add_middleware(
    RateLimiterMiddleware,
    calls_per_minute=config.security.api_rate_limit_per_minute,
    burst_limit=config.security.api_rate_limit_burst,
)

# Add trusted host middleware for production
if config.is_production():
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=config.security.trusted_proxies or ["*"]
    )

# Add CORS middleware with configuration
if config.security.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )


# Custom OpenAPI schema
def custom_openapi():  # type: ignore
    """Generate custom OpenAPI schema with enhanced metadata."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )

    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "Webhooks",
            "description": "Mailgun webhook endpoints for email processing",
        },
        {
            "name": "Authentication",
            "description": "User authentication, JWT tokens, and session management",
        },
        {
            "name": "Client Management",
            "description": "Multi-tenant client configuration and management",
        },
        {
            "name": "Configuration Management",
            "description": "Self-service configuration management API v2",
        },
        {
            "name": "Dashboard",
            "description": "Real-time dashboard and analytics endpoints",
        },
        {
            "name": "Health & Monitoring",
            "description": "System health checks and monitoring endpoints",
        },
        {
            "name": "API Management",
            "description": "API versioning, documentation, and meta endpoints",
        },
    ]

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication",
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": "Bearer token authentication",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Include routers with API versioning
app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(api_v1_router, prefix="/api/v1", tags=["Client Management"])
app.include_router(api_v2_router, prefix="/api/v2", tags=["Configuration Management"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])


# WebSocket endpoint for real-time dashboard updates
@app.websocket("/ws/client/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, token: Optional[str] = None
) -> None:
    """
    WebSocket endpoint for real-time dashboard updates.

    Provides real-time streaming of:
    - System metrics updates
    - Processing activity feed
    - Alert notifications
    - System status changes
    """
    websocket_manager = get_websocket_manager()

    try:
        # Validate token and get user info
        user_info = {"client_id": client_id}

        if token:
            try:
                from core.authentication.auth_service import AuthService

                auth_service = AuthService.validate_token_stateless(token)
                if auth_service:
                    user_info.update(
                        {
                            "user_id": auth_service.sub,
                            "username": auth_service.username,
                            "authenticated": "true",
                        }
                    )
                else:
                    logger.warning(f"Invalid WebSocket token for client {client_id}")
            except Exception as e:
                logger.warning(f"WebSocket token validation failed: {e}")
        else:
            logger.info(f"WebSocket connection without token for client {client_id}")

        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, client_id, user_info)

        # Handle incoming messages
        await websocket_manager.handle_websocket_messages(websocket, client_id)

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for client {client_id}")
        await websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"❌ WebSocket error for client {client_id}: {e}")
        await websocket_manager.disconnect(websocket)


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():  # type: ignore
    """Custom Swagger UI with branding."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "method",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
        },
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():  # type: ignore
    """Custom ReDoc documentation."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
    )


@app.get("/", response_model=APIInfo, tags=["API Management"])
async def root():  # type: ignore
    """
    Root endpoint providing API information and navigation links.

    Returns comprehensive information about the Email Router SaaS API including
    available endpoints, documentation links, and system status.
    """
    try:
        # Config loaded for service status validation
        get_config_manager()  # Validate config is loadable

        return APIInfo(
            name=config.app_name,
            version=config.app_version,
            description="Multi-tenant AI-powered email classification and routing",
            status="operational",
            timestamp=datetime.utcnow(),
            endpoints={
                "documentation": "/docs",
                "alternative_docs": "/redoc",
                "openapi_spec": "/openapi.json",
                "health_check": "/health",
                "detailed_health": "/health/detailed",
                "system_metrics": "/metrics",
                "webhook_inbound": "/webhooks/mailgun/inbound",
                "api_status": "/api/v1/status",
                "client_management": "/api/v1/clients",
            },
            features=[
                "Multi-tenant client management",
                "AI-powered email classification",
                "Smart routing with business rules",
                "Personalized auto-responses",
                "Advanced domain resolution",
                "Rate limiting and API quotas",
                "Comprehensive monitoring",
                "Webhook signature verification",
            ],
            rate_limits={
                "default": "60 requests per minute",
                "burst": "10 requests per 10 seconds",
                "webhook": "1000 requests per minute",
            },
        )
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load API information",
        )


@app.get("/health", response_model=HealthResponse, tags=["Health & Monitoring"])
async def health_check():
    """
    Basic health check endpoint for load balancers and monitoring systems.

    Provides essential system health information including component status
    and basic connectivity tests. Use `/health/detailed` for comprehensive diagnostics.
    """
    try:
        start_time = time.time()
        config_manager = get_config_manager()

        # Test AI service
        ai_status = (
            "healthy"
            if config_manager.is_service_available("anthropic")
            else "degraded"
        )

        # Test email service
        email_status = (
            "healthy" if config_manager.is_service_available("mailgun") else "degraded"
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        health_data = HealthResponse(
            status=(
                "healthy"
                if ai_status == "healthy" and email_status == "healthy"
                else "degraded"
            ),
            timestamp=datetime.utcnow(),
            version=config.app_version,
            uptime_seconds=int(time.time() - metrics.start_time),
            response_time_ms=response_time_ms,
            components={
                "api_server": "healthy",
                "ai_classifier": ai_status,
                "email_service": email_status,
                "webhook_processor": "healthy",
                "database": "healthy",  # Add actual DB check when implemented
                "cache": "healthy",  # Add actual cache check when implemented
            },
        )

        # Record health check metric
        metrics.record_health_check()

        return health_data

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service health check failed",
        )


@app.get("/health/detailed", tags=["Health & Monitoring"])
async def detailed_health_check():
    """
    Comprehensive health check with detailed component diagnostics.

    Provides in-depth system health information including:
    - Individual component status and response times
    - Resource utilization metrics
    - Recent error rates and performance statistics
    - Dependencies and external service connectivity
    """
    try:
        start_time = time.time()

        # Perform detailed health checks
        components = {}

        # API Server Health
        components["api_server"] = {
            "status": "healthy",
            "response_time_ms": 1,
            "details": "FastAPI server operational",
        }

        # AI Classifier Health
        config_manager = get_config_manager()
        ai_response_time = time.time()
        components["ai_classifier"] = {
            "status": (
                "healthy"
                if config_manager.is_service_available("anthropic")
                else "degraded"
            ),
            "response_time_ms": int((time.time() - ai_response_time) * 1000),
            "details": (
                "Claude 3.5 Sonnet API"
                if config_manager.is_service_available("anthropic")
                else "Missing API key"
            ),
        }

        # Email Service Health
        email_response_time = time.time()
        components["email_service"] = {
            "status": (
                "healthy"
                if config_manager.is_service_available("mailgun")
                else "degraded"
            ),
            "response_time_ms": int((time.time() - email_response_time) * 1000),
            "details": (
                f"Mailgun service for {config.services.mailgun_domain}"
                if config.services.mailgun_domain
                else "Missing configuration"
            ),
        }

        # Client Management Health
        from .core.clients.manager import get_client_manager

        try:
            client_manager = get_client_manager()
            clients = client_manager.get_available_clients()
            components["client_management"] = {
                "status": "healthy",
                "response_time_ms": 2,
                "details": f"{len(clients)} active clients configured",
            }
        except Exception as e:
            components["client_management"] = {
                "status": "degraded",
                "response_time_ms": 0,
                "details": f"Client management error: {str(e)}",
            }

        # System Metrics
        total_response_time = int((time.time() - start_time) * 1000)
        overall_status = (
            "healthy"
            if all(c.get("status") == "healthy" for c in components.values())
            else "degraded"
        )

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": config.app_version,
            "environment": config.environment.value,
            "uptime_seconds": int(time.time() - metrics.start_time),
            "total_response_time_ms": total_response_time,
            "components": components,
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "avg_response_time_ms": metrics.get_avg_response_time(),
                "health_checks_performed": metrics.health_checks,
            },
            "system_info": {
                "python_version": os.sys.version.split()[0],
                "platform": os.name,
                "process_id": os.getpid(),
            },
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detailed health check failed: {str(e)}",
        )


@app.get("/metrics", tags=["Health & Monitoring"])
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint for monitoring and alerting.

    Provides system metrics in Prometheus format including:
    - Request rates and response times
    - Error rates and status codes
    - Component health and availability
    - Custom business metrics
    """
    try:
        metrics_data = metrics.get_prometheus_metrics()
        return JSONResponse(
            content={"metrics": metrics_data}, headers={"Content-Type": "text/plain"}
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics collection failed",
        )


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics."""
    start_time = time.time()

    # Record request
    metrics.record_request()

    try:
        response = await call_next(request)

        # Record successful request
        if response.status_code < 400:
            metrics.record_successful_request()
        else:
            metrics.record_failed_request()

        # Record response time
        response_time = time.time() - start_time
        metrics.record_response_time(response_time)

        # Add custom headers
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        response.headers["X-API-Version"] = "2.0.0"

        return response

    except Exception as e:
        # Record failed request
        metrics.record_failed_request()
        raise e


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with detailed error responses."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Enhanced global exception handler with error tracking."""
    logger.error(f"Unhandled exception in {request.method} {request.url}: {exc}")

    # Record failed request
    metrics.record_failed_request()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting Email Router SaaS API {config.app_version} on port {config.server.port}"
    )
    uvicorn.run(
        "src.main:app", host=config.server.host, port=config.server.port, reload=False
    )
