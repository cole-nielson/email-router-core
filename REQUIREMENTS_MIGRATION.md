# Requirements Migration Notice

## ⚠️ Important: Requirements Structure Has Changed

The project's dependency management has been reorganized for better environment separation.

### Old Structure (Deprecated)
```
requirements.txt  # Mixed all dependencies together
```

### New Structure
```
backend/requirements/
├── base.txt      # Core dependencies (all environments)
├── dev.txt       # Development dependencies
├── test.txt      # Testing dependencies
├── prod.txt      # Production dependencies
└── README.md     # Detailed documentation
```

## Migration Steps

### For Local Development
```bash
# Old way (deprecated)
pip install -r requirements.txt

# New way
pip install -r backend/requirements/dev.txt
```

### For Testing
```bash
pip install -r backend/requirements/test.txt
```

### For Production Deployment
```bash
pip install -r backend/requirements/prod.txt
```

### For Docker Builds
The Dockerfile has been updated to use `backend/requirements/prod.txt`.

### For CI/CD
GitHub Actions workflows have been updated to use the appropriate requirements files.

## Benefits of New Structure

1. **Smaller production images** - Only necessary dependencies in production
2. **Faster CI builds** - Test dependencies separate from dev tools
3. **Better security** - Production doesn't include development tools
4. **Clearer dependencies** - Easy to see what's needed where
5. **Easier maintenance** - Update dependencies by environment

## Need Help?

- See `backend/requirements/README.md` for detailed documentation
- Run `./scripts/migrate_to_new_requirements.sh` for a quick guide
- The old `requirements.txt` is preserved as `requirements.txt.deprecated`
