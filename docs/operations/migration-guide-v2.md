# 📋 Migration Guide: V1.x to V2.0

## Overview

Email Router V2.0 introduces **breaking changes** that require a full migration from V1.x installations. This guide provides step-by-step instructions for upgrading your deployment.

## ⚠️ Pre-Migration Checklist

### **Backup Your Data**
```bash
# Backup your V1.x configuration
cp -r app/config/ backup_v1_config/
cp -r app/templates/ backup_v1_templates/
cp .env backup_v1_env

# Export any custom configurations
# Document current client settings
# Backup any custom email templates
```

### **System Requirements**
- Python 3.9+ (V2.0 requires newer Python)
- Node.js 18+ (for future web UI)
- Docker (recommended for deployment)
- Google Cloud access (for production deployment)

## 🔄 Migration Steps

### **Step 1: Fresh Installation**

⚠️ **Do NOT upgrade in-place** - V2.0 requires fresh installation due to architectural changes.

```bash
# Clone V2.0 codebase
git clone https://github.com/colenielsonauto/email-router-core.git email-router-v2
cd email-router-v2

# Switch to V2.0 release branch
git checkout release/v2.0-architectural-overhaul

# Install dependencies
cd backend
pip install -e .[dev]
```

### **Step 2: Environment Configuration**

```bash
# Copy your V1.x environment variables
cp /path/to/v1/backup_v1_env .env

# Update environment file for V2.0 requirements
# Add these new required variables:
echo "EMAIL_ROUTER_ENVIRONMENT=production" >> .env
echo "JWT_SECRET_KEY=your-secure-jwt-secret-32-chars-minimum" >> .env
```

### **Step 3: Client Configuration Migration**

V2.0 uses YAML-based client configurations. Convert your V1.x JSON configs:

```bash
# Create client directory structure
mkdir -p clients/active/client-001-yourname

# Convert V1.x configuration to V2.0 YAML format
```

**V1.x Configuration (JSON)**:
```json
{
  "client_id": "client-001-yourname",
  "name": "Your Company",
  "domains": ["example.com"],
  "routing": {
    "support": "support@example.com"
  }
}
```

**V2.0 Configuration (YAML)**:
```yaml
# clients/active/client-001-yourname/client-config.yaml
client_id: client-001-yourname
name: Your Company
industry: Technology
timezone: UTC
active: true

domains:
  primary: example.com
  aliases: []
  catch_all: false
  support: support@example.com
  mailgun: mg.example.com

branding:
  company_name: Your Company
  primary_color: "#007bff"
  secondary_color: "#6c757d"

contacts:
  primary_contact: admin@example.com
  escalation_contact: escalation@example.com
  billing_contact: billing@example.com

routing:
  - category: support
    email: support@example.com
    enabled: true
  - category: general
    email: general@example.com
    enabled: true

sla:
  response_times:
    urgent: 15
    high: 60
    medium: 240
    low: 1440

settings:
  auto_reply_enabled: true
  ai_classification_enabled: true
  team_forwarding_enabled: true
```

### **Step 4: Authentication Setup**

V2.0 requires authentication setup:

```bash
# Create initial admin user
python scripts/simple_create_admin.py
# Follow prompts to create admin credentials
```

### **Step 5: Template Migration**

V2.0 uses enhanced email templates. Update your custom templates:

```bash
# Copy V1.x templates
cp /path/to/v1/backup_v1_templates/* clients/active/client-001-yourname/templates/

# Update template syntax for V2.0 variable injection
# Replace V1.x {{variable}} with V2.0 {{variable}} format
```

### **Step 6: Database Migration (if applicable)**

If you were using a database in V1.x:

```bash
# V2.0 starts with SQLite by default
# Data migration tools available in scripts/migration/
python scripts/migration/migrate_v1_to_v2.py --source /path/to/v1/data
```

## 🧪 Testing Your Migration

### **Local Testing**

```bash
# Start V2.0 application
python -m uvicorn src.main:app --port 8080 --reload

# Test health endpoint
curl http://localhost:8080/health

# Test authentication
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Test client configuration
curl http://localhost:8080/api/v1/clients/client-001-yourname
```

### **Email Flow Testing**

```bash
# Test webhook endpoint (replace with your webhook URL)
curl -X POST http://localhost:8080/webhooks/mailgun/inbound \
  -F "From=test@example.com" \
  -F "To=support@example.com" \
  -F "Subject=Test Email" \
  -F "stripped-text=This is a test email"
```

## 🚀 Production Deployment

### **Google Cloud Run Deployment**

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/your-project/email-router-v2
gcloud run deploy email-router-v2 \
  --image gcr.io/your-project/email-router-v2 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY}"
```

### **Domain Configuration**

Update your Mailgun webhook URLs:
```
OLD: https://your-v1-domain.com/webhook
NEW: https://your-v2-domain.com/webhooks/mailgun/inbound
```

## 🔍 Post-Migration Verification

### **Checklist**
- [ ] Health endpoint returns 200 OK
- [ ] Authentication system working
- [ ] Client configuration loading correctly
- [ ] AI classification functioning (test with sample email)
- [ ] Email delivery working (check Mailgun logs)
- [ ] Dashboard analytics accessible
- [ ] All webhooks updated to new URLs
- [ ] Monitoring and alerting configured

### **Performance Validation**
- [ ] Email processing time < 7 seconds
- [ ] Classification accuracy > 90%
- [ ] No memory leaks or performance degradation
- [ ] All integrations (Mailgun, Anthropic) functioning

## 🆘 Troubleshooting

### **Common Issues**

**Authentication Errors**:
```bash
# Recreate admin user
python scripts/simple_create_admin.py --force
```

**Configuration Loading Errors**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('clients/active/client-001-yourname/client-config.yaml'))"
```

**Import Errors**:
```bash
# Reinstall dependencies
pip install -e .[dev] --force-reinstall
```

**Performance Issues**:
```bash
# Check logs
tail -f logs/email-router.log

# Monitor resources
docker stats email-router-v2
```

## 📞 Support

If you encounter issues during migration:

1. **Check Documentation**: `/docs` directory has comprehensive guides
2. **Review Logs**: Enable debug logging for detailed information
3. **Test Incrementally**: Migrate one client at a time
4. **Rollback Plan**: Keep V1.x deployment running during migration

## 🔄 Rollback Plan

If migration fails:

```bash
# Switch back to V1.x deployment
# Update Mailgun webhooks to V1.x URLs
# Restore V1.x configuration from backups
```

---

**Need Help?** Check the [troubleshooting guide](./docs/development/known-issues.md) or review the [architecture documentation](./docs/architecture/system-architecture.md).
