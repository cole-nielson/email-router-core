"""
Centralized Configuration Manager
🏗️ Unified configuration loading, validation, and management system.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import ValidationError

from ..utils.logger import get_logger
from .config_schema import AppConfig, ClientConfig, Environment

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Configuration-related errors."""

    pass


class ConfigManager:
    """Centralized configuration manager for the entire application."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        self._config: Optional[AppConfig] = None
        self._clients: Dict[str, ClientConfig] = {}
        self._config_path = config_path
        self._env_loaded = False

        # Load configuration on initialization
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load and validate all configuration."""
        try:
            # Load environment variables first
            self._load_environment_variables()

            # Load main app configuration
            self._config = self._build_app_config()

            # Validate configuration
            self._validate_configuration()

            # Load client configurations
            self._load_client_configurations()

            logger.info(
                f"Configuration loaded successfully for {self._config.environment} environment"
            )

        except Exception as e:
            logger.critical(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}") from e

    def _load_environment_variables(self) -> None:
        """Load and validate environment variables with comprehensive checks."""
        # Define required and optional variables with validation rules
        validation_rules = {
            "JWT_SECRET_KEY": {
                "required": True,
                "min_length": 32,
                "description": "JWT signing secret key (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')",
            },
            "ANTHROPIC_API_KEY": {
                "required": True,
                "starts_with": "sk-ant-",
                "description": "Anthropic Claude API key from https://console.anthropic.com/",
            },
            "MAILGUN_API_KEY": {
                "required": True,
                "starts_with": [
                    "key-",
                    "4bcea0",
                ],  # Allow both private and public keys for flexibility
                "description": "Mailgun API key from https://app.mailgun.com/",
            },
            "MAILGUN_DOMAIN": {
                "required": True,
                "must_contain": ".",
                "description": "Mailgun domain for sending emails",
            },
            "MAILGUN_WEBHOOK_SIGNING_KEY": {
                "required": False,
                "min_length": 10,
                "description": "Mailgun webhook signing key for security (recommended)",
            },
            "EMAIL_ROUTER_ENVIRONMENT": {
                "required": False,
                "allowed_values": ["development", "staging", "production", "test", "testing"],
                "description": "Application environment",
            },
        }

        missing_vars = []
        validation_warnings = []
        validation_errors = []

        for var_name, rules in validation_rules.items():
            value = os.getenv(var_name)

            # Check if required variable is missing
            if rules.get("required", False) and not value:
                missing_vars.append({"name": var_name, "description": rules.get("description", "")})
                continue

            # Skip validation if variable is not set and not required
            if not value:
                continue

            # Validate minimum length
            if "min_length" in rules and len(value) < rules["min_length"]:
                validation_errors.append(
                    f"{var_name} must be at least {rules['min_length']} characters long"
                )

            # Validate starts_with patterns
            if "starts_with" in rules:
                patterns = rules["starts_with"]
                if isinstance(patterns, str):
                    patterns = [patterns]
                if not any(value.startswith(pattern) for pattern in patterns):
                    validation_errors.append(
                        f"{var_name} must start with one of: {', '.join(patterns)}"
                    )

            # Validate must_contain patterns
            if "must_contain" in rules and rules["must_contain"] not in value:
                validation_errors.append(f"{var_name} must contain '{rules['must_contain']}'")

            # Validate allowed values
            if "allowed_values" in rules and value not in rules["allowed_values"]:
                validation_errors.append(
                    f"{var_name} must be one of: {', '.join(rules['allowed_values'])}"
                )

        # Handle missing required variables
        if missing_vars:
            error_msg = "Missing required environment variables:\n"
            for var in missing_vars:
                error_msg += f"  - {var['name']}: {var['description']}\n"
            error_msg += "\nSee .env.example for complete configuration template."

            logger.critical(error_msg)
            # Allow missing vars in test environment
            if not os.getenv("EMAIL_ROUTER_ENVIRONMENT", "").lower().startswith("test"):
                raise ConfigurationError(error_msg)

        # Handle validation errors
        if validation_errors:
            error_msg = "Environment variable validation failed:\n"
            for error in validation_errors:
                error_msg += f"  - {error}\n"

            logger.critical(error_msg)
            raise ConfigurationError(error_msg)

        # Log warnings for optional but recommended variables
        if not os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY"):
            validation_warnings.append(
                "MAILGUN_WEBHOOK_SIGNING_KEY not set - webhook security is reduced"
            )

        for warning in validation_warnings:
            logger.warning(warning)

        self._env_loaded = True
        logger.info(f"Environment variables loaded and validated successfully")
        if validation_warnings:
            logger.info(f"Configuration loaded with {len(validation_warnings)} warnings")

    def _build_app_config(self) -> AppConfig:
        """Build main application configuration from environment and files."""
        config_data = {}

        # Load from configuration file if specified
        if self._config_path and Path(self._config_path).exists():
            with open(self._config_path, "r") as f:
                file_config = yaml.safe_load(f)
                config_data.update(file_config)

        # Override with environment variables
        env_config = self._extract_env_config()
        config_data.update(env_config)

        # Build and validate configuration
        try:
            return AppConfig(**config_data)
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigurationError(f"Invalid configuration: {e}")

    def _extract_env_config(self) -> Dict[str, Any]:
        """Extract configuration from environment variables."""
        config = {}

        # Environment and basics
        config["environment"] = os.getenv("EMAIL_ROUTER_ENVIRONMENT", "development")
        config["debug"] = os.getenv("EMAIL_ROUTER_DEBUG", "false").lower() == "true"

        # Database configuration
        db_config = {}
        if db_url := os.getenv("DATABASE_URL"):
            db_config["url"] = db_url
        else:
            db_config.update(
                {
                    "type": os.getenv("DB_TYPE", "sqlite"),
                    "host": os.getenv("DB_HOST"),
                    "port": int(os.getenv("DB_PORT", "0")) or None,
                    "database": os.getenv("DB_NAME", "data/email_router.db"),
                    "username": os.getenv("DB_USER"),
                    "password": os.getenv("DB_PASSWORD"),
                }
            )
        config["database"] = db_config

        # Security configuration
        security_config = {
            "jwt_secret_key": os.getenv("JWT_SECRET_KEY", ""),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
            "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            "enable_cors": os.getenv("ENABLE_CORS", "true").lower() == "true",
        }

        if allowed_origins := os.getenv("ALLOWED_ORIGINS"):
            security_config["allowed_origins"] = allowed_origins.split(",")

        config["security"] = security_config

        # Services configuration
        services_config = {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "mailgun_api_key": os.getenv("MAILGUN_API_KEY", ""),
            "mailgun_domain": os.getenv("MAILGUN_DOMAIN", ""),
            "mailgun_webhook_signing_key": os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY"),
            "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "google_cloud_region": os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
        }
        config["services"] = services_config

        # Server configuration
        server_config = {
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8080")),
            "workers": int(os.getenv("WORKERS", "1")),
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "access_log": os.getenv("ACCESS_LOG", "true").lower() == "true",
        }
        config["server"] = server_config

        # Cache configuration
        cache_config = {
            "enabled": os.getenv("CACHE_ENABLED", "true").lower() == "true",
            "default_ttl_seconds": int(os.getenv("CACHE_TTL", "300")),
            "max_size_mb": int(os.getenv("CACHE_MAX_SIZE_MB", "128")),
        }
        config["cache"] = cache_config

        # Monitoring configuration
        monitoring_config = {
            "enable_tracing": os.getenv("ENABLE_TRACING", "false").lower() == "true",
            "enable_profiling": os.getenv("ENABLE_PROFILING", "false").lower() == "true",
            "error_tracking_dsn": os.getenv("ERROR_TRACKING_DSN"),
        }
        config["monitoring"] = monitoring_config

        return config

    def _validate_configuration(self) -> None:
        """Validate configuration for current environment."""
        if not self._config:
            raise ConfigurationError("No configuration loaded")

        # Production-specific validations
        if self._config.is_production():
            if self._config.debug:
                logger.warning("Debug mode enabled in production - this is not recommended")

            if self._config.security.jwt_secret_key == "dev-secret":
                raise ConfigurationError("Production environment requires a secure JWT secret")

            if not self._config.services.mailgun_webhook_signing_key:
                logger.warning("Mailgun webhook signing key not set - webhook security is reduced")

        # Development-specific validations
        if self._config.is_development():
            if len(self._config.security.jwt_secret_key) < 32:
                logger.warning("JWT secret key is shorter than recommended (32+ characters)")

        logger.debug("Configuration validation completed")

    def _load_client_configurations(self) -> None:
        """Load all client configurations from the client directory."""
        client_path = Path(self._config.client_config_path)

        if not client_path.exists():
            logger.warning(f"Client configuration directory not found: {client_path}")
            return

        loaded_count = 0
        for client_dir in client_path.iterdir():
            if not client_dir.is_dir():
                continue

            config_file = client_dir / "client-config.yaml"
            if not config_file.exists():
                logger.warning(f"Client config file not found: {config_file}")
                continue

            try:
                with open(config_file, "r") as f:
                    client_data = yaml.safe_load(f)

                # Ensure client_id matches directory name
                client_data["client_id"] = client_dir.name

                client_config = ClientConfig(**client_data)
                self._clients[client_config.client_id] = client_config
                loaded_count += 1

                logger.debug(f"Loaded client configuration: {client_config.client_id}")

            except Exception as e:
                logger.error(f"Failed to load client config from {config_file}: {e}")
                continue

        logger.info(f"Loaded {loaded_count} client configurations")

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    @property
    def config(self) -> AppConfig:
        """Get main application configuration."""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """Get configuration for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Client configuration or None if not found
        """
        return self._clients.get(client_id)

    def get_all_clients(self) -> Dict[str, ClientConfig]:
        """Get all client configurations.

        Returns:
            Dictionary of client_id -> ClientConfig
        """
        return self._clients.copy()

    def get_active_clients(self) -> Dict[str, ClientConfig]:
        """Get only active client configurations.

        Returns:
            Dictionary of active client configurations
        """
        return {client_id: config for client_id, config in self._clients.items() if config.active}

    def reload_client_config(self, client_id: str) -> bool:
        """Reload configuration for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            True if reloaded successfully, False otherwise
        """
        client_path = Path(self._config.client_config_path) / client_id / "client-config.yaml"

        if not client_path.exists():
            logger.warning(f"Client config file not found for reload: {client_path}")
            return False

        try:
            with open(client_path, "r") as f:
                client_data = yaml.safe_load(f)

            client_data["client_id"] = client_id
            client_config = ClientConfig(**client_data)
            self._clients[client_id] = client_config

            logger.info(f"Reloaded client configuration: {client_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reload client config for {client_id}: {e}")
            return False

    def validate_client_config(self, client_data: Dict[str, Any]) -> bool:
        """Validate client configuration data.

        Args:
            client_data: Client configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            ClientConfig(**client_data)
            return True
        except ValidationError as e:
            logger.error(f"Client configuration validation failed: {e}")
            return False

    def get_feature_flag(self, feature_name: str) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: Name of the feature

        Returns:
            True if feature is enabled, False otherwise
        """
        return self._config.features.get(feature_name, False)

    def is_service_available(self, service_name: str) -> bool:
        """Check if an external service is available.

        Args:
            service_name: Name of the service (anthropic, mailgun, etc.)

        Returns:
            True if service is configured and available
        """
        services = self._config.services

        if service_name == "anthropic":
            return bool(services.anthropic_api_key)
        elif service_name == "mailgun":
            return bool(services.mailgun_api_key and services.mailgun_domain)
        elif service_name == "google_cloud":
            return bool(services.google_cloud_project)

        return False

    def get_database_url(self) -> str:
        """Get the database connection URL.

        Returns:
            Database URL string
        """
        return self._config.database.url

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and runtime information.

        Returns:
            Dictionary with environment details
        """
        return {
            "environment": self._config.environment.value,
            "debug": self._config.debug,
            "app_name": self._config.app_name,
            "app_version": self._config.app_version,
            "python_version": sys.version,
            "config_loaded": self._config is not None,
            "clients_loaded": len(self._clients),
            "features_enabled": sum(1 for enabled in self._config.features.values() if enabled),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_config_manager: Optional[ConfigManager] = None


@lru_cache(maxsize=1)
def get_config_manager() -> ConfigManager:
    """Get the singleton configuration manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager()

    return _config_manager


def reload_configuration() -> None:
    """Force reload of all configuration."""
    global _config_manager
    _config_manager = None
    # Clear the cache
    get_config_manager.cache_clear()
    # Load fresh configuration
    get_config_manager()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_app_config() -> AppConfig:
    """Get main application configuration.

    Returns:
        AppConfig instance
    """
    return get_config_manager().config


def get_client_config(client_id: str) -> Optional[ClientConfig]:
    """Get client configuration by ID.

    Args:
        client_id: Client identifier

    Returns:
        ClientConfig instance or None
    """
    return get_config_manager().get_client_config(client_id)


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled.

    Args:
        feature_name: Feature name

    Returns:
        True if enabled, False otherwise
    """
    return get_config_manager().get_feature_flag(feature_name)


def is_service_available(service_name: str) -> bool:
    """Check if a service is available.

    Args:
        service_name: Service name

    Returns:
        True if available, False otherwise
    """
    return get_config_manager().is_service_available(service_name)
