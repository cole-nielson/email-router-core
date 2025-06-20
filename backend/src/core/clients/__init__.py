"""
Core Clients Module
Multi-tenant client management with advanced domain resolution.
"""

from .manager import ClientManager, get_client_manager
from .resolver import (
    DomainMatcher,
    calculate_domain_similarity,
    extract_domain_from_email,
    extract_domain_from_url,
    get_domain_hierarchy,
    is_valid_domain_format,
    normalize_domain,
)

__all__ = [
    # Manager
    "ClientManager",
    "get_client_manager",
    # Domain utilities
    "DomainMatcher",
    "extract_domain_from_email",
    "extract_domain_from_url",
    "normalize_domain",
    "is_valid_domain_format",
    "get_domain_hierarchy",
    "calculate_domain_similarity",
]
