"""
Permission Definitions for Unified Authorization System
🛡️ Centralized permission constants and resource actions.
"""

from enum import Enum
from typing import Dict, List


class ResourceActions(str, Enum):
    """Standard actions that can be performed on resources."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    MONITOR = "monitor"


class Permissions:
    """
    Centralized permission definitions for consistency across the application.

    This consolidates all permission strings used throughout the system,
    replacing the scattered permission definitions from the old RBAC system.
    """

    # ==========================================================================
    # CLIENT MANAGEMENT PERMISSIONS
    # ==========================================================================

    # Single client operations
    CLIENT_READ = "client:read"
    CLIENT_WRITE = "client:write"
    CLIENT_DELETE = "client:delete"
    CLIENT_ADMIN = "client:admin"

    # Multi-client operations (super admin)
    CLIENTS_READ = "clients:read"
    CLIENTS_WRITE = "clients:write"
    CLIENTS_DELETE = "clients:delete"
    CLIENTS_ADMIN = "clients:admin"

    # ==========================================================================
    # CONFIGURATION PERMISSIONS
    # ==========================================================================

    # Routing rules
    ROUTING_READ = "routing:read"
    ROUTING_WRITE = "routing:write"
    ROUTING_DELETE = "routing:delete"
    ROUTING_ADMIN = "routing:admin"

    # Branding configuration
    BRANDING_READ = "branding:read"
    BRANDING_WRITE = "branding:write"
    BRANDING_DELETE = "branding:delete"
    BRANDING_ADMIN = "branding:admin"

    # AI prompts and settings
    AI_PROMPTS_READ = "ai_prompts:read"
    AI_PROMPTS_WRITE = "ai_prompts:write"
    AI_PROMPTS_DELETE = "ai_prompts:delete"
    AI_PROMPTS_ADMIN = "ai_prompts:admin"

    # Response time configuration
    RESPONSE_TIMES_READ = "response_times:read"
    RESPONSE_TIMES_WRITE = "response_times:write"
    RESPONSE_TIMES_DELETE = "response_times:delete"
    RESPONSE_TIMES_ADMIN = "response_times:admin"

    # ==========================================================================
    # USER MANAGEMENT PERMISSIONS
    # ==========================================================================

    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    USERS_ADMIN = "users:admin"

    # ==========================================================================
    # SYSTEM PERMISSIONS
    # ==========================================================================

    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_EXECUTE = "system:execute"

    # ==========================================================================
    # WEBHOOK PERMISSIONS
    # ==========================================================================

    WEBHOOKS_READ = "webhooks:read"
    WEBHOOKS_WRITE = "webhooks:write"
    WEBHOOKS_ADMIN = "webhooks:admin"

    # ==========================================================================
    # API PERMISSIONS
    # ==========================================================================

    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"

    # ==========================================================================
    # ANALYTICS PERMISSIONS
    # ==========================================================================

    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    ANALYTICS_ADMIN = "analytics:admin"


class PermissionSets:
    """
    Predefined permission sets for common role assignments.

    This provides convenient groupings of permissions that can be
    assigned to roles or users based on their responsibilities.
    """

    # Basic user permissions
    BASIC_USER = [
        Permissions.CLIENT_READ,
        Permissions.ROUTING_READ,
        Permissions.BRANDING_READ,
        Permissions.RESPONSE_TIMES_READ,
        Permissions.ANALYTICS_READ,
    ]

    # Client admin permissions
    CLIENT_ADMIN = BASIC_USER + [
        Permissions.CLIENT_WRITE,
        Permissions.CLIENT_ADMIN,
        Permissions.ROUTING_WRITE,
        Permissions.ROUTING_ADMIN,
        Permissions.BRANDING_WRITE,
        Permissions.BRANDING_ADMIN,
        Permissions.AI_PROMPTS_READ,
        Permissions.AI_PROMPTS_WRITE,
        Permissions.RESPONSE_TIMES_WRITE,
        Permissions.RESPONSE_TIMES_ADMIN,
        Permissions.USERS_READ,
        Permissions.USERS_WRITE,
        Permissions.ANALYTICS_WRITE,
    ]

    # Super admin permissions
    SUPER_ADMIN = CLIENT_ADMIN + [
        Permissions.CLIENTS_READ,
        Permissions.CLIENTS_WRITE,
        Permissions.CLIENTS_DELETE,
        Permissions.CLIENTS_ADMIN,
        Permissions.USERS_DELETE,
        Permissions.USERS_ADMIN,
        Permissions.SYSTEM_ADMIN,
        Permissions.SYSTEM_CONFIG,
        Permissions.SYSTEM_MONITOR,
        Permissions.SYSTEM_EXECUTE,
        Permissions.WEBHOOKS_READ,
        Permissions.WEBHOOKS_WRITE,
        Permissions.WEBHOOKS_ADMIN,
        Permissions.API_READ,
        Permissions.API_WRITE,
        Permissions.API_ADMIN,
        Permissions.ANALYTICS_ADMIN,
    ]

    # API key permissions (automated systems)
    API_KEY_STANDARD = [
        Permissions.CLIENT_READ,
        Permissions.WEBHOOKS_WRITE,
        Permissions.SYSTEM_MONITOR,
        Permissions.API_READ,
    ]

    # API key admin permissions
    API_KEY_ADMIN = API_KEY_STANDARD + [
        Permissions.CLIENTS_READ,
        Permissions.SYSTEM_ADMIN,
        Permissions.WEBHOOKS_ADMIN,
        Permissions.API_WRITE,
        Permissions.API_ADMIN,
    ]


class PermissionUtils:
    """Utility functions for working with permissions."""

    @staticmethod
    def parse_permission(permission: str) -> tuple[str, str]:
        """
        Parse permission string into resource and action.

        Args:
            permission: Permission string (e.g., "routing:write")

        Returns:
            Tuple of (resource, action)

        Raises:
            ValueError: If permission format is invalid
        """
        if ":" not in permission:
            raise ValueError(f"Invalid permission format: {permission}")

        resource, action = permission.split(":", 1)
        return resource, action

    @staticmethod
    def build_permission(resource: str, action: str) -> str:
        """
        Build permission string from resource and action.

        Args:
            resource: Resource name (e.g., "routing")
            action: Action name (e.g., "write")

        Returns:
            Permission string (e.g., "routing:write")
        """
        return f"{resource}:{action}"

    @staticmethod
    def get_resource_permissions(resource: str) -> List[str]:
        """
        Get all permissions for a specific resource.

        Args:
            resource: Resource name

        Returns:
            List of permissions for the resource
        """
        permissions = []

        # Use reflection to find all permissions for the resource
        for attr_name in dir(Permissions):
            if not attr_name.startswith("_"):
                permission = getattr(Permissions, attr_name)
                if isinstance(permission, str) and permission.startswith(
                    f"{resource}:"
                ):
                    permissions.append(permission)

        return permissions

    @staticmethod
    def validate_permissions(permissions: List[str]) -> tuple[bool, List[str]]:
        """
        Validate a list of permissions.

        Args:
            permissions: List of permission strings to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        valid_permissions = PermissionUtils.get_all_permissions()

        for permission in permissions:
            try:
                # Check format
                PermissionUtils.parse_permission(permission)

                # Check if permission exists
                if permission not in valid_permissions:
                    errors.append(f"Unknown permission: {permission}")

            except ValueError as e:
                errors.append(str(e))

        return len(errors) == 0, errors

    @staticmethod
    def get_all_permissions() -> List[str]:
        """
        Get all defined permissions.

        Returns:
            List of all permission strings
        """
        permissions = []

        for attr_name in dir(Permissions):
            if not attr_name.startswith("_"):
                permission = getattr(Permissions, attr_name)
                if isinstance(permission, str) and ":" in permission:
                    permissions.append(permission)

        return permissions

    @staticmethod
    def get_permission_hierarchy() -> Dict[str, List[str]]:
        """
        Get permission hierarchy organized by resource.

        Returns:
            Dictionary of resource -> [permissions]
        """
        hierarchy: Dict[str, List[str]] = {}

        for permission in PermissionUtils.get_all_permissions():
            resource, action = PermissionUtils.parse_permission(permission)

            if resource not in hierarchy:
                hierarchy[resource] = []

            hierarchy[resource].append(permission)

        return hierarchy
