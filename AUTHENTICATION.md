# Authentication & Authorization Guide

🔐 **Complete guide to Email Router's enterprise-grade authentication system**

## Overview

The Email Router implements a sophisticated dual authentication system supporting both human users (JWT tokens) and automated systems (API keys). This design enables secure access for web applications, mobile apps, and automated integrations while maintaining strict multi-tenant isolation.

## Authentication Methods

### 1. JWT Authentication (Human Users)

**Best for:** Web applications, mobile apps, interactive dashboards

JWT (JSON Web Token) authentication provides secure, stateless authentication for human users with features like:

- ✅ **Secure Login/Logout** with session management
- ✅ **Token Refresh** for extended sessions
- ✅ **Role-Based Access Control (RBAC)** with fine-grained permissions
- ✅ **Multi-tenant Client Scoping** for data isolation
- ✅ **Session Revocation** for security events

#### JWT Token Flow

```mermaid
sequenceDiagram
    participant Client as Web/Mobile App
    participant API as Email Router API
    participant DB as Database

    Client->>API: POST /auth/login (username, password)
    API->>DB: Validate credentials
    DB-->>API: User data
    API->>DB: Create session records
    API-->>Client: Access token + Refresh token

    Note over Client,API: Use access token for API calls
    Client->>API: GET /api/v2/clients (Bearer token)
    API->>API: Validate JWT + permissions
    API-->>Client: Protected resource

    Note over Client,API: Refresh when token expires
    Client->>API: POST /auth/refresh (refresh token)
    API-->>Client: New access token
```

### 2. API Key Authentication (Bots/Integrations)

**Best for:** Webhook handlers, automated scripts, CI/CD pipelines, external integrations

API key authentication provides simple, reliable authentication for automated systems:

- ✅ **Long-lived Credentials** for stable integrations
- ✅ **Client-scoped Access** for security isolation
- ✅ **Rate Limiting** with tier-based controls
- ✅ **Usage Tracking** and analytics
- ✅ **Easy Revocation** when needed

#### API Key Format

```
sk-{client-prefix}-{random-suffix}

Examples:
sk-client001-abc123def456789  # Maps to client-001-cole-nielson
sk-test-xyz789012345          # Maps to test-client
sk-demo-qwe456rty789          # Maps to demo-client
```

### 3. Dual Authentication System

The system automatically chooses the appropriate authentication method:

1. **JWT Priority**: If a valid Bearer token is provided, JWT authentication is used
2. **API Key Fallback**: If JWT fails, the system attempts API key authentication
3. **Endpoint-Specific**: Some endpoints prefer or require specific auth types

```http
# Both auth methods in same request (JWT takes priority)
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
X-API-Key: sk-client001-abc123def456789
```

## API Endpoints

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "securepass123",
  "client_id": "client-001-cole-nielson"  // Optional for scoping
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "client_id": "client-001-cole-nielson",
  "role": "client_admin",
  "permissions": ["client:read", "client:write", "routing:write"]
}
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@company.com",
  "full_name": "Admin User",
  "role": "client_admin",
  "client_id": "client-001-cole-nielson",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

#### Change Password
```http
PUT /auth/me/password
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

### User Management (Admin Only)

#### Register New User
```http
POST /auth/register
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...  // Requires super_admin
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@company.com",
  "password": "securepass123",
  "full_name": "New User",
  "client_id": "client-001-cole-nielson",
  "role": "client_user"
}
```

#### List Users
```http
GET /auth/users?client_id=client-001-cole-nielson&limit=50&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...  // Requires users:read
```

#### Delete User
```http
DELETE /auth/users/{user_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...  // Requires super_admin
```

### Session Management

#### List Active Sessions
```http
GET /auth/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "abc123...",
      "token_type": "access",
      "created_at": "2024-01-15T10:30:00Z",
      "last_used_at": "2024-01-15T14:25:00Z",
      "expires_at": "2024-01-15T16:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

#### Revoke Session
```http
DELETE /auth/sessions/{session_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

## Role-Based Access Control (RBAC)

### User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `super_admin` | Global system administrator | All permissions across all clients |
| `client_admin` | Client administrator | Full access to assigned client |
| `client_user` | Standard client user | Read-only access to assigned client |
| `api_user` | API key user | Limited permissions for integrations |

### Permission System

Permissions follow the format: `{resource}:{action}`

**Resources:**
- `client` - Client configuration
- `clients` - Multi-client access (super admin)
- `routing` - Email routing rules
- `branding` - Client branding settings
- `ai_prompts` - AI classification prompts
- `response_times` - Response time settings
- `users` - User management
- `system` - System administration

**Actions:**
- `read` - View/list resources
- `write` - Create/update resources
- `delete` - Remove resources
- `admin` - Full administrative access

**Examples:**
```
client:read          # Read client configuration
routing:write        # Modify routing rules
users:admin          # Full user management
system:admin         # System administration
```

### Client Scoping

Non-super-admin users are automatically scoped to their assigned client:

```json
{
  "user": {
    "client_id": "client-001-cole-nielson",
    "role": "client_admin"
  },
  "access": {
    "can_read": ["client-001-cole-nielson"],
    "can_write": ["client-001-cole-nielson"],
    "cannot_access": ["other-client-123"]
  }
}
```

## Security Features

### Password Security

- ✅ **bcrypt hashing** with automatic salting
- ✅ **Minimum 8 characters** with complexity requirements
- ✅ **Rate limiting** on login attempts
- ✅ **Account lockout** after 5 failed attempts (30 min)
- ✅ **Token revocation** on password change

### Token Security

- ✅ **HS256 JWT signing** with secret rotation support
- ✅ **Short-lived access tokens** (30 minutes)
- ✅ **Long-lived refresh tokens** (30 days)
- ✅ **Unique JWT IDs (jti)** for revocation tracking
- ✅ **Session management** with audit trails

### API Key Security

- ✅ **Client-scoped access** with automatic isolation
- ✅ **Rate limiting** by tier (standard/premium/enterprise)
- ✅ **Usage tracking** and analytics
- ✅ **Easy revocation** and rotation

## Integration Examples

### Web Application (React/Vue/Angular)

```javascript
// Login flow
const login = async (username, password) => {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const tokens = await response.json();
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);

  return tokens;
};

