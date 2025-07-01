# Known Test Issues

This document tracks test failures that are expected due to business logic changes, integration dependencies, or architectural issues that require broader refactoring beyond the scope of repository cleanup.

## Test Failures by Category

### 1. Integration / External Dependencies
These tests require external services or complex integration setup:

#### Integration Pipeline Tests
- **Issue**: Tests expect full email processing pipeline with external AI/email services
- **Status**: Business logic changes needed
- **Files**: `tests/test_integration_pipeline.py`

### 2. Business Logic Evolution
These tests reflect outdated business logic or changed requirements:

#### Template Engine Tests
- **Issue**: Template branding logic has evolved, test assertions are outdated
- **Status**: Business logic changes needed
- **Files**: `tests/test_enhanced_templates.py`

### 3. Mock/Fixture Setup Issues
These are fixable test infrastructure issues:

#### Dual Auth Middleware Tests
- **Issue**: Middleware constructor requires app parameter in tests
- **Status**: Fixable via test updates
- **Files**: `tests/test_dual_auth_middleware.py`

### 4. JWT Token Management Tests
These tests may require database state or session management:

#### JWT Service Tests
- **Issue**: Token validation tests expect specific database session state
- **Status**: May need test fixture improvements
- **Files**: `tests/test_jwt_service.py`

---

## Tracking

**Last Updated**: June 18, 2025
**Total Known Issues**: 20 test failures
**Fixable via Tests**: ~5 issues
**Business Logic Related**: ~15 issues
