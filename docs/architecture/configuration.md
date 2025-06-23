# Configuration System Documentation

## Overview

The Email Router uses a unified configuration system that provides centralized management of all application settings, from core system configuration to client-specific settings.

## Architecture

### Configuration Hierarchy

```
📁 Configuration Structure
├── 🏗️ Global App Configuration (Environment Variables + Files)
│   ├── Database Settings
│   ├── Security Settings
│   ├── Service Configuration (Anthropic, Mailgun, etc.)
│   ├── Server Settings
│   └── Feature Flags
├── 👥 Client Configurations (YAML Files)
│   ├── client-001-example/
│   │   └── client-config.yaml
│   └── client-002-another/
│       └── client-config.yaml
└── 🎨 Templates & AI Context
    ├── Default templates
    └── Client-specific overrides
```

### Core Components

- **`AppConfig`**: Main application configuration schema
- **`ClientConfig`**: Individual client configuration schema
- **`ConfigManager`**: Centralized configuration loader and manager
- **Environment Variables**: Runtime configuration overrides

## Configuration Files

### 1. Main Application Configuration

The main app configuration is built from environment variables and optional YAML files.

#### Required Environment Variables

```bash
# Security (Required)
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
ANTHROPIC_API_KEY=your-anthropic-api-key
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-mailgun-domain.com

# Optional Configuration
EMAIL_ROUTER_ENVIRONMENT=development|staging|production
EMAIL_ROUTER_DEBUG=true|false
DATABASE_URL=sqlite:///data/email_router.db
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
PORT=8080
```

#### Optional YAML Configuration

You can also provide a YAML configuration file:

```yaml
# config.yaml (optional)
environment: production
debug: false

database:
  type: postgresql
  host: localhost
  port: 5432
  database: email_router
  username: postgres
  password: password

security:
  access_token_expire_minutes: 30
  max_login_attempts: 5
  enable_cors: true
  allowed_origins:
    - "https://yourdomain.com"

services:
  anthropic_model: "claude-3-5-sonnet-20241022"
  mailgun_timeout: 30

server:
  host: "0.0.0.0"
  port: 8080
  workers: 4
  log_level: INFO
```

### 2. Client Configuration

Each client has their own configuration file: `clients/active/{client-id}/client-config.yaml`

```yaml
# Client identification
client_id: "client-001-example"
name: "Example Company Email Router"
industry: "Technology"
timezone: "America/New_York"
active: true

# Domain configuration
domains:
  primary: "support.example.com"
  aliases:
    - "help.example.com"
    - "contact.example.com"
  catch_all: false

# Branding and styling
branding:
  company_name: "Example Company"
  logo_url: "https://example.com/logo.png"
  primary_color: "#007bff"
  secondary_color: "#6f42c1"
  header_gradient: "linear-gradient(135deg, #007bff, #6f42c1)"
  email_signature: "Example Company Support Team"

# Email routing rules
routing:
  - category: "support"
    email: "support-team@example.com"
    backup_email: "manager@example.com"
    priority: 1
    enabled: true
  - category: "billing"
    email: "billing@example.com"
    priority: 1
    enabled: true

# SLA configuration
sla:
  response_times:
    urgent: 15      # minutes
    high: 60        # minutes
    medium: 240     # minutes
    low: 1440       # minutes
  business_hours:
    timezone: "America/New_York"
    weekdays:
      start: "09:00"
      end: "17:00"
    weekends:
      enabled: false
  escalation_enabled: true
  escalation_rules:
    - trigger_type: "time"
      trigger_value: 4  # hours
      action: "escalate"
      target_email: "manager@example.com"
      enabled: true

# Feature settings
settings:
  auto_reply_enabled: true
  ai_classification_enabled: true
  team_forwarding_enabled: true
  escalation_enabled: true
  analytics_enabled: true
  webhook_notifications_enabled: false

# AI classification categories
ai_categories:
  - "general"
  - "support"
  - "billing"
  - "sales"

# Custom AI prompts (optional)
custom_prompts:
  classification: "Custom classification prompt..."
  acknowledgment: "Custom acknowledgment prompt..."
```

## Usage

### Accessing Configuration

```python
from app.core import get_app_config, get_client_config, get_config_manager

# Get main app configuration
config = get_app_config()
print(f"Environment: {config.environment}")
print(f"Database URL: {config.database.url}")

# Get specific client configuration
client_config = get_client_config("client-001-example")
if client_config:
    print(f"Client: {client_config.name}")
    print(f"Primary domain: {client_config.domains.primary}")

# Use configuration manager for advanced operations
config_manager = get_config_manager()
all_clients = config_manager.get_all_clients()
active_clients = config_manager.get_active_clients()

# Check feature flags
if config_manager.get_feature_flag("ai_classification"):
    print("AI classification is enabled")

# Check service availability
if config_manager.is_service_available("anthropic"):
    print("Anthropic AI service is configured")
```