// API calls with token
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch(endpoint, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token expired, try refresh
    await refreshToken();
    return apiCall(endpoint, options); // Retry
  }

  return response;
};

// Token refresh
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const tokens = await response.json();
  localStorage.setItem('access_token', tokens.access_token);
};
```

### Webhook Handler (Python)

```python
import httpx

# Using API key authentication
async def send_webhook_data(data):
    headers = {
        'X-API-Key': 'sk-client001-abc123def456789',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.emailrouter.com/webhooks/mailgun/inbound',
            json=data,
            headers=headers
        )

        return response.json()
```

### CLI Tool (Node.js)

```javascript
// Using JWT for interactive CLI
const axios = require('axios');

class EmailRouterClient {
  constructor(apiUrl) {
    this.apiUrl = apiUrl;
    this.accessToken = null;
  }

  async login(username, password) {
    const response = await axios.post(`${this.apiUrl}/auth/login`, {
      username,
      password
    });

    this.accessToken = response.data.access_token;
    return response.data;
  }

  async getClients() {
    const response = await axios.get(`${this.apiUrl}/api/v2/clients`, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    return response.data;
  }
}
```

## Admin Tools

### Create Admin User

Use the provided script to create the initial super admin:

```bash
# Interactive mode (recommended)
python scripts/simple_create_admin.py

# Command line mode
python scripts/create_admin_user.py --username admin --email admin@company.com

# List existing admins
python scripts/simple_create_admin.py --list
```

### Generate API Keys

API keys are currently managed through client configuration. Future versions will include API key management endpoints.

## Testing Authentication

### Unit Tests

```bash
# Run authentication tests
python -m pytest tests/test_authentication.py -v

# Run JWT-specific tests
python -m pytest tests/test_jwt_service.py -v

# Run middleware tests
python -m pytest tests/test_dual_auth_middleware.py -v
```

### Manual Testing

```bash
# Test login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "securepass123"}'

# Test protected endpoint
curl -X GET http://localhost:8080/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Test API key endpoint
curl -X GET http://localhost:8080/webhooks/status \
  -H "X-API-Key: sk-client001-abc123def456789"
```

## Troubleshooting

### Common Issues

**1. "Invalid or expired token"**
- Check token expiration time
- Verify token format (should start with `ey`)
- Ensure proper `Bearer ` prefix in Authorization header

**2. "Permission denied"**
- Verify user role and permissions
- Check client scoping for non-super-admin users
- Confirm endpoint requires correct permission level

**3. "Account locked"**
- Wait 30 minutes or reset via database
- Check for too many failed login attempts
- Contact super admin for account unlock

**4. "Missing API key"**
- Include `X-API-Key` header or `Authorization: Bearer sk-...`
- Verify API key format matches expected pattern
- Check API key is valid for the target client

### Debug Mode

Enable debug logging for authentication:

```python
import logging
logging.getLogger('app.services.auth_service').setLevel(logging.DEBUG)
logging.getLogger('app.middleware.dual_auth').setLevel(logging.DEBUG)
```

## Security Considerations

### Production Deployment

1. **Environment Variables:**
   ```bash
   JWT_SECRET_KEY=your-256-bit-secret-key-here  # Required
   ANTHROPIC_API_KEY=your-anthropic-key
   MAILGUN_API_KEY=your-mailgun-key
   ```

2. **HTTPS Only:**
   - Always use HTTPS in production
   - Secure token transmission
   - Enable HSTS headers

3. **Secret Rotation:**
   - Rotate JWT secret keys regularly
   - Implement gradual key rotation
   - Update API keys periodically

4. **Network Security:**
   - Use firewalls and VPNs
   - Limit API access by IP if possible
   - Monitor for unusual access patterns

### Compliance

The authentication system supports common compliance requirements:

- **SOC 2**: Audit trails and session management
- **GDPR**: User data protection and deletion capabilities
- **HIPAA**: Access controls and encryption (when deployed securely)
- **ISO 27001**: Security controls and monitoring

For specific compliance needs, contact support for configuration guidance.

---

📚 **Additional Resources:**
- [API Reference](https://api.emailrouter.com/docs)
- [Python SDK](https://github.com/emailrouter/python-sdk)
- [Support Portal](https://support.emailrouter.com)
