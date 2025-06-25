"""
Configuration Manager Adapter

This adapter implements the ConfigurationProvider interface,
wrapping the existing ConfigManager to provide configuration
services to the core layer.
"""

from typing import Any, Dict, Optional

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

    def get_all_clients(self) -> Dict[str, ClientConfig]:
        """
        Get all available client configurations.

        Returns:
            Dictionary mapping client_id to ClientConfig objects
        """
        return self._config_manager.get_all_clients()

    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """
        Get configuration for a specific client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            ClientConfig object if found, None otherwise
        """
        return self._config_manager.get_client_config(client_id)

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
