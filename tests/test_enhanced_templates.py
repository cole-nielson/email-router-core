"""
Tests for enhanced template engine and branded email templates.
🧪 Validates template variable injection, branding integration, and template validation.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.src.core.clients.manager import ClientManager
from backend.src.core.email.composer import EmailService
from backend.src.infrastructure.templates.email import (
    _get_default_branding,
    create_branded_template,
)


class TestEnhancedTemplateEngine:
    """Test the enhanced template engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_manager = Mock()
        self.engine = EmailService(self.mock_client_manager)

        # Mock client config
        self.mock_client_config = Mock()
        self.mock_client_config.branding.company_name = "Test Company"
        self.mock_client_config.branding.primary_color = "#667eea"
        self.mock_client_config.branding.secondary_color = "#764ba2"
        self.mock_client_config.branding.logo_url = "https://example.com/logo.png"

    def test_template_validation_success(self):
        """Test successful template validation."""
        template = """
        <div style="color: {{branding.primary_color}};">
            <h1>Welcome {{client.name}}</h1>
            <p>{{message|default:"No message"}}</p>
        </div>
        """

        result = self.engine.validate_template(template, "test-client")

        assert result.is_valid
        assert len(result.errors) == 0

    def test_template_validation_errors(self):
        """Test template validation with errors."""
        # Template with invalid default syntax
        template = """
        <div style="color: red;">
            <h1>Welcome {{client.name}}</h1>
            <p>{{invalid|default:no quotes}}</p>
        </div>
        """

        result = self.engine.validate_template(template, "test-client")

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("Invalid default syntax" in error for error in result.errors)

    def test_variable_injection_with_defaults(self):
        """Test variable injection with default values."""
        template = 'Hello {{client.name|default:"Guest"}}! Color: {{branding.primary_color|default:"#000"}}'
        context = {"client": {"name": "John Doe"}, "branding": {"primary_color": "#667eea"}}

        result = self.engine._inject_template_variables(template, context)

        assert result == "Hello John Doe! Color: #667eea"

    def test_variable_injection_missing_with_defaults(self):
        """Test variable injection with missing values using defaults."""
        template = 'Hello {{client.missing_name|default:"Guest"}}! Color: {{branding.missing_color|default:"#000"}}'
        context = {"client": {}, "branding": {}}

        result = self.engine._inject_template_variables(template, context)

        assert result == "Hello Guest! Color: #000"

    def test_nested_variable_access(self):
        """Test nested variable access."""
        template = "Company: {{client.company.name}}, Email: {{client.company.email}}"
        context = {"client": {"company": {"name": "Test Corp", "email": "test@corp.com"}}}

        result = self.engine._inject_template_variables(template, context)

        assert result == "Company: Test Corp, Email: test@corp.com"

    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    @pytest.mark.xfail(
        reason="Client branding test needs updated business logic - see docs/known_issues.md"
    )
    def test_load_client_branding(self, mock_open, mock_exists):
        """Test loading client branding configuration."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = """
        email:
          header_background: "linear-gradient(135deg, #667eea, #764ba2)"
          header_text: "#ffffff"
          body_background: "#ffffff"
        """

        # Mock yaml.safe_load
        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = {
                "email": {
                    "header_background": "linear-gradient(135deg, #667eea, #764ba2)",
                    "header_text": "#ffffff",
                    "body_background": "#ffffff",
                }
            }

            self.mock_client_manager.get_client_config.return_value = self.mock_client_config

            branding = self.engine._load_client_branding("test-client")

            assert branding["company_name"] == "Test Company"
            assert branding["primary_color"] == "#667eea"
            # Check if the header_background color was loaded into branding
            assert "header_background" in branding or "header_gradient" in branding


class TestBrandedEmailTemplates:
    """Test branded email template generation."""

    def test_default_branding(self):
        """Test default branding configuration."""
        branding = _get_default_branding()

        assert branding["company_name"] == "Email Router"
        assert branding["primary_color"] == "#667eea"
        assert branding["header_text_color"] == "#ffffff"
        assert "header_gradient" in branding

    def test_customer_template_generation(self):
        """Test customer template generation with branding."""
        context = {
            "draft_response": "Thank you for contacting us.",
            "classification": {"category": "support"},
            "email_data": {"subject": "Test Subject"},
        }

        branding = {
            "company_name": "Test Company",
            "primary_color": "#667eea",
            "logo_url": "https://example.com/logo.png",
            "header_gradient": "linear-gradient(135deg, #667eea, #764ba2)",
            "header_text_color": "#ffffff",
            "body_background": "#ffffff",
            "body_text_color": "#374151",
            "accent_background": "#f8f9ff",
            "accent_border_color": "#667eea",
            "footer_background": "#f8f9fa",
            "footer_text_color": "#6b7280",
            "link_color": "#667eea",
            "footer_text": "",
        }

        text_body, html_body = create_branded_template("customer_reply", context, branding)

        assert "Thank you for contacting us." in text_body
        assert "Test Company" in text_body
        assert "Test Company" in html_body
        assert "linear-gradient(135deg, #667eea, #764ba2)" in html_body
        assert "#ffffff" in html_body

    def test_team_template_generation(self):
        """Test team template generation with branding."""
        context = {
            "email_data": {
                "from": "test@example.com",
                "subject": "Test Subject",
                "stripped_text": "Test message content",
            },
            "classification": {
                "category": "support",
                "confidence": 0.95,
                "reasoning": "Technical support inquiry",
            },
            "draft_response": "Suggested response content",
        }

        branding = {
            "company_name": "Test Company",
            "primary_color": "#667eea",
            "header_gradient": "linear-gradient(135deg, #1e293b, #334155)",
            "header_text_color": "white",
            "body_background": "#ffffff",
            "body_text_color": "#374151",
            "accent_background": "#f9fafb",
            "accent_border_color": "#3b82f6",
            "footer_background": "#f8f9fa",
            "footer_text_color": "#64748b",
            "link_color": "#1e40af",
            "logo_url": "",
        }

        text_body, html_body = create_branded_template("team_forward", context, branding)

        assert "TEST COMPANY" in text_body
        assert "**95%** (HIGH)" in text_body  # Updated to match new enhanced format
        assert "test@example.com" in html_body
        assert "95% HIGH" in html_body  # Confidence indicator
        assert "Test Company" in html_body


class TestTemplateIntegration:
    """Test template integration with email composer."""

    @pytest.mark.asyncio
    async def test_render_template_with_branding(self):
        """Test template rendering with branding integration."""
        template = """
        <div style="background: {{branding.header_gradient}};">
            <h1 style="color: {{branding.header_text_color}};">
                {{branding.company_name}}
            </h1>
        </div>
        """

        context = {"message": "Test message"}

        # Test with default branding (no client_id) - skip this test for now
        pytest.skip("render_template_with_branding function removed in consolidation")

        assert "Email Router" in result
        assert "linear-gradient(135deg, #667eea, #764ba2)" in result
        assert "#ffffff" in result

    @pytest.mark.xfail(
        reason="Template error handling test needs updated business logic - see docs/known_issues.md"
    )
    def test_template_error_handling(self):
        """Test template error handling and fallbacks."""
        engine = EmailService(None)

        # Test with invalid template syntax
        template = "{{invalid.syntax.here}}"
        context = {}

        result = engine._inject_template_variables(template, context)

        # Should return placeholder for missing variables
        assert "MISSING:" in result or "ERROR:" in result


if __name__ == "__main__":
    pytest.main([__file__])
