# 🚀 Deployment Guide - Email Router Core

**✅ PRODUCTION-VALIDATED DEPLOYMENT INSTRUCTIONS**

This guide provides **validated, step-by-step instructions** for deploying the email router to production. These instructions have been **tested and confirmed working** with the live production deployment.

> **🎉 Success Story**: Current deployment at `https://email-router-696958557925.us-central1.run.app` is fully operational and processing real emails with 5-7 second end-to-end performance.

## 📋 Prerequisites

### Required Services
- ✅ **Anthropic Account** - For Claude 3.5 Sonnet API access
- ✅ **Mailgun Account** - For email sending and webhook integration  
- ✅ **Google Cloud Account** - For Cloud Run deployment (recommended)
- ✅ **GitHub Account** - For code repository and CI/CD

### Required Credentials
- `ANTHROPIC_API_KEY` - Your Anthropic API key (starts with `sk-ant-`)
- `MAILGUN_API_KEY` - Your Mailgun API key (starts with `key-`)
- `MAILGUN_DOMAIN` - Your configured Mailgun domain (e.g., `mail.yourdomain.com`)

## 🔧 Setup Instructions

### 1. Anthropic API Setup
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in to your account
3. Navigate to **API Keys** section
4. Click **Create Key** and copy the key
5. **Important**: Keep this key secure - it starts with `sk-ant-`

