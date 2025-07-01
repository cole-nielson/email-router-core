# Email Router Backend

FastAPI-based backend service for the Email Router application.

## Project Structure

```
backend/
├── src/                           # Source code
│   ├── api/                      # API layer
│   │   ├── v1/                   # Version 1 endpoints
│   │   └── v2/                   # Version 2 endpoints
│   ├── core/                     # Core business logic
│   │   ├── authentication/       # Auth logic
│   │   ├── clients/             # Client management
│   │   ├── email/               # Email processing
│   │   └── models/              # Domain models
│   ├── infrastructure/           # External integrations
│   │   ├── config/              # Configuration
│   │   ├── database/            # Database layer
│   │   ├── external/            # External services
│   │   └── monitoring/          # Monitoring
│   └── application/             # Application layer
│       ├── middleware/          # FastAPI middleware
│       └── dependencies/        # Dependency injection
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
└── requirements/                 # Dependencies
```

## Development

### Setup

```bash
# Install dependencies
pip install -e .[dev]

# Set up pre-commit hooks
pre-commit install

# Create .env file
cp .env.example .env
```

### Running

```bash
# Development server
uvicorn src.main:app --reload

# Production server
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_auth.py
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
ruff src/ tests/
```