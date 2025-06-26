"""
SQLAlchemy models for configuration storage.
🗄️ Database schema for multi-tenant email router configurations.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


# Create base class for all models using SQLAlchemy 2.0 syntax
class Base(DeclarativeBase):
    pass


# =============================================================================
# USER MANAGEMENT & AUTHENTICATION MODELS
# =============================================================================


class UserRole(enum.Enum):
    """User role enumeration for RBAC system."""

    SUPER_ADMIN = "super_admin"  # Global access across all clients
    CLIENT_ADMIN = "client_admin"  # Full access within assigned client
    CLIENT_USER = "client_user"  # Limited access within assigned client


class UserStatus(enum.Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User accounts for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    username = Column(String(50), nullable=False, unique=True)  # Unique login identifier
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash

    # User information
    full_name = Column(String(200), nullable=False)
    role: Column[UserRole] = Column(Enum(UserRole), nullable=False, default=UserRole.CLIENT_USER)
    status: Column[UserStatus] = Column(
        Enum(UserStatus), nullable=False, default=UserStatus.PENDING
    )

    # Client association (null for super_admin)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=True)

    # Security fields
    last_login_at = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)

    # Token management
    jwt_refresh_token_hash = Column(String(255), nullable=True)  # For token revocation
    jwt_token_version = Column(Integer, nullable=False, default=1)  # For global logout

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # API access for agents
    api_access_enabled = Column(Boolean, nullable=False, default=True)
    rate_limit_tier = Column(
        String(20), nullable=False, default="standard"
    )  # standard, premium, enterprise

    # Relationships
    client = relationship("Client", back_populates="users")
    creator = relationship("User", remote_side=[id], foreign_keys=[created_by])
    permissions = relationship(
        "UserPermission",
        back_populates="user",
        cascade="all, delete-orphan",
        primaryjoin="User.id == UserPermission.user_id",
    )
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserPermission(Base):
    """Granular permissions for fine-grained access control (future agentic workflows)."""

    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Permission structure: resource:action (e.g., "routing:read", "branding:write")
    resource = Column(String(50), nullable=False)  # routing, branding, ai_prompts, etc.
    action = Column(String(20), nullable=False)  # read, write, delete, admin

    # Optional client scoping (null = all clients for super_admin)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=True)

    # Conditional permissions (JSON rules for complex logic)
    conditions = Column(JSON, nullable=True)  # Future: time-based, IP-based, etc.

    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship(
        "User",
        back_populates="permissions",
        foreign_keys=[user_id],
        primaryjoin="UserPermission.user_id == User.id",
    )
    client = relationship("Client")
    granter = relationship("User", foreign_keys=[granted_by])


class UserSession(Base):
    """Active user sessions for JWT token management and security."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session identification
    session_id = Column(String(255), nullable=False, unique=True)  # JWT jti claim
    token_type = Column(String(20), nullable=False)  # access, refresh

    # Security tracking
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)  # Geo-location if available

    # Session lifecycle
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # Session status
    is_active = Column(Boolean, nullable=False, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


class Client(Base):
    """Core client information table."""

    __tablename__ = "clients"

    id = Column(String(100), primary_key=True)  # client-001-example
    name = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    timezone = Column(String(50), nullable=False, default="UTC")
    business_hours = Column(String(20), nullable=False, default="9-17")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="client", cascade="all, delete-orphan")
    domains = relationship("ClientDomain", back_populates="client", cascade="all, delete-orphan")
    branding = relationship(
        "ClientBranding", back_populates="client", uselist=False, cascade="all, delete-orphan"
    )
    routing_rules = relationship(
        "RoutingRule", back_populates="client", cascade="all, delete-orphan"
    )
    response_times = relationship(
        "ResponseTime", back_populates="client", cascade="all, delete-orphan"
    )
    ai_prompts = relationship("AIPrompt", back_populates="client", cascade="all, delete-orphan")
    settings = relationship("ClientSetting", back_populates="client", cascade="all, delete-orphan")
    routing_history = relationship(
        "RoutingHistory", back_populates="client", cascade="all, delete-orphan"
    )


class ClientDomain(Base):
    """Client domain configuration."""

    __tablename__ = "client_domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False)

    domain_type = Column(String(20), nullable=False)  # primary, support, mailgun, alias
    domain_value = Column(String(200), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="domains")


