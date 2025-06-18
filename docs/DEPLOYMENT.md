# 🚀 Email Router Deployment Guide

This document provides comprehensive instructions for deploying the email router to production and troubleshooting common deployment issues.

## 📋 Pre-Deployment Checklist

### 1. Environment Variables Verification

**Required Environment Variables:**
- `ANTHROPIC_API_KEY` - Claude API key for AI classification and response generation
- `MAILGUN_API_KEY` - Mailgun API key for email delivery
- `MAILGUN_DOMAIN` - Configured Mailgun domain (e.g., mail.colesportfolio.com)

**Optional Environment Variables:**
- `ANTHROPIC_MODEL` - Claude model version (defaults to claude-3-5-sonnet-20241022)
- `MAILGUN_WEBHOOK_SIGNING_KEY` - Webhook signature verification
- `PORT` - Server port (defaults to 8080)

### 2. Environment Variables Validation Script

Run this command to verify all required environment variables are set:

```bash
# Verify environment variables are loaded
source .env
echo "✅ Environment Variables Check:"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}..."
echo "MAILGUN_API_KEY: ${MAILGUN_API_KEY:0:10}..."
echo "MAILGUN_DOMAIN: ${MAILGUN_DOMAIN}"

# Verify lengths (keys should be substantial)
if [ ${#ANTHROPIC_API_KEY} -lt 50 ]; then
    echo "❌ ANTHROPIC_API_KEY appears too short"
else
    echo "✅ ANTHROPIC_API_KEY length OK"
fi

if [ ${#MAILGUN_API_KEY} -lt 30 ]; then
    echo "❌ MAILGUN_API_KEY appears too short"
else
    echo "✅ MAILGUN_API_KEY length OK"
fi

if [ -z "$MAILGUN_DOMAIN" ]; then
    echo "❌ MAILGUN_DOMAIN not set"
else
    echo "✅ MAILGUN_DOMAIN set"
fi
```

### 3. Local Testing Verification

Before deploying, ensure the system works locally:

```bash
# Start local server
python -m uvicorn app.main:app --port 8080 --reload

# Test health endpoint
curl http://localhost:8080/health

# Expected response: {"status":"healthy", ...}
```

## 🚀 Production Deployment

### Google Cloud Run Deployment

**CRITICAL:** Always source environment variables before deployment to avoid missing configuration issues.

```bash
# 1. Source environment variables from .env file
source .env

# 2. Verify variables are loaded (run the validation script above)

# 3. Deploy to Google Cloud Run
gcloud run deploy email-router \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"

# 4. Note the service URL from deployment output
```

### Post-Deployment Verification

```bash
# 1. Test health endpoint
curl https://email-router-696958557925.us-central1.run.app/health

# Expected: All components should show "healthy"

# 2. Test webhook endpoint (optional - requires valid Mailgun signature)
curl -X POST https://email-router-696958557925.us-central1.run.app/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"test": "deployment_verification"}'

# 3. Check recent logs for any errors
gcloud run services logs read email-router --limit=20 --region=us-central1
```

## 🔧 Troubleshooting Common Issues

### Issue 1: Missing Environment Variables

**Symptoms:**
- `AI service unavailable: ANTHROPIC_API_KEY not configured`
- `Email service unavailable: MAILGUN_API_KEY or MAILGUN_DOMAIN not configured`
- 401 Unauthorized errors in logs

**Solution:**
```bash
# 1. Verify .env file exists and contains valid keys
cat .env | grep -E "(ANTHROPIC|MAILGUN)"

# 2. Re-source environment variables
source .env

# 3. Verify they're loaded in current shell
echo $ANTHROPIC_API_KEY | cut -c1-10

# 4. Redeploy with explicit environment sourcing
source .env && gcloud run deploy email-router \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"
```

### Issue 2: Malformed Mailgun URLs

**Symptoms:**
- `405 Method Not Allowed` errors
- Mailgun URLs showing double slashes: `https://api.mailgun.net/v3//messages`

**Solution:**
- Verify MAILGUN_DOMAIN doesn't have leading/trailing slashes
- Check email sender configuration for proper URL construction

### Issue 3: AI Classification Failures

**Symptoms:**
- `Failed to parse AI response as JSON`
- `Template processing completed with X missing variables`

**Solution:**
- Check client AI prompt templates for proper variable syntax
- Verify template variables use `{{variable}}` format
- Review recent prompt changes

### Issue 4: Email Delivery Failures

**Symptoms:**
- Emails not being sent to recipients
- Mailgun API errors

**Solution:**
```bash
# 1. Verify Mailgun domain is properly configured
# 2. Check Mailgun dashboard for domain verification status
# 3. Test Mailgun API directly:
curl -s --user "api:${MAILGUN_API_KEY}" \
  https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages \
  -F from="test@${MAILGUN_DOMAIN}" \
  -F to="your-email@example.com" \
  -F subject="Test" \
  -F text="Testing Mailgun configuration"
```

## 📊 Monitoring and Logs

### Checking Deployment Status

```bash
# View service status
gcloud run services describe email-router --region=us-central1

# View recent revisions
gcloud run revisions list --service=email-router --region=us-central1

# View real-time logs
gcloud run services logs read email-router --follow --region=us-central1
```

### Key Log Patterns to Monitor

**Healthy System:**
- `✅ All services available: AI classification and email processing enabled`
- `📧 Received email from [sender] to [recipient]`
- `🎯 Identified client: [client] (confidence: 1.00)`
- `✍️ Generated client-specific acknowledgment for [client]`
- `📨 Auto-reply sent to [recipient]`

**Warning Signs:**
- `AI service unavailable`
- `Email service unavailable`
- `Failed to parse AI response`
- `MISSING: [variable]` in template processing
- `401 Unauthorized` API errors

## 🔄 Rollback Procedures

If deployment fails or causes issues:

```bash
# 1. List recent revisions
gcloud run revisions list --service=email-router --region=us-central1

# 2. Rollback to previous working revision
gcloud run services update-traffic email-router \
  --to-revisions=[PREVIOUS_REVISION]=100 \
  --region=us-central1

# 3. Verify rollback worked
curl https://email-router-696958557925.us-central1.run.app/health
```

## 🔐 Security Considerations

1. **Never commit environment variables** to version control
2. **Rotate API keys regularly** (especially after team changes)
3. **Use webhook signing keys** in production for security
4. **Monitor logs** for unauthorized access attempts
5. **Limit Cloud Run access** to necessary personnel

## 📝 Deployment Checklist Summary

- [ ] Source environment variables (`source .env`)
- [ ] Validate all required env vars are set
- [ ] Test system locally
- [ ] Deploy with explicit env var injection
- [ ] Verify health endpoint post-deployment
- [ ] Check logs for any errors
- [ ] Test email flow with real email
- [ ] Document any issues or changes

---

**Last Updated:** June 2025
**Contact:** For deployment issues, check logs first, then escalate with specific error messages and revision numbers.
