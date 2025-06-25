"""
Ports (interfaces) for the core layer.

Following hexagonal architecture principles, these define the contracts
that the core layer expects from external systems and infrastructure.
"""

from .config_provider import ConfigurationProvider

__all__ = ["ConfigurationProvider"]