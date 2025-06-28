"""
Customer acknowledgment email generator.

Handles generation of customer acknowledgment emails for both
client-specific and generic scenarios.
"""

import logging
from typing import Any, Dict, Optional

from core.ports.config_provider import ConfigurationProvider

from .base import BaseEmailGenerator

logger = logging.getLogger(__name__)


class AcknowledgmentGenerator(BaseEmailGenerator):
    """
    Generator for customer acknowledgment emails.

    This generator creates brief, professional acknowledgment emails
    that confirm receipt of customer inquiries and set appropriate
    response time expectations.
    """

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        client_manager,
        ai_client,
        fallback_provider,
        template_loader,
        template_engine,
        context_builder,
    ):
        """
        Initialize the acknowledgment generator.

        Args:
            client_manager: ClientManager instance for accessing client data
            ai_client: AI client for generating email content
            fallback_provider: Provider for fallback responses
            template_loader: Template loader for client-specific templates
            template_engine: Template engine for variable injection
            context_builder: Context builder for template variables
        """
        super().__init__(client_manager, ai_client, fallback_provider)
        self._config_provider = config_provider
        self._template_loader = template_loader
        self._template_engine = template_engine
        self._context_builder = context_builder

    async def generate(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate customer acknowledgment email.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated acknowledgment text
        """
        return await self.generate_with_fallback(email_data, classification, client_id)

    async def generate_client_specific(
        self, email_data: Dict[str, Any], classification: Dict[str, Any], client_id: str
    ) -> str:
        """
        Generate client-specific acknowledgment using templates and AI.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Client identifier

        Returns:
            Generated client-specific acknowledgment text
        """
        try:
            # Compose acknowledgment prompt using client templates
            prompt = self._compose_acknowledgment_prompt(
                client_id, email_data, classification
            )

            # Generate acknowledgment using AI
            acknowledgment = await self._ai_client.call_ai_service(prompt)

            logger.info(f"✍️ Generated client-specific acknowledgment for {client_id}")
            return acknowledgment

        except Exception as e:
            logger.error(
                f"Client-specific acknowledgment generation failed for {client_id}: {e}"
            )
            raise

    async def generate_generic(
        self, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Generate generic acknowledgment when no client is identified.

        Args:
            email_data: Email data from webhook
            classification: Email classification result

        Returns:
            Generated generic acknowledgment text
        """
        category = classification.get("category", "general")

        prompt = f"""Generate a brief, professional email acknowledgment for a {category} inquiry.

        Original email subject: {email_data.get('subject', 'No subject')}
        From: {email_data.get('from', 'Unknown sender')}

        Requirements:
        - Keep it under 100 words
        - Be warm and professional
        - Acknowledge the specific type of inquiry
        - Set expectation for response time
        - Thank them for contacting
        """

        try:
            return await self._ai_client.call_ai_service(prompt)
        except Exception as e:
            logger.error(f"Generic acknowledgment generation failed: {e}")
            raise

    def get_fallback_response(self, classification: Dict[str, Any]) -> str:
        """
        Get hard fallback acknowledgment response.

        Args:
            classification: Email classification result

        Returns:
            Hard fallback acknowledgment text
        """
        return self._fallback_provider.get_hard_fallback_acknowledgment(classification)

    def get_client_fallback_response(self, client_id: str, category: str) -> str:
        """
        Get client-specific fallback acknowledgment response.

        Args:
            client_id: Client identifier
            category: Email category

        Returns:
            Client-specific fallback acknowledgment text
        """
        try:
            fallback_responses = self._config_provider.load_fallback_responses(
                client_id
            )

            if "customer_acknowledgments" in fallback_responses:
                responses = fallback_responses["customer_acknowledgments"]
                if category in responses:
                    return responses[category]
                elif "general" in responses:
                    return responses["general"]

            # Fall back to hard fallback
            return self._fallback_provider.get_hard_fallback_response(
                "customer_acknowledgments", category
            )

        except Exception:
            return self._fallback_provider.get_hard_fallback_response(
                "customer_acknowledgments", category
            )

    def _compose_acknowledgment_prompt(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Compose acknowledgment prompt for a client using templates.

        Args:
            client_id: Client identifier
            email_data: Original email data
            classification: Email classification result

        Returns:
            Composed acknowledgment prompt
        """
        try:
            template = self._template_loader.load_template(client_id, "acknowledgment")
            context = self._context_builder.create_context_with_classification(
                client_id, email_data, classification
            )

            prompt = self._template_engine.inject_variables(template, context)

            logger.debug(f"Composed acknowledgment prompt for {client_id}")
            return prompt

        except Exception as e:
            logger.error(
                f"Failed to compose acknowledgment prompt for {client_id}: {e}"
            )
            # Return fallback prompt
            return self._get_fallback_acknowledgment_prompt(client_id, classification)

    def _get_fallback_acknowledgment_prompt(
        self, client_id: str, classification: Dict[str, Any]
    ) -> str:
        """
        Get fallback acknowledgment prompt when template loading fails.

        Args:
            client_id: Client identifier
            classification: Email classification result

        Returns:
            Fallback acknowledgment prompt
        """
        category = classification.get("category", "general")
        return f"Generate a professional acknowledgment for a {category} inquiry from {client_id}. Keep it brief and set appropriate expectations."


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_acknowledgment_generator(
    client_manager=None,
    ai_client=None,
    fallback_provider=None,
    template_loader=None,
    template_engine=None,
    context_builder=None,
) -> AcknowledgmentGenerator:
    """
    Dependency injection function for AcknowledgmentGenerator.

    Args:
        client_manager: ClientManager instance
        ai_client: AI client instance
        fallback_provider: Fallback response provider instance
        template_loader: Template loader instance
        template_engine: Template engine instance
        context_builder: Context builder instance

    Returns:
        AcknowledgmentGenerator instance
    """
    if not hasattr(get_acknowledgment_generator, "_instance"):
        # Import dependencies if not provided
        if not all(
            [
                client_manager,
                ai_client,
                fallback_provider,
                template_loader,
                template_engine,
                context_builder,
            ]
        ):
            from ...clients.manager import get_client_manager
            from ..ai.client import get_ai_client
            from ..fallbacks.responses import get_fallback_response_provider
            from ..templates.context import get_template_context_builder
            from ..templates.engine import get_template_engine
            from ..templates.loader import get_template_loader
            from ..templates.validator import get_template_validator

            client_manager = client_manager or get_client_manager()
            ai_client = ai_client or get_ai_client()
            fallback_provider = fallback_provider or get_fallback_response_provider()
            template_validator = get_template_validator()
            template_loader = template_loader or get_template_loader(template_validator)
            template_engine = template_engine or get_template_engine()
            context_builder = context_builder or get_template_context_builder(
                client_manager
            )

        get_acknowledgment_generator._instance = AcknowledgmentGenerator(
            client_manager,
            ai_client,
            fallback_provider,
            template_loader,
            template_engine,
            context_builder,
        )
    return get_acknowledgment_generator._instance
