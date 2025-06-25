"""
Infrastructure adapters that implement core interfaces.

These adapters bridge the gap between the core business logic
and the infrastructure layer, implementing the interfaces defined
in the core layer's ports.
"""

from .config_provider import ConfigManagerAdapter

__all__ = ["ConfigManagerAdapter"]