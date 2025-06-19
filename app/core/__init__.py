"""
Core Configuration Module
🏗️ Centralized configuration management for the email router application.
"""

from .config_manager import (
    ConfigManager,
    get_app_config,
    get_client_config,
    get_config_manager,
    is_feature_enabled,
    is_service_available,
    reload_configuration,
)
from .config_schema import (
    AppConfig,
    CacheConfig,
    ClientConfig,
    DatabaseConfig,
    Environment,
    MonitoringConfig,
    SecurityConfig,
    ServerConfig,
    ServiceConfig,
)

__all__ = [
    # Manager
    "ConfigManager",
    "get_config_manager",
    "get_app_config",
    "get_client_config",
    "is_feature_enabled",
    "is_service_available",
    "reload_configuration",
    # Schema
    "AppConfig",
    "ClientConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "ServiceConfig",
    "ServerConfig",
    "CacheConfig",
    "MonitoringConfig",
    "Environment",
]
