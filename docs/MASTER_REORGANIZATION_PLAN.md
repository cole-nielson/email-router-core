# Email Router - Master Codebase Reorganization Plan

**Document Version:** 1.0  
**Created:** June 2025  
**Purpose:** Complete codebase reorganization roadmap with detailed implementation strategy  
**Status:** Ready for Review

---

## 🎯 Executive Summary

This document provides a comprehensive plan to reorganize the email-router-core codebase from its current monolithic structure into a modern, scalable, and maintainable architecture with clear separation of concerns, proper frontend/backend organization, and professional project structure.

### Current Problems
- **No frontend/backend separation** - UI code mixed with backend in single repo
- **Scattered configuration** - 4 different config files with overlapping responsibilities  
- **Poor organization** - Services, models, and utilities scattered without clear boundaries
- **17,741+ files in UI directory** - Including node_modules and build artifacts
- **Inconsistent patterns** - Different approaches used throughout codebase
- **Missing shared code structure** - No clear place for common types/utilities

### Target Solution
- **Clear frontend/backend separation** with shared types
- **Modern monorepo structure** with proper workspace management
- **Domain-driven organization** within each application
- **Professional tooling** for development, testing, and deployment
- **Scalable architecture** ready for microservices if needed

---

## 📁 Proposed Project Structure

### Complete Target Directory Tree

