"""
Configuration Provider Interface

This module defines the abstract interface for configuration management
that the core layer depends on. This follows the Dependency Inversion Principle,
allowing the core layer to depend on abstractions rather than concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from infrastructure.config.schema import ClientConfig


class ConfigurationProvider(ABC):
    """
    Abstract interface for configuration management.
    
    This interface defines the contract that any configuration provider
    must implement to be used by the core business logic layer.
    It abstracts away the details of how configuration is stored,
    loaded, and managed.
    """
    
    @abstractmethod
    def get_all_clients(self) -> Dict[str, ClientConfig]:
        """
        Get all available client configurations.
        
        Returns:
            Dictionary mapping client_id to ClientConfig objects
        """
        pass
    
    @abstractmethod
    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """
        Get configuration for a specific client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            ClientConfig object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def reload_client_config(self, client_id: str) -> bool:
        """
        Reload configuration for a specific client.
        
        This method forces a refresh of the client's configuration,
        useful when configuration files have been updated.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            True if reload was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def reload_configuration(self) -> None:
        """
        Reload all configurations.
        
        This method forces a complete refresh of all configurations,
        useful when multiple configuration files have been updated.
        """
        pass
    
    @abstractmethod
    def load_ai_prompt(self, client_id: str, template_type: str) -> str:
        """
        Load an AI prompt/template for a specific client.
        
        Args:
            client_id: Unique identifier for the client
            template_type: Type of template to load 
                          ('classification', 'acknowledgment', 'team-analysis')
                          
        Returns:
            The prompt/template content as a string
            
        Raises:
            ConfigurationError: If the template cannot be loaded
        """
        pass
    
    @abstractmethod
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
        pass