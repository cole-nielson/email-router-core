"""
Fallback response templates.

Provides hard-coded fallback responses organized by type and category
for use when AI services are unavailable.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FallbackResponseProvider:
    """
    Provides hard-coded fallback responses when AI services are unavailable.

    This class manages fallback templates for different types of email responses
    including customer acknowledgments and team analysis messages.
    """

    @staticmethod
    def get_hard_fallback_acknowledgment(classification: Dict[str, Any]) -> str:
        """
        Get hard-coded fallback acknowledgment - used only when AI is completely unavailable.

        Args:
            classification: Email classification result containing category information

        Returns:
            Human-like acknowledgment text with automation disclaimer
        """
        category = classification.get("category", "general")

        # Human-like fallback responses with automation disclaimer
        fallbacks = {
            "support": """Hi!

I got your tech support message and I can see you're having some trouble. I've flagged this for our technical team and they'll dig into it for you.

You should hear back within 4 business hours - they're pretty quick with these things.

Thanks for reaching out!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "billing": """Hey there!

Thanks for getting in touch about the billing question. I can see this is important to you, so I've sent it straight to our accounting folks who handle all the payment stuff.

They'll take a look and get back to you within 24 hours with an answer.

Appreciate your patience!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "sales": """Hi!

Great to hear from you! I can see you're interested in learning more about what we offer.

I've let our sales team know you reached out and they'll be in touch within 2 business hours to chat about your needs and see how we can help.

Looking forward to connecting!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "general": """Hi there!

Thanks for your message! I've received it and made sure it gets to the right people for a proper response.

You should hear back within 24 hours.

Thanks for taking the time to reach out!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
        }

        response = fallbacks.get(category, fallbacks["general"])
        logger.info(f"Providing hard fallback acknowledgment for category: {category}")
        return response

    @staticmethod
    def get_hard_fallback_team_analysis(classification: Dict[str, Any]) -> str:
        """
        Get hard-coded fallback team analysis.

        Args:
            classification: Email classification result containing category information

        Returns:
            Simple team analysis fallback message
        """
        category = classification.get("category", "general")
        response = f"Email classified as {category.upper()} inquiry (fallback classification). Please review the original message and respond accordingly."

        logger.info(f"Providing hard fallback team analysis for category: {category}")
        return response

    @staticmethod
    def get_hard_fallback_response(response_type: str, category: str) -> str:
        """
        Get hard-coded fallback response for generic usage.

        Args:
            response_type: Type of response needed (e.g., 'customer_acknowledgments', 'team_analysis')
            category: Email category for the response

        Returns:
            Generic fallback response text
        """
        if response_type == "customer_acknowledgments":
            response = f"Thank you for contacting us regarding your {category} inquiry. We will respond as soon as possible."
        else:
            response = f"Email classified as {category.upper()} inquiry. Please review and respond accordingly."

        logger.info(f"Providing generic hard fallback for {response_type}, category: {category}")
        return response


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_fallback_response_provider() -> FallbackResponseProvider:
    """Dependency injection function for FallbackResponseProvider."""
    if not hasattr(get_fallback_response_provider, "_instance"):
        get_fallback_response_provider._instance = FallbackResponseProvider()
    return get_fallback_response_provider._instance
