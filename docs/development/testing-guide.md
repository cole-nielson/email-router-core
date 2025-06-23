# Email Router Testing Guide

## Overview

The Email Router project uses a comprehensive testing strategy covering unit tests, integration tests, and end-to-end tests. This guide explains how to write, run, and maintain tests.

## Test Organization

```
backend/tests/
├── conftest.py              # Root configuration and fixtures
├── fixtures/                # Shared test fixtures
│   ├── auth_fixtures.py    # Authentication fixtures
│   ├── client_fixtures.py  # Client configuration fixtures
│   └── conftest.py         # Main fixture definitions
├── unit/                   # Unit tests (isolated components)
│   ├── test_jwt_service.py
│   ├── test_config_validation.py
│   └── test_multi_tenant.py
└── integration/            # Integration tests (full workflows)
    └── test_authentication.py
```

## Running Tests

### Quick Start

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_jwt_service.py

# Run specific test class
pytest tests/unit/test_jwt_service.py::TestJWTTokenSecurity

# Run specific test method
pytest tests/unit/test_jwt_service.py::TestJWTTokenSecurity::test_token_expiration_time
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage in terminal
pytest --cov=src --cov-report=term-missing

# Coverage for specific module
pytest --cov=src.core.authentication --cov-report=term
```

### Test Selection

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests matching pattern
pytest -k "test_auth"

# Run tests by marker
pytest -m "slow"

# Exclude slow tests
pytest -m "not slow"
```

## Writing Tests

### Unit Tests

Unit tests should test individual components in isolation:

```python
# backend/tests/unit/test_example_service.py
import pytest
from unittest.mock import Mock, patch

from core.services.example import ExampleService

class TestExampleService:
    """Test the ExampleService business logic."""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked dependencies."""
        mock_config = Mock()
        mock_config.get_setting.return_value = "test_value"
        return ExampleService(mock_config)

    def test_process_item_success(self, service):
        """Test successful item processing."""
        # Arrange
        item = {"id": "123", "name": "Test Item"}

        # Act
        result = service.process_item(item)

        # Assert
        assert result.status == "processed"
        assert result.id == "123"

    def test_process_item_validation_error(self, service):
        """Test item processing with invalid input."""
        # Arrange
        invalid_item = {"id": ""}  # Missing required field

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid item"):
            service.process_item(invalid_item)

    @patch('core.services.example.external_api_call')
    def test_process_with_external_service(self, mock_api, service):
        """Test processing that involves external API."""
        # Arrange
        mock_api.return_value = {"status": "success"}

        # Act
        result = service.process_with_api("test_data")

        # Assert
        mock_api.assert_called_once_with("test_data")
        assert result.external_status == "success"
```

### Integration Tests

Integration tests should test complete workflows:

```python
# backend/tests/integration/test_email_workflow.py
import pytest
from fastapi.testclient import TestClient

class TestEmailWorkflow:
    """Test complete email processing workflow."""

    def test_webhook_to_delivery(self, client: TestClient, sample_email_webhook_data):
        """Test email from webhook receipt to delivery."""
        # Arrange
        webhook_data = sample_email_webhook_data

        # Act - Send webhook
        response = client.post(
            "/webhooks/mailgun/inbound",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - Webhook accepted
        assert response.status_code == 202

        # TODO: In real test, would verify:
        # - Email was classified
        # - Routing was determined
        # - Emails were sent
        # - Database was updated

    def test_authentication_flow(self, client: TestClient, test_user):
        """Test complete authentication flow."""
        # Login
        login_response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == test_user.username

        # Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200

        # Verify token is invalid
        invalid_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert invalid_response.status_code == 401
```

### Testing Best Practices

#### 1. Use Fixtures for Common Setup

