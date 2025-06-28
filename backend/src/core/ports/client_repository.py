"""
Client Repository Interface (Port) for Clean Architecture
🏗️ Abstract interface for client data access operations.

This interface defines the contract for client data operations without
depending on any specific database technology or ORM.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from core.models.schemas import ClientSummary


class ClientRepository(ABC):
    """
    Abstract repository interface for client data operations.

    This interface defines all client-related data operations needed by
    the core business logic. Concrete implementations will be provided
    in the infrastructure layer.
    """

    # =========================================================================
    # CLIENT LOOKUP OPERATIONS
    # =========================================================================

    @abstractmethod
    async def find_by_id(self, client_id: str) -> Optional[ClientSummary]:
        """
        Find client by ID.

        Args:
            client_id: Client ID to search for

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_domain(self, domain: str) -> Optional[ClientSummary]:
        """
        Find client by domain.

        Args:
            domain: Domain to search for

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[ClientSummary]:
        """
        Find client by name.

        Args:
            name: Client name to search for

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all_clients(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[ClientSummary]:
        """
        List all clients with optional filtering.

        Args:
            limit: Maximum number of clients to return
            offset: Number of clients to skip
            status: Filter by status
            industry: Filter by industry

        Returns:
            List of clients
        """
        pass

    @abstractmethod
    async def count_clients(self, status: Optional[str] = None) -> int:
        """
        Count total number of clients.

        Args:
            status: Optional status filter

        Returns:
            Total number of clients
        """
        pass

    # =========================================================================
    # CLIENT CRUD OPERATIONS
    # =========================================================================

    @abstractmethod
    async def create_client(self, client_data: Dict) -> ClientSummary:
        """
        Create a new client.

        Args:
            client_data: Client creation data

        Returns:
            Created client

        Raises:
            ValueError: If client data is invalid
            ConflictError: If client ID already exists
        """
        pass

    @abstractmethod
    async def update_client(
        self, client_id: str, client_data: Dict
    ) -> Optional[ClientSummary]:
        """
        Update an existing client.

        Args:
            client_id: ID of client to update
            client_data: Updated client data

        Returns:
            Updated client if found, None otherwise

        Raises:
            ValueError: If client data is invalid
        """
        pass

    @abstractmethod
    async def delete_client(self, client_id: str) -> bool:
        """
        Delete a client.

        Args:
            client_id: ID of client to delete

        Returns:
            True if client was deleted, False if not found
        """
        pass

    @abstractmethod
    async def activate_client(self, client_id: str) -> bool:
        """
        Activate a client.

        Args:
            client_id: ID of client to activate

        Returns:
            True if client was activated, False if not found
        """
        pass

    @abstractmethod
    async def deactivate_client(self, client_id: str) -> bool:
        """
        Deactivate a client.

        Args:
            client_id: ID of client to deactivate

        Returns:
            True if client was deactivated, False if not found
        """
        pass

    # =========================================================================
    # DOMAIN OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_client_domains(self, client_id: str) -> Set[str]:
        """
        Get all domains associated with a client.

        Args:
            client_id: Client ID

        Returns:
            Set of domains for the client
        """
        pass

    @abstractmethod
    async def add_client_domain(
        self, client_id: str, domain: str, domain_type: str
    ) -> bool:
        """
        Add a domain to a client.

        Args:
            client_id: Client ID
            domain: Domain to add
            domain_type: Type of domain (primary, support, mailgun, alias)

        Returns:
            True if domain was added, False otherwise
        """
        pass

    @abstractmethod
    async def remove_client_domain(self, client_id: str, domain: str) -> bool:
        """
        Remove a domain from a client.

        Args:
            client_id: Client ID
            domain: Domain to remove

        Returns:
            True if domain was removed, False if not found
        """
        pass

    @abstractmethod
    async def update_domain_type(
        self, client_id: str, domain: str, domain_type: str
    ) -> bool:
        """
        Update the type of a domain.

        Args:
            client_id: Client ID
            domain: Domain to update
            domain_type: New domain type

        Returns:
            True if domain type was updated, False if not found
        """
        pass

    @abstractmethod
    async def find_clients_by_domain_pattern(self, pattern: str) -> List[ClientSummary]:
        """
        Find clients with domains matching a pattern.

        Args:
            pattern: Domain pattern to match

        Returns:
            List of matching clients
        """
        pass

    # =========================================================================
    # ROUTING OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_routing_rules(self, client_id: str) -> Optional[Dict[str, str]]:
        """
        Get routing rules for a client.

        Args:
            client_id: Client ID

        Returns:
            Dictionary of category -> email mappings, None if not found
        """
        pass

    @abstractmethod
    async def update_routing_rule(
        self, client_id: str, category: str, email: str
    ) -> bool:
        """
        Update a routing rule for a client.

        Args:
            client_id: Client ID
            category: Email category
            email: Destination email

        Returns:
            True if rule was updated, False if client not found
        """
        pass

    @abstractmethod
    async def add_routing_rule(self, client_id: str, category: str, email: str) -> bool:
        """
        Add a routing rule for a client.

        Args:
            client_id: Client ID
            category: Email category
            email: Destination email

        Returns:
            True if rule was added, False if client not found
        """
        pass

    @abstractmethod
    async def remove_routing_rule(self, client_id: str, category: str) -> bool:
        """
        Remove a routing rule for a client.

        Args:
            client_id: Client ID
            category: Email category to remove

        Returns:
            True if rule was removed, False if not found
        """
        pass

    @abstractmethod
    async def get_escalation_rules(self, client_id: str) -> Optional[Dict]:
        """
        Get escalation rules for a client.

        Args:
            client_id: Client ID

        Returns:
            Escalation rules dictionary, None if not found
        """
        pass

    # =========================================================================
    # BRANDING OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_client_branding(self, client_id: str) -> Optional[Dict]:
        """
        Get branding configuration for a client.

        Args:
            client_id: Client ID

        Returns:
            Branding configuration dictionary, None if not found
        """
        pass

    @abstractmethod
    async def update_client_branding(self, client_id: str, branding_data: Dict) -> bool:
        """
        Update branding configuration for a client.

        Args:
            client_id: Client ID
            branding_data: Branding configuration data

        Returns:
            True if branding was updated, False if client not found
        """
        pass

    # =========================================================================
    # RESPONSE TIME OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_response_times(self, client_id: str) -> Optional[Dict[str, int]]:
        """
        Get response time SLAs for a client.

        Args:
            client_id: Client ID

        Returns:
            Dictionary of category -> minutes mappings, None if not found
        """
        pass

    @abstractmethod
    async def update_response_time(
        self, client_id: str, category: str, minutes: int
    ) -> bool:
        """
        Update response time SLA for a client category.

        Args:
            client_id: Client ID
            category: Email category
            minutes: Response time in minutes

        Returns:
            True if response time was updated, False if client not found
        """
        pass

    # =========================================================================
    # AI PROMPT OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_ai_prompts(self, client_id: str) -> Optional[Dict[str, str]]:
        """
        Get AI prompts for a client.

        Args:
            client_id: Client ID

        Returns:
            Dictionary of prompt_type -> content mappings, None if not found
        """
        pass

    @abstractmethod
    async def update_ai_prompt(
        self, client_id: str, prompt_type: str, content: str
    ) -> bool:
        """
        Update AI prompt for a client.

        Args:
            client_id: Client ID
            prompt_type: Type of prompt (classification, acknowledgment, etc.)
            content: Prompt content

        Returns:
            True if prompt was updated, False if client not found
        """
        pass

    # =========================================================================
    # SETTINGS OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_client_settings(self, client_id: str) -> Optional[Dict]:
        """
        Get settings for a client.

        Args:
            client_id: Client ID

        Returns:
            Settings dictionary, None if not found
        """
        pass

    @abstractmethod
    async def update_client_setting(
        self, client_id: str, setting_key: str, setting_value: Any
    ) -> bool:
        """
        Update a specific setting for a client.

        Args:
            client_id: Client ID
            setting_key: Setting key
            setting_value: Setting value

        Returns:
            True if setting was updated, False if client not found
        """
        pass

    # =========================================================================
    # AUDIT OPERATIONS
    # =========================================================================

    @abstractmethod
    async def log_configuration_change(
        self,
        client_id: str,
        change_type: str,
        table_name: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> None:
        """
        Log a configuration change for audit purposes.

        Args:
            client_id: Client ID
            change_type: Type of change (CREATE, UPDATE, DELETE)
            table_name: Name of table/resource changed
            old_values: Previous values
            new_values: New values
            changed_by: User/API key that made the change
            change_reason: Reason for the change
        """
        pass

    @abstractmethod
    async def get_configuration_changes(
        self, client_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """
        Get configuration change history for a client.

        Args:
            client_id: Client ID
            limit: Maximum number of changes to return
            offset: Number of changes to skip

        Returns:
            List of configuration changes
        """
        pass
