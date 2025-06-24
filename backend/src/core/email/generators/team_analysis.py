"""
Team analysis email generator.

Handles generation of detailed team analysis emails for both
client-specific and generic scenarios.
"""

import logging
from typing import Any, Dict, Optional

from infrastructure.config.manager import get_config_manager

from .base import BaseEmailGenerator

logger = logging.getLogger(__name__)


class TeamAnalysisGenerator(BaseEmailGenerator):
    """
    Generator for team analysis emails.

    This generator creates detailed internal analysis emails
    that provide teams with comprehensive information about
    customer inquiries and suggested response approaches.
    """

    def __init__(
        self,
        client_manager,
        ai_client,
        fallback_provider,
        template_loader,
        template_engine,
        context_builder,
    ):
        """
        Initialize the team analysis generator.

        Args:
            client_manager: ClientManager instance for accessing client data
            ai_client: AI client for generating email content
            fallback_provider: Provider for fallback responses
            template_loader: Template loader for client-specific templates
            template_engine: Template engine for variable injection
            context_builder: Context builder for template variables
        """
        super().__init__(client_manager, ai_client, fallback_provider)
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
        Generate team analysis email.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated team analysis text
        """
        return await self.generate_with_fallback(email_data, classification, client_id)

    async def generate_client_specific(
        self, email_data: Dict[str, Any], classification: Dict[str, Any], client_id: str
    ) -> str:
        """
        Generate client-specific team analysis using templates and AI.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Client identifier

        Returns:
            Generated client-specific team analysis text
        """
        try:
            # Compose team analysis prompt using client templates
            prompt = self._compose_team_analysis_prompt(client_id, email_data, classification)

            # Generate team analysis using AI
            analysis = await self._ai_client.call_ai_service(prompt)

            logger.info(f"✍️ Generated client-specific team analysis for {client_id}")
            return analysis

        except Exception as e:
            logger.error(f"Client-specific team analysis generation failed for {client_id}: {e}")
            raise

    async def generate_generic(
        self, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Generate generic team analysis when no client is identified.

        Args:
            email_data: Email data from webhook
            classification: Email classification result

        Returns:
            Generated generic team analysis text
        """
        category = classification.get("category", "general")
        confidence = classification.get("confidence", 0.5)

        prompt = f"""Analyze this email for team routing and response.

        Classification: {category} (confidence: {confidence:.2f})
        From: {email_data.get('from', 'Unknown')}
        Subject: {email_data.get('subject', 'No subject')}
        Content: {email_data.get('stripped_text', email_data.get('body_text', ''))[:500]}...

        Provide:
        1. Summary of the issue/request
        2. Suggested response approach
        3. Priority level
        4. Any special considerations
        """

        try:
            return await self._ai_client.call_ai_service(prompt)
        except Exception as e:
            logger.error(f"Generic team analysis generation failed: {e}")
            raise

    def get_fallback_response(self, classification: Dict[str, Any]) -> str:
        """
        Get hard fallback team analysis response.

        Args:
            classification: Email classification result

        Returns:
            Hard fallback team analysis text
        """
        return self._fallback_provider.get_hard_fallback_team_analysis(classification)

    def get_client_fallback_response(self, client_id: str, category: str) -> str:
        """
        Get client-specific fallback team analysis response.

        Args:
            client_id: Client identifier
            category: Email category

        Returns:
            Client-specific fallback team analysis text
        """
        try:
            fallback_responses = get_config_manager().load_fallback_responses(client_id)

            if "team_analysis" in fallback_responses:
                responses = fallback_responses["team_analysis"]
                if category in responses:
                    return responses[category]
                elif "general" in responses:
                    return responses["general"]

            # Fall back to hard fallback
            return self._fallback_provider.get_hard_fallback_response("team_analysis", category)

        except Exception:
            return self._fallback_provider.get_hard_fallback_response("team_analysis", category)

    def _compose_team_analysis_prompt(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Compose team analysis prompt for a client using templates.

        Args:
            client_id: Client identifier
            email_data: Original email data
            classification: Email classification result

        Returns:
            Composed team analysis prompt
        """
        try:
            template = self._template_loader.load_template(client_id, "team-analysis")
            context = self._context_builder.create_context_with_routing(
                client_id, email_data, classification
            )

            prompt = self._template_engine.inject_variables(template, context)

            logger.debug(f"Composed team analysis prompt for {client_id}")
            return prompt

        except Exception as e:
            logger.error(f"Failed to compose team analysis prompt for {client_id}: {e}")
            # Return fallback prompt
            return self._get_fallback_team_analysis_prompt(client_id, classification)

    def _get_fallback_team_analysis_prompt(
        self, client_id: str, classification: Dict[str, Any]
    ) -> str:
        """
        Get fallback team analysis prompt when template loading fails.

        Args:
            client_id: Client identifier
            classification: Email classification result

        Returns:
            Fallback team analysis prompt
        """
        category = classification.get("category", "general")
        return f"""
Email classified as {category.upper()} inquiry (fallback classification).
Client: {client_id}

Please review the original message and respond according to standard {category} procedures.
Check for any special handling requirements or escalation needs.
"""


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_team_analysis_generator(
    client_manager=None,
    ai_client=None,
    fallback_provider=None,
    template_loader=None,
    template_engine=None,
    context_builder=None,
) -> TeamAnalysisGenerator:
    """
    Dependency injection function for TeamAnalysisGenerator.

    Args:
        client_manager: ClientManager instance
        ai_client: AI client instance
        fallback_provider: Fallback response provider instance
        template_loader: Template loader instance
        template_engine: Template engine instance
        context_builder: Context builder instance

    Returns:
        TeamAnalysisGenerator instance
    """
    if not hasattr(get_team_analysis_generator, "_instance"):
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
            context_builder = context_builder or get_template_context_builder(client_manager)

        get_team_analysis_generator._instance = TeamAnalysisGenerator(
            client_manager,
            ai_client,
            fallback_provider,
            template_loader,
            template_engine,
            context_builder,
        )
    return get_team_analysis_generator._instance
