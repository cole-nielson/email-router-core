"""
SQLAlchemy-based ClientRepository Implementation
🔌 Concrete implementation of ClientRepository interface using SQLAlchemy ORM.

This adapter provides database persistence for client operations while implementing
the clean architecture repository pattern.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.models.schemas import ClientSummary
from core.ports.client_repository import ClientRepository
from infrastructure.database.models import (
    AIPrompt,
    Client,
    ClientBranding,
    ClientDomain,
    ClientSetting,
    ConfigurationChange,
    ResponseTime,
    RoutingRule,
)

logger = logging.getLogger(__name__)


class ConflictError(Exception):
    """Raised when a resource conflict occurs (e.g., client ID already exists)."""

    pass


class SQLAlchemyClientRepository(ClientRepository):
    """
    SQLAlchemy-based implementation of ClientRepository.

    This adapter translates between core domain models and database models,
    providing persistence while keeping the core logic database-agnostic.
    """

    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _client_to_domain_model(self, client: Client) -> ClientSummary:
        """
        Convert database Client model to domain ClientSummary model.

        Args:
            client: Database client model

        Returns:
            Domain client summary model
        """
        # Get domains
        domains = [domain.domain_value for domain in client.domains]
        primary_domain = next(
            (d.domain_value for d in client.domains if d.domain_type == "primary"),
            domains[0] if domains else "",
        )

        # Get routing categories
        routing_categories = [
            rule.category for rule in client.routing_rules if rule.is_active
        ]

        # Get settings
        settings = {}
        for setting in client.settings:
            settings[setting.setting_key] = setting.setting_value

        return ClientSummary(
            client_id=client.id,
            name=client.name,
            industry=client.industry,
            status=client.status,
            domains=domains,
            primary_domain=primary_domain,
            routing_categories=routing_categories,
            total_domains=len(domains),
            settings=settings,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    # =========================================================================
    # CLIENT LOOKUP OPERATIONS
    # =========================================================================

    async def find_by_id(self, client_id: str) -> Optional[ClientSummary]:
        """Find client by ID."""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            return self._client_to_domain_model(client) if client else None
        except Exception as e:
            logger.error(f"Error finding client by ID {client_id}: {e}")
            return None

    async def find_by_domain(self, domain: str) -> Optional[ClientSummary]:
        """Find client by domain."""
        try:
            domain_record = (
                self.db.query(ClientDomain)
                .filter(ClientDomain.domain_value == domain)
                .first()
            )

            if not domain_record:
                return None

            client = (
                self.db.query(Client)
                .filter(Client.id == domain_record.client_id)
                .first()
            )
            return self._client_to_domain_model(client) if client else None
        except Exception as e:
            logger.error(f"Error finding client by domain {domain}: {e}")
            return None

    async def find_by_name(self, name: str) -> Optional[ClientSummary]:
        """Find client by name."""
        try:
            client = self.db.query(Client).filter(Client.name == name).first()
            return self._client_to_domain_model(client) if client else None
        except Exception as e:
            logger.error(f"Error finding client by name {name}: {e}")
            return None

    async def list_all_clients(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[ClientSummary]:
        """List all clients with optional filtering."""
        try:
            query = self.db.query(Client)

            if status:
                query = query.filter(Client.status == status)

            if industry:
                query = query.filter(Client.industry == industry)

            clients = query.offset(offset).limit(limit).all()
            return [self._client_to_domain_model(client) for client in clients]

        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return []

    async def count_clients(self, status: Optional[str] = None) -> int:
        """Count total number of clients."""
        try:
            query = self.db.query(Client)

            if status:
                query = query.filter(Client.status == status)

            return query.count()
        except Exception as e:
            logger.error(f"Error counting clients: {e}")
            return 0

    # =========================================================================
    # CLIENT CRUD OPERATIONS
    # =========================================================================

    async def create_client(self, client_data: Dict) -> ClientSummary:
        """Create a new client."""
        try:
            # Check for existing client ID
            existing_client = (
                self.db.query(Client)
                .filter(Client.id == client_data["client_id"])
                .first()
            )
            if existing_client:
                raise ConflictError(
                    f"Client ID '{client_data['client_id']}' already exists"
                )

            # Create new client
            new_client = Client(
                id=client_data["client_id"],
                name=client_data["name"],
                industry=client_data.get("industry", ""),
                status=client_data.get("status", "active"),
                timezone=client_data.get("timezone", "UTC"),
                business_hours=client_data.get("business_hours", "9-17"),
            )

            self.db.add(new_client)
            self.db.commit()
            self.db.refresh(new_client)

            logger.info(f"Created new client: {client_data['client_id']}")
            return self._client_to_domain_model(new_client)

        except ConflictError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating client {client_data.get('client_id')}: {e}")
            raise ValueError(f"Failed to create client: {e}")

    async def update_client(
        self, client_id: str, client_data: Dict
    ) -> Optional[ClientSummary]:
        """Update an existing client."""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return None

            # Update fields if provided
            if "name" in client_data:
                client.name = client_data["name"]
            if "industry" in client_data:
                client.industry = client_data["industry"]
            if "status" in client_data:
                client.status = client_data["status"]
            if "timezone" in client_data:
                client.timezone = client_data["timezone"]
            if "business_hours" in client_data:
                client.business_hours = client_data["business_hours"]

            client.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(client)

            logger.info(f"Updated client: {client_id}")
            return self._client_to_domain_model(client)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating client {client_id}: {e}")
            raise ValueError(f"Failed to update client: {e}")

    async def delete_client(self, client_id: str) -> bool:
        """Delete a client."""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False

            self.db.delete(client)
            self.db.commit()

            logger.info(f"Deleted client: {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting client {client_id}: {e}")
            return False

    async def activate_client(self, client_id: str) -> bool:
        """Activate a client."""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False

            client.status = "active"
            client.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Activated client: {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error activating client {client_id}: {e}")
            return False

    async def deactivate_client(self, client_id: str) -> bool:
        """Deactivate a client."""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False

            client.status = "inactive"
            client.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Deactivated client: {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating client {client_id}: {e}")
            return False

    # =========================================================================
    # DOMAIN OPERATIONS
    # =========================================================================

    async def get_client_domains(self, client_id: str) -> Set[str]:
        """Get all domains associated with a client."""
        try:
            domains = (
                self.db.query(ClientDomain)
                .filter(ClientDomain.client_id == client_id)
                .all()
            )
            return {domain.domain_value for domain in domains}
        except Exception as e:
            logger.error(f"Error getting domains for client {client_id}: {e}")
            return set()

    async def add_client_domain(
        self, client_id: str, domain: str, domain_type: str
    ) -> bool:
        """Add a domain to a client."""
        try:
            # Check if domain already exists
            existing = (
                self.db.query(ClientDomain)
                .filter(ClientDomain.domain_value == domain)
                .first()
            )

            if existing:
                return False  # Domain already exists

            domain_record = ClientDomain(
                client_id=client_id, domain_type=domain_type, domain_value=domain
            )

            self.db.add(domain_record)
            self.db.commit()

            logger.info(f"Added domain {domain} to client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding domain {domain} to client {client_id}: {e}")
            return False

    async def remove_client_domain(self, client_id: str, domain: str) -> bool:
        """Remove a domain from a client."""
        try:
            domain_record = (
                self.db.query(ClientDomain)
                .filter(
                    ClientDomain.client_id == client_id,
                    ClientDomain.domain_value == domain,
                )
                .first()
            )

            if not domain_record:
                return False

            self.db.delete(domain_record)
            self.db.commit()

            logger.info(f"Removed domain {domain} from client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing domain {domain} from client {client_id}: {e}")
            return False

    async def update_domain_type(
        self, client_id: str, domain: str, domain_type: str
    ) -> bool:
        """Update the type of a domain."""
        try:
            domain_record = (
                self.db.query(ClientDomain)
                .filter(
                    ClientDomain.client_id == client_id,
                    ClientDomain.domain_value == domain,
                )
                .first()
            )

            if not domain_record:
                return False

            domain_record.domain_type = domain_type
            self.db.commit()

            logger.info(
                f"Updated domain {domain} type to {domain_type} for client {client_id}"
            )
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error updating domain type for {domain} in client {client_id}: {e}"
            )
            return False

    async def find_clients_by_domain_pattern(self, pattern: str) -> List[ClientSummary]:
        """Find clients with domains matching a pattern."""
        try:
            domains = (
                self.db.query(ClientDomain)
                .filter(ClientDomain.domain_value.like(f"%{pattern}%"))
                .all()
            )

            client_ids = {domain.client_id for domain in domains}
            clients = self.db.query(Client).filter(Client.id.in_(client_ids)).all()

            return [self._client_to_domain_model(client) for client in clients]

        except Exception as e:
            logger.error(f"Error finding clients by domain pattern {pattern}: {e}")
            return []

    # =========================================================================
    # ROUTING OPERATIONS
    # =========================================================================

    async def get_routing_rules(self, client_id: str) -> Optional[Dict[str, str]]:
        """Get routing rules for a client."""
        try:
            rules = (
                self.db.query(RoutingRule)
                .filter(
                    RoutingRule.client_id == client_id, RoutingRule.is_active == True
                )
                .all()
            )

            if not rules:
                return None

            return {rule.category: rule.email_address for rule in rules}

        except Exception as e:
            logger.error(f"Error getting routing rules for client {client_id}: {e}")
            return None

    async def update_routing_rule(
        self, client_id: str, category: str, email: str
    ) -> bool:
        """Update a routing rule for a client."""
        try:
            rule = (
                self.db.query(RoutingRule)
                .filter(
                    RoutingRule.client_id == client_id, RoutingRule.category == category
                )
                .first()
            )

            if not rule:
                return False

            rule.email_address = email
            rule.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated routing rule {category} for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating routing rule for client {client_id}: {e}")
            return False

    async def add_routing_rule(self, client_id: str, category: str, email: str) -> bool:
        """Add a routing rule for a client."""
        try:
            # Check if rule already exists
            existing = (
                self.db.query(RoutingRule)
                .filter(
                    RoutingRule.client_id == client_id, RoutingRule.category == category
                )
                .first()
            )

            if existing:
                # Update existing rule
                existing.email_address = email
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
            else:
                # Create new rule
                rule = RoutingRule(
                    client_id=client_id, category=category, email_address=email
                )
                self.db.add(rule)

            self.db.commit()

            logger.info(f"Added routing rule {category} for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding routing rule for client {client_id}: {e}")
            return False

    async def remove_routing_rule(self, client_id: str, category: str) -> bool:
        """Remove a routing rule for a client."""
        try:
            rule = (
                self.db.query(RoutingRule)
                .filter(
                    RoutingRule.client_id == client_id, RoutingRule.category == category
                )
                .first()
            )

            if not rule:
                return False

            rule.is_active = False
            rule.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Removed routing rule {category} for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing routing rule for client {client_id}: {e}")
            return False

    async def get_escalation_rules(self, client_id: str) -> Optional[Dict]:
        """Get escalation rules for a client."""
        try:
            rules = (
                self.db.query(RoutingRule)
                .filter(
                    RoutingRule.client_id == client_id,
                    RoutingRule.is_active == True,
                    RoutingRule.escalation_rules.is_not(None),
                )
                .all()
            )

            if not rules:
                return None

            escalation_rules = {}
            for rule in rules:
                if rule.escalation_rules:
                    escalation_rules[rule.category] = rule.escalation_rules

            return escalation_rules if escalation_rules else None

        except Exception as e:
            logger.error(f"Error getting escalation rules for client {client_id}: {e}")
            return None

    # =========================================================================
    # BRANDING OPERATIONS
    # =========================================================================

    async def get_client_branding(self, client_id: str) -> Optional[Dict]:
        """Get branding configuration for a client."""
        try:
            branding = (
                self.db.query(ClientBranding)
                .filter(ClientBranding.client_id == client_id)
                .first()
            )

            if not branding:
                return None

            return {
                "company_name": branding.company_name,
                "primary_color": branding.primary_color,
                "secondary_color": branding.secondary_color,
                "logo_url": branding.logo_url,
                "email_signature": branding.email_signature,
                "footer_text": branding.footer_text,
                "colors": branding.colors or {},
            }

        except Exception as e:
            logger.error(f"Error getting branding for client {client_id}: {e}")
            return None

    async def update_client_branding(self, client_id: str, branding_data: Dict) -> bool:
        """Update branding configuration for a client."""
        try:
            branding = (
                self.db.query(ClientBranding)
                .filter(ClientBranding.client_id == client_id)
                .first()
            )

            if not branding:
                # Create new branding record
                branding = ClientBranding(client_id=client_id)
                self.db.add(branding)

            # Update fields
            if "company_name" in branding_data:
                branding.company_name = branding_data["company_name"]
            if "primary_color" in branding_data:
                branding.primary_color = branding_data["primary_color"]
            if "secondary_color" in branding_data:
                branding.secondary_color = branding_data["secondary_color"]
            if "logo_url" in branding_data:
                branding.logo_url = branding_data["logo_url"]
            if "email_signature" in branding_data:
                branding.email_signature = branding_data["email_signature"]
            if "footer_text" in branding_data:
                branding.footer_text = branding_data["footer_text"]
            if "colors" in branding_data:
                branding.colors = branding_data["colors"]

            branding.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated branding for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating branding for client {client_id}: {e}")
            return False

    # =========================================================================
    # RESPONSE TIME OPERATIONS
    # =========================================================================

    async def get_response_times(self, client_id: str) -> Optional[Dict[str, int]]:
        """Get response time SLAs for a client."""
        try:
            response_times = (
                self.db.query(ResponseTime)
                .filter(ResponseTime.client_id == client_id)
                .all()
            )

            if not response_times:
                return None

            # Parse response time strings to minutes
            result = {}
            for rt in response_times:
                # Simple parsing - assume format like "within 4 hours"
                target = rt.target_response.lower()
                if "hour" in target:
                    hours = int("".join(filter(str.isdigit, target)))
                    result[rt.category] = hours * 60
                elif "minute" in target:
                    minutes = int("".join(filter(str.isdigit, target)))
                    result[rt.category] = minutes
                elif "day" in target:
                    days = int("".join(filter(str.isdigit, target)))
                    result[rt.category] = days * 24 * 60
                else:
                    result[rt.category] = 1440  # Default to 24 hours

            return result

        except Exception as e:
            logger.error(f"Error getting response times for client {client_id}: {e}")
            return None

    async def update_response_time(
        self, client_id: str, category: str, minutes: int
    ) -> bool:
        """Update response time SLA for a client category."""
        try:
            response_time = (
                self.db.query(ResponseTime)
                .filter(
                    ResponseTime.client_id == client_id,
                    ResponseTime.category == category,
                )
                .first()
            )

            # Convert minutes to human readable format
            if minutes >= 1440:  # 24 hours or more
                days = minutes // 1440
                target_response = f"within {days} day{'s' if days > 1 else ''}"
            elif minutes >= 60:  # 1 hour or more
                hours = minutes // 60
                target_response = f"within {hours} hour{'s' if hours > 1 else ''}"
            else:
                target_response = f"within {minutes} minutes"

            if not response_time:
                # Create new response time
                response_time = ResponseTime(
                    client_id=client_id,
                    category=category,
                    target_response=target_response,
                )
                self.db.add(response_time)
            else:
                # Update existing
                response_time.target_response = target_response
                response_time.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Updated response time for {category} in client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating response time for client {client_id}: {e}")
            return False

    # =========================================================================
    # AI PROMPT OPERATIONS
    # =========================================================================

    async def get_ai_prompts(self, client_id: str) -> Optional[Dict[str, str]]:
        """Get AI prompts for a client."""
        try:
            prompts = (
                self.db.query(AIPrompt)
                .filter(AIPrompt.client_id == client_id, AIPrompt.is_active == True)
                .all()
            )

            if not prompts:
                return None

            return {prompt.prompt_type: prompt.prompt_content for prompt in prompts}

        except Exception as e:
            logger.error(f"Error getting AI prompts for client {client_id}: {e}")
            return None

    async def update_ai_prompt(
        self, client_id: str, prompt_type: str, content: str
    ) -> bool:
        """Update AI prompt for a client."""
        try:
            # Deactivate existing prompts of this type
            self.db.query(AIPrompt).filter(
                AIPrompt.client_id == client_id, AIPrompt.prompt_type == prompt_type
            ).update({"is_active": False})

            # Create new prompt
            prompt = AIPrompt(
                client_id=client_id, prompt_type=prompt_type, prompt_content=content
            )

            self.db.add(prompt)
            self.db.commit()

            logger.info(f"Updated AI prompt {prompt_type} for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating AI prompt for client {client_id}: {e}")
            return False

    # =========================================================================
    # SETTINGS OPERATIONS
    # =========================================================================

    async def get_client_settings(self, client_id: str) -> Optional[Dict]:
        """Get settings for a client."""
        try:
            settings = (
                self.db.query(ClientSetting)
                .filter(ClientSetting.client_id == client_id)
                .all()
            )

            if not settings:
                return None

            return {setting.setting_key: setting.setting_value for setting in settings}

        except Exception as e:
            logger.error(f"Error getting settings for client {client_id}: {e}")
            return None

    async def update_client_setting(
        self, client_id: str, setting_key: str, setting_value: Any
    ) -> bool:
        """Update a specific setting for a client."""
        try:
            setting = (
                self.db.query(ClientSetting)
                .filter(
                    ClientSetting.client_id == client_id,
                    ClientSetting.setting_key == setting_key,
                )
                .first()
            )

            if not setting:
                # Create new setting
                setting = ClientSetting(
                    client_id=client_id,
                    setting_key=setting_key,
                    setting_value=setting_value,
                )
                self.db.add(setting)
            else:
                # Update existing
                setting.setting_value = setting_value
                setting.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Updated setting {setting_key} for client {client_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating setting for client {client_id}: {e}")
            return False

    # =========================================================================
    # AUDIT OPERATIONS
    # =========================================================================

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
        """Log a configuration change for audit purposes."""
        try:
            change = ConfigurationChange(
                client_id=client_id,
                change_type=change_type,
                table_name=table_name,
                old_values=old_values,
                new_values=new_values,
                changed_by=changed_by,
                change_reason=change_reason,
            )

            self.db.add(change)
            self.db.commit()

            logger.info(
                f"Logged configuration change for client {client_id}: {change_type} on {table_name}"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error logging configuration change for client {client_id}: {e}"
            )

    async def get_configuration_changes(
        self, client_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """Get configuration change history for a client."""
        try:
            changes = (
                self.db.query(ConfigurationChange)
                .filter(ConfigurationChange.client_id == client_id)
                .order_by(ConfigurationChange.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": change.id,
                    "client_id": change.client_id,
                    "change_type": change.change_type,
                    "table_name": change.table_name,
                    "old_values": change.old_values,
                    "new_values": change.new_values,
                    "changed_by": change.changed_by,
                    "change_reason": change.change_reason,
                    "created_at": change.created_at,
                }
                for change in changes
            ]

        except Exception as e:
            logger.error(
                f"Error getting configuration changes for client {client_id}: {e}"
            )
            return []
