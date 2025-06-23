"""
Client-specific test fixtures and factories.
"""

from unittest.mock import patch

import pytest


@pytest.fixture(scope="function")
def sample_client_config():
    """Sample client configuration for testing."""
    return {
        "name": "Test Client",
        "client_id": "test-client",
        "domains": {
            "primary": "test.example.com",
            "aliases": ["support.test.example.com", "help.test.example.com"],
        },
        "branding": {
            "company_name": "Test Company",
            "primary_color": "#667eea",
            "secondary_color": "#764ba2",
            "logo_url": "https://test.example.com/logo.png",
        },
        "settings": {
            "auto_reply_enabled": True,
            "ai_classification_enabled": True,
            "team_forwarding_enabled": True,
        },
        "routing": {
            "support": "support@test.example.com",
            "billing": "billing@test.example.com",
            "sales": "sales@test.example.com",
            "general": "general@test.example.com",
        },
    }


@pytest.fixture(scope="function")
def sample_email_webhook_data():
    """Sample Mailgun webhook data for testing."""
    return {
        "sender": "user@customer.com",
        "recipient": "support@test.example.com",
        "subject": "Need help with my account",
        "body-plain": "I'm having trouble logging into my account. Can you help?",
        "body-html": "<p>I'm having trouble logging into my account. Can you help?</p>",
        "timestamp": "1609459200",
        "signature": "test-webhook-signature",
        "token": "test-webhook-token",
        "Message-Id": "<test-message@customer.com>",
    }


@pytest.fixture(scope="function")
def mock_client_config_loader():
    """Mock client configuration loading for isolated testing."""

    def _mock_loader(client_config=None):
        if client_config is None:
            client_config = {
                "test-client": {
                    "name": "Test Client",
                    "client_id": "test-client",
                    "domains": {"primary": "test.example.com", "aliases": []},
                    "branding": {"company_name": "Test Company"},
                    "settings": {"auto_reply_enabled": True},
                }
            }

        with patch("app.utils.client_loader.load_client_config") as mock_load:
            mock_load.return_value = client_config
            yield mock_load

    return _mock_loader


@pytest.fixture(scope="function")
def ai_classification_responses():
    """Factory for different AI classification responses."""
    return {
        "support": {
            "classification": "support",
            "confidence": 0.95,
            "reasoning": "User is asking for help with account access.",
        },
        "billing": {
            "classification": "billing",
            "confidence": 0.88,
            "reasoning": "Question related to payment or billing issues.",
        },
        "sales": {
            "classification": "sales",
            "confidence": 0.92,
            "reasoning": "Inquiry about products or services.",
        },
        "general": {
            "classification": "general",
            "confidence": 0.75,
            "reasoning": "General inquiry that doesn't fit other categories.",
        },
    }


@pytest.fixture(scope="function")
def email_processing_factory():
    """Factory for creating email processing test scenarios."""

    def _create_scenario(
        email_type="support",
        client_config=None,
        expected_classification="support",
        should_auto_reply=True,
        should_forward=True,
    ):
        return {
            "email_type": email_type,
            "client_config": client_config,
            "expected_classification": expected_classification,
            "should_auto_reply": should_auto_reply,
            "should_forward": should_forward,
        }

    return _create_scenario
