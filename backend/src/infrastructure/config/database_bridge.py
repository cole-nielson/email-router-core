"""
Database Configuration Bridge
🌉 Bridges the new ConfigManager with legacy database operations.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..database.models import (
    AIPrompt,
    Client,
    ClientBranding,
    ConfigurationChange,
    ResponseTime,
    RoutingRule,
)
from .manager import ConfigManager, get_config_manager

logger = logging.getLogger(__name__)


class DatabaseConfigBridge:
    """Bridges configuration manager with database operations."""

    def __init__(self, db: Session, config_manager: Optional[ConfigManager] = None):
        self.db = db
        self.config_manager = config_manager or get_config_manager()

    # =============================================================================
    # CLIENT OPERATIONS
    # =============================================================================

    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID from database or config manager."""
        # First try database
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if client:
            return client

        # Fall back to config manager and create DB entry
        config = self.config_manager.get_client_config(client_id)
        if config:
            return self._create_client_from_config(config)

        return None

    def list_clients(self, status: Optional[str] = None) -> List[Client]:
        """List all clients, optionally filtered by status."""
        # Get from database
        query = self.db.query(Client)
        if status:
            query = query.filter(Client.status == status)
        db_clients = {c.id: c for c in query.all()}

        # Merge with config manager clients
        config_clients = self.config_manager.get_all_clients()
        for client_id, config in config_clients.items():
            if client_id not in db_clients:
                client = self._create_client_from_config(config)
                if not status or client.status == status:
                    db_clients[client_id] = client

        return list(db_clients.values())

    def create_client(
        self, client_data: Dict[str, Any], created_by: Optional[str] = None
    ) -> Client:
        """Create new client configuration."""
        client = Client(
            id=client_data["id"],
            name=client_data["name"],
            industry=client_data["industry"],
            status=client_data.get("status", "active"),
            timezone=client_data.get("timezone", "UTC"),
            business_hours=client_data.get("business_hours", "9-17"),
        )

        self.db.add(client)
        self.db.flush()

        # Log creation
        self._log_change("CREATE", "clients", client.id, None, client_data, created_by)

        logger.info(f"✅ Created client: {client.id}")
        return client

    def update_client(
        self, client_id: str, updates: Dict[str, Any], updated_by: Optional[str] = None
    ) -> Optional[Client]:
        """Update client information."""
        client = self.get_client(client_id)
        if not client:
            return None

        # Store old values for audit
        old_values = {
            "name": client.name,
            "industry": client.industry,
            "status": client.status,
            "timezone": client.timezone,
            "business_hours": client.business_hours,
        }

        # Apply updates
        for key, value in updates.items():
            if hasattr(client, key):
                setattr(client, key, value)

        # Log change
        self._log_change("UPDATE", "clients", client_id, old_values, updates, updated_by)

        logger.info(f"📝 Updated client: {client_id}")
        return client

    # =============================================================================
    # ROUTING RULES
    # =============================================================================

    def get_routing_rules(self, client_id: str) -> List[RoutingRule]:
        """Get all routing rules for a client."""
        # First get from database
        db_rules = (
            self.db.query(RoutingRule)
            .filter(RoutingRule.client_id == client_id, RoutingRule.is_active == True)
            .all()
        )

        # If no DB rules, load from config
        if not db_rules:
            config = self.config_manager.get_client_config(client_id)
            if config and config.routing:
                for category, email in config.routing.items():
                    rule = RoutingRule(client_id=client_id, category=category, email_address=email)
                    self.db.add(rule)
                    db_rules.append(rule)
                self.db.flush()

        return db_rules

    def update_routing_rule(
        self, client_id: str, category: str, email_address: str, updated_by: Optional[str] = None
    ) -> RoutingRule:
        """Update or create routing rule for a category."""
        rule = (
            self.db.query(RoutingRule)
            .filter(RoutingRule.client_id == client_id, RoutingRule.category == category)
            .first()
        )

        if rule:
            old_email = rule.email_address
            rule.email_address = email_address
            self._log_change(
                "UPDATE",
                "routing_rules",
                rule.id,
                {"email_address": old_email},
                {"email_address": email_address},
                updated_by,
            )
        else:
            rule = RoutingRule(client_id=client_id, category=category, email_address=email_address)
            self.db.add(rule)
            self.db.flush()
            self._log_change(
                "CREATE",
                "routing_rules",
                rule.id,
                None,
                {"category": category, "email_address": email_address},
                updated_by,
            )

        logger.info(f"📍 Updated routing rule: {client_id} -> {category}: {email_address}")
        return rule

    def delete_routing_rule(
        self, client_id: str, category: str, deleted_by: Optional[str] = None
    ) -> bool:
        """Delete routing rule for a category."""
        rule = (
            self.db.query(RoutingRule)
            .filter(RoutingRule.client_id == client_id, RoutingRule.category == category)
            .first()
        )

        if rule:
            old_values = {"category": rule.category, "email_address": rule.email_address}
            rule.is_active = False
            self._log_change("DELETE", "routing_rules", rule.id, old_values, None, deleted_by)
            logger.info(f"🗑️ Deleted routing rule: {client_id} -> {category}")
            return True

        return False

    # =============================================================================
    # BRANDING
    # =============================================================================

    def get_branding(self, client_id: str) -> Optional[ClientBranding]:
        """Get client branding configuration."""
        # First try database
        branding = (
            self.db.query(ClientBranding).filter(ClientBranding.client_id == client_id).first()
        )
        if branding:
            return branding

        # Fall back to config manager
        config = self.config_manager.get_client_config(client_id)
        if config and config.branding:
            branding = ClientBranding(
                client_id=client_id,
                company_name=config.branding.company_name,
                primary_color=config.branding.primary_color,
                secondary_color=config.branding.secondary_color,
                logo_url=config.branding.logo_url,
                email_signature=config.branding.email_signature,
                footer_text=config.branding.footer_text,
                colors=getattr(config.branding, "colors", None),
            )
            self.db.add(branding)
            self.db.flush()
            return branding

        return None

    def update_branding(
        self, client_id: str, branding_data: Dict[str, Any], updated_by: Optional[str] = None
    ) -> ClientBranding:
        """Update client branding configuration."""
        branding = self.get_branding(client_id)

        if branding:
            old_values = {
                "company_name": branding.company_name,
                "primary_color": branding.primary_color,
                "secondary_color": branding.secondary_color,
                "logo_url": branding.logo_url,
                "email_signature": branding.email_signature,
                "footer_text": branding.footer_text,
                "colors": branding.colors,
            }

            # Apply updates
            for key, value in branding_data.items():
                if hasattr(branding, key):
                    setattr(branding, key, value)

            self._log_change(
                "UPDATE", "client_branding", branding.id, old_values, branding_data, updated_by
            )
        else:
            branding = ClientBranding(client_id=client_id, **branding_data)
            self.db.add(branding)
            self.db.flush()
            self._log_change(
                "CREATE", "client_branding", branding.id, None, branding_data, updated_by
            )

        logger.info(f"🎨 Updated branding: {client_id}")
        return branding

    # =============================================================================
    # RESPONSE TIMES
    # =============================================================================

    def get_response_times(self, client_id: str) -> List[ResponseTime]:
        """Get all response time configurations for a client."""
        # First get from database
        db_times = self.db.query(ResponseTime).filter(ResponseTime.client_id == client_id).all()

        # If no DB times, load from config
        if not db_times:
            config = self.config_manager.get_client_config(client_id)
            if config and config.response_times:
                # Handle different response time categories
                for category in ["support", "billing", "sales", "general", "urgent"]:
                    if hasattr(config.response_times, category):
                        settings = getattr(config.response_times, category)
                        if settings:
                            if isinstance(settings, str):
                                target = settings
                                business_hours = True
                            else:
                                target = settings.target
                                business_hours = getattr(settings, "business_hours_only", True)

                            response_time = ResponseTime(
                                client_id=client_id,
                                category=category,
                                target_response=target,
                                business_hours_only=business_hours,
                            )
                            self.db.add(response_time)
                            db_times.append(response_time)
                self.db.flush()

        return db_times

    def update_response_time(
        self,
        client_id: str,
        category: str,
        target_response: str,
        business_hours_only: bool = True,
        updated_by: Optional[str] = None,
    ) -> ResponseTime:
        """Update response time for a category."""
        response_time = (
            self.db.query(ResponseTime)
            .filter(ResponseTime.client_id == client_id, ResponseTime.category == category)
            .first()
        )

        if response_time:
            old_values = {
                "target_response": response_time.target_response,
                "business_hours_only": response_time.business_hours_only,
            }
            response_time.target_response = target_response
            response_time.business_hours_only = business_hours_only
            self._log_change(
                "UPDATE",
                "response_times",
                response_time.id,
                old_values,
                {"target_response": target_response, "business_hours_only": business_hours_only},
                updated_by,
            )
        else:
            response_time = ResponseTime(
                client_id=client_id,
                category=category,
                target_response=target_response,
                business_hours_only=business_hours_only,
            )
            self.db.add(response_time)
            self.db.flush()
            self._log_change(
                "CREATE",
                "response_times",
                response_time.id,
                None,
                {"category": category, "target_response": target_response},
                updated_by,
            )

        logger.info(f"⏱️ Updated response time: {client_id} -> {category}: {target_response}")
        return response_time

    # =============================================================================
    # AI PROMPTS
    # =============================================================================

    def get_ai_prompt(self, client_id: str, prompt_type: str) -> Optional[AIPrompt]:
        """Get active AI prompt for a type."""
        # First try database
        prompt = (
            self.db.query(AIPrompt)
            .filter(
                AIPrompt.client_id == client_id,
                AIPrompt.prompt_type == prompt_type,
                AIPrompt.is_active == True,
            )
            .first()
        )

        if prompt:
            return prompt

        # Fall back to config manager
        try:
            prompt_content = self.config_manager.load_ai_prompt(client_id, prompt_type)
            if prompt_content:
                prompt = AIPrompt(
                    client_id=client_id,
                    prompt_type=prompt_type,
                    prompt_content=prompt_content,
                    version=1,
                )
                self.db.add(prompt)
                self.db.flush()
                return prompt
        except Exception as e:
            logger.debug(f"Could not load AI prompt from config: {e}")

        return None

    def update_ai_prompt(
        self,
        client_id: str,
        prompt_type: str,
        prompt_content: str,
        updated_by: Optional[str] = None,
    ) -> AIPrompt:
        """Update AI prompt content."""
        # Deactivate current prompt
        current = self.get_ai_prompt(client_id, prompt_type)
        if current:
            current.is_active = False

        # Create new version
        prompt = AIPrompt(
            client_id=client_id,
            prompt_type=prompt_type,
            prompt_content=prompt_content,
            version=(current.version + 1) if current else 1,
        )
        self.db.add(prompt)
        self.db.flush()

        self._log_change(
            "CREATE",
            "ai_prompts",
            prompt.id,
            None,
            {"prompt_type": prompt_type, "version": prompt.version},
            updated_by,
        )

        logger.info(f"🤖 Updated AI prompt: {client_id} -> {prompt_type} (v{prompt.version})")
        return prompt

    # =============================================================================
    # YAML SYNCHRONIZATION
    # =============================================================================

    def sync_from_yaml(self, client_id: str) -> bool:
        """Load configuration from YAML files into database."""
        try:
            # Load existing YAML configuration
            config = self.config_manager.get_client_config(client_id)

            if not config:
                raise ValueError(f"Client config for {client_id} not found in ConfigManager")

            # Create or update client
            client_data = {
                "id": config.client_id,
                "name": config.name,
                "industry": config.industry,
                "status": "active" if config.active else "inactive",
                "timezone": config.timezone,
                "business_hours": "9-17",  # Placeholder
            }

            existing_client = self.get_client(client_id)
            if existing_client:
                self.update_client(client_id, client_data, "yaml_sync")
            else:
                self.create_client(client_data, "yaml_sync")

            # Sync branding
            if config.branding:
                branding_data = {
                    "company_name": config.branding.company_name,
                    "primary_color": config.branding.primary_color,
                    "secondary_color": config.branding.secondary_color,
                    "logo_url": config.branding.logo_url,
                    "email_signature": config.branding.email_signature,
                    "footer_text": config.branding.footer_text,
                    "colors": getattr(config.branding, "colors", None),
                }
                self.update_branding(client_id, branding_data, "yaml_sync")

            # Sync routing rules
            if config.routing:
                for category, email in config.routing.items():
                    self.update_routing_rule(client_id, category, email, "yaml_sync")

            # Sync response times
            if config.response_times:
                for category in ["support", "billing", "sales", "general", "urgent"]:
                    if hasattr(config.response_times, category):
                        settings = getattr(config.response_times, category)
                        if settings:
                            if isinstance(settings, str):
                                target = settings
                                business_hours = True
                            else:
                                target = settings.target
                                business_hours = getattr(settings, "business_hours_only", True)
                            self.update_response_time(
                                client_id, category, target, business_hours, "yaml_sync"
                            )

            self.db.commit()
            logger.info(f"✅ Synced {client_id} from YAML to database")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to sync {client_id} from YAML: {e}")
            return False

    def sync_to_yaml(self, client_id: str) -> bool:
        """Export database configuration to YAML files."""
        # This will be implemented in a later milestone
        logger.info(f"📝 YAML sync for {client_id} (not implemented yet)")
        return True

    # =============================================================================
    # AUDIT LOGGING
    # =============================================================================

    def _log_change(
        self,
        change_type: str,
        table_name: str,
        record_id: Any,
        old_values: Optional[Dict[Any, Any]] = None,
        new_values: Optional[Dict[Any, Any]] = None,
        changed_by: Optional[str] = None,
    ) -> None:
        """Log configuration change for audit trail."""
        change = ConfigurationChange(
            client_id=(
                record_id
                if table_name == "clients"
                else getattr(self, "_current_client_id", "unknown")
            ),
            change_type=change_type,
            table_name=table_name,
            record_id=str(record_id),
            old_values=old_values,
            new_values=new_values,
            changed_by=changed_by or "system",
        )
        self.db.add(change)

    def get_audit_trail(self, client_id: str, limit: int = 100) -> List[ConfigurationChange]:
        """Get audit trail for a client."""
        return (
            self.db.query(ConfigurationChange)
            .filter(ConfigurationChange.client_id == client_id)
            .order_by(ConfigurationChange.created_at.desc())
            .limit(limit)
            .all()
        )

    # =============================================================================
    # PRIVATE HELPERS
    # =============================================================================

    def _create_client_from_config(self, config: Any) -> Client:
        """Create a Client model instance from ConfigManager config."""
        client = Client(
            id=config.client_id,
            name=config.name,
            industry=config.industry,
            status="active" if config.active else "inactive",
            timezone=config.timezone,
            business_hours="9-17",  # Default, could be enhanced
        )
        # Don't add to DB session here, just return the model
        return client


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================


def get_database_config_bridge(db: Session) -> DatabaseConfigBridge:
    """Dependency injection for DatabaseConfigBridge."""
    return DatabaseConfigBridge(db)
