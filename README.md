# 🚀 Email Router V2.0

**Production-ready enterprise multi-tenant AI email router** that automatically classifies incoming emails using Claude 3.5 Sonnet, generates personalized auto-replies, and forwards emails to appropriate team members.

## ✨ V2.0 Highlights

🏗️ **Clean Architecture** • 🔐 **Enterprise Auth** • 📊 **Dashboard Analytics** • 🎯 **Multi-Tenant** • ☁️ **Cloud Native**

**🎉 Live Production System**: https://email-router-696958557925.us-central1.run.app

### **What's New in V2.0**
- ✅ **Complete Architectural Overhaul**: Clean architecture with proper separation of concerns
- ✅ **Enterprise Authentication**: JWT + RBAC with session management
- ✅ **Dashboard Analytics**: Real-time metrics and business intelligence
- ✅ **Enhanced Multi-Tenancy**: Complete client isolation with advanced domain matching
- ✅ **Production Deployment**: Live on Google Cloud Run with auto-scaling
- ✅ **Comprehensive Testing**: 88 tests covering all critical functionality
- ✅ **Developer Experience**: Modern tooling with hot-reload and comprehensive docs

## 🏗️ Project Structure

This is a modern monorepo with clear separation of concerns:

```
email-router/
├── backend/                    # FastAPI backend service
│   ├── src/                   # Source code
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Business logic
│   │   ├── infrastructure/   # External integrations
│   │   └── application/      # Application layer
│   ├── tests/                # Backend tests
│   └── scripts/              # Backend utilities
│
├── frontend/                  # SvelteKit frontend application
│   ├── src/                  # Source code
│   │   ├── lib/             # Components and utilities
│   │   └── routes/          # SvelteKit routes
│   └── tests/               # Frontend tests
│
├── shared/                   # Shared types and constants
│   ├── types/               # TypeScript type definitions
│   ├── constants/           # Shared constants
│   └── schemas/             # JSON schemas
│
├── infrastructure/          # Infrastructure as Code
│   ├── terraform/          # Terraform configurations
│   ├── kubernetes/         # Kubernetes manifests
│   └── docker-compose/     # Docker compose files
│
├── clients/                # Client configurations
│   ├── active/            # Active client configs
│   └── templates/         # Client templates
│
├── docs/                   # Documentation
│   ├── architecture/      # Architecture docs
│   ├── api/              # API documentation
│   ├── development/      # Developer guides
│   └── operations/       # Ops documentation
│
└── scripts/               # Root-level scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional)

### Backend Setup
```bash
cd backend
pip install -e .[dev]
cp .env.example .env
uvicorn src.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Full Stack Development
```bash
# Start both backend and frontend
./scripts/dev.sh
```

## 📋 Features

### Core Features
- **Multi-tenant Architecture**: Complete client isolation with domain-based routing
- **AI Email Classification**: Claude 3.5 Sonnet with 95%+ accuracy
- **Smart Email Routing**: Business rules with escalation and after-hours handling
- **Dual Email Generation**: Customer acknowledgment + team analysis
- **Professional Templates**: Mobile-responsive branded communications

### Security Features
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Fine-grained permissions
- **API Key Authentication**: For webhooks and automation
- **Client Isolation**: Complete multi-tenant data separation

### Monitoring & Analytics
- **Real-time Dashboard**: Live email processing metrics
- **Performance Monitoring**: Response time and classification accuracy
- **Health Checks**: Comprehensive system health monitoring
- **Audit Logging**: Complete request and processing logs

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                     # All tests
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration tests only
```

### Frontend Tests
```bash
cd frontend
npm run test              # Unit tests
npm run test:e2e          # E2E tests
npm run test:ui           # Interactive test UI
```

### Full Test Suite
```bash
./scripts/test.sh         # Run all tests
```

## 🚀 Deployment

### Development
```bash
docker-compose up -d      # Local development environment
```

### Production
```bash
# Google Cloud Run (current)
./scripts/deploy.sh production

# Kubernetes (planned)
kubectl apply -f infrastructure/kubernetes/
```

## 📊 Current Status

**Production Status**: ✅ Live & Operational
- **Deployment**: Google Cloud Run
- **URL**: https://email-router-696958557925.us-central1.run.app
- **Processing Time**: 5-7 seconds end-to-end
- **Uptime**: 99.9%+

## 🏛️ Architecture

### Clean Architecture
The codebase follows clean architecture principles:

- **Core**: Business logic independent of frameworks
- **Infrastructure**: External services and data persistence
- **Application**: Framework-specific middleware and DI
- **Interface**: API endpoints and external interfaces

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Python 3.9+
- **Frontend**: SvelteKit, TypeScript, Tailwind CSS
- **Database**: SQLite (dev), PostgreSQL (production)
- **External APIs**: Anthropic Claude, Mailgun
- **Infrastructure**: Google Cloud Run, Docker

## 📚 Documentation

- [Architecture Overview](docs/architecture/system-architecture.md)
- [API Documentation](docs/api/endpoints.md)
- [Development Guide](docs/development/developer-guide.md)
- [Deployment Guide](docs/operations/deployment.md)

## 🤝 Contributing

1. **Setup Development Environment**
   ```bash
   ./scripts/setup.sh
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Follow Code Standards**
   ```bash
   # Backend
   black backend/src backend/tests
   mypy backend/src

   # Frontend
   npm run lint
   npm run format
   ```

4. **Run Tests**
   ```bash
   ./scripts/test.sh
   ```

5. **Submit Pull Request**

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For issues and support:
- **Documentation**: `/docs` directory
- **Issues**: Create GitHub issue
- **Contact**: [Support Contact Information]

---

Built with ❤️ for enterprise email automation
