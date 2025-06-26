"""
Configuration Manager Adapter

This adapter implements the ConfigurationProvider interface,
wrapping the existing ConfigManager to provide configuration
services to the core layer.
"""

from typing import Any, Dict, Optional

from core.models.client import (
    BrandingInfo,
    ClientInfo,
    ContactsInfo,
    DomainInfo,
    EscalationRule,
    RoutingRule,
    SettingsInfo,
    SLAInfo,
)
from core.ports.config_provider import ConfigurationProvider
from infrastructure.config.manager import ConfigManager, get_config_manager
from infrastructure.config.schema import ClientConfig


class ConfigManagerAdapter(ConfigurationProvider):
    """
    Adapter that implements ConfigurationProvider interface using ConfigManager.

    This adapter wraps the existing ConfigManager infrastructure component
    to provide configuration services through the abstract interface expected
    by the core business logic layer.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the adapter with a ConfigManager instance.

        Args:
            config_manager: Optional ConfigManager instance. If not provided,
                          the singleton instance will be used.
        """
        self._config_manager = config_manager or get_config_manager()

    def get_all_clients(self) -> Dict[str, ClientInfo]:
        """
        Get all available client configurations.

        Returns:
            Dictionary mapping client_id to ClientInfo objects
        """
        infra_clients = self._config_manager.get_all_clients()
        return {
            client_id: self._convert_to_domain_model(client_config)
            for client_id, client_config in infra_clients.items()
        }

    def get_client_config(self, client_id: str) -> Optional[ClientInfo]:
        """
        Get configuration for a specific client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            ClientInfo object if found, None otherwise
        """
        infra_config = self._config_manager.get_client_config(client_id)
        return self._convert_to_domain_model(infra_config) if infra_config else None

    def reload_client_config(self, client_id: str) -> bool:
        """
        Reload configuration for a specific client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            True if reload was successful, False otherwise
        """
        return self._config_manager.reload_client_config(client_id)

    def reload_configuration(self) -> None:
        """
        Reload all configurations.

        Note: The ConfigManager's reload_configuration is a module-level function,
        not a method. We need to import and call it directly.
        """
        from infrastructure.config.manager import reload_configuration

        reload_configuration()

    def load_ai_prompt(self, client_id: str, template_type: str) -> str:
        """
        Load an AI prompt/template for a specific client.

        Args:
            client_id: Unique identifier for the client
            template_type: Type of template to load

        Returns:
            The prompt/template content as a string

        Raises:
            ConfigurationError: If the template cannot be loaded
        """
        return self._config_manager.load_ai_prompt(client_id, template_type)

    def load_fallback_responses(self, client_id: str) -> Dict[str, Any]:
        """
        Load fallback response configuration for a client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            Dictionary containing fallback response configuration

        Raises:
            ConfigurationError: If fallback responses cannot be loaded
        """
        return self._config_manager.load_fallback_responses(client_id)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key (e.g., 'services.anthropic_api_key')
            default: Default value if key is not found

        Returns:
            The configuration value or default if not found
        """
        # Navigate nested configuration using dot notation
        config = self._config_manager._config
        if not config:
            return default

        parts = key.split(".")
        value = config

        try:
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default
            return value
        except (AttributeError, KeyError):
            return default

    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value by key.

        Args:
            key: The configuration key

        Returns:
            The configuration value

        Raises:
            ValueError: If the key is not found
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required configuration '{key}' not found")
        return value

    def _convert_to_domain_model(self, client_config: ClientConfig) -> ClientInfo:
        """
        Convert infrastructure ClientConfig to domain ClientInfo.

        Args:
            client_config: Infrastructure client configuration

        Returns:
            Domain client information model
        """
        # Convert domains
        domains = DomainInfo(
            primary=client_config.domains.primary,
            aliases=client_config.domains.aliases,
            catch_all=client_config.domains.catch_all,
            support_email=client_config.domains.support,
            mailgun_domain=client_config.domains.mailgun,
        )

        # Convert branding
        branding = BrandingInfo(
            company_name=client_config.branding.company_name,
            logo_url=client_config.branding.logo_url,
            primary_color=client_config.branding.primary_color,
            secondary_color=client_config.branding.secondary_color,
            header_gradient=client_config.branding.header_gradient,
            header_text_color=client_config.branding.header_text_color,
            body_background=client_config.branding.body_background,
            body_text_color=client_config.branding.body_text_color,
            accent_background=client_config.branding.accent_background,
            accent_border_color=client_config.branding.accent_border_color,
            footer_background=client_config.branding.footer_background,
            footer_text_color=client_config.branding.footer_text_color,
            link_color=client_config.branding.link_color,
            footer_text=client_config.branding.footer_text,
            email_signature=client_config.branding.email_signature,
        )

        # Convert contacts
        contacts = ContactsInfo(
            primary_contact=client_config.contacts.primary_contact,
            escalation_contact=client_config.contacts.escalation_contact,
            billing_contact=client_config.contacts.billing_contact,
        )

        # Convert routing rules
        routing = [
            RoutingRule(
                category=rule.category,
                email=rule.email,
                backup_email=rule.backup_email,
                priority=rule.priority,
                enabled=rule.enabled,
            )
            for rule in client_config.routing
        ]

        # Convert escalation rules
        escalation_rules = [
            EscalationRule(
                trigger_type=rule.trigger_type,
                trigger_value=str(rule.trigger_value),
                action=rule.action,
                target_email=rule.target_email,
                enabled=rule.enabled,
            )
            for rule in client_config.sla.escalation_rules
        ]

        # Convert SLA
        sla = SLAInfo(
            response_times=client_config.sla.response_times,
            business_hours=client_config.sla.business_hours,
            escalation_enabled=client_config.sla.escalation_enabled,
            escalation_rules=escalation_rules,
        )

        # Convert settings
        settings = SettingsInfo(
            auto_reply_enabled=client_config.settings.auto_reply_enabled,
            ai_classification_enabled=client_config.settings.ai_classification_enabled,
            team_forwarding_enabled=client_config.settings.team_forwarding_enabled,
            escalation_enabled=client_config.settings.escalation_enabled,
            custom_templates_enabled=client_config.settings.custom_templates_enabled,
            analytics_enabled=client_config.settings.analytics_enabled,
            webhook_notifications_enabled=client_config.settings.webhook_notifications_enabled,
            webhook_url=client_config.settings.webhook_url,
            debug_logging_enabled=client_config.settings.debug_logging_enabled,
        )

        # Create domain model
        return ClientInfo(
            client_id=client_config.client_id,
            name=client_config.name,
            domains=domains,
            branding=branding,
            contacts=contacts,
            routing=routing,
            sla=sla,
            settings=settings,
            industry=client_config.industry,
            timezone=client_config.timezone,
            active=client_config.active,
            created_at=client_config.created_at,
            updated_at=client_config.updated_at,
            ai_categories=client_config.ai_categories,
            custom_prompts=client_config.custom_prompts,
        )
