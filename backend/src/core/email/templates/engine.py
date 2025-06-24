"""
Template engine for variable injection.

Processes templates by replacing {{variable}} placeholders with actual values,
handling default values and nested variable access.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .context import TemplateContextBuilder

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Processes email templates by injecting variables from context."""

    def __init__(self) -> None:
        """Initialize the template engine."""
        self._pattern = re.compile(r"{{\s*([^}]+)\s*}}")

    def inject_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Inject variables into template using {{variable}} syntax.

        Args:
            template: Template string with {{variable}} placeholders
            context: Context dictionary with variable values

        Returns:
            Template with variables injected
        """
        missing_variables = []

        def replace_variable(match: Any) -> str:
            var_expression = match.group(1).strip()

            # Handle default values: {{variable|default:"fallback"}}
            if "|default:" in var_expression:
                var_name, default_expr = var_expression.split("|default:", 1)
                var_name = var_name.strip()
                default_value = default_expr.strip().strip("\"'")
            else:
                var_name = var_expression
                default_value = f"[{var_name}]"  # Less disruptive placeholder

            # Get nested value
            value = TemplateContextBuilder.get_nested_value(context, var_name, default_value)

            # Track missing variables for logging
            if value == default_value and "|default:" not in var_expression:
                missing_variables.append(var_name)
                logger.warning(f"Missing template variable: {var_name}")

            return str(value)

        # Replace all {{variable}} patterns
        result: str = self._pattern.sub(replace_variable, template)

        # Log missing variables
        if missing_variables:
            logger.warning(
                f"Template processing completed with {len(missing_variables)} missing variables: {missing_variables}"
            )

        # Check for any remaining MISSING: patterns that would break AI
        if "MISSING:" in result:
            logger.error(
                "Template still contains MISSING: patterns after processing - this will break AI prompts"
            )

        return result

    def render_template(
        self, template: str, context: Dict[str, Any], validate_output: bool = True
    ) -> str:
        """
        Render a template with full processing and optional validation.

        Args:
            template: Template string with placeholders
            context: Context dictionary with variable values
            validate_output: Whether to validate the rendered output

        Returns:
            Fully rendered template string
        """
        try:
            rendered = self.inject_variables(template, context)

            if validate_output:
                self._validate_rendered_output(rendered)

            logger.debug(f"Template rendered successfully ({len(rendered)} characters)")
            return rendered

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def extract_variables(self, template: str) -> List[str]:
        """
        Extract all variable names from a template.

        Args:
            template: Template string to analyze

        Returns:
            List of variable names found in the template
        """
        variables = []
        matches = self._pattern.findall(template)

        for match in matches:
            var_expression = match.strip()

            # Handle default values: {{variable|default:"fallback"}}
            if "|default:" in var_expression:
                var_name = var_expression.split("|default:", 1)[0].strip()
            else:
                var_name = var_expression

            if var_name not in variables:
                variables.append(var_name)

        return variables

    def preview_rendering(self, template: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview template rendering without actually processing it.

        Args:
            template: Template string to preview
            context: Context dictionary

        Returns:
            Dictionary with preview information
        """
        variables = self.extract_variables(template)
        available_vars = []
        missing_vars = []

        for var in variables:
            if TemplateContextBuilder.get_nested_value(context, var, None) is not None:
                available_vars.append(var)
            else:
                missing_vars.append(var)

        return {
            "total_variables": len(variables),
            "available_variables": available_vars,
            "missing_variables": missing_vars,
            "template_length": len(template),
            "has_missing": len(missing_vars) > 0,
        }

    def batch_render(self, templates: Dict[str, str], context: Dict[str, Any]) -> Dict[str, str]:
        """
        Render multiple templates with the same context.

        Args:
            templates: Dictionary of template_name -> template_content
            context: Context dictionary for all templates

        Returns:
            Dictionary of template_name -> rendered_content
        """
        results = {}

        for template_name, template_content in templates.items():
            try:
                results[template_name] = self.inject_variables(template_content, context)
                logger.debug(f"Rendered template: {template_name}")
            except Exception as e:
                logger.error(f"Failed to render template {template_name}: {e}")
                results[template_name] = f"[ERROR: {e}]"

        return results

    def _validate_rendered_output(self, rendered: str) -> None:
        """
        Validate the rendered template output.

        Args:
            rendered: Rendered template string

        Raises:
            ValueError: If validation fails
        """
        # Check for unresolved placeholders
        remaining_placeholders = self._pattern.findall(rendered)
        if remaining_placeholders:
            logger.warning(f"Unresolved placeholders found: {remaining_placeholders}")

        # Check for error patterns
        if "MISSING:" in rendered:
            raise ValueError("Template contains unresolved MISSING: patterns")

        if "ERROR:" in rendered:
            raise ValueError("Template contains ERROR: patterns")

        # Check for empty output
        if not rendered.strip():
            raise ValueError("Template rendered to empty content")

    def set_variable_pattern(self, pattern: str) -> None:
        """
        Set a custom variable pattern for template processing.

        Args:
            pattern: Regular expression pattern for variable matching
        """
        try:
            self._pattern = re.compile(pattern)
            logger.debug(f"Variable pattern updated: {pattern}")
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            raise ValueError(f"Invalid regex pattern: {e}")


# Singleton instance
_template_engine_instance: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """
    Get or create the singleton TemplateEngine instance.

    Returns:
        TemplateEngine instance
    """
    global _template_engine_instance
    if _template_engine_instance is None:
        _template_engine_instance = TemplateEngine()
    return _template_engine_instance
