"""Client domain models.

These models represent client-related business entities in the core domain,
independent of infrastructure concerns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DomainInfo:
    """Represents domain configuration for a client."""

    primary: str
    aliases: List[str] = field(default_factory=list)
    catch_all: bool = False
    support_email: Optional[str] = None
    mailgun_domain: Optional[str] = None


@dataclass
class BrandingInfo:
    """Represents branding configuration for a client."""

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


@dataclass
class RoutingRule:
    """Represents an email routing rule."""

    category: str
    email: str
    backup_email: Optional[str] = None
    priority: int = 1
    enabled: bool = True


@dataclass
class EscalationRule:
    """Represents an escalation rule."""

    trigger_type: str  # "time", "keyword", "confidence"
    trigger_value: str  # Will be parsed based on trigger_type
    action: str  # "escalate", "route_to", "alert"
    target_email: str
    enabled: bool = True


@dataclass
class SLAInfo:
    """Represents Service Level Agreement configuration."""

    response_times: Dict[str, int] = field(
        default_factory=lambda: {
            "urgent": 15,  # minutes
            "high": 60,
            "medium": 240,
            "low": 1440,
        }
    )
    business_hours: Dict[str, Any] = field(
        default_factory=lambda: {
            "timezone": "UTC",
            "weekdays": {"start": "09:00", "end": "17:00"},
            "weekends": {"enabled": False},
        }
    )
    escalation_enabled: bool = True
    escalation_rules: List[EscalationRule] = field(default_factory=list)


@dataclass
class SettingsInfo:
    """Represents client-specific feature settings."""

    auto_reply_enabled: bool = True
    ai_classification_enabled: bool = True
    team_forwarding_enabled: bool = True
    escalation_enabled: bool = True
    custom_templates_enabled: bool = False
    analytics_enabled: bool = True
    webhook_notifications_enabled: bool = False
    webhook_url: Optional[str] = None
    debug_logging_enabled: bool = False


@dataclass
class ContactsInfo:
    """Represents contact information for the client."""

    primary_contact: str
    escalation_contact: str
    billing_contact: str


@dataclass
class ClientInfo:
    """Core domain model representing a client.

    This is the core business representation of a client,
    independent of how it's stored or configured.
    """

    client_id: str
    name: str
    domains: DomainInfo
    branding: BrandingInfo
    contacts: ContactsInfo
    routing: List[RoutingRule] = field(default_factory=list)
    sla: SLAInfo = field(default_factory=SLAInfo)
    settings: SettingsInfo = field(default_factory=SettingsInfo)
    industry: Optional[str] = None
    timezone: str = "UTC"
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    ai_categories: List[str] = field(
        default_factory=lambda: ["general", "support", "billing", "sales"]
    )
    custom_prompts: Dict[str, str] = field(default_factory=dict)
