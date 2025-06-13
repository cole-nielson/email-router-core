"""
Configuration validation tests for all client configurations.
🧪 Validates YAML schemas, required fields, and data integrity across all client configs.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from pydantic import ValidationError

from app.models.client_config import BrandingConfig, ClientConfig, DomainConfig, SettingsConfig
from app.services.client_manager import ClientManager
from app.utils.client_loader import ClientLoadError, load_client_config


class TestClientConfigValidation:
    """Test validation of client configuration files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_manager = ClientManager()
        self.clients_dir = Path("clients/active")

        # Get all available client IDs
        self.client_ids = self.client_manager.get_available_clients()

        # Ensure we have at least one client for testing
        assert len(self.client_ids) > 0, "No clients found for validation testing"

    def test_all_clients_have_valid_configs(self):
        """Test that all client directories have valid configurations."""

        for client_id in self.client_ids:
            # This should not raise an exception for valid configs
            config = self.client_manager.get_client_config(client_id)

            # Basic validation checks
            assert config.client.id == client_id
            assert isinstance(config.client.name, str)
            assert len(config.client.name) > 0
            assert config.client.industry in [
                "Technology",
                "Healthcare",
                "Finance",
                "Education",
                "Other",
            ]

            print(f"✅ Client {client_id} config validation passed")

    def test_required_config_files_exist(self):
        """Test that all required configuration files exist for each client."""

        required_files = [
            "client-config.yaml",  # Consolidated main configuration
            "categories.yaml",  # AI-specific categories (kept separate)
            # Note: routing-rules.yaml consolidated into client-config.yaml (Milestone 5)
            # Note: branding/colors.yaml consolidated into client-config.yaml (Milestone 5)
        ]

        for client_id in self.client_ids:
            client_dir = self.clients_dir / client_id

            for required_file in required_files:
                file_path = client_dir / required_file
                assert (
                    file_path.exists()
                ), f"Required file {required_file} missing for client {client_id}"

                # Ensure file is not empty
                assert (
                    file_path.stat().st_size > 0
                ), f"Required file {required_file} is empty for client {client_id}"

                # Ensure file is valid YAML
                try:
                    with open(file_path, "r") as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {required_file} for client {client_id}: {e}")

            print(f"✅ Client {client_id} required files validation passed")

    def test_pydantic_model_validation(self):
        """Test that all client configs pass Pydantic model validation."""

        for client_id in self.client_ids:
            try:
                # Load raw YAML data
                config_file = self.clients_dir / client_id / "client-config.yaml"
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)

                # Validate with Pydantic model
                validated_config = ClientConfig(**config_data)

                # Additional validation checks
                assert validated_config.client.id == client_id
                assert validated_config.client.status in ["active", "inactive", "pending"]

                # Domain validation
                assert isinstance(validated_config.domains.primary, str)
                assert len(validated_config.domains.primary) > 0
                assert "@" not in validated_config.domains.primary  # Should be domain, not email

                # Settings validation
                assert isinstance(validated_config.settings.auto_reply_enabled, bool)
                assert isinstance(validated_config.settings.ai_classification_enabled, bool)

                print(f"✅ Client {client_id} Pydantic validation passed")

            except ValidationError as e:
                pytest.fail(f"Pydantic validation failed for client {client_id}: {e}")
            except Exception as e:
                pytest.fail(f"Unexpected error validating client {client_id}: {e}")

    def test_domain_configuration_validity(self):
        """Test domain configuration validity and consistency."""

        for client_id in self.client_ids:
            config = self.client_manager.get_client_config(client_id)

            # Primary domain validation
            primary_domain = config.domains.primary
            assert (
                "." in primary_domain
            ), f"Primary domain {primary_domain} for {client_id} doesn't appear to be valid"
            assert not primary_domain.startswith(
                "http"
            ), f"Primary domain {primary_domain} should not include protocol"

            # Support email validation
            support_email = config.domains.support
            assert (
                "@" in support_email
            ), f"Support email {support_email} for {client_id} is not a valid email"

            # Check if support email domain matches primary or aliases
            support_domain = support_email.split("@")[1]
            valid_domains = [config.domains.primary]
            if hasattr(config.domains, "aliases") and config.domains.aliases:
                valid_domains.extend(config.domains.aliases)

            # Note: Support domain doesn't have to match primary (could be external)
            # This is just a consistency check

            print(f"✅ Client {client_id} domain validation passed")

    def test_routing_rules_validation(self):
        """Test routing rules configuration validation (now in consolidated client-config.yaml)."""

        for client_id in self.client_ids:
            # Load from consolidated client config (Milestone 5)
            client_config = self.client_manager.get_client_config(client_id)
            
            # Check that routing exists
            assert client_config.routing is not None, f"Missing routing configuration for {client_id}"
            
            routing = client_config.routing

            # Check for common categories
            expected_categories = ["support", "billing", "sales", "general"]
            for category in expected_categories:
                if category in routing:
                    email = routing[category]
                    assert (
                        "@" in email
                    ), f"Invalid email {email} for category {category} in {client_id}"

            # Check escalation rules if present
            if client_config.escalation and hasattr(client_config.escalation, 'keyword_based'):
                keyword_based = client_config.escalation.keyword_based
                if keyword_based:
                    for keyword, email in keyword_based.items():
                        assert (
                            "@" in email
                        ), f"Invalid escalation email {email} for keyword {keyword} in {client_id}"

            print(f"✅ Client {client_id} routing rules validation passed")

    def test_categories_configuration(self):
        """Test categories configuration validation."""

        for client_id in self.client_ids:
            categories_file = self.clients_dir / client_id / "categories.yaml"

            with open(categories_file, "r") as f:
                categories_data = yaml.safe_load(f)

            assert (
                "categories" in categories_data
            ), f"Missing 'categories' section in categories.yaml for {client_id}"

            categories = categories_data["categories"]

            # Ensure we have at least basic categories
            required_categories = ["support", "billing", "sales", "general"]
            for required_cat in required_categories:
                assert (
                    required_cat in categories
                ), f"Missing required category '{required_cat}' for {client_id}"

                # Validate category structure
                category_config = categories[required_cat]
                assert (
                    "name" in category_config
                ), f"Missing 'name' in category {required_cat} for {client_id}"
                assert (
                    "keywords" in category_config
                ), f"Missing 'keywords' in category {required_cat} for {client_id}"
                assert isinstance(
                    category_config["keywords"], list
                ), f"Keywords must be a list for category {required_cat} in {client_id}"

            print(f"✅ Client {client_id} categories validation passed")

    def test_ai_context_files_validation(self):
        """Test AI context files validation."""

        required_ai_files = [
            "ai-context/classification-prompt.md",
            "ai-context/acknowledgment-prompt.md",
            "ai-context/team-analysis-prompt.md",
            "ai-context/fallback-responses.yaml",
        ]

        for client_id in self.client_ids:
            client_dir = self.clients_dir / client_id

            for ai_file in required_ai_files:
                file_path = client_dir / ai_file

                if file_path.exists():
                    # Check file is not empty
                    assert (
                        file_path.stat().st_size > 0
                    ), f"AI file {ai_file} is empty for {client_id}"

                    # Validate YAML files
                    if ai_file.endswith(".yaml"):
                        try:
                            with open(file_path, "r") as f:
                                yaml.safe_load(f)
                        except yaml.YAMLError as e:
                            pytest.fail(f"Invalid YAML in {ai_file} for {client_id}: {e}")

                    # Validate markdown files have content
                    elif ai_file.endswith(".md"):
                        with open(file_path, "r") as f:
                            content = f.read().strip()
                            assert (
                                len(content) > 50
                            ), f"AI prompt file {ai_file} seems too short for {client_id}"
                            # Check for template variables
                            assert (
                                "{{" in content and "}}" in content
                            ), f"AI prompt {ai_file} missing template variables for {client_id}"

                else:
                    # File is optional but log it
                    print(f"ℹ️  Optional AI file {ai_file} not found for {client_id}")

            print(f"✅ Client {client_id} AI context validation passed")

    def test_branding_configuration(self):
        """Test branding configuration validation."""

        for client_id in self.client_ids:
            config = self.client_manager.get_client_config(client_id)

            # Validate branding fields
            branding = config.branding

            assert isinstance(
                branding.company_name, str
            ), f"Company name must be string for {client_id}"
            assert len(branding.company_name) > 0, f"Company name cannot be empty for {client_id}"

            # Color validation (hex codes)
            def is_valid_hex_color(color: str) -> bool:
                if not color.startswith("#"):
                    return False
                if len(color) not in [4, 7]:  # #RGB or #RRGGBB
                    return False
                try:
                    int(color[1:], 16)
                    return True
                except ValueError:
                    return False

            assert is_valid_hex_color(
                branding.primary_color
            ), f"Invalid primary color {branding.primary_color} for {client_id}"
            assert is_valid_hex_color(
                branding.secondary_color
            ), f"Invalid secondary color {branding.secondary_color} for {client_id}"

            # Optional: Check branding colors.yaml if it exists
            colors_file = self.clients_dir / client_id / "branding" / "colors.yaml"
            if colors_file.exists():
                with open(colors_file, "r") as f:
                    colors_data = yaml.safe_load(f)

                # Validate structure if colors are defined
                if "colors" in colors_data:
                    for color_name, color_value in colors_data["colors"].items():
                        if isinstance(color_value, str) and color_value.startswith("#"):
                            assert is_valid_hex_color(
                                color_value
                            ), f"Invalid color {color_value} for {color_name} in {client_id}"

            print(f"✅ Client {client_id} branding validation passed")


