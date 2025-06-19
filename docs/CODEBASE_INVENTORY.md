# Codebase Inventory & Migration Mapping

**Generated:** June 2025  
**Purpose:** Detailed file-by-file inventory for reorganization  
**Total Python Files:** 56 files in app/ directory

## Migration Mapping Table

| **Current Location** | **Domain/Layer** | **Suggested New Location** | **Key Dependencies** | **Migration Priority** | **Notes** |
|---------------------|------------------|---------------------------|---------------------|----------------------|-----------|
| **API LAYER (Interfaces)** |
| `app/main.py` | Application | `backend/src/main.py` | FastAPI, all routers, config | **HIGH** | Main FastAPI app entry point |
| `app/routers/webhooks.py` | Interface | `backend/src/api/v1/webhooks/` | Services, middleware | **HIGH** | Core webhook endpoints |
| `app/routers/auth.py` | Interface | `backend/src/api/v1/auth/` | Security services | **HIGH** | Authentication endpoints |
| `app/routers/api/v1.py` | Interface | `backend/src/api/v1/clients/` | Services, models | **MEDIUM** | Client management API |
| `app/routers/api/v2.py` | Interface | `backend/src/api/v2/config/` | Services, models | **MEDIUM** | Configuration API |
| `app/routers/dashboard.py` | Interface | `backend/src/api/v1/dashboard/` | Dashboard service | **LOW** | Dashboard endpoints |
| **CORE BUSINESS LOGIC** |
| `app/services/client_manager.py` | Use Case | `backend/src/core/clients/manager.py` | Domain models, utils | **HIGH** | Multi-tenant client operations |
| `app/services/ai_classifier.py` | Use Case | `backend/src/core/email/classifier.py` | External AI service | **HIGH** | AI classification logic |
| `app/services/email_service.py` | Use Case | `backend/src/core/email/composer.py` | Email entities | **HIGH** | Email composition logic |
| `app/services/routing_engine.py` | Use Case | `backend/src/core/email/router.py` | Client config | **HIGH** | Business routing rules |
| `app/services/email_sender.py` | Use Case | `backend/src/infrastructure/external/mailgun.py` | External email service | **HIGH** | Email delivery via Mailgun |
| `app/models/client_config.py` | Entity | `backend/src/core/models/client.py` | Pydantic | **HIGH** | Client domain model |
| `app/models/schemas.py` | Entity | `backend/src/core/models/schemas.py` | Pydantic | **MEDIUM** | API & domain schemas |
| `app/models/dashboard_schemas.py` | Entity | `backend/src/core/models/dashboard.py` | Pydantic | **LOW** | Dashboard domain model |
| **INFRASTRUCTURE LAYER** |
| `app/database/connection.py` | Infrastructure | `backend/src/infrastructure/database/connection.py` | SQLAlchemy | **MEDIUM** | Database connectivity |
| `app/database/models.py` | Infrastructure | `backend/src/infrastructure/database/models.py` | SQLAlchemy | **MEDIUM** | Database schema |
| `app/utils/client_loader.py` | Infrastructure | `backend/src/core/clients/loader.py` | YAML, filesystem | **MEDIUM** | File-based config |
| `app/utils/domain_resolver.py` | Infrastructure | `backend/src/core/clients/resolver.py` | String matching | **MEDIUM** | Domain matching logic |
| `app/utils/email_templates.py` | Infrastructure | `backend/src/infrastructure/templates/email.py` | HTML templates | **LOW** | Template management |
| **SECURITY LAYER** |
| `app/security/core/security_manager.py` | Security | `backend/src/core/authentication/manager.py` | All security components | **HIGH** | Central security coordinator |
| `app/security/authentication/jwt_service.py` | Security | `backend/src/core/authentication/jwt.py` | JWT, database | **HIGH** | JWT token management |
| `app/security/authentication/handlers.py` | Security | `backend/src/core/authentication/handlers.py` | JWT service | **HIGH** | Auth request handlers |
| `app/security/authentication/middleware.py` | Security | `backend/src/application/middleware/auth.py` | JWT, FastAPI | **HIGH** | Auth middleware |
| `app/security/authentication/dependencies.py` | Security | `backend/src/application/dependencies/auth.py` | FastAPI | **HIGH** | Dependency injection |
| `app/security/authorization/rbac.py` | Security | `backend/src/core/authentication/rbac.py` | Permissions | **MEDIUM** | Role-based access |
| `app/security/authorization/permissions.py` | Security | `backend/src/core/authentication/permissions.py` | RBAC models | **MEDIUM** | Permission definitions |
| `app/security/authorization/decorators.py` | Security | `backend/src/application/middleware/decorators.py` | FastAPI | **MEDIUM** | Auth decorators |
| `app/security/middleware/security_headers.py` | Security | `backend/src/application/middleware/security.py` | FastAPI | **LOW** | Security headers |
| `app/security/middleware/threat_detection.py` | Security | `backend/src/application/middleware/threat_detection.py` | FastAPI | **LOW** | Threat detection |
| **CONFIGURATION** |
| `app/core/config_manager.py` | Infrastructure | `backend/src/infrastructure/config/manager.py` | Pydantic, YAML | **HIGH** | Configuration management |
| `app/core/config_schema.py` | Infrastructure | `backend/src/infrastructure/config/schema.py` | Pydantic | **HIGH** | Configuration validation |
| `app/security/core/config.py` | Infrastructure | `backend/src/infrastructure/config/security.py` | Security config | **HIGH** | Security configuration |
| `app/utils/config.py` | Infrastructure | `backend/src/infrastructure/config/legacy.py` | Legacy wrapper | **LOW** | Backward compatibility |
| **UTILITIES & MONITORING** |
| `app/utils/logger.py` | Infrastructure | `backend/src/infrastructure/logging/logger.py` | Python logging | **LOW** | Logging configuration |
| `app/utils/startup_validator.py` | Infrastructure | `backend/src/application/startup.py` | Config validation | **LOW** | System validation |
| `app/middleware/rate_limiter.py` | Infrastructure | `backend/src/application/middleware/rate_limit.py` | FastAPI | **MEDIUM** | Rate limiting |
| `app/services/monitoring.py` | Infrastructure | `backend/src/infrastructure/monitoring/metrics.py` | Prometheus | **LOW** | Metrics collection |
| `app/services/dashboard_service.py` | Use Case | `backend/src/core/dashboard/service.py` | Monitoring | **LOW** | Dashboard business logic |
| `app/services/websocket_manager.py` | Infrastructure | `backend/src/infrastructure/websockets/manager.py` | WebSockets | **LOW** | Real-time communication |
| **LEGACY/COMPATIBILITY** |
| `app/services/auth_service_compat.py` | Legacy | `backend/src/infrastructure/legacy/auth_compat.py` | Security services | **LOW** | Backward compatibility |
| `app/services/config_service.py` | Legacy | `backend/src/infrastructure/legacy/config_service.py` | Database | **LOW** | Legacy config service |

