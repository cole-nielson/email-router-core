"""
Unified Configuration Schema for Email Router
🏗️ Centralized configuration types and validation for the entire application.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# ENUMS FOR CONFIGURATION
# =============================================================================


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"
    TESTING = "testing"


class DatabaseType(str, Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityTier(str, Enum):
    """Security configuration tiers."""

    DEVELOPMENT = "development"
    STANDARD = "standard"
    HIGH = "high"
    ENTERPRISE = "enterprise"


# =============================================================================
# CORE CONFIGURATION MODELS
# =============================================================================


class DatabaseConfig(BaseModel):
    """Database connection and settings configuration."""

    type: DatabaseType = DatabaseType.SQLITE
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = Field(default=5, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=300)
    echo_sql: bool = False

    @field_validator("url", mode="before")
    @classmethod
    def build_database_url(cls, v: Optional[str], info: Any) -> str:
        """Build database URL from components if not provided."""
        if v:
            return v

        values = info.data if hasattr(info, "data") else {}
        db_type = values.get("type", DatabaseType.SQLITE)

        if db_type == DatabaseType.SQLITE:
            database = values.get("database", "data/email_router.db")
            return f"sqlite:///{database}"
        elif db_type == DatabaseType.POSTGRESQL:
            host = values.get("host", "localhost")
            port = values.get("port", 5432)
            database = values.get("database", "email_router")
            username = values.get("username", "postgres")
            password = values.get("password", "")
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == DatabaseType.MYSQL:
            host = values.get("host", "localhost")
            port = values.get("port", 3306)
            database = values.get("database", "email_router")
            username = values.get("username", "root")
            password = values.get("password", "")
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

        # Fallback to SQLite if database type is unknown
        database = values.get("database", "data/email_router.db")
        return f"sqlite:///{database}"


class SecurityConfig(BaseModel):
    """Security settings and policies."""

    tier: SecurityTier = SecurityTier.STANDARD
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=90)
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    lockout_duration_minutes: int = Field(default=15, ge=5, le=60)
    password_min_length: int = Field(default=12, ge=8, le=128)
    require_password_complexity: bool = True
    max_sessions_per_user: int = Field(default=5, ge=1, le=20)
    session_timeout_minutes: int = Field(default=60, ge=15, le=480)
    rate_limit_per_minute: int = Field(default=60, ge=10, le=1000)
    api_rate_limit_per_minute: int = Field(default=300, ge=50, le=5000)
    api_rate_limit_burst: int = Field(default=50, ge=10, le=200)
    enable_cors: bool = True
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    trusted_proxies: List[str] = Field(default_factory=list)
    enable_https_redirect: bool = False
    hsts_max_age: int = Field(default=31536000, ge=300)

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is sufficiently strong."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v


class ServiceConfig(BaseModel):
    """External service configuration."""

    anthropic_api_key: str
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = Field(default=1000, ge=100, le=4000)
    anthropic_timeout: int = Field(default=30, ge=5, le=120)

    mailgun_api_key: str
    mailgun_domain: str
    mailgun_webhook_signing_key: Optional[str] = None
    mailgun_timeout: int = Field(default=30, ge=5, le=120)

    google_cloud_project: Optional[str] = None
    google_cloud_region: str = "us-central1"

    enable_fallbacks: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=1, ge=0, le=30)


class ServerConfig(BaseModel):
    """Server and runtime configuration."""

    host: str = "0.0.0.0"
    port: int = Field(default=8080, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=32)
    max_connections: int = Field(default=1000, ge=100, le=10000)
    keepalive_timeout: int = Field(default=5, ge=1, le=30)
    log_level: LogLevel = LogLevel.INFO
    access_log: bool = True
    error_log: bool = True
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_metrics: bool = True
    metrics_path: str = "/metrics"
    enable_health_check: bool = True
    health_check_path: str = "/health"


class CacheConfig(BaseModel):
    """Caching configuration."""

    enabled: bool = True
    default_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    client_config_ttl: int = Field(default=600, ge=60, le=3600)
    ai_response_ttl: int = Field(default=1800, ge=300, le=7200)
    template_ttl: int = Field(default=3600, ge=600, le=86400)
    max_size_mb: int = Field(default=128, ge=16, le=1024)


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    enable_tracing: bool = False
    enable_profiling: bool = False
    error_tracking_dsn: Optional[str] = None
    metrics_retention_days: int = Field(default=30, ge=7, le=365)
    log_retention_days: int = Field(default=90, ge=7, le=365)
    alert_webhooks: List[str] = Field(default_factory=list)
    performance_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "response_time_ms": 1000.0,
            "error_rate_percent": 5.0,
            "cpu_usage_percent": 80.0,
            "memory_usage_percent": 85.0,
        }
    )


# =============================================================================
# CLIENT CONFIGURATION MODELS
# =============================================================================


class ClientDomainConfig(BaseModel):
    """Client domain configuration."""

    primary: str
    aliases: List[str] = Field(default_factory=list)
    catch_all: bool = False
    support: Optional[str] = None  # Support email address
    mailgun: Optional[str] = None  # Mailgun domain

    @field_validator("primary")
    @classmethod
    def validate_primary_domain(cls, v: str) -> str:
        """Basic domain validation."""
        if not v or "." not in v:
            raise ValueError("Primary domain must be a valid domain")
        return v.lower()

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, v: List[str]) -> List[str]:
        """Validate alias domains."""
        return [alias.lower() for alias in v]


class ClientBrandingConfig(BaseModel):
    """Client branding and visual configuration."""

    company_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    header_gradient: Optional[str] = None
    header_text_color: str = "#ffffff"
    body_background: str = "#ffffff"
    body_text_color: str = "#374151"
    accent_background: str = "#f8f9ff"
    accent_border_color: str = "#667eea"
    footer_background: str = "#f8f9fa"
    footer_text_color: str = "#6b7280"
    link_color: str = "#667eea"
    footer_text: str = ""
    email_signature: Optional[str] = None

    @field_validator(
        "primary_color",
        "secondary_color",
        "header_text_color",
        "body_background",
        "body_text_color",
        "accent_background",
        "accent_border_color",
        "footer_background",
        "footer_text_color",
        "link_color",
    )
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith("#") or len(v) not in [4, 7]:
            raise ValueError("Colors must be valid hex codes (#RGB or #RRGGBB)")
        return v


class ClientRoutingRule(BaseModel):
    """Individual routing rule for email categories."""

    category: str
    email: str
    backup_email: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)
    enabled: bool = True


class ClientEscalationRule(BaseModel):
    """Escalation rule configuration."""

    trigger_type: str  # "time", "keyword", "confidence"
    trigger_value: Union[int, str, float]
    action: str  # "escalate", "route_to", "alert"
    target_email: str
    enabled: bool = True


class ClientSLAConfig(BaseModel):
    """Service Level Agreement configuration."""

    response_times: Dict[str, int] = Field(
        default_factory=lambda: {
            "urgent": 15,  # minutes
            "high": 60,  # minutes
            "medium": 240,  # minutes (4 hours)
            "low": 1440,  # minutes (24 hours)
        }
    )
    business_hours: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timezone": "UTC",
            "weekdays": {"start": "09:00", "end": "17:00"},
            "weekends": {"enabled": False},
        }
    )
    escalation_enabled: bool = True
    escalation_rules: List[ClientEscalationRule] = Field(default_factory=list)


class ClientSettingsConfig(BaseModel):
    """Client-specific feature settings."""

    auto_reply_enabled: bool = True
    ai_classification_enabled: bool = True
    team_forwarding_enabled: bool = True
    escalation_enabled: bool = True
    custom_templates_enabled: bool = False
    analytics_enabled: bool = True
    webhook_notifications_enabled: bool = False
    webhook_url: Optional[str] = None
    debug_logging_enabled: bool = False


class ClientContactsConfig(BaseModel):
    """Contact information for the client."""

    primary_contact: str = Field(..., description="Primary contact email")
    escalation_contact: str = Field(..., description="Escalation contact email")
    billing_contact: str = Field(..., description="Billing contact email")


class ClientConfig(BaseModel):
    """Complete client configuration."""

    client_id: str
    name: str
    industry: Optional[str] = None
    timezone: str = "UTC"
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    domains: ClientDomainConfig
    branding: ClientBrandingConfig
    routing: List[ClientRoutingRule] = Field(default_factory=list)
    sla: ClientSLAConfig = Field(default_factory=ClientSLAConfig)
    settings: ClientSettingsConfig = Field(default_factory=ClientSettingsConfig)
    contacts: ClientContactsConfig

    # AI and Template Configuration
    ai_categories: List[str] = Field(
        default_factory=lambda: ["general", "support", "billing", "sales"]
    )
    custom_prompts: Dict[str, str] = Field(default_factory=dict)

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client ID format."""
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Client ID must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v.lower()


# =============================================================================
# MAIN APPLICATION CONFIGURATION
# =============================================================================


class AppConfig(BaseModel):
    """Main application configuration container."""

    # Environment and Meta
    environment: Environment = Environment.DEVELOPMENT
    app_name: str = "Email Router SaaS API"
    app_version: str = "2.0.0"
    debug: bool = False

    # Core Configuration Sections
    database: DatabaseConfig
    security: SecurityConfig
    services: ServiceConfig
    server: ServerConfig
    cache: CacheConfig = Field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Client Management
    client_config_path: str = "clients/active"
    template_path: str = "clients/templates"
    enable_client_isolation: bool = True
    max_clients: int = Field(default=100, ge=1, le=1000)

    # Fallback Configuration
    fallback_admin_email: str = Field(
        default="admin@example.com",
        description="Fallback admin email for unknown clients",
    )

    # Feature Flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "ai_classification": True,
            "email_sending": True,
            "webhooks": True,
            "analytics": True,
            "monitoring": True,
            "rate_limiting": True,
            "caching": True,
            "hot_reload": False,
        }
    )

    class Config:
        """Pydantic configuration."""

        env_prefix = "EMAIL_ROUTER_"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v: Union[str, Environment]) -> Environment:
        """Parse environment from string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
