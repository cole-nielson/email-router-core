"""
Unified AI email classifier with client-specific prompts.
🤖 Multi-tenant email classification with personalized AI context and fallback handling.
Consolidates all AI classification functionality in a single service.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from core.ports.config_provider import ConfigurationProvider

from ..clients.manager import ClientManager
from ..clients.resolver import extract_domain_from_email
from ..email.service import EmailService

logger = logging.getLogger(__name__)


class AIClassifier:
    """
    Unified AI email classifier for multi-tenant email processing.

    Features:
    - Client-specific AI prompts and classification logic
    - Intelligent fallback to keyword-based classification
    - Claude 3.5 Sonnet integration with error handling
    - Confidence scoring and detailed reasoning
    """

    def __init__(self, config_provider: ConfigurationProvider, client_manager: ClientManager):
        """
        Initialize dynamic classifier.

        Args:
            config_provider: Configuration provider interface
            client_manager: ClientManager instance for client operations
        """
        self.config_provider = config_provider
        self.client_manager = client_manager
        self.email_service = EmailService(client_manager)

    async def classify_email(
        self, email_data: Dict[str, Any], client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify email using client-specific AI prompts.

        Args:
            email_data: Email data from webhook containing subject, body, sender, etc.
            client_id: Optional client ID. If not provided, will attempt to identify from email

        Returns:
            Classification result dictionary with category, confidence, reasoning, etc.
        """
        try:
            # Identify client if not provided
            if not client_id:
                client_id = self._identify_client_from_email(email_data)
                if not client_id:
                    logger.warning("No client identified for email, using fallback classification")
                    return await self._classify_with_fallback(email_data)

            # Validate client exists
            try:
                client_config = self.client_manager.get_client_config(client_id)
            except Exception as e:
                logger.error(f"Failed to load client config for {client_id}: {e}")
                return await self._classify_with_fallback(email_data)

            # Check if AI classification is enabled for this client
            if client_config is None or not client_config.settings.ai_classification_enabled:
                logger.info(f"AI classification disabled for client {client_id}, using fallback")
                return self._classify_with_keywords(client_id, email_data)

            # Compose client-specific classification prompt
            prompt = self.email_service.compose_classification_prompt(client_id, email_data)

            # Call AI service with composed prompt
            classification = await self._call_ai_service(prompt)

            # Add metadata
            classification.update(
                {
                    "client_id": client_id,
                    "ai_model": self.config_provider.get(
                        "services.anthropic_model", "claude-3-5-sonnet-20241022"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": "ai_client_specific",
                }
            )

            logger.info(
                f"🎯 AI Classification for {client_id}: {classification['category']} "
                f"({classification['confidence']:.2f})"
            )

            return classification

        except Exception as e:
            logger.error(f"AI classification failed for client {client_id}: {e}")

            # Fallback to keyword-based classification
            if client_id:
                return self._classify_with_keywords(client_id, email_data)
            else:
                return await self._classify_with_fallback(email_data)

    def _identify_client_from_email(self, email_data: Dict[str, Any]) -> Optional[str]:
        """
        Identify client from email data.

        Args:
            email_data: Email data from webhook

        Returns:
            Client ID if identified, None otherwise
        """
        # Try to identify from recipient (TO field)
        recipient = email_data.get("to") or email_data.get("recipient", "")
        if recipient:
            client_result = self.client_manager.identify_client_by_email(recipient)
            if hasattr(client_result, "client_id") and client_result.client_id:
                logger.debug(
                    f"Identified client {client_result.client_id} from recipient: {recipient}"
                )
                return client_result.client_id
            elif isinstance(client_result, str) and client_result:
                logger.debug(f"Identified client {client_result} from recipient: {recipient}")
                return client_result

        # Try to identify from sender domain (less reliable, but possible for replies)
        sender = email_data.get("from", "")
        if sender:
            domain = extract_domain_from_email(sender)
            if domain:
                client_result = self.client_manager.identify_client_by_domain(domain)
                if hasattr(client_result, "client_id") and client_result.client_id:
                    logger.debug(
                        f"Identified client {client_result.client_id} from sender domain: {domain}"
                    )
                    return client_result.client_id
                elif isinstance(client_result, str) and client_result:
                    logger.debug(f"Identified client {client_result} from sender domain: {domain}")
                    return client_result

        return None

    async def _call_ai_service(self, prompt: str) -> Dict[str, Any]:
        """
        Call Anthropic Claude API with composed prompt.

        Args:
            prompt: Composed AI prompt

        Returns:
            AI classification result

        Raises:
            Exception: If AI service call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.config_provider.get_required("services.anthropic_api_key"),
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.config_provider.get(
                        "services.anthropic_model", "claude-3-5-sonnet-20241022"
                    ),
                    "max_tokens": 500,
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )

            response.raise_for_status()
            result = response.json()

            # Parse AI response
            ai_response = result["content"][0]["text"]

            try:
                logger.debug(f"Parsing AI response: {ai_response[:100]}...")
                classification = json.loads(ai_response)

                # Validate required fields
                if "category" not in classification:
                    raise ValueError("Missing 'category' in AI response")
                if "confidence" not in classification:
                    classification["confidence"] = 0.5

                logger.debug(f"✅ Successfully parsed AI classification: {classification}")
                return dict(classification)

            except json.JSONDecodeError as e:
                logger.error(
                    f"❌ Failed to parse AI response as JSON. Response: {ai_response[:500]}"
                )
                logger.error(f"JSON decode error: {e}")
                raise ValueError(f"Invalid AI response format: {e}")

    def _classify_with_keywords(self, client_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback classification using client-specific keywords.

        Args:
            client_id: Client identifier
            email_data: Email data from webhook

        Returns:
            Keyword-based classification result
        """
        try:
            # Load client-specific categories if available
            # For now, use simple keyword matching
            subject = email_data.get("subject", "").lower()
            body = (email_data.get("stripped_text") or email_data.get("body_text", "")).lower()
            text = f"{subject} {body}"

            # Basic keyword classification
            if any(word in text for word in ["billing", "invoice", "payment", "charge", "refund"]):
                category, confidence = "billing", 0.85
                reasoning = "Keyword-based: billing-related terms detected"
                actions = ["check_payment", "billing_support"]

            elif any(
                word in text for word in ["support", "help", "problem", "issue", "error", "bug"]
            ):
                category, confidence = "support", 0.90
                reasoning = "Keyword-based: support-related terms detected"
                actions = ["technical_assistance", "troubleshooting"]

            elif any(
                word in text for word in ["sales", "pricing", "demo", "purchase", "buy", "trial"]
            ):
                category, confidence = "sales", 0.80
                reasoning = "Keyword-based: sales-related terms detected"
                actions = ["schedule_demo", "send_pricing"]

            else:
                category, confidence = "general", 0.60
                reasoning = "Keyword-based: no specific category indicators found"
                actions = ["manual_review", "general_inquiry"]

            classification = {
                "category": category,
                "confidence": confidence,
                "reasoning": reasoning,
                "suggested_actions": actions,
                "client_id": client_id,
                "method": "keyword_fallback",
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"📝 Keyword classification for {client_id}: {category} ({confidence:.2f})")
            return classification

        except Exception as e:
            logger.error(f"Keyword classification failed for {client_id}: {e}")
            return self._get_default_classification(client_id, email_data)

    async def _classify_with_fallback(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback classification when no client is identified.

        Args:
            email_data: Email data from webhook

        Returns:
            Generic fallback classification
        """
        try:
            # Use basic AI prompt without client-specific context
            fallback_prompt = self.email_service._get_fallback_classification_prompt(email_data)
            classification = await self._call_ai_service(fallback_prompt)

            # Add fallback metadata
            classification.update(
                {
                    "client_id": None,
                    "ai_model": self.config_provider.get(
                        "services.anthropic_model", "claude-3-5-sonnet-20241022"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": "ai_generic_fallback",
                }
            )

            logger.info(
                f"🔄 Generic AI classification: {classification['category']} "
                f"({classification['confidence']:.2f})"
            )

            return classification

        except Exception as e:
            logger.error(f"Generic AI classification failed: {e}")
            return self._get_default_classification(None, email_data)

    def _get_default_classification(
        self, client_id: Optional[str], email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get default classification when all else fails.

        Args:
            client_id: Optional client identifier
            email_data: Email data from webhook

        Returns:
            Default classification result
        """
        return {
            "category": "general",
            "confidence": 0.3,
            "reasoning": "Default classification - all other methods failed",
            "suggested_actions": ["manual_review", "escalate"],
            "client_id": client_id,
            "method": "default_fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def classify_with_context(
        self,
        email_data: Dict[str, Any],
        client_id: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Classify email with additional context.

        Args:
            email_data: Email data from webhook
            client_id: Client identifier
            additional_context: Additional context for classification

        Returns:
            Enhanced classification result
        """
        # Add additional context to email data if provided
        if additional_context:
            enhanced_email_data = {
                **email_data,
                "additional_context": additional_context,
            }
        else:
            enhanced_email_data = email_data

        classification = await self.classify_email(enhanced_email_data, client_id)

        # Enhance classification with client-specific response time
        if client_id:
            try:
                response_time = self.client_manager.get_response_time(
                    client_id, classification["category"]
                )
                classification["expected_response_time"] = response_time
            except Exception as e:
                logger.warning(f"Failed to get response time for {client_id}: {e}")

        return classification

    def get_client_categories(self, client_id: str) -> Dict[str, Any]:
        """
        Get available categories for a client.

        Args:
            client_id: Client identifier

        Returns:
            Dictionary of available categories and their properties
        """
        try:
            # Load categories from client-specific categories.yaml file
            categories_data = get_config_manager().load_categories(client_id)

            # Extract just the categories section for backward compatibility
            if "categories" in categories_data:
                return categories_data["categories"]
            else:
                # Fallback to the full data if no categories section
                return categories_data

        except Exception as e:
            logger.error(f"Failed to get categories for {client_id}: {e}")
            # Return basic fallback categories on error
            return {
                "support": {"name": "Technical Support", "priority": "high"},
                "billing": {"name": "Billing & Payments", "priority": "high"},
                "sales": {"name": "Sales Inquiries", "priority": "medium"},
                "general": {"name": "General Inquiries", "priority": "low"},
            }


_ai_classifier_instance: Optional[AIClassifier] = None


def get_ai_classifier() -> AIClassifier:
    """Dependency injection function for AIClassifier."""
    global _ai_classifier_instance
    if _ai_classifier_instance is None:
        from application.dependencies.config import (
            get_client_manager,
            get_config_provider,
        )

        config_provider = get_config_provider()
        client_manager = get_client_manager()
        _ai_classifier_instance = AIClassifier(config_provider, client_manager)
    return _ai_classifier_instance


# Backward compatibility aliases
DynamicClassifier = AIClassifier


def get_dynamic_classifier() -> AIClassifier:
    """Backward compatibility function - use get_ai_classifier() instead."""
    return get_ai_classifier()
