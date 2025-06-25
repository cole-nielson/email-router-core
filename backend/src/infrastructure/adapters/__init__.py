"""
Infrastructure adapters that implement core interfaces.

These adapters bridge the gap between the core business logic
and the infrastructure layer, implementing the interfaces defined
in the core layer's ports.
"""

from .client_repository_impl import SQLAlchemyClientRepository
from .config_provider import ConfigManagerAdapter
from .user_repository_impl import SQLAlchemyUserRepository

__all__ = [
    "ConfigManagerAdapter",
    "SQLAlchemyUserRepository",
    "SQLAlchemyClientRepository",
]