```
email-router/
├── .github/                        # GitHub-specific configuration
│   ├── workflows/                  # CI/CD workflows
│   │   ├── backend-ci.yml         # Backend tests and linting
│   │   ├── frontend-ci.yml        # Frontend tests and build
│   │   ├── deploy-staging.yml     # Staging deployment
│   │   └── deploy-production.yml  # Production deployment
│   ├── ISSUE_TEMPLATE/            # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md   # PR template
│
├── backend/                        # All backend services
│   ├── src/                       # Source code
│   │   ├── api/                   # API layer
│   │   │   ├── v1/               # Version 1 endpoints
│   │   │   │   ├── auth/         # Authentication endpoints
│   │   │   │   ├── clients/      # Client management
│   │   │   │   ├── webhooks/     # Webhook handlers
│   │   │   │   └── dashboard/    # Dashboard API
│   │   │   └── v2/               # Version 2 endpoints
│   │   │       └── config/       # Configuration API
│   │   │
│   │   ├── core/                  # Core business logic
│   │   │   ├── authentication/    # Auth logic
│   │   │   │   ├── jwt.py        # JWT handling
│   │   │   │   ├── rbac.py       # Role-based access
│   │   │   │   └── sessions.py   # Session management
│   │   │   ├── email/            # Email processing
│   │   │   │   ├── classifier.py # AI classification
│   │   │   │   ├── composer.py   # Email composition
│   │   │   │   ├── router.py     # Routing logic
│   │   │   │   └── sender.py     # Email delivery
│   │   │   └── clients/          # Client management
│   │   │       ├── manager.py    # Client manager
│   │   │       ├── resolver.py   # Domain resolution
│   │   │       └── loader.py     # Config loading
│   │   │
│   │   ├── infrastructure/        # External integrations
│   │   │   ├── database/         # Database layer
│   │   │   │   ├── models.py     # SQLAlchemy models
│   │   │   │   ├── connection.py # DB connection
│   │   │   │   └── migrations/   # Alembic migrations
│   │   │   ├── external/         # External services
│   │   │   │   ├── anthropic.py  # Claude API
│   │   │   │   ├── mailgun.py    # Mailgun API
│   │   │   │   └── monitoring.py # Monitoring services
│   │   │   └── config/           # Configuration
│   │   │       ├── manager.py    # Config manager
│   │   │       ├── schema.py     # Config schemas
│   │   │       └── validator.py  # Validation
│   │   │
│   │   ├── application/           # Application layer
│   │   │   ├── middleware/       # FastAPI middleware
│   │   │   │   ├── auth.py       # Auth middleware
│   │   │   │   ├── security.py   # Security headers
│   │   │   │   ├── rate_limit.py # Rate limiting
│   │   │   │   └── monitoring.py # Request monitoring
│   │   │   ├── dependencies/     # Dependency injection
│   │   │   └── startup.py        # App initialization
│   │   │
│   │   └── main.py               # FastAPI app entry
│   │
│   ├── tests/                     # Test suite
│   │   ├── unit/                 # Unit tests
│   │   │   ├── core/            # Core logic tests
│   │   │   ├── api/             # API tests
│   │   │   └── infrastructure/  # Infra tests
│   │   ├── integration/          # Integration tests
│   │   │   ├── email_flow/      # E2E email tests
│   │   │   └── auth_flow/       # Auth flow tests
│   │   ├── fixtures/             # Test fixtures
│   │   └── conftest.py          # Pytest config
│   │
│   ├── scripts/                   # Utility scripts
│   │   ├── create_admin.py       # Admin creation
│   │   ├── migrate_db.py         # DB migrations
│   │   └── validate_config.py    # Config validation
│   │
│   ├── requirements/              # Python dependencies
│   │   ├── base.txt             # Core dependencies
│   │   ├── dev.txt              # Dev dependencies
│   │   └── prod.txt             # Prod dependencies
│   │
│   ├── Dockerfile                 # Backend container
│   ├── pyproject.toml           # Python project config
│   ├── setup.cfg                # Tool configurations
│   └── README.md                # Backend documentation
│
├── frontend/                      # All frontend code
│   ├── src/                      # Source code
│   │   ├── lib/                  # Library code
│   │   │   ├── api/             # API client
│   │   │   │   ├── client.ts    # API client class
│   │   │   │   ├── auth.ts      # Auth endpoints
│   │   │   │   └── types.ts     # API types
│   │   │   ├── components/       # Reusable components
│   │   │   │   ├── auth/        # Auth components
│   │   │   │   ├── dashboard/   # Dashboard widgets
│   │   │   │   ├── layout/      # Layout components
│   │   │   │   └── ui/          # UI primitives
│   │   │   ├── stores/          # State management
│   │   │   │   ├── auth.ts      # Auth store
│   │   │   │   ├── dashboard.ts # Dashboard store
│   │   │   │   └── theme.ts     # Theme store
│   │   │   └── utils/           # Utilities
│   │   │       ├── validators.ts # Form validators
│   │   │       └── formatters.ts # Data formatters
│   │   │
│   │   ├── routes/               # SvelteKit routes
│   │   │   ├── +layout.svelte   # Root layout
│   │   │   ├── +page.svelte     # Home page
│   │   │   ├── login/           # Login page
│   │   │   ├── dashboard/       # Dashboard
│   │   │   └── admin/           # Admin panel
│   │   │
│   │   ├── app.html             # HTML template
│   │   ├── app.css              # Global styles
│   │   └── app.d.ts             # Global types
│   │
│   ├── static/                   # Static assets
│   │   ├── images/              # Images
│   │   └── fonts/               # Fonts
│   │
│   ├── tests/                    # Frontend tests
│   │   ├── unit/                # Unit tests
│   │   ├── integration/         # Integration tests
│   │   └── e2e/                 # E2E tests
│   │
│   ├── package.json             # NPM dependencies
│   ├── tsconfig.json            # TypeScript config
│   ├── vite.config.ts           # Vite config
│   ├── svelte.config.js         # SvelteKit config
│   ├── tailwind.config.js       # Tailwind config
│   ├── Dockerfile               # Frontend container
│   └── README.md                # Frontend documentation
│
├── shared/                       # Shared code/types
│   ├── types/                   # TypeScript types
│   │   ├── api.ts              # API contracts
│   │   ├── models.ts           # Data models
│   │   └── enums.ts            # Shared enums
│   ├── constants/               # Shared constants
│   └── schemas/                 # JSON schemas
│
├── infrastructure/               # Infrastructure code
│   ├── terraform/               # Terraform configs
│   │   ├── environments/        # Per-env configs
│   │   │   ├── dev/           # Dev environment
│   │   │   ├── staging/       # Staging env
│   │   │   └── production/    # Prod env
│   │   └── modules/            # Reusable modules
│   ├── kubernetes/             # K8s manifests
│   │   ├── base/              # Base configs
│   │   └── overlays/          # Environment overlays
│   └── docker-compose/         # Docker compose files
│       ├── docker-compose.yml  # Base compose
│       └── docker-compose.dev.yml # Dev overrides
│
├── clients/                     # Client configurations
│   ├── active/                 # Active clients
│   │   └── {client-id}/       # Per-client config
│   │       ├── config.yaml    # Client settings
│   │       ├── routing.yaml   # Routing rules
│   │       ├── branding/      # Branding assets
│   │       └── templates/     # Email templates
│   └── templates/              # Client templates
│       └── default/           # Default template
│
├── docs/                        # Documentation
│   ├── architecture/           # Architecture docs
│   │   ├── overview.md        # System overview
│   │   ├── backend.md         # Backend architecture
│   │   ├── frontend.md        # Frontend architecture
│   │   └── deployment.md      # Deployment guide
│   ├── api/                   # API documentation
│   │   ├── authentication.md  # Auth docs
│   │   └── endpoints.md       # Endpoint reference
│   ├── development/           # Developer guides
│   │   ├── getting-started.md # Setup guide
│   │   ├── conventions.md     # Code conventions
│   │   └── testing.md         # Testing guide
│   └── operations/            # Ops documentation
│       ├── monitoring.md      # Monitoring setup
│       ├── troubleshooting.md # Common issues
│       └── runbooks/          # Operational runbooks
│
├── scripts/                    # Root-level scripts
│   ├── setup.sh               # Initial setup
│   ├── dev.sh                 # Development startup
│   └── deploy.sh              # Deployment script
│
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── docker-compose.yml         # Development compose
├── Makefile                   # Common commands
├── README.md                  # Project overview
└── LICENSE                    # License file
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Preparation & Safety (Week 1)

#### 1.1 Create Safety Checkpoints
**Objective:** Ensure we can rollback at any point

**Tasks:**
1. Create comprehensive backup branch
   ```bash
   git checkout -b reorganization/safety-backup
   git push origin reorganization/safety-backup
   ```

2. Document current working state
   - [ ] Run full test suite and document results
   - [ ] Test all API endpoints manually
   - [ ] Verify production deployment process
   - [ ] Create rollback documentation

3. Set up new branch structure
   ```bash
   git checkout -b reorganization/main
   git checkout -b reorganization/phase-1-structure
   ```

#### 1.2 Inventory & Analysis
**Objective:** Complete understanding of current codebase

**Tasks:**
1. Create detailed file mapping
   - [ ] Map every file to its new location
   - [ ] Identify deprecated/outdated files
   - [ ] Document all import dependencies
   - [ ] Identify shared code candidates

2. Dependency analysis
   - [ ] Map all import statements
   - [ ] Identify circular dependencies
   - [ ] Document external dependencies
   - [ ] Plan dependency migration

3. Configuration audit
   - [ ] List all config files and their purposes
   - [ ] Document all environment variables
   - [ ] Map configuration dependencies
   - [ ] Plan consolidation strategy

---

### Phase 2: Core Structure Creation (Week 1-2)

#### 2.1 Create New Directory Structure
**Objective:** Establish new project organization

**Tasks:**
1. Create backend structure
   ```bash
   mkdir -p backend/src/{api,core,infrastructure,application}
   mkdir -p backend/tests/{unit,integration,fixtures}
   mkdir -p backend/{scripts,requirements}
   ```

2. Create frontend structure
   ```bash
   mkdir -p frontend/src/{lib,routes}
   mkdir -p frontend/tests/{unit,integration,e2e}
   ```

3. Create shared structure
   ```bash
   mkdir -p shared/{types,constants,schemas}
   ```

4. Create infrastructure structure
   ```bash
   mkdir -p infrastructure/{terraform,kubernetes,docker-compose}
   ```

#### 2.2 Move Core Backend Files
**Objective:** Migrate backend code to new structure

**Migration Map:**
```
Current Location                    → New Location
app/main.py                        → backend/src/main.py
app/routers/                       → backend/src/api/v1/
app/services/ai_classifier.py      → backend/src/core/email/classifier.py
app/services/email_service.py      → backend/src/core/email/composer.py
app/services/routing_engine.py     → backend/src/core/email/router.py
app/services/email_sender.py       → backend/src/infrastructure/external/mailgun.py
app/services/client_manager.py     → backend/src/core/clients/manager.py
app/security/                      → backend/src/core/authentication/
app/database/                      → backend/src/infrastructure/database/
app/middleware/                    → backend/src/application/middleware/
app/models/                        → backend/src/core/models/
app/utils/config.py               → backend/src/infrastructure/config/manager.py
tests/                            → backend/tests/
scripts/                          → backend/scripts/
```

**Implementation Steps:**
1. Move files maintaining git history
   ```bash
   git mv app/main.py backend/src/main.py
   # Continue for all files...
   ```

2. Update all import statements
   - [ ] Create import mapping script
   - [ ] Run automated import updates
   - [ ] Manual verification of imports
   - [ ] Update relative imports

3. Update configuration paths
   - [ ] Update file path references
   - [ ] Update client config paths
   - [ ] Update test fixtures paths

---

### Phase 3: Frontend Separation (Week 2)

#### 3.1 Extract Frontend Code
**Objective:** Separate frontend into its own application

**Tasks:**
1. Move UI files to frontend directory
   ```bash
   git mv ui/* frontend/
   ```

2. Clean up frontend structure
   - [ ] Remove node_modules from git
   - [ ] Update .gitignore
   - [ ] Organize components by domain
   - [ ] Extract shared types

3. Update frontend configuration
   - [ ] Update import paths
   - [ ] Configure API endpoint URLs
   - [ ] Update build configuration
   - [ ] Set up environment variables

#### 3.2 Create Shared Types
**Objective:** Establish type sharing between frontend and backend

**Tasks:**
1. Extract common types
   - [ ] API request/response types
   - [ ] Data model interfaces
   - [ ] Enum definitions
   - [ ] Validation schemas

2. Set up type generation
   - [ ] Install type generation tools
   - [ ] Create generation scripts
   - [ ] Set up CI/CD for type sync
   - [ ] Document type sharing process

---

### Phase 4: Configuration Consolidation (Week 2-3)

#### 4.1 Unify Configuration System
**Objective:** Single source of truth for configuration

**Current Issues:**
- 4 separate config files with overlapping responsibilities
- No clear configuration hierarchy
- Missing validation

**Target Structure:**
```
backend/src/infrastructure/config/
├── manager.py         # Main configuration manager
├── schema.py         # All configuration schemas
├── validator.py      # Configuration validation
├── loaders/          # Environment-specific loaders
│   ├── env.py       # Environment variable loader
│   ├── yaml.py      # YAML file loader
│   └── vault.py     # Secret management loader
└── defaults.py       # Default configurations
```

**Implementation:**
1. Consolidate configuration files
   - [ ] Merge all config schemas
   - [ ] Create unified config manager
   - [ ] Implement validation layer
   - [ ] Add configuration tests

2. Update all config references
   - [ ] Update service dependencies
   - [ ] Update middleware config
   - [ ] Update test configurations
   - [ ] Document configuration system

---

### Phase 5: Dependency Cleanup (Week 3)

#### 5.1 Backend Dependency Management
**Objective:** Clean, organized dependency management

**Tasks:**
1. Split requirements by environment
   ```
   backend/requirements/
   ├── base.txt      # Core dependencies
   ├── dev.txt       # Development only
   └── prod.txt      # Production optimized
   ```

2. Remove unused dependencies
   - [ ] Audit current requirements.txt
   - [ ] Remove unused packages
   - [ ] Update to latest versions
   - [ ] Add security scanning

3. Implement dependency injection properly
   - [ ] Create DI container
   - [ ] Update service registration
   - [ ] Remove circular dependencies
   - [ ] Document DI patterns

#### 5.2 Frontend Dependency Management
**Objective:** Optimize frontend dependencies

**Tasks:**
1. Audit package.json
   - [ ] Remove unused packages
   - [ ] Update to latest versions
   - [ ] Separate dev dependencies
   - [ ] Add security scanning

2. Optimize bundle size
   - [ ] Analyze bundle composition
   - [ ] Implement code splitting
   - [ ] Remove duplicate dependencies
   - [ ] Add bundle size monitoring

---

### Phase 6: Testing Infrastructure (Week 3-4)

#### 6.1 Reorganize Test Suite
**Objective:** Fast, reliable, organized tests

**Target Structure:**
```
backend/tests/
├── unit/                  # Fast, isolated tests
│   ├── core/             # Business logic tests
│   ├── api/              # API endpoint tests
│   └── infrastructure/   # Infrastructure tests
├── integration/          # Integration tests
│   ├── email_flow/       # Email processing tests
│   ├── auth_flow/        # Authentication tests
│   └── client_flow/      # Client management tests
├── fixtures/             # Shared test data
│   ├── auth.py          # Auth fixtures
│   ├── clients.py       # Client fixtures
│   └── emails.py        # Email fixtures
└── conftest.py          # Pytest configuration
```

**Implementation:**
1. Separate unit and integration tests
   - [ ] Move tests to appropriate directories
   - [ ] Update test imports
   - [ ] Configure test runners
   - [ ] Update CI/CD pipelines

2. Fix test infrastructure issues
   - [ ] Implement proper mocking
   - [ ] Fix environment dependencies
   - [ ] Add database fixtures
   - [ ] Speed up test execution

---

### Phase 7: Documentation & Cleanup (Week 4)

#### 7.1 Update Documentation
**Objective:** Comprehensive, current documentation

**Tasks:**
1. Architecture documentation
   - [ ] Document new structure
   - [ ] Create architecture diagrams
   - [ ] Document design decisions
   - [ ] Add ADRs for major changes

2. Developer documentation
   - [ ] Update getting started guide
   - [ ] Document new workflows
   - [ ] Create troubleshooting guide
   - [ ] Add code examples

3. API documentation
   - [ ] Update OpenAPI specs
   - [ ] Document authentication
   - [ ] Add request/response examples
   - [ ] Create Postman collection

#### 7.2 Final Cleanup
**Objective:** Remove all legacy code and organize

**Tasks:**
1. Remove deprecated files
   - [ ] Delete old configuration files
   - [ ] Remove unused modules
   - [ ] Clean up old documentation
   - [ ] Remove commented code

2. Optimize repository
   - [ ] Run git garbage collection
   - [ ] Update .gitignore
   - [ ] Add pre-commit hooks
   - [ ] Configure linters

---

## 🛡️ Risk Mitigation Strategy

### Critical Risks & Mitigations

#### 1. Import Path Breaking
**Risk:** Changing file locations breaks all imports
**Mitigation:**
- Automated import update script
- Gradual migration with compatibility layers
- Comprehensive import mapping documentation
- Automated testing after each move

#### 2. Configuration Breaking
**Risk:** Consolidating configs breaks deployment
**Mitigation:**
- Backward compatibility layer
- Environment variable mapping
- Staged rollout with testing
- Rollback plan for each environment

#### 3. Test Suite Failure
**Risk:** Tests fail after reorganization
**Mitigation:**
- Fix tests incrementally during migration
- Maintain test coverage metrics
- Parallel test execution during migration
- Document all test changes

#### 4. Deployment Pipeline Breaking
**Risk:** CI/CD fails with new structure
**Mitigation:**
- Update pipelines incrementally
- Test in staging environment first
- Maintain old and new pipelines temporarily
- Document all pipeline changes

### Rollback Procedures

#### Immediate Rollback
```bash
# If critical failure at any point
git checkout reorganization/safety-backup
git push --force origin main
```

#### Partial Rollback
```bash
# Rollback specific phase
git checkout reorganization/phase-X-complete
git cherry-pick <specific-fixes>
```

#### Configuration Rollback
```bash
# Restore old configuration
cp backup/.env.backup .env
cp -r backup/clients/ clients/
```

---

## 📊 Success Metrics

### Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Directory Depth | 5+ levels | 3-4 levels | `find . -type d | awk -F/ '{print NF}' | sort -n | tail -1` |
| Import Complexity | High | Low | Custom script to analyze imports |
| Test Execution Time | Unknown | <30s | `time pytest` |
| Build Time | Unknown | <2min | `time npm run build` |
| Deploy Time | Unknown | <5min | CI/CD metrics |
| Code Duplication | Unknown | <5% | Code analysis tools |
| Type Coverage | ~70% | 95%+ | `mypy --strict` |

### Qualitative Metrics

#### Developer Experience
- [ ] Clear separation of concerns
- [ ] Intuitive file organization  
- [ ] Easy to find code
- [ ] Consistent patterns
- [ ] Fast development cycle

#### Maintainability
- [ ] Easy to add new features
- [ ] Clear dependency graph
- [ ] Modular architecture
- [ ] Comprehensive documentation
- [ ] Easy onboarding

#### Scalability
- [ ] Ready for microservices split
- [ ] Horizontal scaling capability
- [ ] Performance optimization ready
- [ ] Cloud-native architecture
- [ ] Multi-region ready

---

## 🚀 Implementation Guidelines

### Week-by-Week Schedule

#### Week 1: Foundation
- Days 1-2: Safety setup and inventory
- Days 3-5: Core structure creation
- Day 5: Checkpoint and validation

#### Week 2: Migration
- Days 1-3: Backend migration
- Days 4-5: Frontend separation
- Day 5: Integration testing

#### Week 3: Consolidation  
- Days 1-2: Configuration consolidation
- Days 3-4: Dependency cleanup
- Day 5: Testing infrastructure

#### Week 4: Polish
- Days 1-2: Documentation update
- Days 3-4: Final cleanup
- Day 5: Final validation and launch

### Daily Workflow

#### Morning
1. Review plan for the day
2. Create feature branch
3. Run tests to ensure starting state
4. Begin scheduled work

#### During Development
1. Commit frequently with clear messages
2. Run tests after major changes
3. Update documentation as you go
4. Track progress in project board

#### End of Day
1. Push all changes
2. Run full test suite
3. Update progress tracking
4. Note any blockers or issues

### Communication Plan

#### Daily Standup Addition
- What reorganization work was completed
- What is planned for today
- Any blockers or concerns
- Help needed from team

#### Weekly Progress Report
- Completed milestones
- Current status vs plan
- Risks and mitigations
- Next week's goals

#### Phase Completion Review
- Demo of new structure
- Performance comparisons
- Team feedback session
- Go/no-go for next phase

---

## 🎯 Expected Outcomes

### Immediate Benefits
1. **Clear code organization** - Easy to navigate and understand
2. **Faster development** - Clear patterns and structure
3. **Better testing** - Organized, fast test suite
4. **Improved deployment** - Separate frontend/backend deploys
5. **Enhanced security** - Clear boundaries and isolation

### Long-term Benefits
1. **Microservices ready** - Easy to extract services
2. **Team scalability** - Multiple teams can work independently
3. **Technology flexibility** - Can change frontend/backend independently
4. **Performance optimization** - Clear optimization points
5. **Cost optimization** - Efficient resource usage

### Business Impact
1. **Faster feature delivery** - Improved developer productivity
2. **Higher quality** - Better testing and organization
3. **Reduced bugs** - Clear separation of concerns
4. **Easier maintenance** - Well-organized codebase
5. **Better scalability** - Ready for growth

---

## 📋 Checklist for Completion

### Phase Completion Criteria

#### ✅ Phase 1: Preparation
- [ ] Safety backup created and tested
- [ ] Complete file inventory documented
- [ ] Dependency map created
- [ ] Team briefed on plan

#### ✅ Phase 2: Core Structure  
- [ ] Directory structure created
- [ ] Backend files migrated
- [ ] Imports updated and working
- [ ] Tests passing

#### ✅ Phase 3: Frontend Separation
- [ ] Frontend extracted to separate app
- [ ] Shared types established
- [ ] Build process working
- [ ] Frontend tests passing

#### ✅ Phase 4: Configuration
- [ ] Configuration consolidated
- [ ] Environment variables documented
- [ ] Validation implemented
- [ ] Configuration tests passing

#### ✅ Phase 5: Dependencies
- [ ] Requirements split by environment
- [ ] Unused dependencies removed
- [ ] DI patterns implemented
- [ ] No circular dependencies

#### ✅ Phase 6: Testing
- [ ] Tests reorganized
- [ ] Test execution <30s
- [ ] Coverage maintained
- [ ] CI/CD updated

#### ✅ Phase 7: Documentation
- [ ] Architecture documented
- [ ] Developer guides updated
- [ ] API docs current
- [ ] Deployment docs updated

### Final Validation
- [ ] All tests passing
- [ ] Deployment successful
- [ ] Performance benchmarks met
- [ ] Team sign-off received
- [ ] Documentation complete

---

## 🔚 Conclusion

This reorganization plan transforms the email-router codebase from its current monolithic structure into a modern, scalable architecture. The systematic approach ensures minimal risk while delivering significant improvements in developer experience, maintainability, and scalability.

The new structure provides:
- **Clear separation** between frontend, backend, and shared code
- **Domain-driven organization** within each application
- **Professional tooling** and development experience
- **Scalable architecture** ready for future growth
- **Comprehensive documentation** and testing

With careful execution of this plan, the email-router will be positioned for long-term success and easy maintenance.

---

**Document End**  
*This master reorganization plan serves as the single source of truth for the codebase restructuring effort. All reorganization activities should reference this document.*