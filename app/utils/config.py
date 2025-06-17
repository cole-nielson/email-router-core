"""
Clean configuration management with environment variables.
🔧 Optimized for Cloud Run deployment.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

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
    Load configuration from environment variables.

    For production email processing, the following are required:
    - ANTHROPIC_API_KEY: Your Anthropic API key
    - MAILGUN_API_KEY: Your Mailgun API key
    - MAILGUN_DOMAIN: Your Mailgun domain

    For API management and development, these can be omitted and services will run in degraded mode.

    Optional environment variables:
    - ANTHROPIC_MODEL: Claude model (default: claude-3-5-sonnet-20241022)
    - GOOGLE_CLOUD_PROJECT: Google Cloud project ID
    - GOOGLE_CLOUD_REGION: Google Cloud region (default: us-central1)
    - ENVIRONMENT: Application environment (default: development)
    - PORT: Server port (default: 8080)
    - LOG_LEVEL: Logging level (default: INFO)
    """

    # Check service availability
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    mailgun_api_key = os.environ.get("MAILGUN_API_KEY")
    mailgun_domain = os.environ.get("MAILGUN_DOMAIN")
    mailgun_webhook_signing_key = os.environ.get("MAILGUN_WEBHOOK_SIGNING_KEY")

    ai_service_available = bool(anthropic_api_key)
    email_service_available = bool(mailgun_api_key and mailgun_domain)

    # Log service status
    import logging

    logger = logging.getLogger(__name__)

    if not ai_service_available:
        logger.warning("AI service unavailable: ANTHROPIC_API_KEY not configured")

    if not email_service_available:
        logger.warning(
            "Email service unavailable: MAILGUN_API_KEY or MAILGUN_DOMAIN not configured"
        )

    if ai_service_available and email_service_available:
        logger.info("All services available: AI classification and email processing enabled")
    else:
        logger.info("Running in API management mode: some services degraded")

    return Config(
        # Service credentials (optional)
        anthropic_api_key=anthropic_api_key,
        mailgun_api_key=mailgun_api_key,
        mailgun_domain=mailgun_domain,
        mailgun_webhook_signing_key=mailgun_webhook_signing_key,
        # Optional with defaults
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        google_project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        google_region=os.environ.get("GOOGLE_CLOUD_REGION", "us-central1"),
        environment=os.environ.get("ENVIRONMENT", "development"),
        port=int(os.environ.get("PORT", 8080)),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        # Service availability flags
        ai_service_available=ai_service_available,
        email_service_available=email_service_available,
    )
