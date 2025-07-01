# 🏗️ Email Router V2.0 Architecture

## Executive Summary

Email Router V2.0 represents a complete architectural transformation from a monolithic structure to a modern, scalable, multi-tenant platform built on clean architecture principles. This document provides comprehensive technical details of the V2.0 architecture.

## 🎯 Architectural Principles

### **Clean Architecture**
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Separation of Concerns**: Each layer has distinct responsibilities
- **Testability**: Each component can be tested in isolation
- **Framework Independence**: Business logic independent of external frameworks

### **Domain-Driven Design**
- **Bounded Contexts**: Clear boundaries between different business domains
- **Domain Models**: Rich domain objects with business logic
- **Ubiquitous Language**: Consistent terminology across codebase
- **Aggregate Patterns**: Consistency boundaries for business operations

## 🏛️ System Architecture

### **High-Level Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                   Email Router V2.0                        │
│                     (Multi-Tenant)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 API Gateway Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   v1/auth    │  │  v1/clients  │  │   v1/webhooks    │   │
│  │   v1/dash    │  │   v2/config  │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Application Layer                             │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │  Dependencies   │  │          Middleware                 │ │
│  │   auth.py       │  │ auth, security, rate_limit, etc.   │ │
│  └─────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Core Layer (Business Logic)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  clients/    │  │    email/    │  │ authentication/  │   │
│  │  manager.py  │  │ classifier   │  │    jwt.py        │   │
│  │  resolver.py │  │ composer.py  │  │   handlers.py    │   │
│  │              │  │  router.py   │  │    rbac.py       │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Infrastructure Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   config/    │  │  database/   │  │   external/      │   │
│  │  manager.py  │  │ connection   │  │   mailgun.py     │   │
│  │  schema.py   │  │  models.py   │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📱 Layer-by-Layer Breakdown

### **1. Interface Layer (API)**

**Purpose**: HTTP interface for external interactions

**Components**:
- **Authentication Endpoints** (`api/v1/auth.py`)
  - Login/logout with JWT token management
  - User registration and management
  - Session handling and revocation
  - Password management and security

- **Client Management** (`api/v1/clients.py`)
  - Client CRUD operations
  - Domain resolution testing
  - Configuration validation
  - Multi-tenant isolation

- **Configuration API** (`api/v2/config.py`)
  - Real-time configuration updates
  - YAML validation and parsing
  - Client-specific settings management
  - Branding and routing configuration

- **Webhook Handlers** (`api/v1/webhooks.py`)
  - Mailgun inbound email processing
  - Background task orchestration
  - Error handling and recovery
  - Performance monitoring

- **Dashboard API** (`api/v1/dashboard.py`)
  - Real-time analytics endpoints
  - Metrics aggregation and reporting
  - Client-specific dashboards
  - Performance insights

### **2. Application Layer**

**Purpose**: Orchestration, middleware, and cross-cutting concerns

**Components**:
- **Dependency Injection** (`application/dependencies/`)
  - Service registration and resolution
  - Lifecycle management
  - Configuration binding
  - Database connections

- **Middleware** (`application/middleware/`)
  - Authentication and authorization
  - Rate limiting and throttling
  - Security headers and CORS
  - Request/response logging
  - Error handling and recovery

- **Background Tasks** (`application/startup.py`)
  - Application initialization
  - Health check registration
  - Monitoring setup
  - Graceful shutdown handling

### **3. Core Layer (Domain)**

**Purpose**: Business logic and domain models

#### **Client Management Domain**
- **Client Manager** (`core/clients/manager.py`)
  - Multi-tenant client operations
  - Domain resolution and matching
  - Configuration loading and caching
  - Client validation and setup

- **Domain Resolver** (`core/clients/resolver.py`)
  - Advanced domain matching algorithms
  - Fuzzy matching and similarity scoring
  - Hierarchy resolution
  - Confidence-based identification

#### **Email Processing Domain**
- **AI Classifier** (`core/email/classifier.py`)
  - Claude 3.5 Sonnet integration
  - Client-specific prompt management
  - Classification confidence scoring
  - Fallback classification strategies

- **Email Composer** (`core/email/composer.py`)
  - Dual-mode email generation
  - Client-specific branding
  - Template engine integration
  - Dynamic content generation

- **Email Router** (`core/email/router.py`)
  - Smart routing logic
  - Business rule evaluation
  - Escalation handling
  - After-hours routing

#### **Authentication Domain**
- **JWT Service** (`core/authentication/jwt.py`)
  - Token generation and validation
  - Refresh token handling
  - Session management
  - Security policy enforcement

- **RBAC System** (`core/authentication/rbac.py`)
  - Role-based access control
  - Permission checking
  - Resource-level authorization
  - Multi-tenant permission isolation

#### **Dashboard Domain**
- **Analytics Service** (`core/dashboard/service.py`)
  - Metrics calculation and aggregation
  - Trend analysis and insights
  - Performance monitoring
  - Client-specific analytics

### **4. Infrastructure Layer**

**Purpose**: External services, persistence, and technical concerns

**Components**:
- **Configuration Management** (`infrastructure/config/`)
  - Environment-specific settings
  - YAML parsing and validation
  - Hot configuration reloading
  - Security configuration

