# Backend Requirements Management

This directory contains environment-specific Python dependencies for the Email Router backend service.

## Structure

- **base.txt** - Core dependencies required in all environments
- **dev.txt** - Development-only dependencies (includes base.txt)
- **test.txt** - Testing dependencies (includes base.txt)
- **prod.txt** - Production-optimized dependencies (includes base.txt)

## Usage

### Development Environment
```bash
pip install -r backend/requirements/dev.txt
```

### Testing Environment
```bash
pip install -r backend/requirements/test.txt
```

### Production Environment
```bash
pip install -r backend/requirements/prod.txt
```

### Docker
In your Dockerfile:
```dockerfile
# For production
COPY backend/requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# For development
COPY backend/requirements/dev.txt /app/requirements.txt
RUN pip install -r requirements.txt
```

## Dependency Management

### Adding New Dependencies

1. **Core functionality** → Add to `base.txt`
2. **Development tools** → Add to `dev.txt`
3. **Testing tools** → Add to `test.txt`
4. **Production monitoring/optimization** → Add to `prod.txt`

### Security Scanning

Run security checks on dependencies:
```bash
pip install safety
safety check -r backend/requirements/prod.txt
```

### Updating Dependencies

Update all dependencies to latest compatible versions:
```bash
pip install pip-tools
pip-compile --upgrade backend/requirements/base.txt
```

## Version Pinning

All dependencies are pinned to specific versions for reproducibility. Update versions carefully and test thoroughly before deploying.
