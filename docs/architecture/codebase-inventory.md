# Current Codebase Architecture

**Updated:** December 2024
**Purpose:** Document current production architecture after successful reorganization
**Status:** ✅ Reorganization Complete

## Current Architecture Overview

The email router codebase has been successfully reorganized into a modern, scalable architecture with clear separation of concerns:

```
email-router-core/
├── backend/src/                    # FastAPI Backend Application
│   ├── main.py                    # Application entry point
│   ├── api/                       # API Layer (Interface)
│   │   ├── v1/                   # Version 1 APIs
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── clients.py        # Client management API
│   │   │   ├── dashboard.py      # Dashboard endpoints
│   │   │   └── webhooks.py       # Core webhook handlers
│   │   └── v2/
│   │       └── config.py         # Configuration API
│   ├── core/                      # Business Logic Layer
│   │   ├── authentication/       # Auth domain
│   │   │   ├── jwt.py           # JWT token management
│   │   │   ├── handlers.py      # Auth handlers
│   │   │   ├── manager.py       # Security coordinator
│   │   │   ├── rbac.py          # Role-based access
│   │   │   └── permissions.py   # Permission definitions
│   │   ├── clients/              # Client domain
│   │   │   ├── manager.py       # Multi-tenant client ops
│   │   │   └── resolver.py      # Domain matching
│   │   ├── email/                # Email domain
│   │   │   ├── classifier.py    # AI classification
│   │   │   ├── composer.py      # Email composition
│   │   │   └── router.py        # Business routing
│   │   ├── dashboard/
│   │   │   └── service.py       # Dashboard logic
│   │   └── models/              # Domain models
│   │       ├── schemas.py       # API schemas
│   │       └── dashboard.py     # Dashboard models
│   ├── infrastructure/           # Infrastructure Layer
│   │   ├── config/              # Configuration management
│   │   │   ├── manager.py       # Config coordinator
│   │   │   ├── schema.py        # Config validation
│   │   │   └── security.py      # Security config
│   │   ├── database/            # Data persistence
│   │   │   ├── connection.py    # DB connectivity
│   │   │   └── models.py        # SQLAlchemy models
│   │   ├── external/            # External services
│   │   │   └── mailgun.py       # Email delivery
│   │   ├── logging/
│   │   │   └── logger.py        # Logging setup
│   │   ├── monitoring/
│   │   │   └── metrics.py       # Metrics collection
│   │   ├── templates/
│   │   │   └── email.py         # Email templates
│   │   └── websockets/
│   │       └── manager.py       # Real-time comms
│   └── application/             # Application Layer
│       ├── dependencies/        # Dependency injection
│       │   └── auth.py          # Auth dependencies
│       ├── middleware/          # Cross-cutting concerns
│       │   ├── auth.py          # Auth middleware
│       │   ├── decorators.py    # Auth decorators
│       │   ├── rate_limit.py    # Rate limiting
│       │   ├── security.py      # Security headers
│       │   └── threat_detection.py # Threat detection
│       └── startup.py           # Application startup
├── frontend/src/                # SvelteKit Frontend
├── shared/                      # Shared Types & Schemas
├── clients/                     # Multi-tenant configurations
└── infrastructure/             # Deployment & Infrastructure
```

## Key Components

### Core Email Processing Pipeline
1. **Mailgun Webhook** → `backend/src/api/v1/webhooks.py`
2. **Client Identification** → `backend/src/core/clients/manager.py`
3. **AI Classification** → `backend/src/core/email/classifier.py`
4. **Smart Routing** → `backend/src/core/email/router.py`
5. **Email Generation** → `backend/src/core/email/composer.py`
6. **Email Delivery** → `backend/src/infrastructure/external/mailgun.py`

### Multi-Tenant Architecture
- **Client Manager**: Advanced domain matching with confidence scoring
- **Client Configurations**: YAML-based in `/clients/active/`
- **Domain Resolver**: Fuzzy matching and domain hierarchy support
- **Client Isolation**: Complete separation of data and configuration

### Authentication & Security
- **JWT Authentication**: Token-based with refresh capability
- **Role-Based Access Control**: Three-tier permission system
- **API Key Authentication**: For webhooks and automation
- **Security Middleware**: Headers, threat detection, rate limiting

### Technology Stack
- **Backend**: FastAPI 0.104+, SQLAlchemy, Pydantic
- **Frontend**: SvelteKit, TypeScript, Tailwind CSS
- **Database**: SQLite (dev), PostgreSQL (production)
- **External APIs**: Anthropic Claude 3.5 Sonnet, Mailgun
- **Infrastructure**: Google Cloud Run, Docker

## Production Status ✅

**Current Deployment:**
- **Live URL**: https://email-router-696958557925.us-central1.run.app
- **Processing Time**: 5-7 seconds end-to-end
- **Uptime**: 99.9%+
- **AI Accuracy**: 95%+ classification success rate
- **Email Delivery**: 100% success rate via Mailgun

**Operational Metrics:**
- All FastAPI dependency injection working
- Multi-tenant client isolation verified (1.00 confidence)
- Complete email processing pipeline operational
- Real-time health monitoring active
- Comprehensive audit logging in place

## Architectural Principles

### Clean Architecture Implementation
- **Core**: Business logic independent of frameworks
- **Infrastructure**: External services and data persistence
- **Application**: Framework-specific middleware and DI
- **Interface**: API endpoints and external interfaces

### Dependency Flow
```
API Layer → Application Layer → Core Layer ← Infrastructure Layer
```

### Key Design Decisions
- **Dependency Injection**: FastAPI's built-in DI system
- **Multi-Tenancy**: Client-based isolation with YAML configs
- **Background Processing**: FastAPI BackgroundTasks for email pipeline
- **Configuration Management**: Environment variables + YAML client configs
- **Error Handling**: Comprehensive fallbacks and confidence scoring
