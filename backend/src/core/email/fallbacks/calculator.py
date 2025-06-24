"""
Response time calculator.

Calculates response time targets and applies business rules
for SLA commitments.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ResponseTimeCalculator:
    """
    Calculates response time targets based on email categories and client configurations.

    This class encapsulates the business logic for determining appropriate
    response time commitments based on email category, client SLA requirements,
    and fallback policies.
    """

    def __init__(self, client_manager):
        """
        Initialize the response time calculator.

        Args:
            client_manager: ClientManager instance for accessing client configurations
        """
        self.client_manager = client_manager

    def get_response_time_target(self, client_id: str, category: str) -> str:
        """
        Get response time target for a specific client and email category.

        This method applies business rules to determine the appropriate response
        time commitment, considering:
        1. Client-specific SLA configurations
        2. Category-based defaults
        3. Industry standard fallbacks

        Args:
            client_id: Client identifier
            category: Email category (support, billing, sales, urgent, general)

        Returns:
            Response time target string (e.g., "within 4 hours")
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)

            # Check if response_times exists in config
            if hasattr(client_config, "response_times") and client_config.response_times:
                response_times = client_config.response_times

                # Get the specific category target
                if hasattr(response_times, category):
                    category_config = getattr(response_times, category)
                    if hasattr(category_config, "target"):
                        target = category_config.target
                        logger.debug(
                            f"Using client-specific response time for {client_id}:{category}: {target}"
                        )
                        return target

            # Apply fallback targets based on category
            target = self._get_fallback_response_time(category)
            logger.debug(f"Using fallback response time for {client_id}:{category}: {target}")
            return target

        except Exception as e:
            logger.warning(f"Could not get response time target for {client_id}:{category}: {e}")
            return self._get_fallback_response_time(category)

    def _get_fallback_response_time(self, category: str) -> str:
        """
        Get fallback response time targets based on industry standards.

        These targets represent reasonable industry standard response times
        for different types of business communications.

        Args:
            category: Email category

        Returns:
            Fallback response time target string
        """
        # Industry standard fallback targets
        fallback_targets = {
            "support": "within 4 hours",  # Technical support - same business day
            "billing": "within 24 hours",  # Billing inquiries - next business day
            "sales": "within 2 hours",  # Sales inquiries - quick response for leads
            "urgent": "within 1 hour",  # Urgent matters - immediate attention
            "general": "within 24 hours",  # General inquiries - standard response
        }

        return fallback_targets.get(category, "within 24 hours")

    def get_all_category_targets(self, client_id: str) -> Dict[str, str]:
        """
        Get response time targets for all standard categories.

        Args:
            client_id: Client identifier

        Returns:
            Dictionary mapping categories to their response time targets
        """
        categories = ["support", "billing", "sales", "urgent", "general"]
        return {
            category: self.get_response_time_target(client_id, category) for category in categories
        }

    def is_urgent_category(self, category: str) -> bool:
        """
        Check if a category requires urgent response handling.

        Args:
            category: Email category

        Returns:
            True if category requires urgent handling
        """
        urgent_categories = {"urgent", "critical", "emergency"}
        return category.lower() in urgent_categories

    def get_escalation_threshold(self, client_id: str, category: str) -> Optional[str]:
        """
        Get escalation threshold for delayed responses.

        Args:
            client_id: Client identifier
            category: Email category

        Returns:
            Escalation threshold string or None if not configured
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)

            if hasattr(client_config, "response_times") and client_config.response_times:
                response_times = client_config.response_times

                if hasattr(response_times, category):
                    category_config = getattr(response_times, category)
                    if hasattr(category_config, "escalation_threshold"):
                        return category_config.escalation_threshold

            return None

        except Exception as e:
            logger.debug(f"Could not get escalation threshold for {client_id}:{category}: {e}")
            return None


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_response_time_calculator(client_manager=None) -> ResponseTimeCalculator:
    """
    Dependency injection function for ResponseTimeCalculator.

    Args:
        client_manager: ClientManager instance (required for first call)

    Returns:
        ResponseTimeCalculator instance
    """
    if not hasattr(get_response_time_calculator, "_instance"):
        if client_manager is None:
            raise ValueError("client_manager is required for first initialization")
        get_response_time_calculator._instance = ResponseTimeCalculator(client_manager)
    return get_response_time_calculator._instance
