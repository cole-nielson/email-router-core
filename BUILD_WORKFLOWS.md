# Build Workflows & Repository Hygiene

## Separate Build Systems

This repository maintains clean separation between frontend and backend build processes:

### Backend (Python/FastAPI)
```bash
# Development
python -m uvicorn app.main:app --reload --port 8080

# Production
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Testing
python -m pytest tests/ -v

# Code Quality
black app/ tests/
isort app/ tests/
mypy app/
```

### Frontend (SvelteKit)
```bash
cd ui/
npm install
npm run dev       # Development server
npm run build     # Production build
npm run check     # Type checking
npm run lint      # ESLint
```

## Repository Hygiene Rules

### ✅ What to Commit
- Source code (.py, .ts, .svelte, .md)
- Configuration files (package.json, requirements.txt, .yaml)
- Documentation and README files
- Essential static assets

### ❌ What NOT to Commit
- Build artifacts (ui/.svelte-kit/, ui/build/, ui/dist/)
- Dependencies (ui/node_modules/, __pycache__/)
- Environment files (.env, .env.local)
- IDE settings (.vscode/settings.json, .idea/)
- Log files (*.log)
- Database files (*.db)

## Pre-commit Hooks

Automated checks run before each commit:
- **Python**: Black formatting, isort imports, MyPy type checking
- **Security**: Bandit security scanning
- **Frontend**: ESLint for TypeScript/Svelte files
- **General**: Trailing whitespace, large files, merge conflicts
- **Build Artifacts**: Prevents committing ui/build artifacts

Install hooks:
```bash
pre-commit install
```

## Build Artifact Management

### Current Status
- ✅ ui/node_modules/ properly ignored
- ✅ ui/.svelte-kit/ removed from git tracking
- ✅ Comprehensive .gitignore patterns
- ✅ Pre-commit hooks prevent future artifacts

### Repository Size Reduction
- **Before**: 17,741 files in ui/ (208MB)
- **After**: ~20 source files tracked (<1MB)
- **Savings**: 99.5% reduction in tracked frontend files

## Deployment Strategies

### Backend Deployment
```dockerfile
# Dockerfile for backend-only deployment
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Frontend Deployment
```bash
# Build for static hosting
cd ui/
npm run build
# Deploy ui/build/ to static hosting (Vercel, Netlify, etc.)
```

### Full-Stack Deployment
```bash
# 1. Build frontend
cd ui/ && npm run build

# 2. Copy build to backend static directory
cp -r ui/build/* app/static/

# 3. Deploy backend with static files
docker build -t email-router .
```

## Development Workflow

### For Backend Changes
```bash
# 1. Create feature branch
git checkout -b feature/backend-improvement

# 2. Make changes to app/
# 3. Run tests
python -m pytest tests/ -v

# 4. Check code quality
black app/ tests/
mypy app/

# 5. Commit and push
git add app/ tests/
git commit -m "feat: add new feature"
git push origin feature/backend-improvement
```

### For Frontend Changes
```bash
# 1. Create feature branch
git checkout -b feature/ui-improvement

# 2. Work in ui/ directory
cd ui/
npm run dev

# 3. Test changes
npm run check
npm run lint

# 4. Commit only source files
cd ..
git add ui/src/ ui/package.json  # Only source files
git commit -m "feat: improve UI component"
git push origin feature/ui-improvement
```

## Monitoring Repository Health

### Check for accidentally committed artifacts:
```bash
# Find large files in git history
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | \
  sort --numeric-sort --key=2 | \
  tail -20

# Check current repository size
git count-objects -vH
```

### Cleanup commands if needed:
```bash
# Remove build artifacts from git history (USE WITH CAUTION)
git filter-branch --index-filter 'git rm --cached --ignore-unmatch ui/.svelte-kit/' --prune-empty --tag-name-filter cat -- --all

# Force garbage collection
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```
