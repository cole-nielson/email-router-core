"""
Configuration validation tests for all client configurations.
🧪 Validates YAML schemas, required fields, and data integrity across all client configs.
"""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from core.clients.manager import ClientManager
from infrastructure.config.schema import ClientConfig

# Load the test client configuration file
TEST_CLIENT_CONFIG_PATH = "clients/active/client-001-cole-nielson/client-config.yaml"


class TestClientConfigValidation:
    """Test validation of client configuration files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_manager = ClientManager()
        self.clients_dir = Path("clients/active")

    async def test_all_clients_have_valid_configs(self):
        """Test that all client directories have valid configurations."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            # This should not raise an exception for valid configs
            config = await self.client_manager.get_client_config(client_id)

            # Basic validation checks
            assert config.client_id == client_id
            assert isinstance(config.name, str)
            assert len(config.name) > 0
            assert config.industry in [
                "Technology",
                "Healthcare",
                "Finance",
                "Education",
                "Other",
            ]

    async def test_specific_client_config_validation(self):
        """Test validation of the specific test client configuration."""
        if not Path(TEST_CLIENT_CONFIG_PATH).exists():
            pytest.skip("Test client configuration file not found")

        config = await self.client_manager.get_client_config("client-001-cole-nielson")

        # Validate specific configuration elements
        assert config.client_id == "client-001-cole-nielson"
        assert config.name == "Cole Nielson Email Router"
        assert config.industry == "Technology"

        # Validate domains configuration
        assert config.domains.primary in [
            "colesportfolio.com",
            "mail.colesportfolio.com",
        ]

        # Validate branding is present
        assert config.branding.company_name
        assert config.branding.primary_color
        assert config.branding.secondary_color

        # Validate settings
        assert isinstance(config.settings.auto_reply_enabled, bool)
        assert isinstance(config.settings.ai_classification_enabled, bool)
        assert isinstance(config.settings.team_forwarding_enabled, bool)

    async def test_invalid_config_handling(self):
        """Test that invalid configurations are properly rejected."""
        # Test with invalid client ID - should return None
        config = await self.client_manager.get_client_config("nonexistent-client")
        assert config is None

    async def test_required_files_exist(self):
        """Test that all required configuration files exist for each client."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            client_dir = self.clients_dir / client_id

            # Required files (routing rules are embedded in client-config.yaml)
            required_files = [
                "client-config.yaml",
                "categories.yaml",
            ]

            for required_file in required_files:
                file_path = client_dir / required_file
                assert file_path.exists(), f"Missing {required_file} for client {client_id}"

    async def test_yaml_syntax_validation(self):
        """Test that all YAML files have valid syntax."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            client_dir = self.clients_dir / client_id

            # Find all YAML files
            yaml_files = list(client_dir.glob("*.yaml")) + list(client_dir.glob("*.yml"))

            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, "r") as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML syntax in {yaml_file}: {e}")

    async def test_pydantic_model_validation(self):
        """Test that client configs pass Pydantic model validation."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            config_path = self.clients_dir / client_id / "client-config.yaml"

            if config_path.exists():
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)

                try:
                    # This should not raise a ValidationError
                    ClientConfig(**config_data)
                except ValidationError as e:
                    pytest.fail(f"Client {client_id} has invalid config: {e}")

    async def test_domain_configuration_validity(self):
        """Test that domain configurations are valid."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            config = await self.client_manager.get_client_config(client_id)

            # Primary domain should be set
            assert config.domains.primary
            assert isinstance(config.domains.primary, str)
            assert "." in config.domains.primary  # Basic domain format check

            # Aliases should be a list
            assert isinstance(config.domains.aliases, list)

            # Check for duplicate domains
            all_domains = [config.domains.primary] + config.domains.aliases
            assert len(all_domains) == len(set(all_domains)), "Duplicate domains found"

    async def test_routing_configuration_validity(self):
        """Test that routing configurations are valid."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            routing_path = self.clients_dir / client_id / "routing-rules.yaml"

            if routing_path.exists():
                with open(routing_path, "r") as f:
                    routing_data = yaml.safe_load(f)

                # Validate routing structure
                assert "routing" in routing_data
                routing = routing_data["routing"]

                # Check for required routing categories
                required_categories = ["support", "general"]
                for category in required_categories:
                    assert category in routing, f"Missing {category} routing for {client_id}"

                # Validate email format for routing addresses
                import re

                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                for category, email in routing.items():
                    assert re.match(
                        email_pattern, email
                    ), f"Invalid email format for {category}: {email}"

    async def test_branding_configuration_completeness(self):
        """Test that branding configurations are complete."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            config = await self.client_manager.get_client_config(client_id)

            # Required branding fields
            assert config.branding.company_name
            assert config.branding.primary_color
            assert config.branding.secondary_color

            # Color format validation (should be hex colors)
            hex_color_pattern = r"^#[0-9a-fA-F]{6}$"
            import re

            assert re.match(
                hex_color_pattern, config.branding.primary_color
            ), f"Invalid primary color format: {config.branding.primary_color}"
            assert re.match(
                hex_color_pattern, config.branding.secondary_color
            ), f"Invalid secondary color format: {config.branding.secondary_color}"

    async def test_categories_configuration_validity(self):
        """Test that categories configurations are valid."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            categories_path = self.clients_dir / client_id / "categories.yaml"

            if categories_path.exists():
                with open(categories_path, "r") as f:
                    categories_data = yaml.safe_load(f)

                # Validate categories structure
                assert "categories" in categories_data
                categories = categories_data["categories"]

                # Each category should have required fields
                for category_name, category_config in categories.items():
                    assert "description" in category_config
                    assert "keywords" in category_config
                    assert isinstance(category_config["keywords"], list)
                    assert len(category_config["keywords"]) > 0

    async def test_configuration_consistency(self):
        """Test consistency between different configuration files."""
        # Setup client ids if not already done
        if not hasattr(self, "client_ids"):
            self.client_ids = await self.client_manager.get_available_clients()

        for client_id in self.client_ids:
            # Get main config
            config = await self.client_manager.get_client_config(client_id)

            # Load routing config
            routing_path = self.clients_dir / client_id / "routing-rules.yaml"
            if routing_path.exists():
                with open(routing_path, "r") as f:
                    routing_data = yaml.safe_load(f)

                # Load categories config
                categories_path = self.clients_dir / client_id / "categories.yaml"
                if categories_path.exists():
                    with open(categories_path, "r") as f:
                        categories_data = yaml.safe_load(f)

                    # Check that routing categories match category definitions
                    routing_categories = set(routing_data.get("routing", {}).keys())
                    defined_categories = set(categories_data.get("categories", {}).keys())

                    # Allow for general category even if not explicitly defined
                    if "general" in routing_categories:
                        defined_categories.add("general")

                    # Every routing category should have a definition
                    missing_definitions = routing_categories - defined_categories
                    assert (
                        len(missing_definitions) == 0
                    ), f"Categories missing definitions: {missing_definitions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
