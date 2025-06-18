"""
Essential tests for MVP webhook endpoint.
🧪 Tests core email processing functionality.
"""

import hashlib
import hmac
import os
import time

from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["MAILGUN_API_KEY"] = "test-key"
os.environ["MAILGUN_DOMAIN"] = "test.domain.com"
os.environ["MAILGUN_WEBHOOK_SIGNING_KEY"] = "test-signing-key"


# client = TestClient(app) # Remove the old client instance


def generate_mailgun_signature(timestamp: str, token: str, api_key: str) -> str:
    """Generate a valid Mailgun webhook signature for testing."""
    signing_string = f"{timestamp}{token}"
    signature = hmac.new(
        key=api_key.encode("utf-8"),
        msg=signing_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return signature


def get_test_mailgun_headers() -> dict:
    """Get test Mailgun webhook headers with valid signature."""
    timestamp = str(int(time.time()))
    token = "test-token-123"
    signing_key = "test-signing-key"  # Same as MAILGUN_WEBHOOK_SIGNING_KEY env var
    signature = generate_mailgun_signature(timestamp, token, signing_key)
    
    return {
        "timestamp": timestamp,
        "token": token,
        "signature": signature,
    }


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "ai_classifier" in data["components"]
    assert "email_service" in data["components"]


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Email Router SaaS API" in data["name"]
    assert data["status"] == "operational"
    assert "/webhooks/mailgun/inbound" in data["endpoints"]["webhook_inbound"]


def test_webhook_endpoint_valid_data(client: TestClient, auth_headers: dict):
    """Test Mailgun webhook endpoint with valid data."""
    mailgun_headers = get_test_mailgun_headers()
    form_data = {
        "from": "test@example.com",
        "subject": "Test Support Email",
        "body-plain": "I need help with my account",
        "recipient": "support@yourcompany.com",
        "stripped-text": "I need help with my account",
        **mailgun_headers,  # Include Mailgun signature headers
    }

    response = client.post("/webhooks/mailgun/inbound", data=form_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "processing started" in data["message"]


def test_webhook_endpoint_missing_data(client: TestClient, auth_headers: dict):
    """Test webhook endpoint with minimal data."""
    mailgun_headers = get_test_mailgun_headers()
    form_data = {
        "from": "test@example.com",
        # Missing subject and body
        **mailgun_headers,  # Include Mailgun signature headers
    }

    response = client.post("/webhooks/mailgun/inbound", data=form_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"  # Should still accept and process


def test_webhook_endpoint_empty_request(client: TestClient, auth_headers: dict):
    """Test webhook endpoint with empty request."""
    mailgun_headers = get_test_mailgun_headers()
    form_data = {
        **mailgun_headers,  # Include Mailgun signature headers even for empty request
    }
    
    response = client.post("/webhooks/mailgun/inbound", data=form_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"  # Should handle gracefully


def test_docs_endpoint(client: TestClient):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