```python
@pytest.fixture
def authenticated_client(client: TestClient, test_user):
    """Provide a client with authentication headers."""
    response = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

#### 2. Mock External Services

```python
@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests."""
    with patch('anthropic.Anthropic') as mock_anthropic, \
         patch('requests.post') as mock_requests:

        # Configure default responses
        mock_anthropic.return_value.messages.create.return_value.content = [
            Mock(text="support")
        ]
        mock_requests.return_value.status_code = 200

        yield {
            "anthropic": mock_anthropic,
            "requests": mock_requests
        }
```

#### 3. Use Parametrized Tests

```python
@pytest.mark.parametrize("email,expected_domain", [
    ("user@example.com", "example.com"),
    ("test@sub.domain.com", "sub.domain.com"),
    ("admin@localhost", "localhost"),
])
def test_extract_domain(email, expected_domain):
    """Test domain extraction with various inputs."""
    assert extract_domain_from_email(email) == expected_domain
```

#### 4. Test Error Cases

```python
def test_api_error_handling(client: TestClient):
    """Test that API errors are handled gracefully."""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    assert "detail" in response.json()
```

## Test Fixtures

### Database Fixtures

```python
@pytest.fixture(scope="function")
def db_session():
    """Provide a clean database session for each test."""
    # Create test database
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
```

### User Fixtures

```python
@pytest.fixture
def test_users(db_session, auth_service):
    """Create a set of test users with different roles."""
    users = {
        "admin": create_test_user(db_session, auth_service,
                                 role=UserRole.SUPER_ADMIN),
        "client_admin": create_test_user(db_session, auth_service,
                                        role=UserRole.CLIENT_ADMIN),
        "user": create_test_user(db_session, auth_service,
                                role=UserRole.CLIENT_USER)
    }
    return users
```

### Client Configuration Fixtures

```python
@pytest.fixture
def mock_client_config():
    """Provide mock client configuration."""
    return {
        "client_id": "test-client",
        "name": "Test Client",
        "domains": {
            "primary": "test.example.com",
            "aliases": ["support.test.example.com"]
        },
        "routing": {
            "support": "support@test.example.com",
            "billing": "billing@test.example.com"
        }
    }
```

## Mocking Strategies

### Mocking Time

```python
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00")
def test_token_expiration():
    """Test token expiration with fixed time."""
    token = create_token()

    # Move time forward
    with freeze_time("2024-01-01 12:31:00"):
        # Token should be expired after 30 minutes
        assert is_token_expired(token)
```

### Mocking API Responses

```python
@pytest.fixture
def mock_anthropic_classifier():
    """Mock Anthropic API for classification."""
    def _mock_classify(category="support", confidence=0.95):
        with patch('core.email.classifier.anthropic') as mock:
            mock_response = Mock()
            mock_response.content = [Mock(text=f"{category}:{confidence}")]
            mock.Anthropic.return_value.messages.create.return_value = mock_response
            yield mock
    return _mock_classify

def test_email_classification(mock_anthropic_classifier):
    """Test email classification with mocked AI."""
    with mock_anthropic_classifier("billing", 0.88):
        result = classify_email("Question about my invoice")
        assert result.category == "billing"
        assert result.confidence == 0.88
```

## Testing AsyncIO Code

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_service():
    """Test asynchronous service methods."""
    service = AsyncService()
    result = await service.process_async("data")
    assert result.status == "completed"

# Alternative using pytest-asyncio
def test_async_with_fixture(event_loop):
    """Test async code with event loop fixture."""
    async def async_test():
        service = AsyncService()
        return await service.process_async("data")

    result = event_loop.run_until_complete(async_test())
    assert result.status == "completed"
```

## Performance Testing

```python
import pytest
import time

@pytest.mark.slow
def test_response_time(client: TestClient, auth_headers):
    """Test API response time is within SLA."""
    start_time = time.time()

    response = client.get("/api/v1/clients", headers=auth_headers)

    response_time = time.time() - start_time

    assert response.status_code == 200
    assert response_time < 1.0  # Should respond within 1 second

@pytest.mark.benchmark
def test_classification_performance(benchmark):
    """Benchmark email classification performance."""
    email_content = "I need help with my account login"

    # Benchmark the classification function
    result = benchmark(classify_email, email_content)

    assert result.category in ["support", "general"]
    assert benchmark.stats["mean"] < 0.1  # Average under 100ms
```

## Test Data Management

### Using Factory Pattern

```python
from factory import Factory, Faker, SubFactory

class UserFactory(Factory):
    class Meta:
        model = User

    username = Faker('user_name')
    email = Faker('email')
    full_name = Faker('name')
    role = UserRole.CLIENT_USER
    status = UserStatus.ACTIVE

class ClientConfigFactory(Factory):
    class Meta:
        model = ClientConfig

    client_id = Faker('uuid4')
    name = Faker('company')
    domains = {
        "primary": Faker('domain_name'),
        "aliases": []
    }

# Usage
def test_with_factory():
    user = UserFactory(role=UserRole.SUPER_ADMIN)
    assert user.role == UserRole.SUPER_ADMIN
```

### Test Data Files

```python
# backend/tests/data/emails.json
{
    "support_email": {
        "subject": "Can't login to my account",
        "body": "I forgot my password and need help"
    },
    "billing_email": {
        "subject": "Invoice question",
        "body": "Why was I charged twice this month?"
    }
}

# Load in tests
import json

@pytest.fixture
def test_emails():
    with open('tests/data/emails.json') as f:
        return json.load(f)
```

## Debugging Tests

### Using pytest debugger

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

### Print debugging

```python
def test_complex_logic(capsys):
    """Test with debug output."""
    result = complex_function()

    # Capture and check output
    captured = capsys.readouterr()
    print(f"Debug: result = {result}")

    assert result.status == "success"
```

### VS Code debugging

```json
// .vscode/launch.json
{
    "name": "Pytest: Current File",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "args": [
        "${file}",
        "-v"
    ],
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}/backend"
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements/test.txt

    - name: Run tests with coverage
      run: |
        cd backend
        pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

## Common Testing Patterns

### Testing Permissions

```python
def test_permission_required(client: TestClient, test_users):
    """Test endpoint requires specific permission."""
    # User without permission
    user_token = get_token(test_users["user"])
    response = client.delete(
        "/api/v1/users/123",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

    # Admin with permission
    admin_token = get_token(test_users["admin"])
    response = client.delete(
        "/api/v1/users/123",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code in [200, 204]
```

### Testing Multi-Tenant Isolation

```python
def test_client_isolation(client: TestClient):
    """Test that clients can't access each other's data."""
    # Create data for client A
    client_a_token = create_client_user("client-a")
    response = client.post(
        "/api/v1/data",
        json={"name": "Client A Data"},
        headers={"Authorization": f"Bearer {client_a_token}"}
    )
    data_id = response.json()["id"]

    # Try to access with client B
    client_b_token = create_client_user("client-b")
    response = client.get(
        f"/api/v1/data/{data_id}",
        headers={"Authorization": f"Bearer {client_b_token}"}
    )
    assert response.status_code == 404
```

## Test Maintenance

1. **Keep tests fast** - Mock external services
2. **Keep tests isolated** - Each test should be independent
3. **Keep tests simple** - Test one thing at a time
4. **Keep tests updated** - Update when code changes
5. **Remove obsolete tests** - Don't keep dead code

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Ensure PYTHONPATH is set
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest
```

**Database connection errors:**
```python
# Use in-memory database for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
```

**Async test failures:**
```python
# Ensure pytest-asyncio is installed
# Mark async tests properly
@pytest.mark.asyncio
async def test_async_function():
    pass
```