### Environment-Specific Configuration

The configuration system automatically adapts to different environments:

#### Development
- Debug logging enabled
- Relaxed security settings
- Local database (SQLite)
- CORS enabled for localhost

#### Staging
- Moderate security settings
- External database support
- Limited CORS origins
- Enhanced logging

#### Production
- Strict security enforcement
- Full monitoring enabled
- Optimized database settings
- Security headers required

### Configuration Validation

All configuration is validated using Pydantic schemas:

```python
from app.core.config_schema import ClientConfig

# Validate client configuration
try:
    client_data = {
        "client_id": "test-client",
        "name": "Test Client",
        # ... other required fields
    }
    client_config = ClientConfig(**client_data)
    print("✅ Configuration is valid")
except ValidationError as e:
    print(f"❌ Configuration error: {e}")
```

## Configuration Schema Reference

### AppConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | Environment | development | Application environment |
| `app_name` | str | "Email Router" | Application name |
| `app_version` | str | "2.0.0" | Application version |
| `debug` | bool | False | Debug mode flag |
| `database` | DatabaseConfig | - | Database configuration |
| `security` | SecurityConfig | - | Security settings |
| `services` | ServiceConfig | - | External service config |
| `server` | ServerConfig | - | Server settings |
| `cache` | CacheConfig | - | Caching configuration |
| `monitoring` | MonitoringConfig | - | Monitoring settings |

### DatabaseConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | DatabaseType | sqlite | Database type |
| `url` | str | auto-generated | Database connection URL |
| `pool_size` | int | 5 | Connection pool size |
| `echo_sql` | bool | False | Log SQL queries |

### SecurityConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `jwt_secret_key` | str | - | JWT signing key (required) |
| `access_token_expire_minutes` | int | 30 | Access token lifetime |
| `max_login_attempts` | int | 5 | Failed login limit |
| `enable_cors` | bool | True | Enable CORS |
| `allowed_origins` | List[str] | ["http://localhost:3000"] | CORS origins |

### ClientConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `client_id` | str | - | Unique client identifier |
| `name` | str | - | Client display name |
| `active` | bool | True | Client status |
| `domains` | ClientDomainConfig | - | Domain configuration |
| `branding` | ClientBrandingConfig | - | Branding settings |
| `routing` | List[ClientRoutingRule] | [] | Email routing rules |
| `sla` | ClientSLAConfig | - | SLA configuration |
| `settings` | ClientSettingsConfig | - | Feature settings |

## Best Practices

### 1. Environment Variables
- Use environment variables for sensitive data (API keys, passwords)
- Prefix custom variables with `EMAIL_ROUTER_`
- Use uppercase for environment variable names

### 2. Configuration Files
- Use YAML for structured configuration
- Keep client configs in version control
- Use meaningful client IDs (e.g., `client-001-company-name`)

### 3. Security
- Never commit API keys or secrets to version control
- Use strong JWT secret keys (32+ characters)
- Restrict CORS origins in production

### 4. Client Management
- Use descriptive client names
- Set appropriate SLA response times
- Configure proper escalation rules
- Test routing rules before deployment

### 5. Performance
- Enable caching for production
- Use connection pooling for databases
- Monitor configuration loading times

## Migration Guide

### From Legacy Configuration

If migrating from the legacy configuration system:

1. **Move environment variables** to the new naming convention
2. **Convert client configurations** to the new YAML schema
3. **Update imports** from `app.utils.config` to `app.core`
4. **Test configuration loading** before deployment

### Example Migration

Old:
```python
from app.utils.config import get_config
config = get_config()
```

New:
```python
from app.core import get_app_config
config = get_app_config()
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   Error: Missing required environment variables: JWT_SECRET_KEY
   ```
   Solution: Set all required environment variables

2. **Invalid Client Configuration**
   ```
   Error: 2 validation errors for ClientConfig
   ```
   Solution: Check client YAML against schema requirements

3. **Database Connection Errors**
   ```
   Error: could not connect to server
   ```
   Solution: Verify database configuration and connectivity

4. **Configuration Loading Errors**
   ```
   Error: Configuration loading failed
   ```
   Solution: Check file permissions and YAML syntax

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```bash
export EMAIL_ROUTER_DEBUG=true
export LOG_LEVEL=DEBUG
```

This will provide detailed logging about configuration loading and validation.
