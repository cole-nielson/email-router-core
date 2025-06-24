"""
Email service orchestrator for AI-powered response generation.
🚀 Coordinates specialized email generators and template processing services.
🎯 Provides a unified interface for email generation with comprehensive fallback handling.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.config.manager import get_config_manager
from infrastructure.templates.email import _get_default_branding, create_branded_template

from ..clients.manager import ClientManager
from .ai.client import get_ai_client
from .branding.manager import get_branding_manager
from .fallbacks.responses import get_fallback_response_provider
from .generators.acknowledgment import get_acknowledgment_generator
from .generators.team_analysis import get_team_analysis_generator
from .templates.context import TemplateContextBuilder
from .templates.engine import get_template_engine
from .templates.loader import get_template_loader
from .templates.validator import ValidationResult, get_template_validator

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service orchestrator that coordinates specialized generators.

    This service acts as a unified interface for email generation by delegating to
    specialized generator classes while maintaining template processing capabilities.

    Architecture:
    - Delegates email generation to specialized generator classes
    - Coordinates template processing and validation
    - Manages client branding and configuration
    - Provides comprehensive fallback handling
    - Maintains backward compatibility with existing APIs
    """

    def __init__(self, client_manager: ClientManager):
        """
        Initialize the email service orchestrator.

        Args:
            client_manager: ClientManager instance for accessing client data
        """
        self.client_manager = client_manager
        self._branding_manager = get_branding_manager()
        self._template_validator = get_template_validator()
        self._context_builder = TemplateContextBuilder(client_manager)
        self._template_loader = get_template_loader(self._template_validator)
        self._template_engine = get_template_engine()
        self._ai_client = get_ai_client()
        self._fallback_provider = get_fallback_response_provider()
        self._acknowledgment_generator = get_acknowledgment_generator(
            client_manager,
            self._ai_client,
            self._fallback_provider,
            self._template_loader,
            self._template_engine,
            self._context_builder,
        )
        self._team_analysis_generator = get_team_analysis_generator(
            client_manager,
            self._ai_client,
            self._fallback_provider,
            self._template_loader,
            self._template_engine,
            self._context_builder,
        )

    # =============================================================================
    # EMAIL GENERATION ORCHESTRATION API
    # =============================================================================

    async def generate_customer_acknowledgment(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate customer acknowledgment by delegating to acknowledgment generator.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated acknowledgment text
        """
        return await self._acknowledgment_generator.generate(email_data, classification, client_id)

    async def generate_team_analysis(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate team analysis by delegating to team analysis generator.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated team analysis text
        """
        return await self._team_analysis_generator.generate(email_data, classification, client_id)

    async def generate_plain_text_emails(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate complete email pair by coordinating generators and applying branding.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID

        Returns:
            Tuple of (plain_text_customer_response, html_team_analysis)
        """
        try:
            # Generate human-like plain text customer response
            customer_content = await self.generate_customer_acknowledgment(
                email_data, classification, client_id
            )

            # Generate team analysis (keep as structured content for internal use)
            team_content = await self.generate_team_analysis(email_data, classification, client_id)

            # For team analysis, apply HTML branding for internal readability
            if client_id:
                client_config = self.client_manager.get_client_config(client_id)
                branding = self._branding_manager.load_client_branding(client_id, client_config)
            else:
                branding = _get_default_branding()

            team_template = create_branded_template(
                content=team_content,
                branding=branding,
                context={
                    "email_type": "team_analysis",
                    "classification": classification,
                    "original_sender": email_data.get("from", ""),
                    "original_subject": email_data.get("subject", "No Subject"),
                    "routing_info": {
                        "category": classification.get("category", "general"),
                        "confidence": classification.get("confidence", 0.0),
                        "priority": classification.get("priority", "medium"),
                    },
                },
            )

            # Customer gets plain text, team gets HTML
            return customer_content, team_template

        except Exception as e:
            logger.error(f"Plain text email generation failed: {e}")
            # Return basic fallback responses
            customer_fallback = self._acknowledgment_generator.get_fallback_response(classification)
            team_fallback = self._team_analysis_generator.get_fallback_response(classification)
            return customer_fallback, team_fallback

    # =============================================================================
    # TEMPLATE AND UTILITY SERVICES
    # =============================================================================

    def compose_classification_prompt(self, client_id: str, email_data: Dict[str, Any]) -> str:
        """
        Compose classification prompt for a client.

        Args:
            client_id: Client identifier
            email_data: Email data to classify

        Returns:
            Composed classification prompt
        """
        try:
            logger.debug(f"Loading classification template for {client_id}")
            template = self._template_loader.load_template(client_id, "classification")

            logger.debug(f"Preparing template context for {client_id}")
            context = self._context_builder.prepare_template_context(client_id, email_data)

            logger.debug(f"Injecting template variables for {client_id}")
            prompt = self._template_engine.inject_variables(template, context)

            # Check for any remaining MISSING values in the final prompt
            missing_vars = re.findall(r"MISSING: ([^}]+)", prompt)
            if missing_vars:
                logger.warning(
                    f"Template contains missing variables for {client_id}: {missing_vars}"
                )
                logger.debug(f"Full template context keys: {list(context.keys())}")

            logger.info(f"✅ Composed classification prompt for {client_id} ({len(prompt)} chars)")
            logger.debug(f"Classification prompt preview: {prompt[:200]}...")
            return prompt

        except Exception as e:
            logger.error(f"❌ Failed to compose classification prompt for {client_id}: {e}")
            logger.debug(f"Exception details: {str(e)}", exc_info=True)

            # Fallback to basic classification prompt
            logger.warning(f"Using fallback classification prompt for {client_id}")
            return self._get_fallback_classification_prompt(email_data)

    def validate_template(self, template_content: str, client_id: str = None) -> ValidationResult:
        """
        Validate template content for correctness and security.

        Args:
            template_content: Template content to validate
            client_id: Optional client ID for context

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        return self._template_validator.validate_template(template_content, client_id)

    def get_fallback_response(
        self, client_id: str, response_type: str, category: str = "general"
    ) -> str:
        """
        Get fallback response for a client and category.

        Args:
            client_id: Client identifier
            response_type: Type of response ('customer_acknowledgments', 'team_analysis')
            category: Email category

        Returns:
            Fallback response text
        """
        try:
            fallback_responses = get_config_manager().load_fallback_responses(client_id)

            if response_type in fallback_responses:
                responses = fallback_responses[response_type]
                if category in responses:
                    return responses[category]
                elif "general" in responses:
                    return responses["general"]

            # Hard fallback
            return self._fallback_provider.get_hard_fallback_response(response_type, category)

        except Exception:
            return self._fallback_provider.get_hard_fallback_response(response_type, category)

    def clear_cache(self):
        """Clear all caches."""
        self._template_loader.clear_cache()
        self._branding_manager.clear_cache()
        logger.info("Template and branding caches cleared")

    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================

    def _get_fallback_classification_prompt(self, email_data: Dict[str, Any]) -> str:
        """Get basic fallback classification prompt."""
        return f"""
You are an intelligent email classifier. Analyze this email and classify it:

Categories:
- support: Technical problems, how-to questions, product issues
- billing: Payment issues, invoices, account billing questions
- sales: Pricing inquiries, product demos, new business opportunities
- general: Everything else that doesn't fit the above categories

Email to classify:
From: {email_data.get('from', 'Unknown')}
Subject: {email_data.get('subject', 'No subject')}
Content: {email_data.get('stripped_text', email_data.get('body_text', ''))[:1000]}

Respond with JSON: {{"category": "support|billing|sales|general", "confidence": 0.95, "reasoning": "explanation"}}
"""


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_email_service() -> EmailService:
    """Dependency injection function for EmailService."""
    if not hasattr(get_email_service, "_instance"):
        from ..clients.manager import get_client_manager

        client_manager = get_client_manager()
        get_email_service._instance = EmailService(client_manager)
    return get_email_service._instance


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================


async def generate_plain_text_emails(
    email_data: Dict[str, Any], classification: Dict[str, Any], client_id: Optional[str] = None
) -> Tuple[str, str]:
    """Generate human-like plain text customer response and HTML team analysis."""
    email_service = get_email_service()
    return await email_service.generate_plain_text_emails(email_data, classification, client_id)
