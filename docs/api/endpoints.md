# Email Router API Documentation

## Base URL

```
Development: http://localhost:8080
Production: https://your-domain.com
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with dual authentication support:
- **JWT Tokens**: For human users (web apps, mobile apps)
- **API Keys**: For automated systems (webhooks, integrations)

### Authentication Headers

```http
# JWT Authentication
Authorization: Bearer <jwt_token>

# API Key Authentication
X-API-Key: <api_key>
```

## API Endpoints

### Health & Status

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-23T10:30:00Z"
}
```

#### GET /health/detailed
Detailed health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-23T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "external_services": {
      "anthropic": {
        "status": "healthy",
        "latency_ms": 150
      },
      "mailgun": {
        "status": "healthy",
        "latency_ms": 80
      }
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Authentication Endpoints

#### POST /auth/login
Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "username": "john.doe",
  "password": "secure_password",
  "client_id": "client-001"  // Optional: for client-scoped login
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "client_user",
  "client_id": "client-001",
  "permissions": [
    "client:read",
    "routing:read",
    "branding:read"
  ]
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /auth/logout
Logout and revoke current token.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

#### GET /auth/me
Get current user information.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john.doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "client_user",
  "client_id": "client-001",
  "permissions": [
    "client:read",
    "routing:read"
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-06-23T10:00:00Z"
}
```

#### PUT /auth/me/password
Change current user's password.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

### User Management (Admin Only)

#### POST /auth/register
Register a new user (requires admin role).

**Headers:**
```http
Authorization: Bearer <admin_jwt_token>
```

**Request:**
```json
{
  "username": "new.user",
  "email": "new.user@example.com",
  "password": "secure_password",
  "full_name": "New User",
  "role": "client_user",
  "client_id": "client-001"
}
```

**Response:**
```json
{
  "id": 2,
  "username": "new.user",
  "email": "new.user@example.com",
  "full_name": "New User",
  "role": "client_user",
  "client_id": "client-001",
  "status": "active",
  "created_at": "2024-06-23T10:30:00Z"
}
```

#### GET /auth/users
List all users (requires admin role).

**Headers:**
```http
Authorization: Bearer <admin_jwt_token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `client_id` (string): Filter by client
- `role` (string): Filter by role

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john.doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "client_user",
      "client_id": "client-001",
      "status": "active",
      "last_login_at": "2024-06-23T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "pages": 3
}
```

#### DELETE /auth/users/{user_id}
Delete a user (requires super admin role).

**Headers:**
```http
Authorization: Bearer <super_admin_jwt_token>
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

### Session Management

#### GET /auth/sessions
List active sessions for current user.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "abc123...",
      "token_type": "access",
      "created_at": "2024-06-23T10:00:00Z",
      "expires_at": "2024-06-23T10:30:00Z",
      "last_used_at": "2024-06-23T10:15:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

#### DELETE /auth/sessions/{session_id}
Revoke a specific session.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Session revoked successfully"
}
```

### Webhook Endpoints

#### POST /webhooks/mailgun/inbound
Receive inbound emails from Mailgun.

**Headers:**
```http
Content-Type: application/x-www-form-urlencoded
```

**Request (Form Data):**
```
sender=customer@example.com
recipient=support@yourdomain.com
subject=Need help with my account
body-plain=I'm having trouble logging in...
body-html=<p>I'm having trouble logging in...</p>
timestamp=1624890123
token=abc123...
signature=def456...
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Email queued for processing"
}
```

#### GET /webhooks/status
Get webhook processing status.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "webhook_enabled": true,
  "last_received": "2024-06-23T10:25:00Z",
  "processed_today": 150,
  "pending_queue": 5,
  "average_processing_time_ms": 3500
}
```

### Client Management API (v1)

#### GET /api/v1/status
Get comprehensive system status.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "system": {
    "status": "operational",
    "version": "1.0.0",
    "uptime_seconds": 86400
  },
  "clients": {
    "total": 5,
    "active": 5
  },
  "processing": {
    "emails_today": 1500,
    "average_classification_time_ms": 500,
    "average_total_time_ms": 3500
  }
}
```

#### GET /api/v1/clients
List all clients (requires appropriate permissions).

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `page` (int): Page number
- `limit` (int): Items per page
- `search` (string): Search by name or domain

**Response:**
```json
{
  "clients": [
    {
      "client_id": "client-001",
      "name": "Example Corp",
      "domains": {
        "primary": "example.com",
        "aliases": ["support.example.com"]
      },
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "pages": 1
}
```

#### GET /api/v1/clients/{client_id}
Get specific client details.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "client_id": "client-001",
  "name": "Example Corp",
  "industry": "Technology",
  "domains": {
    "primary": "example.com",
    "aliases": ["support.example.com", "help.example.com"]
  },
  "branding": {
    "company_name": "Example Corporation",
    "primary_color": "#0066cc",
    "secondary_color": "#00aa44",
    "logo_url": "https://example.com/logo.png"
  },
  "settings": {
    "auto_reply_enabled": true,
    "ai_classification_enabled": true,
    "team_forwarding_enabled": true,
    "business_hours": {
      "timezone": "America/New_York",
      "monday": {"start": "09:00", "end": "17:00"},
      "tuesday": {"start": "09:00", "end": "17:00"}
    }
  },
  "routing": {
    "support": "support@example.com",
    "billing": "billing@example.com",
    "sales": "sales@example.com",
    "general": "info@example.com"
  },
  "statistics": {
    "emails_processed_today": 150,
    "emails_processed_month": 3500,
    "average_response_time_minutes": 15
  }
}
```

#### POST /api/v1/clients/{client_id}/validate
Validate client configuration.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "valid": true,
  "checks": {
    "configuration": {
      "status": "pass",
      "message": "All configuration files present"
    },
    "routing": {
      "status": "pass",
      "message": "All routing emails valid"
    },
    "domains": {
      "status": "pass",
      "message": "All domains resolvable"
    },
    "ai_prompts": {
      "status": "pass",
      "message": "AI prompts configured"
    }
  }
}
```

#### POST /api/v1/domain/resolve
Test domain resolution.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "domain": "support.example.com"
}
```

**Response:**
```json
{
  "resolved": true,
  "client_id": "client-001",
  "confidence": 1.0,
  "method": "exact_match",
  "client_name": "Example Corp"
}
```

### Configuration API (v2)

#### GET /api/v2/clients/{client_id}/routing
Get client routing configuration.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "routing": {
    "support": {
      "email": "support@example.com",
      "response_time": "within 4 hours",
      "auto_reply": true
    },
    "billing": {
      "email": "billing@example.com",
      "response_time": "within 24 hours",
      "auto_reply": true
    }
  },
  "escalation": {
    "keywords": ["urgent", "emergency"],
    "route_to": "manager@example.com"
  }
}
```

#### PUT /api/v2/clients/{client_id}/routing/{category}
Update routing for a category.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "email": "new-support@example.com",
  "response_time": "within 2 hours",
  "auto_reply": true
}
```