- **Database Layer** (`infrastructure/database/`)
  - SQLAlchemy models and migrations
  - Connection pooling and management
  - Query optimization
  - Transaction handling

- **External Services** (`infrastructure/external/`)
  - Mailgun API integration
  - Anthropic Claude API client
  - HTTP client configuration
  - Error handling and retries

- **Monitoring** (`infrastructure/monitoring/`)
  - Prometheus metrics export
  - Application performance monitoring
  - Health check implementations
  - Alerting and notifications

## 🔄 Data Flow Architecture

### **Email Processing Pipeline**

```
1. Mailgun Webhook → 2. Authentication → 3. Client Resolution → 4. Background Task
                                                                        ↓
8. Email Delivery ← 7. Template Engine ← 6. Email Composer ← 5. AI Classification
```

**Detailed Flow**:
1. **Webhook Reception**: Mailgun sends POST to `/webhooks/mailgun/inbound`
2. **Authentication**: Verify webhook signature and API authentication
3. **Client Resolution**: Identify client using domain matching algorithms
4. **Background Processing**: Queue email for asynchronous processing
5. **AI Classification**: Claude 3.5 Sonnet categorizes email intent
6. **Email Composition**: Generate customer acknowledgment and team analysis
7. **Template Engine**: Apply client-specific branding and formatting
8. **Email Delivery**: Send emails via Mailgun with tracking

### **Configuration Management Flow**

```
YAML Files → Configuration Loader → Validation → Caching → Runtime Access
```

### **Authentication Flow**

```
Login Request → Credential Validation → JWT Generation → Session Storage → Token Response
```

## 🔒 Security Architecture

### **Authentication & Authorization**
- **JWT Tokens**: HS256 signed with 30-minute expiry
- **Refresh Tokens**: Secure refresh with 30-day expiry
- **Session Management**: Database-backed with audit trails
- **Role-Based Access**: Three-tier permission system
- **API Key Authentication**: For automated system access

### **Multi-Tenant Security**
- **Client Isolation**: Complete data separation per tenant
- **Permission Scoping**: Client-specific resource access
- **Configuration Isolation**: Separate config namespaces
- **Audit Logging**: Complete activity tracking

### **Infrastructure Security**
- **Rate Limiting**: Per-client and global limits
- **CORS Configuration**: Restrictive cross-origin policies
- **Security Headers**: HSTS, CSP, X-Frame-Options
- **Input Validation**: Comprehensive request sanitization
- **Error Handling**: Secure error responses without leakage

## 📊 Performance Architecture

### **Scalability Patterns**
- **Async/Await**: Non-blocking I/O throughout
- **Connection Pooling**: Efficient database connections
- **Caching**: Multi-layer caching strategy
- **Background Tasks**: Async email processing
- **Load Balancing**: Cloud Run auto-scaling

### **Performance Metrics**
- **Email Processing**: < 7 seconds end-to-end
- **API Response Times**: < 200ms for most endpoints
- **Database Queries**: Optimized with indexes and caching
- **Memory Usage**: < 512MB per instance
- **CPU Utilization**: < 50% under normal load

## 🔧 Technology Stack

### **Core Framework**
- **FastAPI**: Modern async web framework
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: ORM and database abstraction
- **Alembic**: Database migrations

### **External Services**
- **Anthropic Claude**: AI classification
- **Mailgun**: Email delivery service
- **Google Cloud Run**: Container deployment
- **SQLite/PostgreSQL**: Database options

### **Development Tools**
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Git hooks

## 🧪 Testing Architecture

### **Test Categories**
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning

### **Test Coverage**
- **88 Total Tests**: Comprehensive coverage
- **Critical Path Testing**: All major workflows covered
- **Mocking Strategy**: External dependencies mocked
- **CI/CD Integration**: Automated test execution
- **Coverage Reporting**: Detailed metrics and reports

## 🚀 Deployment Architecture

### **Cloud Run Deployment**
```
GitHub → Cloud Build → Container Registry → Cloud Run → Live Service
```

### **Environment Management**
- **Development**: Local with SQLite
- **Staging**: Cloud Run with test data
- **Production**: Cloud Run with PostgreSQL

### **Monitoring & Observability**
- **Health Checks**: Multi-level system monitoring
- **Metrics Export**: Prometheus-compatible metrics
- **Logging**: Structured JSON logging
- **Alerting**: Real-time issue notifications
- **Performance Monitoring**: APM integration

## 🔮 Future Architecture Considerations

### **Planned Enhancements**
- **Microservices Evolution**: Service decomposition
- **Event-Driven Architecture**: Async event processing
- **CQRS Implementation**: Command/query separation
- **Database Sharding**: Multi-tenant data partitioning
- **API Gateway**: Centralized API management

### **Scalability Roadmap**
- **Horizontal Scaling**: Multi-region deployment
- **Caching Layer**: Redis for session and data caching
- **Message Queues**: Async processing with Pub/Sub
- **CDN Integration**: Static asset delivery optimization
- **Edge Computing**: Regional email processing

---

This architecture provides a solid foundation for enterprise-scale email routing with modern best practices, comprehensive security, and excellent maintainability.
