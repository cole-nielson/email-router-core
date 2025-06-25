"""
Configuration Dependencies for FastAPI Dependency Injection
🔧 Provides configuration services to the application layer.
"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from core.clients.manager import EnhancedClientManager
from core.ports.config_provider import ConfigurationProvider
from infrastructure.adapters.config_provider import ConfigManagerAdapter

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION DEPENDENCIES
# =============================================================================


@lru_cache(maxsize=1)
def get_config_provider() -> ConfigurationProvider:
    """
    Get the configuration provider instance.
    
    This is the primary dependency for accessing configuration services
    in the application. It provides the abstract ConfigurationProvider
    interface implemented by the ConfigManagerAdapter.
    
    Returns:
        ConfigurationProvider instance
    """
    logger.debug("Creating ConfigurationProvider instance")
    return ConfigManagerAdapter()


@lru_cache(maxsize=1)
def get_client_manager() -> EnhancedClientManager:
    """
    Get the client manager instance with dependency injection.
    
    This function provides the ClientManager with the proper ConfigurationProvider
    for FastAPI dependency injection.
    
    Returns:
        EnhancedClientManager instance
    """
    config_provider = get_config_provider()
    return EnhancedClientManager(config_provider)


# =============================================================================
# DEPENDENCY INJECTION TYPES
# =============================================================================

# Type annotation for dependency injection
ConfigProviderDep = Annotated[ConfigurationProvider, Depends(get_config_provider)]
ClientManagerDep = Annotated[EnhancedClientManager, Depends(get_client_manager)]