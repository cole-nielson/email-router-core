# Email Router System Architecture

## Overview

The Email Router is a production-ready, multi-tenant AI-powered email processing system built with modern Python and TypeScript. It automatically classifies incoming emails, generates personalized responses, and routes them to appropriate team members.

## System Components

### 1. Backend (FastAPI)

The backend is built with FastAPI and follows a clean, layered architecture:

```
backend/src/
├── api/              # API endpoints and routing
├── application/      # Application layer (middleware, dependencies)
├── core/            # Business logic and domain services
├── infrastructure/  # External services and infrastructure
└── main.py         # Application entry point
```

#### Core Services

**Authentication & Authorization**
- `core/authentication/` - JWT-based authentication with refresh tokens
- Role-Based Access Control (RBAC) with three tiers: super_admin, client_admin, client_user
- Dual authentication support (JWT for users, API keys for services)

**Email Processing**
- `core/email/classifier.py` - AI-powered email classification using Claude 3.5 Sonnet
- `core/email/composer.py` - Dual-mode email generation (customer acknowledgment + team analysis)
- `core/email/router.py` - Smart routing with business rules and escalation policies

**Multi-Tenant Management**
- `core/clients/manager.py` - Client configuration and isolation
- `core/clients/resolver.py` - Advanced domain matching with fuzzy algorithms
- Complete client data isolation with confidence scoring

#### Infrastructure Layer

**Database**
- SQLAlchemy ORM with PostgreSQL/SQLite support
- Alembic for database migrations
- Connection pooling and session management

**External Services**
- `infrastructure/external/mailgun.py` - Email delivery via Mailgun API
- Anthropic Claude API integration for AI classification
- Webhook signature verification

**Configuration**
- Environment-based configuration with Pydantic validation
- YAML-based client configurations
- Centralized configuration management

### 2. Frontend (SvelteKit)

The frontend is a modern SvelteKit application with TypeScript:

```
frontend/src/
├── lib/
│   ├── components/  # Reusable UI components
│   ├── stores/      # Svelte stores for state management
│   ├── types/       # TypeScript type definitions
│   └── utils/       # Utility functions
└── routes/          # SvelteKit routes
```

#### Key Features

**Dashboard**
- Real-time email processing metrics
- Live feed with WebSocket updates
- Performance charts and analytics

**Authentication**
- JWT token management
- Protected routes with auth guards
- Automatic token refresh

**UI/UX**
- Responsive design with Tailwind CSS
- Dark mode support
- Glass morphism design elements
- Skeleton loading states

### 3. Shared Types

Type definitions shared between frontend and backend:

```
shared/
├── schemas/         # Pydantic schemas (Python)
├── types/           # Type definitions (Python & TypeScript)
└── constants/       # Shared constants
```

This ensures type safety across the full stack and maintains API contract consistency.

## Data Flow

### Email Processing Pipeline

1. **Webhook Receipt** → Mailgun sends email to `/webhooks/mailgun/inbound`
2. **Client Identification** → Domain-based client resolution with confidence scoring
3. **Background Processing**:
   - AI classification using client-specific prompts
   - Smart routing based on category and rules
   - Dual email generation (customer + team)
   - Delivery via Mailgun

### Request Flow

```
Client Request
    ↓
Nginx/Load Balancer
    ↓
FastAPI Application
    ↓
Middleware Stack
    - CORS
    - Authentication
    - Rate Limiting
    - Request ID
    ↓
API Router
    ↓
Dependency Injection
    ↓
Service Layer
    ↓
Database/External APIs
```

## Security Architecture

### Authentication Layers

1. **JWT Authentication**
   - Access tokens (30 min expiry)
   - Refresh tokens (30 day expiry)
   - Session tracking and revocation

2. **API Key Authentication**
   - Client-scoped API keys
   - Rate limiting per key
   - Usage tracking

3. **Webhook Security**
   - HMAC signature verification
   - Timestamp validation
   - Replay attack prevention

### Data Security

- Password hashing with bcrypt
- Environment-based secrets management
- SQL injection prevention via ORM
- XSS protection in templates
- CORS configuration for API access

## Deployment Architecture

### Container-Based Deployment

```
Docker Compose (Development)
    ├── Backend Service
    ├── Frontend Service
    └── Database Service

Cloud Run (Production)
    ├── Backend Container
    ├── Environment Variables
    └── Automatic Scaling
```

### Infrastructure as Code

```
infrastructure/
├── terraform/       # Cloud resource provisioning
├── kubernetes/      # K8s manifests (optional)
└── docker-compose/  # Local development
```

## Monitoring & Observability

### Health Checks
- `/health` - Basic health status
- `/health/detailed` - Component-level health
- Database connectivity checks
- External service availability

### Metrics
- Request/response times
- Email processing metrics
- Error rates and types
- Resource utilization

### Logging
- Structured JSON logging
- Request ID correlation
- Error tracking with context
- Audit trails for security events

## Scalability Considerations

### Horizontal Scaling
- Stateless backend design
- Database connection pooling
- Cache-friendly architecture
- Load balancer ready

### Performance Optimizations
- Async request handling
- Background task processing
- Efficient database queries
- CDN for static assets

### Multi-Tenant Isolation
- Client-scoped data access
- Separate configuration per client
- Resource usage limits
- Performance monitoring per tenant

## Development Workflow

### Local Development
```bash
# Backend
cd backend
pip install -r requirements/dev.txt
python -m uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical workflows
- Performance regression tests

### Code Quality
- Type checking with mypy
- Linting with ruff/black
- Pre-commit hooks
- Automated testing in CI/CD