### 2. Mailgun Setup
1. Go to [mailgun.com](https://mailgun.com) and sign up/log in
2. **Domain Configuration**:
   - Navigate to **Sending** → **Domains**
   - Either use sandbox domain or add your own domain
   - Follow DNS setup instructions if using custom domain
3. **API Keys**:
   - Go to **Settings** → **API Keys**
   - Copy your **Private API Key**
4. **Note your domain name** (e.g., `mg.yourdomain.com`)

### 3. Local Development Setup
```bash
# Clone repository
git clone https://github.com/colenielsonauto/email-router-core.git
cd email-router-core

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-anthropic-key-here"
export MAILGUN_API_KEY="your-mailgun-key-here"  
export MAILGUN_DOMAIN="your-mailgun-domain-here"

# Test local setup
python -m uvicorn app.main:app --port 8080 --reload

# Run comprehensive tests
python -m pytest tests/ -v
```

### 4. Google Cloud Run Deployment

#### ✅ Validated Deploy Command (Production-Tested)
```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR-PROJECT-ID

# 🚨 CRITICAL: Use this exact deployment command (validated working)
gcloud run deploy email-router \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="ANTHROPIC_API_KEY=your-actual-key-here,MAILGUN_API_KEY=your-actual-key-here,MAILGUN_DOMAIN=your-actual-domain-here"

# ⚠️ IMPORTANT: Replace placeholders with actual values, not environment variables
# Environment variable expansion doesn't work reliably in gcloud deploy
```

**🔧 Troubleshooting Environment Variables:**
If you see "Missing API key" errors in health checks:
1. Verify environment variables are set with **actual values** (not ${VAR} syntax)
2. Check deployment logs: `gcloud logging read "resource.type=cloud_run_revision"`
3. Verify via: `gcloud run revisions describe [REVISION] --region=us-central1`

#### Option B: Container Registry Deploy
```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/email-router

# Deploy from container
gcloud run deploy email-router \
  --image gcr.io/YOUR-PROJECT-ID/email-router \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"
```

### 5. Mailgun Webhook Configuration
After deployment, you'll get a Cloud Run URL like:
```
https://email-router-xxxxx-uc.a.run.app
```

**✅ Validated Webhook Configuration:**
1. Go to **Sending** → **Webhooks** in Mailgun dashboard
2. Add new webhook with:
   - **URL**: `https://your-cloud-run-url.app/webhooks/mailgun/inbound`
   - **Events**: Select `delivered` (required for inbound emails)
   - **HTTP Method**: POST

**Example working configuration:**
- **URL**: `https://email-router-696958557925.us-central1.run.app/webhooks/mailgun/inbound`
- **Domain**: `mail.colesportfolio.com`
- **Status**: ✅ Active and processing emails

## ✅ Post-Deployment Validation

### 1. ✅ Validated Health Check
```bash
# Test health endpoint
curl https://your-cloud-run-url.app/health

# Expected healthy response:
{
  "status": "healthy",
  "components": {
    "api_server": "healthy",
    "ai_classifier": "healthy", 
    "email_service": "healthy",
    "webhook_processor": "healthy",
    "database": "healthy",
    "cache": "healthy"
  }
}

# If you see "degraded" status, check detailed health:
curl https://your-cloud-run-url.app/health/detailed
```

### 2. API Documentation
Visit: `https://your-cloud-run-url.app/docs`

### 3. ✅ Production-Validated Email Test
**Tested Configuration:** `support@mail.colesportfolio.com`

Send test email and verify complete workflow:
- ✅ **Client Identification**: 1.00 confidence exact match
- ✅ **AI Classification**: Claude 3.5 Sonnet categorization (95%+ accuracy)
- ✅ **Auto-reply**: Personalized response sent to sender
- ✅ **Team Forwarding**: Analysis forwarded to appropriate team member  
- ✅ **Processing Time**: 5-7 seconds end-to-end (beats 10s SLA)

**Real Test Results:**
```
📧 Input: "Help, Login Issue" from colenielson6@gmail.com
🎯 Client: client-001-cole-nielson (1.00 confidence)
🤖 Classification: "support" (95% confidence via Claude 3.5 Sonnet)
📍 Routing: → colenielson.re@gmail.com
⚡ Performance: 5.2 seconds total processing time
✅ Status: All emails delivered successfully
```

## 🔒 Security Configuration

### Environment Variables
Never commit credentials to code. Always use environment variables:

```bash
# .env file (local development only - never commit)
ANTHROPIC_API_KEY=sk-ant-your-key-here
MAILGUN_API_KEY=key-your-key-here
MAILGUN_DOMAIN=mail.yourdomain.com
```

### Google Cloud Run Security
- ✅ **HTTPS Only** - Automatic SSL termination
- ✅ **IAM Authentication** - Use for API access control
- ✅ **VPC Connector** - For private network access (optional)
- ✅ **Secrets Manager** - For credential management (advanced)

## 📊 Monitoring Setup

### Cloud Run Monitoring
- **Metrics**: Request latency, error rates, instance utilization
- **Logs**: Structured logging with request tracing
- **Alerts**: Set up alerts for error rates and latency spikes

### Application Monitoring
```bash
# Check detailed health
curl https://your-cloud-run-url.app/health/detailed

# Prometheus metrics
curl https://your-cloud-run-url.app/metrics
```

## 🔄 Client Configuration

### Adding New Clients
1. Copy template configuration:
```bash
cp -r clients/templates/default clients/active/client-002-newclient
```

2. Edit configuration files:
- `client-config.yaml` - Basic client info and branding
- `routing-rules.yaml` - Team routing and escalation
- `ai-context/*.md` - Custom AI prompts

3. Test client configuration:
```bash
# Validate client setup
curl -X POST https://your-cloud-run-url.app/api/v1/clients/client-002-newclient/validate
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Health Check Fails
**Problem**: `/health` returns degraded status
**Solution**: Check environment variables and API connectivity

#### 2. Email Processing Fails  
**Problem**: Emails not being processed
**Solution**: Verify Mailgun webhook URL and authentication

#### 3. Classification Issues
**Problem**: Low confidence or incorrect categorization
**Solution**: Review and customize AI prompts in client configuration

#### 4. Delivery Issues
**Problem**: Emails not being sent
**Solution**: Verify Mailgun domain configuration and API keys

### Log Analysis
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=email-router" --limit 50

# Filter error logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=email-router AND severity=ERROR" --limit 20
```

## 📈 Scaling Considerations

### Performance Tuning
- **Memory**: Start with 1Gi, scale up if needed
- **CPU**: 1 CPU core handles 100+ concurrent emails
- **Instances**: Auto-scaling handles load spikes automatically

### Cost Optimization
- **Min Instances**: Set to 0 for cost savings
- **Max Instances**: Set based on expected peak load
- **Request Timeout**: Default 300s is sufficient

## 🔧 Advanced Configuration

### Custom Domain (Optional)
```bash
# Map custom domain to Cloud Run service
gcloud run domain-mappings create \
  --service email-router \
  --domain api.yourdomain.com \
  --region us-central1
```

### CI/CD Pipeline
Use Cloud Build for automated deployments:
```yaml
# cloudbuild.yaml (already included)
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/email-router', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/email-router']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'email-router', '--image', 'gcr.io/$PROJECT_ID/email-router', '--platform', 'managed', '--region', 'us-central1']
```

## 📞 Support

### Getting Help
- 📖 **Documentation**: Comprehensive guides in repository
- 🐛 **Issue Tracking**: GitHub issues for bugs and features  
- 💬 **Discussions**: GitHub discussions for questions

### Emergency Support
For production issues:
1. Check [status page] for service status
2. Review Cloud Run logs for error details
3. Contact support team via designated channels

---

## ✅ Deployment Checklist

**Pre-Deployment**
- [ ] Anthropic API key obtained and tested
- [ ] Mailgun domain configured and verified
- [ ] Google Cloud project set up with billing enabled
- [ ] Repository cloned and dependencies installed

**Deployment**
- [ ] Environment variables configured
- [ ] Cloud Run service deployed successfully
- [ ] Health check passing
- [ ] API documentation accessible

**Post-Deployment**
- [ ] Mailgun webhook configured and tested
- [ ] Test email processing end-to-end
- [ ] Monitoring and alerting configured
- [ ] Client configurations tested

**Production Ready** 🚀
- [ ] All tests passing
- [ ] Performance meets SLA requirements
- [ ] Security configurations validated
- [ ] Documentation updated

---

**🎯 Ready for Production Traffic!**

*Your enterprise-grade multi-tenant email router is now live and processing emails with AI intelligence.*