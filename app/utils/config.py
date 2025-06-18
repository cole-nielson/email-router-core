"""
Legacy configuration compatibility wrapper.
🔧 Provides backward compatibility while transitioning to unified configuration system.

DEPRECATED: This module is deprecated. Use app.core.get_app_config() instead.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Legacy configuration class for backward compatibility."""

    # Anthropic Claude (Optional for API management mode)
    anthropic_api_key: Optional[str]
    anthropic_model: str

    # Mailgun (Optional for API management mode)
    mailgun_api_key: Optional[str]
    mailgun_domain: Optional[str]
    mailgun_webhook_signing_key: Optional[str]

    # Google Cloud (Optional for production)
    google_project_id: Optional[str] = None
    google_region: Optional[str] = None

    # Application settings
    environment: str = "development"
    port: int = 8080
    log_level: str = "INFO"

    # Service status flags
    ai_service_available: bool = True
    email_service_available: bool = True


def get_config() -> Config:
    """
    Legacy configuration loader.

    DEPRECATED: Use app.core.get_app_config() instead.

    This function provides backward compatibility by wrapping the new
    unified configuration system in the legacy Config interface.
    """
    logger.warning(
        "app.utils.config.get_config() is deprecated. " "Use app.core.get_app_config() instead."
    )

    try:
        # Import the new configuration system
        from ..core import get_app_config, get_config_manager

        new_config = get_app_config()
        config_manager = get_config_manager()

        # Map new configuration to legacy interface
        return Config(
            # Service credentials
            anthropic_api_key=new_config.services.anthropic_api_key,
            mailgun_api_key=new_config.services.mailgun_api_key,
            mailgun_domain=new_config.services.mailgun_domain,
            mailgun_webhook_signing_key=new_config.services.mailgun_webhook_signing_key,
            # Model and cloud settings
            anthropic_model=new_config.services.anthropic_model,
            google_project_id=new_config.services.google_cloud_project,
            google_region=new_config.services.google_cloud_region,
            # Application settings
            environment=new_config.environment.value,
            port=new_config.server.port,
            log_level=new_config.server.log_level.value,
            # Service availability flags
            ai_service_available=config_manager.is_service_available("anthropic"),
            email_service_available=config_manager.is_service_available("mailgun"),
        )

    except Exception as e:
        logger.error(
            f"Failed to load unified configuration, falling back to environment variables: {e}"
        )

        # Fallback to direct environment variable access
        import os

        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        mailgun_api_key = os.environ.get("MAILGUN_API_KEY")
        mailgun_domain = os.environ.get("MAILGUN_DOMAIN")

        return Config(
            anthropic_api_key=anthropic_api_key,
            mailgun_api_key=mailgun_api_key,
            mailgun_domain=mailgun_domain,
            mailgun_webhook_signing_key=os.environ.get("MAILGUN_WEBHOOK_SIGNING_KEY"),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            google_project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            google_region=os.environ.get("GOOGLE_CLOUD_REGION", "us-central1"),
            environment=os.environ.get("EMAIL_ROUTER_ENVIRONMENT", "development"),
            port=int(os.environ.get("PORT", 8080)),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            ai_service_available=bool(anthropic_api_key),
            email_service_available=bool(mailgun_api_key and mailgun_domain),
        )