class ClientBranding(Base):
    """Client branding configuration."""

    __tablename__ = "client_branding"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False, unique=True)

    company_name = Column(String(200), nullable=False)
    primary_color = Column(String(7), nullable=False, default="#667eea")  # Hex color
    secondary_color = Column(String(7), nullable=False, default="#764ba2")
    logo_url = Column(String(500), nullable=True)
    email_signature = Column(String(200), nullable=False)
    footer_text = Column(String(500), nullable=True)

    # Extended color palette stored as JSON
    colors = Column(JSON, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="branding")


class RoutingRule(Base):
    """Email routing rules for departments."""

    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False)

    category = Column(String(50), nullable=False)  # support, billing, sales, general
    email_address = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Escalation rules stored as JSON
    escalation_rules = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="routing_rules")


class ResponseTime(Base):
    """SLA response time configuration."""

    __tablename__ = "response_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False)

    category = Column(String(50), nullable=False)  # support, billing, sales, general, urgent
    target_response = Column(String(50), nullable=False)  # "within 4 hours"
    business_hours_only = Column(Boolean, nullable=False, default=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="response_times")


class AIPrompt(Base):
    """AI prompt templates for voice & tone."""

    __tablename__ = "ai_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False)

    prompt_type = Column(
        String(50), nullable=False
    )  # classification, acknowledgment, team-analysis
    prompt_content = Column(Text, nullable=False)

    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="ai_prompts")


class ClientSetting(Base):
    """Client-specific settings and feature flags."""

    __tablename__ = "client_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=False)

    setting_key = Column(String(100), nullable=False)
    setting_value = Column(JSON, nullable=True)  # Flexible value storage

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="settings")


class ConfigurationChange(Base):
    """Audit trail for configuration changes."""

    __tablename__ = "configuration_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False)

    change_type = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String(50), nullable=False)
    record_id = Column(String(100), nullable=True)

    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    changed_by = Column(String(100), nullable=True)  # User/API key identifier
    change_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# =============================================================================
# ANALYTICS & ROUTING HISTORY MODELS
# =============================================================================


class RoutingHistory(Base):
    """
    Routing analytics data for tracking email routing decisions.

    This model captures every routing decision made by the system for
    analytics, reporting, and performance analysis.
    """

    __tablename__ = "routing_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Email identification
    email_id = Column(String(255), nullable=True)  # Optional external email ID
    message_id = Column(String(255), nullable=True)  # Mailgun message ID

    # Client context
    client_id = Column(String(100), ForeignKey("clients.id"), nullable=True)

    # Email details
    sender_email = Column(String(200), nullable=False)
    sender_domain = Column(String(100), nullable=True)
    subject = Column(String(500), nullable=True)

    # Routing decision
    category = Column(String(50), nullable=False)  # support, billing, sales, etc.
    primary_destination = Column(String(200), nullable=False)  # Main routing target
    cc_destinations = Column(JSON, nullable=True)  # Additional recipients as JSON list

    # AI classification data
    confidence_level = Column(Float, nullable=True)  # AI confidence score (0.0-1.0)
    ai_model = Column(String(50), nullable=True)  # Model used (e.g., claude-3-5-sonnet)
    classification_method = Column(
        String(30), nullable=False, default="ai"
    )  # ai, keyword, fallback

    # Special handling
    special_handling = Column(JSON, nullable=True)  # List of special flags
    escalated = Column(Boolean, nullable=False, default=False)
    priority_level = Column(String(20), nullable=True)  # urgent, high, medium, low

    # Routing performance
    processing_time_ms = Column(Integer, nullable=True)  # Total processing time
    classification_time_ms = Column(Integer, nullable=True)  # Time for AI classification
    routing_time_ms = Column(Integer, nullable=True)  # Time for routing decision

    # Business context
    business_hours = Column(Boolean, nullable=True)  # Was it during business hours?
    day_of_week = Column(String(10), nullable=True)  # Monday, Tuesday, etc.

    # Routing metadata
    routing_version = Column(String(20), nullable=True)  # Version of routing rules used
    fallback_used = Column(Boolean, nullable=False, default=False)
    error_occurred = Column(Boolean, nullable=False, default=False)
    error_details = Column(Text, nullable=True)

    # Additional metadata for future analysis
    additional_metadata = Column(JSON, nullable=True)  # Flexible storage for additional data

    # Timestamps
    routed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="routing_history", foreign_keys=[client_id])
