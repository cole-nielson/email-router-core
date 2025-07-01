"""
Client branding manager.

Loads and caches client branding configurations, consolidating
branding data from various sources.
"""

import logging
from typing import Any, Dict, Optional

from infrastructure.templates.email import _get_default_branding  # type: ignore

logger = logging.getLogger(__name__)


class BrandingManager:
    """Manages client branding configurations with caching."""

    def __init__(self) -> None:
        """Initialize the branding manager."""
        self._branding_cache: Dict[str, Dict[str, Any]] = {}

    def load_client_branding(
        self, client_id: str, client_config: Any
    ) -> Dict[str, Any]:
        """
        Load and cache client branding configuration.

        Args:
            client_id: Client identifier
            client_config: Client configuration object with branding data

        Returns:
            Dict containing branding configuration
        """
        if client_id in self._branding_cache:
            return self._branding_cache[client_id]

        try:
            # Base branding from client config
            branding = {
                "company_name": client_config.branding.company_name,
                "primary_color": client_config.branding.primary_color,
                "secondary_color": client_config.branding.secondary_color,
                "logo_url": client_config.branding.logo_url or "",
                "email_signature": client_config.branding.email_signature,
                "footer_text": client_config.branding.footer_text or "",
            }

            # Load additional colors from consolidated branding.colors section
            try:
                if hasattr(client_config.branding, "colors"):
                    colors_data = client_config.branding.colors

                    # If colors are available as a dict (from YAML), process them
                    if isinstance(colors_data, dict):
                        # Map email-specific colors to expected branding keys
                        if "email" in colors_data:
                            email_colors = colors_data["email"]
                            if "header_background" in email_colors:
                                branding["header_gradient"] = email_colors[
                                    "header_background"
                                ]
                            branding.update(email_colors)

                        # Add other color categories if needed
                        for category, colors in colors_data.items():
                            if isinstance(colors, dict):
                                branding.update(
                                    {f"{category}_{k}": v for k, v in colors.items()}
                                )

            except Exception as e:
                logger.debug(f"Could not load consolidated colors for {client_id}: {e}")

            # Cache the result
            self._branding_cache[client_id] = branding
            return branding

        except Exception as e:
            logger.error(f"Failed to load branding for {client_id}: {e}")
            default_branding: Dict[str, Any] = _get_default_branding()
            return default_branding

    def clear_cache(self) -> None:
        """Clear the branding cache."""
        self._branding_cache.clear()
        logger.info("Branding cache cleared")

    def get_cached_branding(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached branding if available.

        Args:
            client_id: Client identifier

        Returns:
            Cached branding dict or None if not cached
        """
        return self._branding_cache.get(client_id)


# Singleton instance
_branding_manager_instance: Optional[BrandingManager] = None


def get_branding_manager() -> BrandingManager:
    """Get or create the singleton BrandingManager instance."""
    global _branding_manager_instance
    if _branding_manager_instance is None:
        _branding_manager_instance = BrandingManager()
    return _branding_manager_instance
