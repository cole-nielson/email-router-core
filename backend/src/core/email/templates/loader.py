"""
Template loader with caching.

Loads templates from the filesystem and manages the template cache lifecycle.
"""

import logging
from typing import Any, Dict, List, Optional

from core.ports.config_provider import ConfigurationProvider

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads and caches email templates from client configurations."""

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        template_validator: Optional[Any] = None,
    ) -> None:
        """
        Initialize the template loader.

        Args:
            config_provider: Configuration provider interface
            template_validator: Optional template validator instance
        """
        self._config_provider = config_provider
        self._template_cache: Dict[str, str] = {}
        self._template_validator = template_validator

    def load_template(self, client_id: str, template_type: str) -> str:
        """
        Load template from client configuration.

        Args:
            client_id: Client identifier
            template_type: Type of template ('classification', 'acknowledgment', 'team-analysis')

        Returns:
            Template content

        Raises:
            Exception: If template loading fails
        """
        cache_key = f"{client_id}:{template_type}"

        if cache_key in self._template_cache:
            logger.debug(f"Loading template from cache: {cache_key}")
            return self._template_cache[cache_key]

        try:
            logger.debug(f"Loading template from config manager: {cache_key}")
            template: str = self._config_provider.load_ai_prompt(
                client_id, template_type
            )

            # Validate template if validator is available
            if self._template_validator:
                validation = self._template_validator.validate_template(
                    template, client_id
                )
                if not validation.is_valid:
                    logger.warning(
                        f"Template validation failed for {client_id}:{template_type}: {validation.errors}"
                    )

                if validation.warnings:
                    logger.debug(
                        f"Template warnings for {client_id}:{template_type}: {validation.warnings}"
                    )

            # Cache the template
            self._template_cache[cache_key] = template
            logger.debug(f"Template cached successfully: {cache_key}")
            return template

        except Exception as e:
            logger.error(
                f"Failed to load template {template_type} for {client_id}: {e}"
            )
            raise

    def get_cached_template(self, client_id: str, template_type: str) -> Optional[str]:
        """
        Get cached template without loading from filesystem.

        Args:
            client_id: Client identifier
            template_type: Type of template

        Returns:
            Cached template content or None if not cached
        """
        cache_key = f"{client_id}:{template_type}"
        return self._template_cache.get(cache_key)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        cache_size = len(self._template_cache)
        self._template_cache.clear()
        logger.info(f"Template cache cleared ({cache_size} entries removed)")

    def clear_client_cache(self, client_id: str) -> None:
        """
        Clear cache for a specific client.

        Args:
            client_id: Client identifier
        """
        keys_to_remove = [
            key
            for key in self._template_cache.keys()
            if key.startswith(f"{client_id}:")
        ]
        for key in keys_to_remove:
            del self._template_cache[key]
        logger.info(
            f"Template cache cleared for client {client_id} ({len(keys_to_remove)} entries removed)"
        )

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "total_entries": len(self._template_cache),
            "clients": len(
                set(key.split(":")[0] for key in self._template_cache.keys())
            ),
            "template_types": len(
                set(
                    key.split(":")[1]
                    for key in self._template_cache.keys()
                    if ":" in key
                )
            ),
        }

    def preload_client_templates(
        self, client_id: str, template_types: Optional[List[str]] = None
    ) -> None:
        """
        Preload templates for a client to improve performance.

        Args:
            client_id: Client identifier
            template_types: List of template types to preload (defaults to common types)
        """
        if template_types is None:
            template_types = ["classification", "acknowledgment", "team-analysis"]

        loaded_count = 0
        for template_type in template_types:
            try:
                self.load_template(client_id, template_type)
                loaded_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to preload template {template_type} for {client_id}: {e}"
                )

        logger.info(
            f"Preloaded {loaded_count}/{len(template_types)} templates for client {client_id}"
        )

    def set_validator(self, template_validator: Any) -> None:
        """
        Set the template validator instance.

        Args:
            template_validator: Template validator instance
        """
        self._template_validator = template_validator
        logger.debug("Template validator updated")


# Singleton instance
_template_loader_instance: Optional[TemplateLoader] = None


def get_template_loader(
    config_provider: ConfigurationProvider, template_validator: Optional[Any] = None
) -> TemplateLoader:
    """
    Get or create the singleton TemplateLoader instance.

    Args:
        config_provider: Configuration provider interface
        template_validator: Optional template validator (used only on first initialization)

    Returns:
        TemplateLoader instance
    """
    global _template_loader_instance
    if _template_loader_instance is None:
        _template_loader_instance = TemplateLoader(config_provider, template_validator)
    elif template_validator and _template_loader_instance._template_validator is None:
        # Set validator if it wasn't provided during initialization
        _template_loader_instance.set_validator(template_validator)
    return _template_loader_instance