## Key Dependencies Analysis

### High-Risk Dependencies (Require Careful Migration)
- **FastAPI Routers**: All router files depend on FastAPI and services
- **Security Chain**: JWT → Handlers → Middleware → Dependencies
- **Configuration Chain**: Config Manager → Schema → Legacy Config
- **Client Management**: Manager → Loader → Resolver → Domain Models

### External Dependencies
- **Anthropic API**: AI classification service
- **Mailgun API**: Email delivery service  
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **FastAPI**: Web framework

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Create new directory structure
2. Move configuration files first (least dependencies)
3. Move utilities and logging

### Phase 2: Core Business Logic  
1. Move domain models (entities)
2. Move business logic (use cases)
3. Update imports step by step

### Phase 3: Infrastructure Layer
1. Move database and external service adapters
2. Move security implementation
3. Update dependency injection

### Phase 4: Interface Layer
1. Move API routes and middleware
2. Update main.py and application startup
3. Test all endpoints

## Risk Assessment

### High Risk Items
- **Import chains**: Complex dependency relationships
- **FastAPI DI**: Dependency injection patterns
- **Database sessions**: SQLAlchemy session management
- **Security middleware**: Authentication flow

### Mitigation Strategies  
- **Incremental migration**: Move files gradually
- **Compatibility layers**: Maintain old imports temporarily
- **Extensive testing**: Test after each migration step
- **Rollback plan**: Safety branches for each phase

## Success Metrics
- All imports resolved without errors
- All tests passing after migration
- No circular dependencies
- Clear separation of concerns
- Improved code organization and maintainability