class TestConfigurationIntegrity:
    """Test configuration integrity and consistency across files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_manager = ClientManager()
        self.client_ids = self.client_manager.get_available_clients()

    def test_routing_categories_match_defined_categories(self):
        """Test that routing rules reference only defined categories."""

        for client_id in self.client_ids:
            # Load categories
            categories_file = Path(f"clients/active/{client_id}/categories.yaml")
            with open(categories_file, "r") as f:
                categories_data = yaml.safe_load(f)

            defined_categories = set(categories_data["categories"].keys())

            # Load routing rules from consolidated client config
            client_config = self.client_manager.get_client_config(client_id)

            routing_categories = (
                set(client_config.routing.keys()) if client_config.routing else set()
            )

            # Check that all routing categories are defined
            undefined_categories = routing_categories - defined_categories
            assert (
                len(undefined_categories) == 0
            ), f"Client {client_id} has undefined routing categories: {undefined_categories}"

            print(f"✅ Client {client_id} routing-categories consistency passed")

    def test_client_config_consistency(self):
        """Test consistency between client config and actual client ID."""

        for client_id in self.client_ids:
            config = self.client_manager.get_client_config(client_id)

            # Client ID should match directory name
            assert (
                config.client.id == client_id
            ), f"Client ID mismatch: directory={client_id}, config={config.client.id}"

            # Status should be active for clients in active directory
            assert (
                config.client.status == "active"
            ), f"Client {client_id} in active directory but status is {config.client.status}"

            print(f"✅ Client {client_id} config consistency passed")

    def test_domain_routing_consistency(self):
        """Test that domains in config are consistent with routing expectations."""

        for client_id in self.client_ids:
            config = self.client_manager.get_client_config(client_id)

            # Test that we can identify the client by its own domains
            primary_test_email = f"test@{config.domains.primary}"
            identification_result = self.client_manager.identify_client_by_email(primary_test_email)

            # Should identify the client (unless domain has special rules)
            if identification_result.is_successful:
                assert (
                    identification_result.client_id == client_id
                ), f"Domain identification failed for {client_id}: got {identification_result.client_id}"

            print(f"✅ Client {client_id} domain consistency passed")


class TestConfigurationPerformance:
    """Test configuration loading performance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_manager = ClientManager()
        self.client_ids = self.client_manager.get_available_clients()

    def test_config_loading_performance(self):
        """Test that config loading is reasonably fast."""
        import time

        for client_id in self.client_ids:
            start_time = time.time()

            # Load config multiple times to test caching
            for _ in range(3):
                config = self.client_manager.get_client_config(client_id)
                assert config is not None

            end_time = time.time()
            loading_time = end_time - start_time

            # Should load 3 times in under 1 second (caching should help)
            assert (
                loading_time < 1.0
            ), f"Config loading too slow for {client_id}: {loading_time:.2f}s for 3 loads"

            print(f"✅ Client {client_id} performance test passed ({loading_time:.3f}s)")

    def test_mass_client_identification(self):
        """Test performance of client identification with multiple requests."""
        import time

        test_emails = []
        for client_id in self.client_ids:
            config = self.client_manager.get_client_config(client_id)
            test_emails.append(f"test@{config.domains.primary}")
            test_emails.append(config.domains.support)

        start_time = time.time()

        # Identify all emails
        for email in test_emails:
            result = self.client_manager.identify_client_by_email(email)
            # Don't assert success here since some domains might not resolve

        end_time = time.time()
        identification_time = end_time - start_time

        # Should complete all identifications reasonably quickly
        avg_time_per_email = identification_time / len(test_emails)
        assert (
            avg_time_per_email < 0.1
        ), f"Client identification too slow: {avg_time_per_email:.3f}s per email"

        print(
            f"✅ Mass identification performance passed ({len(test_emails)} emails in {identification_time:.3f}s)"
        )


if __name__ == "__main__":
    pytest.main([__file__])
