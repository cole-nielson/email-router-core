"""
Template validator.

Validates template syntax, structure, HTML balance, variable syntax,
and size limits.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationResult:
    """Template validation result."""

    def __init__(
        self,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class TemplateValidator:
    """Validates email templates for correctness and security."""

    def __init__(self) -> None:
        """Initialize the template validator with default rules."""
        self.validation_rules: Dict[str, Any] = {
            "required_variables": ["client.name"],
            "max_template_size": 50000,  # 50KB limit
            "allowed_html_tags": ["p", "div", "span", "br", "strong", "em", "a", "img"],
        }

    def validate_template(
        self, template_content: str, client_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate template content for correctness and security.

        Args:
            template_content: Template content to validate
            client_id: Optional client ID for context

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        # Check template size
        if len(template_content) > self.validation_rules["max_template_size"]:
            errors.append(
                f"Template size exceeds maximum of {self.validation_rules['max_template_size']} bytes"
            )

        # Check for required variables
        for required_var in self.validation_rules["required_variables"]:
            pattern = r"{{\s*" + re.escape(required_var) + r"\s*}}"
            if not re.search(pattern, template_content):
                warnings.append(
                    f"Required variable '{required_var}' not found in template"
                )

        # Check for balanced HTML tags
        html_tags = re.findall(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)", template_content)
        tag_stack: List[str] = []

        for is_closing, tag_name in html_tags:
            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                else:
                    errors.append(f"Unmatched closing tag: </{tag_name}>")
            else:
                # Self-closing tags don't need to be tracked
                if tag_name not in ["br", "img", "hr", "input", "meta", "link"]:
                    tag_stack.append(tag_name)

        if tag_stack:
            errors.append(f"Unclosed HTML tags: {', '.join(tag_stack)}")

        # Check variable syntax
        variable_pattern = r"{{[^}]*}}"
        variables = re.findall(variable_pattern, template_content)

        for var in variables:
            # Check for valid variable syntax
            inner = var[2:-2].strip()
            if "|" in inner:
                var_name, default = inner.split("|", 1)
                if not default.strip().startswith("default:"):
                    errors.append(f"Invalid default syntax in variable: {var}")
                else:
                    # Check if default value is properly quoted
                    default_value = default.strip()[8:]  # Remove 'default:'
                    if default_value and not (
                        default_value.startswith('"') and default_value.endswith('"')
                    ):
                        errors.append(f"Invalid default syntax in variable: {var}")
            elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_.]*$", inner):
                warnings.append(f"Invalid variable name syntax: {var}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    def update_validation_rules(self, rules: dict) -> None:
        """
        Update validation rules.

        Args:
            rules: Dictionary of validation rules to update
        """
        self.validation_rules.update(rules)

    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get current validation rules.

        Returns:
            Dictionary of current validation rules
        """
        return self.validation_rules.copy()


# Singleton instance
_validator_instance = None


def get_template_validator() -> TemplateValidator:
    """Get or create the singleton TemplateValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = TemplateValidator()
    return _validator_instance
