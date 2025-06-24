"""
Base email generator abstract class.

Defines the interface for all email generators and common error handling patterns.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseEmailGenerator(ABC):
    """
    Abstract base class for all email generators.

    This class defines the common interface and shared functionality
    for all email generation classes in the system.
    """

    def __init__(self, client_manager, ai_client, fallback_provider):
        """
        Initialize the base email generator.

        Args:
            client_manager: ClientManager instance for accessing client data
            ai_client: AI client for generating email content
            fallback_provider: Provider for fallback responses
        """
        self.client_manager = client_manager
        self._ai_client = ai_client
        self._fallback_provider = fallback_provider

    @abstractmethod
    async def generate(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate email content.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated email content
        """
        pass

    @abstractmethod
    async def generate_generic(
        self, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Generate generic email content when no client is identified.

        Args:
            email_data: Email data from webhook
            classification: Email classification result

        Returns:
            Generated generic email content
        """
        pass

    @abstractmethod
    def get_fallback_response(self, classification: Dict[str, Any]) -> str:
        """
        Get hard fallback response when all other methods fail.

        Args:
            classification: Email classification result

        Returns:
            Fallback response text
        """
        pass

    @abstractmethod
    def get_client_fallback_response(self, client_id: str, category: str) -> str:
        """
        Get client-specific fallback response.

        Args:
            client_id: Client identifier
            category: Email category

        Returns:
            Client-specific fallback response text
        """
        pass

    def identify_client(self, email_data: Dict[str, Any]) -> Optional[str]:
        """
        Identify client from email data.

        Args:
            email_data: Email data from webhook

        Returns:
            Client ID if identified, None otherwise
        """
        try:
            result = self.client_manager.identify_client_by_email(
                email_data.get("to") or email_data.get("recipient", "")
            )
            return result.client_id if result.is_successful else None
        except Exception as e:
            logger.warning(f"Client identification failed: {e}")
            return None

    async def generate_with_fallback(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate email content with comprehensive fallback handling.

        This method implements the standard pattern used across all generators:
        1. Try client-specific generation if client identified
        2. Fall back to client-specific fallback responses
        3. Fall back to generic generation
        4. Fall back to hard-coded responses

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID

        Returns:
            Generated email content
        """
        try:
            # Identify client if not provided
            if not client_id:
                client_id = self.identify_client(email_data)

            if client_id:
                # Try client-specific generation
                try:
                    return await self.generate_client_specific(
                        email_data, classification, client_id
                    )
                except Exception as e:
                    logger.warning(f"Client-specific generation failed for {client_id}: {e}")
                    # Try client-specific fallback
                    try:
                        return self.get_client_fallback_response(
                            client_id, classification.get("category", "general")
                        )
                    except Exception as fallback_e:
                        logger.warning(f"Client fallback failed for {client_id}: {fallback_e}")

            # Fall back to generic generation
            try:
                return await self.generate_generic(email_data, classification)
            except Exception as e:
                logger.error(f"Generic generation failed: {e}")

            # Final fallback to hard-coded response
            return self.get_fallback_response(classification)

        except Exception as e:
            logger.error(f"Email generation completely failed: {e}")
            return self.get_fallback_response(classification)

    @abstractmethod
    async def generate_client_specific(
        self, email_data: Dict[str, Any], classification: Dict[str, Any], client_id: str
    ) -> str:
        """
        Generate client-specific email content.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Client identifier

        Returns:
            Generated client-specific email content
        """
        pass


class GeneratorError(Exception):
    """Base exception for email generator errors."""

    pass


class ClientSpecificGenerationError(GeneratorError):
    """Raised when client-specific generation fails."""

    pass


class GenericGenerationError(GeneratorError):
    """Raised when generic generation fails."""

    pass


class FallbackGenerationError(GeneratorError):
    """Raised when fallback generation fails."""

    pass