**Response:**
```json
{
  "message": "Routing updated successfully",
  "category": "support",
  "email": "new-support@example.com"
}
```

#### GET /api/v2/clients/{client_id}/branding
Get client branding configuration.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "company_name": "Example Corporation",
  "primary_color": "#0066cc",
  "secondary_color": "#00aa44",
  "logo_url": "https://example.com/logo.png",
  "email_footer": "Example Corp - Your trusted partner",
  "support_url": "https://support.example.com"
}
```

#### PUT /api/v2/clients/{client_id}/branding
Update client branding.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "primary_color": "#0077dd",
  "secondary_color": "#00bb55",
  "email_footer": "Example Corp - Innovation delivered"
}
```

**Response:**
```json
{
  "message": "Branding updated successfully",
  "updated_fields": ["primary_color", "secondary_color", "email_footer"]
}
```

### Dashboard API

#### GET /api/v1/dashboard/metrics
Get real-time dashboard metrics.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `period` (string): Time period (today, week, month)
- `client_id` (string): Filter by client (admin only)

**Response:**
```json
{
  "period": "today",
  "metrics": {
    "total_emails": 150,
    "classified": 148,
    "auto_replied": 145,
    "forwarded": 148,
    "failed": 2,
    "average_processing_time_ms": 3500,
    "categories": {
      "support": 75,
      "billing": 30,
      "sales": 25,
      "general": 20
    }
  },
  "trends": {
    "emails_vs_yesterday": "+15%",
    "processing_time_vs_yesterday": "-5%"
  }
}
```

#### GET /api/v1/dashboard/activity
Get recent activity feed.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (int): Number of items (default: 20)
- `offset` (int): Skip items

**Response:**
```json
{
  "activities": [
    {
      "id": "act_123",
      "type": "email_processed",
      "timestamp": "2024-06-23T10:25:00Z",
      "data": {
        "from": "customer@example.com",
        "subject": "Need help with login",
        "category": "support",
        "confidence": 0.95,
        "routed_to": "support@example.com",
        "processing_time_ms": 3200
      }
    }
  ],
  "total": 500,
  "has_more": true
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong",
  "type": "error_type",
  "status_code": 400
}
```

### Common Error Codes

- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing or invalid authentication)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

### Validation Error Response

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email address",
      "type": "value_error.email"
    }
  ],
  "status_code": 422
}
```

## Rate Limiting

API endpoints are rate-limited based on authentication method:

- **JWT Authentication**: 1000 requests per hour per user
- **API Key Authentication**: 5000 requests per hour per key
- **Unauthenticated**: 100 requests per hour per IP

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1624894800
```

## Webhooks

### Webhook Security

All webhooks must be verified using HMAC-SHA256 signatures:

```python
import hmac
import hashlib

def verify_webhook(timestamp, token, signature, webhook_key):
    message = f"{timestamp}{token}"
    expected = hmac.new(
        webhook_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Webhook Retry Policy

Failed webhook deliveries are retried with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 1 minute
- Attempt 3: 5 minutes
- Attempt 4: 30 minutes
- Attempt 5: 2 hours

## SDK Examples

### Python
```python
import requests

class EmailRouterClient:
    def __init__(self, base_url, api_key=None, jwt_token=None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        elif jwt_token:
            self.headers["Authorization"] = f"Bearer {jwt_token}"

    def get_clients(self):
        response = requests.get(
            f"{self.base_url}/api/v1/clients",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

### JavaScript/TypeScript
```typescript
class EmailRouterClient {
  constructor(
    private baseUrl: string,
    private apiKey?: string,
    private jwtToken?: string
  ) {}

  async getClients(): Promise<ClientList> {
    const headers: HeadersInit = {};
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    } else if (this.jwtToken) {
      headers["Authorization"] = `Bearer ${this.jwtToken}`;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/clients`, {
      headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }
}
```
