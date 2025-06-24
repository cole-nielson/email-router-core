"""
AI service client for Anthropic API.

Handles communication with Anthropic API, managing requests,
responses, and error handling.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from infrastructure.config.manager import get_app_config

logger = logging.getLogger(__name__)


class AIClient:
    """Client for communicating with Anthropic Claude API."""

    def __init__(self, config=None):
        """
        Initialize the AI client.

        Args:
            config: Optional config instance (will fetch from get_app_config if not provided)
        """
        self.config = config or get_app_config()
        self.default_timeout = 30.0
        self.default_max_tokens = 1000
        self.default_temperature = 0.3
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.api_version = "2023-06-01"

    async def call_ai_service(self, prompt: str, **kwargs) -> str:
        """
        Call Anthropic Claude API with composed prompt.

        Args:
            prompt: Composed AI prompt
            **kwargs: Additional parameters for the API call

        Returns:
            AI response text

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If the response format is invalid
        """
        # Validate prompt quality before sending
        self._validate_prompt_quality(prompt)

        logger.debug(f"📤 Sending prompt to Claude API ({len(prompt)} characters)")

        # Prepare request parameters
        request_params = self._prepare_request_params(prompt, **kwargs)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json=request_params,
                    timeout=kwargs.get("timeout", self.default_timeout),
                )

                response.raise_for_status()
                result = response.json()

                ai_response = self._extract_response_text(result)
                logger.debug(f"📥 Received AI response ({len(ai_response)} characters)")

                # Validate response quality
                self._validate_response_quality(ai_response)

                return ai_response

        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            raise
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse API response: {e}")
            raise ValueError(f"Invalid API response format: {e}")

    async def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate AI response with custom parameters.

        Args:
            prompt: AI prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Model to use

        Returns:
            AI response text
        """
        kwargs = {}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if model is not None:
            kwargs["model"] = model

        return await self.call_ai_service(prompt, **kwargs)

    async def batch_generate(self, prompts: list, **kwargs) -> list:
        """
        Generate responses for multiple prompts.

        Args:
            prompts: List of prompts to process
            **kwargs: Additional parameters for API calls

        Returns:
            List of AI responses
        """
        responses = []
        for i, prompt in enumerate(prompts):
            try:
                response = await self.call_ai_service(prompt, **kwargs)
                responses.append(response)
                logger.debug(f"Processed prompt {i+1}/{len(prompts)}")
            except Exception as e:
                logger.error(f"Failed to process prompt {i+1}: {e}")
                responses.append(f"[ERROR: {e}]")

        return responses

    def _validate_prompt_quality(self, prompt: str):
        """
        Validate prompt quality before sending to AI.

        Args:
            prompt: Prompt to validate

        Logs warnings and errors for quality issues.
        """
        if "MISSING:" in prompt:
            logger.error(
                "🚨 CRITICAL: Sending malformed prompt to AI with MISSING: variables - this will fail!"
            )
            logger.error(f"Prompt preview: {prompt[:200]}...")
        elif "[" in prompt and "]" in prompt:
            logger.warning("⚠️ Prompt contains placeholder brackets - may affect AI quality")

        if not prompt.strip():
            logger.error("🚨 CRITICAL: Empty prompt sent to AI")

        if len(prompt) > 100000:  # 100KB limit
            logger.warning(f"⚠️ Large prompt size: {len(prompt)} characters")

    def _validate_response_quality(self, response: str):
        """
        Validate AI response quality.

        Args:
            response: AI response to validate

        Logs warnings for potential quality issues.
        """
        if "template" in response.lower() or "placeholder" in response.lower():
            logger.warning(
                "⚠️ AI response mentions templates/placeholders - prompt may have been malformed"
            )

        if not response.strip():
            logger.warning("⚠️ Empty response received from AI")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.services.anthropic_api_key,
            "anthropic-version": self.api_version,
        }

    def _prepare_request_params(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare request parameters for API call.

        Args:
            prompt: AI prompt
            **kwargs: Additional parameters

        Returns:
            Dictionary of request parameters
        """
        return {
            "model": kwargs.get("model", self.config.services.anthropic_model),
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "temperature": kwargs.get("temperature", self.default_temperature),
            "messages": [{"role": "user", "content": prompt}],
        }

    def _extract_response_text(self, result: Dict[str, Any]) -> str:
        """
        Extract response text from API result.

        Args:
            result: API response JSON

        Returns:
            Response text

        Raises:
            ValueError: If response format is invalid
        """
        try:
            return result["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Invalid response format: {result}")
            raise ValueError(f"Failed to extract response text: {e}")

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get client configuration information.

        Returns:
            Dictionary with client info
        """
        return {
            "api_url": self.api_url,
            "api_version": self.api_version,
            "model": self.config.services.anthropic_model,
            "default_max_tokens": self.default_max_tokens,
            "default_temperature": self.default_temperature,
            "default_timeout": self.default_timeout,
        }

    def update_config(self, **kwargs):
        """
        Update client configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, f"default_{key}"):
                setattr(self, f"default_{key}", value)
                logger.debug(f"Updated {key}: {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")


# Singleton instance
_ai_client_instance = None


def get_ai_client(config=None):
    """
    Get or create the singleton AIClient instance.

    Args:
        config: Optional config instance

    Returns:
        AIClient instance
    """
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClient(config)
    return _ai_client_instance
