"""
Template context builder.

Builds context dictionaries for template processing by extracting
and formatting data from client configs and email data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..fallbacks.calculator import get_response_time_calculator

logger = logging.getLogger(__name__)


class TemplateContextBuilder:
    """Builds context dictionaries for template variable injection."""

    def __init__(self, client_manager: Any) -> None:
        """
        Initialize the context builder.

        Args:
            client_manager: ClientManager instance for accessing client data
        """
        self.client_manager = client_manager
        self._response_time_calculator = get_response_time_calculator(client_manager)

    def prepare_template_context(
        self, client_id: str, email_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for template variable injection.

        Args:
            client_id: Client identifier
            email_data: Optional email data

        Returns:
            Context dictionary for template injection
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            if not client_config:
                logger.error(f"Could not load client config for {client_id} to prepare context")
                return {"client": {"name": "Unknown Client"}, "email": {}}

            context = {
                "client": {
                    "name": client_config.name,
                    "id": client_config.client_id,
                    "industry": client_config.industry,
                    "timezone": client_config.timezone,
                    "business_hours": "N/A",  # This needs to be adapted from new config
                    "branding": {
                        "company_name": client_config.branding.company_name,
                        "primary_color": client_config.branding.primary_color,
                        "secondary_color": client_config.branding.secondary_color,
                        "logo_url": client_config.branding.logo_url,
                        "email_signature": client_config.branding.email_signature,
                        "footer_text": client_config.branding.footer_text,
                    },
                },
                "today": (str(datetime.now().date()) if "datetime" in globals() else "today"),
                "timestamp": str(datetime.now()) if "datetime" in globals() else "now",
            }

            if email_data:
                context.update(
                    {
                        "email": {
                            "from": email_data.get("from", ""),
                            "to": email_data.get("to", email_data.get("recipient", "")),
                            "subject": email_data.get("subject", ""),
                            "body": email_data.get(
                                "stripped_text", email_data.get("body_text", "")
                            ),
                            "timestamp": email_data.get("timestamp", ""),
                        }
                    }
                )

            return context

        except Exception as e:
            logger.error(f"Failed to prepare template context for {client_id}: {e}")
            return {"client": {"name": "Unknown Client"}, "email": {}}

    @staticmethod
    def get_nested_value(data: Dict[str, Any], path: str, default: Optional[str] = None) -> Any:
        """
        Get nested value from dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'client.branding.primary_color')
            default: Default value if path not found

        Returns:
            Found value or default
        """
        try:
            keys = path.split(".")
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default or f"MISSING: {path}"

            return current

        except Exception:
            return default or f"ERROR: {path}"

    def create_context_with_classification(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create context with additional classification data.

        Args:
            client_id: Client identifier
            email_data: Email data
            classification: Classification result

        Returns:
            Enhanced context dictionary
        """
        context = self.prepare_template_context(client_id, email_data)

        # Add classification-specific context
        category = classification.get("category", "general")
        context.update(
            {
                "category": category,
                "priority": classification.get("priority", "medium"),
                "confidence": classification.get("confidence", 0.5),
                "reasoning": classification.get("reasoning", ""),
                "suggested_actions": classification.get("suggested_actions", []),
            }
        )

        return context

    def create_context_with_routing(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create context with routing information.

        Args:
            client_id: Client identifier
            email_data: Email data
            classification: Classification result

        Returns:
            Context dictionary with routing information
        """
        context = self.create_context_with_classification(client_id, email_data, classification)

        # Add routing-specific context
        category = classification.get("category", "general")
        routing_destination = self.client_manager.get_routing_destination(client_id, category)

        context.update(
            {
                "routing_destination": routing_destination,
                "response_time_target": self._response_time_calculator.get_response_time_target(
                    client_id, category
                ),
            }
        )

        return context


# Singleton instance
_context_builder_instance: Optional[TemplateContextBuilder] = None


def get_template_context_builder(
    client_manager: Optional[Any] = None,
) -> TemplateContextBuilder:
    """
    Get or create the singleton TemplateContextBuilder instance.

    Args:
        client_manager: ClientManager instance (required for first call)

    Returns:
        TemplateContextBuilder instance
    """
    global _context_builder_instance
    if _context_builder_instance is None:
        if client_manager is None:
            raise ValueError("client_manager is required for first initialization")
        _context_builder_instance = TemplateContextBuilder(client_manager)
    return _context_builder_instance
