# Email Router Developer Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Testing](#testing)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git
- Docker (optional, for containerized development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd email-router-core
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements/dev.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run database migrations**
   ```bash
   cd ../backend
   alembic upgrade head
   ```

6. **Create admin user**
   ```bash
   python scripts/simple_create_admin.py
   ```

7. **Start development servers**
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn src.main:app --reload --port 8080

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

## Development Environment

### Required Environment Variables

```bash
# Authentication
JWT_SECRET_KEY=your-secret-key-minimum-32-characters

# External Services
ANTHROPIC_API_KEY=sk-ant-api03-...
MAILGUN_API_KEY=your-mailgun-key
MAILGUN_DOMAIN=your-domain.com
MAILGUN_WEBHOOK_SIGNING_KEY=webhook-signing-key

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Environment
EMAIL_ROUTER_ENVIRONMENT=development
```

### VS Code Setup

Recommended extensions:
- Python
- Pylance
- Black Formatter
- Svelte for VS Code
- Tailwind CSS IntelliSense

### Docker Development

```bash
# Start all services
docker-compose up

# Run with specific services
docker-compose up backend frontend

# Run tests in container
docker-compose run backend pytest
```

## Project Structure

```
email-router-core/
├── backend/                 # FastAPI backend
│   ├── src/                # Source code
│   │   ├── api/           # API endpoints
│   │   ├── application/   # Middleware & dependencies
│   │   ├── core/          # Business logic
│   │   └── infrastructure/# External services
│   ├── tests/             # Test suite
│   └── requirements/      # Dependency files
├── frontend/               # SvelteKit frontend
│   ├── src/               # Source code
│   │   ├── lib/          # Components & utilities
│   │   └── routes/       # Page routes
│   └── tests/            # Frontend tests
├── shared/                # Shared types & schemas
├── clients/              # Client configurations
├── docs/                 # Documentation
└── infrastructure/       # Deployment configs
```

## Backend Development

### Adding a New API Endpoint

1. **Create the route handler** in `backend/src/api/v1/`
   ```python
   from fastapi import APIRouter, Depends
   from typing import List

   from application.dependencies.auth import get_current_user
   from core.models.schemas import YourSchema

   router = APIRouter(prefix="/your-endpoint", tags=["your-tag"])

   @router.get("/", response_model=List[YourSchema])
   async def get_items(
       current_user: User = Depends(get_current_user),
       service: YourService = Depends(get_your_service)
   ):
       return service.get_items_for_user(current_user)
   ```

2. **Register the router** in `backend/src/api/v1/__init__.py`
   ```python
   from .your_endpoint import router as your_router

   api_router.include_router(your_router)
   ```

3. **Add tests** in `backend/tests/integration/`

### Creating a New Service

1. **Define the service** in `backend/src/core/`
   ```python
   from typing import Optional
   from infrastructure.database.models import YourModel

   class YourService:
       def __init__(self, config_manager: ConfigManager):
           self.config_manager = config_manager

       def process_item(self, item_id: str) -> Optional[YourModel]:
           # Business logic here
           pass
   ```

2. **Create dependency injection** in `backend/src/application/dependencies/`
   ```python
   from functools import lru_cache
   from core.your_module import YourService

   @lru_cache()
   def get_your_service() -> YourService:
       return YourService(get_config_manager())
   ```

### Working with the Database

1. **Create a new model** in `backend/src/infrastructure/database/models.py`
   ```python
   from sqlalchemy import Column, String, Integer, ForeignKey
   from .base import Base

   class YourModel(Base):
       __tablename__ = "your_table"

       id = Column(Integer, primary_key=True)
       name = Column(String(255), nullable=False)
       client_id = Column(String(50), ForeignKey("clients.id"))
   ```

2. **Create a migration**
   ```bash
   cd backend
   alembic revision -m "Add your_table"
   # Edit the generated migration file
   alembic upgrade head
   ```

### Authentication & Authorization

**Protecting an endpoint with JWT:**
```python
from fastapi import Depends
from application.dependencies.auth import get_current_user
from infrastructure.database.models import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user.username}
```

**Requiring specific permissions:**
```python
from application.dependencies.auth import require_permission

@router.post("/admin-only")
async def admin_route(
    current_user: User = Depends(require_permission("system:admin"))
):
    return {"message": "Admin access granted"}
```

## Frontend Development

### Creating a New Component

1. **Create component file** in `frontend/src/lib/components/`
   ```svelte
   <!-- YourComponent.svelte -->
   <script lang="ts">
     export let title: string;
     export let onClick: () => void = () => {};
   </script>

   <div class="component-wrapper">
     <h2>{title}</h2>
     <button on:click={onClick}>Click me</button>
   </div>

   <style>
     .component-wrapper {
       @apply p-4 rounded-lg bg-white shadow-md;
     }
   </style>
   ```

2. **Use in a page** in `frontend/src/routes/`
   ```svelte
   <script lang="ts">
     import YourComponent from '$lib/components/YourComponent.svelte';
   </script>

   <YourComponent title="Hello" on:click={() => console.log('Clicked')} />
   ```

### Working with Stores

1. **Create a store** in `frontend/src/lib/stores/`
   ```typescript
   import { writable, derived } from 'svelte/store';

   export const items = writable<Item[]>([]);

   export const itemCount = derived(items, $items => $items.length);

   export function addItem(item: Item) {
     items.update(list => [...list, item]);
   }
   ```

2. **Use in components**
   ```svelte
   <script lang="ts">
     import { items, itemCount, addItem } from '$lib/stores/items';
   </script>

   <p>Total items: {$itemCount}</p>
   {#each $items as item}
     <div>{item.name}</div>
   {/each}
   ```

### API Integration

```typescript
// frontend/src/lib/api/client.ts
import { authStore } from '$lib/stores/auth';
import { get } from 'svelte/store';

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const auth = get(authStore);
  const headers = {
    'Content-Type': 'application/json',
    ...(auth.token && { Authorization: `Bearer ${auth.token}` }),
    ...options.headers,
  };

  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}
```

## Testing

### Backend Testing

**Running tests:**
```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_jwt_service.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

**Writing unit tests:**
```python
import pytest
from core.your_module import YourService

class TestYourService:
    def test_process_item_success(self):
        service = YourService(mock_config)
        result = service.process_item("test-id")
        assert result is not None
        assert result.status == "processed"

    def test_process_item_not_found(self):
        service = YourService(mock_config)
        result = service.process_item("invalid-id")
        assert result is None
```

**Writing integration tests:**
```python
import pytest
from fastapi.testclient import TestClient

def test_endpoint_success(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/items", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
```

### Frontend Testing

```bash
cd frontend

# Run unit tests
npm run test:unit

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e
```

## Common Tasks

### Adding a New Client

1. **Create client directory**
   ```bash
   mkdir -p clients/active/client-002-company
   ```

2. **Copy template files**
   ```bash
   cp -r clients/templates/default/* clients/active/client-002-company/
   ```

3. **Update configuration**
   - Edit `client-config.yaml` with client details
   - Update `routing-rules.yaml` with email routes
   - Customize `categories.yaml` as needed

### Updating Dependencies

**Backend:**
```bash
cd backend
# Update base dependencies
pip-compile requirements/base.in

# Update dev dependencies
pip-compile requirements/dev.in

# Install updated dependencies
pip install -r requirements/dev.txt
```

**Frontend:**
```bash
cd frontend
# Update dependencies
npm update

# Check for outdated packages
npm outdated

# Update specific package
npm install package-name@latest
```

### Database Operations

**Create a backup:**
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Reset database:**
```bash
cd backend
alembic downgrade base
alembic upgrade head
python scripts/seed_database.py  # If available
```

### Debugging

**Backend debugging:**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json:
{
  "name": "FastAPI",
  "type": "python",
  "request": "launch",
  "module": "uvicorn",
  "args": ["src.main:app", "--reload", "--port", "8080"],
  "cwd": "${workspaceFolder}/backend"
}
```

**Frontend debugging:**
- Use browser DevTools
- Add `console.log()` statements
- Use Svelte DevTools extension

## Troubleshooting

### Common Issues

**Import errors:**
- Ensure you're in the correct directory
- Check PYTHONPATH includes `backend/src`
- Verify all dependencies are installed

**Database connection errors:**
- Check DATABASE_URL is set correctly
- Ensure database server is running
- Verify migrations are up to date

**Authentication failures:**
- Check JWT_SECRET_KEY is set
- Verify token hasn't expired
- Ensure user has required permissions

**Frontend build errors:**
- Clear node_modules and reinstall
- Check for TypeScript errors
- Verify API endpoint URLs

### Performance Issues

**Backend optimization:**
- Use database query optimization
- Implement caching where appropriate
- Profile with `cProfile` or `py-spy`

**Frontend optimization:**
- Lazy load components
- Optimize bundle size
- Use production builds for testing

### Getting Help

1. Check existing documentation
2. Search through codebase for examples
3. Review test files for usage patterns
4. Check logs for detailed error messages

## Best Practices

1. **Write tests first** - TDD helps ensure code quality
2. **Use type hints** - Both Python and TypeScript
3. **Follow conventions** - Consistent naming and structure
4. **Document complex logic** - Comments for "why", not "what"
5. **Keep commits atomic** - One feature/fix per commit
6. **Review before pushing** - Self-review catches many issues
