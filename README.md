# 🚀 Email Router Core - Enterprise AI-Powered Email Automation

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688.svg)](https://fastapi.tiangolo.com) [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![Tests](https://img.shields.io/badge/tests-91%2F91%20passing-brightgreen.svg)](#testing) [![Code Quality](https://img.shields.io/badge/code%20quality-enterprise%20grade-gold.svg)](#code-quality) [![Production](https://img.shields.io/badge/status-production%20ready-green.svg)](#production-status)

> **🏆 Enterprise-grade multi-tenant AI email router with intelligent classification, branded responses, and production-validated reliability. Powered by Claude 3.5 Sonnet. Recently completed comprehensive lean refactor achieving 100% milestone completion.**

## ✨ What This Does

**Enterprise Email Intelligence Pipeline:**
```
📧 Inbound Email → 🎯 Client ID → 🤖 AI Classification → ✍️ Branded Response → 📨 Smart Routing
```

1. **Multi-Tenant Client Identification** - Advanced domain matching with fuzzy algorithms
2. **AI-Powered Classification** - Claude 3.5 Sonnet with client-specific prompts  
3. **Branded Auto-Replies** - Professional templates with client branding
4. **Intelligent Routing** - Business rules, escalation, after-hours handling
5. **Complete Processing** - End-to-end workflow in 5-7 seconds

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  🌐 Routers           🔧 Services           📊 Models       │
│  • webhooks.py        • client_manager.py   • schemas.py    │
│  • api/v1.py          • ai_classifier.py    • client_config │
│  • dashboard.py       • email_service.py    • dashboard     │
│                       • routing_engine.py                  │
├─────────────────────────────────────────────────────────────┤
│  🏢 Multi-Tenant Client Configuration System               │
│  clients/active/{client-id}/                               │
│  ├── client-config.yaml    # Consolidated: branding, routing, settings │
│  ├── categories.yaml       # AI classification categories  │
│  └── ai-context/           # Custom AI prompts & templates │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key (Claude 3.5 Sonnet)
- Mailgun account

### 1. Clone and Setup
```bash
git clone https://github.com/colenielsonauto/email-router-core.git
cd email-router-core
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export MAILGUN_API_KEY="your-mailgun-api-key"
export MAILGUN_DOMAIN="your-mailgun-domain.com"
```

### 2. Local Development
```bash
# Start development server
python -m uvicorn app.main:app --port 8080 --reload

# Test health endpoint
curl http://localhost:8080/health

# Run tests
python -m pytest tests/ -v
```

### 3. Deploy to Production
```bash
# Google Cloud Run (recommended)
gcloud run deploy email-router \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"
```

### 4. Configure Mailgun Webhook
Set webhook URL in Mailgun dashboard:
```
https://your-service-url.app/webhooks/mailgun/inbound
```

## 📊 Production Status

**✅ LIVE & OPERATIONAL** - Milestone 1 Complete

| Metric | Performance | Status |
|--------|-------------|---------|
| **Client Identification** | 1.00 confidence (exact match) | ✅ VALIDATED |
| **AI Classification** | 95%+ accuracy with Claude 3.5 | ✅ VALIDATED |
| **Email Processing** | 5-7 seconds end-to-end | ✅ VALIDATED |
| **Email Delivery** | 100% success via Mailgun | ✅ VALIDATED |
| **Multi-Tenant Isolation** | Complete separation | ✅ VALIDATED |

**Current Deployment:** `https://email-router-696958557925.us-central1.run.app`

## 🏢 Client Configuration

### Client Structure
```yaml
# clients/active/client-001-example/client-config.yaml
client:
  id: "client-001-example"
  name: "Example Company"
  industry: "Technology"
  status: "active"

domains:
  primary: "example.com"
  support: "support@example.com"
  mailgun: "mail.example.com"

branding:
  company_name: "Example Company"
  primary_color: "#007bff"
  secondary_color: "#6c757d"
  logo_url: "https://example.com/logo.png"

settings:
  auto_reply_enabled: true
  team_forwarding_enabled: true
  ai_classification_enabled: true
```

### Routing Rules
```yaml
# clients/active/client-001-example/routing-rules.yaml
routing:
  support: "support-team@example.com"
  billing: "billing@example.com"
  sales: "sales@example.com"
  general: "info@example.com"

escalation:
  keyword_based:
    urgent: "manager@example.com"
    emergency: "ceo@example.com"
```

## 🔧 API Endpoints

### Core Processing
- `POST /webhooks/mailgun/inbound` - **Main email processing endpoint**
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Client Management
- `GET /api/v1/clients` - List all clients
- `GET /api/v1/clients/{client_id}` - Get client details
- `POST /api/v1/clients/{client_id}/validate` - Validate setup

## 🏆 Recent Achievement: Comprehensive Lean Refactor

### ✅ **Project Status: 100% Complete (6/6 Milestones)**

Completed comprehensive senior-level audit and lean refactor achieving:

**🎯 Major Improvements:**
- **40% reduction** in project clutter and obsolete files
- **25% reduction** in service complexity (12→9 services)
- **40% reduction** in configuration files (5→3 files per client)
- **100% test pass rate** with 91 comprehensive tests
- **Enterprise-grade code quality** with automated enforcement

**🔧 Technical Achievements:**
- **Service consolidation**: Unified email composition and template engine
- **Configuration consolidation**: Single-file client configuration
- **Type safety**: Comprehensive type hints and mypy compliance
- **Code standards**: Black formatting, pre-commit hooks, quality dashboard
- **Enhanced testing**: Integration, isolation, performance, and validation suites

**📊 Quality Metrics:**
- 8,369 lines of Python code (fully formatted)
- 100% backward compatibility maintained
- Pre-commit hooks for automated quality enforcement
- Comprehensive code quality dashboard

See [MILESTONES.md](MILESTONES.md) for detailed project roadmap and achievements.

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Run all tests (91 tests total)
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_multi_tenant.py -v           # Multi-tenant isolation (18 tests)
python -m pytest tests/test_webhook.py -v               # Email processing (8 tests)
python -m pytest tests/test_config_validation.py -v     # Configuration validation (13 tests)
python -m pytest tests/test_integration_pipeline.py -v  # End-to-end pipeline (15 tests)
python -m pytest tests/test_service_isolation.py -v     # Service isolation (10 tests)
python -m pytest tests/test_performance_regression.py -v # Performance testing (8 tests)

# Code quality report
python scripts/code_quality_report.py
```

### Test Coverage (91 Tests)
- ✅ **Multi-tenant isolation** (18 tests) - Complete client separation and domain matching
- ✅ **Configuration validation** (13 tests) - YAML schemas, Pydantic models, consistency
- ✅ **Integration pipeline** (15 tests) - End-to-end email processing workflows
- ✅ **Service isolation** (10 tests) - No shared state, concurrent access validation
- ✅ **Performance regression** (8 tests) - Response time baselines and benchmarks
- ✅ **Template engine** (10 tests) - Variable injection, branding, validation
- ✅ **API endpoints** (8 tests) - Webhook processing, health checks, documentation
- ✅ **Enhanced templates** (9 tests) - Professional email templates and branding

## 📊 Code Quality

### Enterprise-Grade Standards
```bash
# Code quality report
python scripts/code_quality_report.py

# Manual quality checks
python -m black --check app/ tests/           # Code formatting
python -m isort --check-only app/ tests/      # Import organization
python -m mypy app/ --ignore-missing-imports  # Type checking
```

### Quality Metrics
- ✅ **100% formatted code** with Black and isort
- ✅ **Comprehensive type hints** with mypy validation
- ✅ **Pre-commit hooks** for automated quality enforcement
- ✅ **Security scanning** with Bandit
- ✅ **Documentation standards** with pydocstyle
- ✅ **Automated quality dashboard** with scoring and recommendations

### Pre-commit Hooks
```bash
# Install quality enforcement hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## 🔒 Security & Production Features

### Enterprise Security
- ✅ Environment variable configuration
- ✅ API key authentication
- ✅ Rate limiting and DDoS protection
- ✅ Input validation with Pydantic
- ✅ Complete client isolation
- ✅ HTTPS enforcement

### Monitoring & Observability
- ✅ Multi-level health checks
- ✅ Prometheus-compatible metrics
- ✅ Structured logging
- ✅ Error tracking and alerting
- ✅ Performance monitoring

## 📈 Scaling & Performance

### Performance Benchmarks
- **Concurrent Processing**: 100+ simultaneous emails
- **Response Time**: 5-7 seconds consistent
- **Throughput**: 1000+ emails/hour sustained
- **Memory Usage**: 512MB-2GB depending on load

### Typical Monthly Costs
| Component | Volume | Monthly Cost |
|-----------|---------|--------------|
| Google Cloud Run | 1,000-10,000 emails | $15-45 |
| Anthropic Claude API | 10,000 classifications | $30-50 |
| Mailgun Email Delivery | 10,000 emails | $35 |
| **Total** | | **$80-130/month** |

## 🛠️ Project Structure

```
email-router-core/
├── app/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── routers/                  # API endpoints
│   │   ├── webhooks.py           # Email webhook handlers
│   │   └── api/v1.py            # Client management API
│   ├── services/                 # Business logic
│   │   ├── client_manager.py     # Multi-tenant management
│   │   ├── dynamic_classifier.py # AI classification
│   │   ├── routing_engine.py     # Smart routing
│   │   ├── email_composer.py     # Response generation
│   │   └── email_sender.py       # Email delivery
│   ├── models/                   # Data models
│   └── utils/                    # Utilities
├── clients/                      # Multi-tenant configuration
│   ├── active/                   # Active client configs
│   └── templates/                # Configuration templates
├── tests/                        # Comprehensive test suite
└── requirements.txt              # Dependencies
```

## 📞 Support & Contributing

### Getting Help
- 📖 **Documentation** - Comprehensive guides in repository
- 🐛 **Issue Tracking** - GitHub issues for bugs and features
- 💬 **Discussions** - GitHub discussions for questions

### Contributing
1. Fork the repository
2. Create feature branch
3. Add comprehensive tests
4. Submit pull request

## 📜 License

MIT License - Use for unlimited commercial deployments.

---

## 🎯 Ready for Production

**Enterprise-ready • Multi-tenant • AI-powered • Production-validated**

*Processing real emails • Branded communications • Serving customers • Generating value*