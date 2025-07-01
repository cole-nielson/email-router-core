# Configuration Schema Documentation

## 📋 Consolidated Configuration Structure (Milestone 5)

**Configuration consolidation achieved: 5 files → 3 files (40% reduction)**

### File Structure Overview

```
clients/active/{client-id}/
├── client-config.yaml          # 🎯 CONSOLIDATED: Main configuration + branding + routing
├── categories.yaml             # 🤖 AI-specific: Classification categories
└── ai-context/
    └── fallback-responses.yaml # 🤖 AI-specific: Fallback responses
```

**Files Removed:**
- `branding/colors.yaml` → **Merged into** `client-config.yaml`
- `routing-rules.yaml` → **Merged into** `client-config.yaml`
- `branding/` directory → **Eliminated** (empty after consolidation)

---

## 🎯 Consolidated client-config.yaml

**Sections:**
1. **Client Information** - Basic client metadata
2. **Domain Configuration** - Email domains and aliases
3. **Branding & Colors** - Company branding with extended color palette
4. **Response Times & SLA** - Service level agreements
5. **Business Hours** - Operating hours and timezone
6. **Contacts** - Primary contacts for escalation
7. **Settings** - Feature flags and toggles
8. **Routing Rules** - Complete routing and escalation configuration

### Complete Schema Example

```yaml
# =============================================================================
# CLIENT CONFIGURATION - CONSOLIDATED (Milestone 5)
# =============================================================================

client:
  id: "client-001-example"
  name: "Example Company Email Router"
  industry: "Technology"
  timezone: "America/New_York"
  business_hours: "9-17"
  created_at: "2024-06-09T17:00:00Z"
  status: "active"

# Email domains configuration
domains:
  primary: "mail.example.com"
  support: "support@mail.example.com"
  mailgun: "mail.example.com"
  aliases:
    - "example.dev"
    - "staging.example.com"

# Company branding with consolidated colors
branding:
  company_name: "Example Company"
  primary_color: "#667eea"
  secondary_color: "#764ba2"
  logo_url: "https://example.com/logo.png"
  email_signature: "Example Company Support Team"
  footer_text: "© 2024 Example Company. All rights reserved."

  # Extended color palette (consolidated from colors.yaml)
  colors:
    # Primary brand colors
    primary:
      main: "#667eea"
      light: "#a5b4fc"
      dark: "#4338ca"
      contrast: "#ffffff"

    # Secondary brand colors
    secondary:
      main: "#764ba2"
      light: "#c084fc"
      dark: "#581c87"
      contrast: "#ffffff"

    # Semantic colors
    semantic:
      success: "#22c55e"
      warning: "#f59e0b"
      error: "#ef4444"
      info: "#3b82f6"

    # Email template colors
    email:
      header_background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
      header_text: "#ffffff"
      body_background: "#ffffff"
      body_text: "#374151"
      accent_background: "#f8f9ff"
      accent_border: "#667eea"
      footer_background: "#f8f9fa"
      footer_text: "#6b7280"
      link_color: "#667eea"
      link_hover: "#4338ca"

    # Category-specific colors
    categories:
      support: "#3b82f6"
      billing: "#22c55e"
      sales: "#f59e0b"
      general: "#6b7280"
      urgent: "#ef4444"
      complaint: "#dc2626"

# Response time commitments
response_times:
  support:
    target: "within 4 hours"
    business_hours_only: true
  billing:
    target: "within 24 hours"
    business_hours_only: false
  sales:
    target: "within 2 hours"
    business_hours_only: true
  general:
    target: "within 24 hours"
    business_hours_only: false
  urgent:
    target: "within 1 hour"
    business_hours_only: false

# Business hours configuration
business_hours:
  timezone: "America/New_York"
  workdays: ["monday", "tuesday", "wednesday", "thursday", "friday"]
  start_time: "09:00"
  end_time: "17:00"

# SLA tracking
sla:
  escalation_enabled: true
  escalate_after_percentage: 80
  track_metrics: true

# Contact information
contacts:
  primary_contact: "admin@example.com"
  escalation_contact: "manager@example.com"
  billing_contact: "billing@example.com"

# Feature settings
settings:
  auto_reply_enabled: true
  team_forwarding_enabled: true
  ai_classification_enabled: true
  escalation_enabled: true
  monitoring_enabled: true

# =============================================================================
# ROUTING CONFIGURATION (consolidated from routing-rules.yaml)
# =============================================================================

# Primary routing rules
routing:
  support: "support@example.com"
  billing: "billing@example.com"
  sales: "sales@example.com"
  technical: "tech@example.com"
  complaint: "manager@example.com"
  general: "info@example.com"

# Escalation rules
escalation:
  time_based:
    support:
      - hours: 4
        escalate_to: "manager@example.com"
    billing:
      - hours: 8
        escalate_to: "admin@example.com"
    sales:
      - hours: 2
        escalate_to: "sales-manager@example.com"

  keyword_based:
    urgent: "manager@example.com"
    vip: "admin@example.com"
    refund: "billing@example.com"
    cancellation: "billing@example.com"
    legal: "legal@example.com"

# Backup routing
backup_routing:
  support: "admin@example.com"
  billing: "admin@example.com"
  sales: "admin@example.com"
  general: "admin@example.com"

# Special rules
special_rules:
  vip_domains: ["important-client.com", "enterprise-partner.com"]
  vip_route_to: "admin@example.com"
  after_hours_route_to: "oncall@example.com"
  weekend_route_to: "oncall@example.com"
```

---

## 🤖 AI-Specific Configuration Files

### categories.yaml - Classification Categories

```yaml
# Email classification categories
categories:
  support:
    name: "Technical Support"
    description: "Technical problems and product issues"
    priority: "high"
    keywords: ["help", "problem", "issue", "error", "bug"]
    confidence_threshold: 0.8

  billing:
    name: "Billing & Payments"
    description: "Payment and billing inquiries"
    priority: "high"
    keywords: ["invoice", "payment", "billing", "charge", "refund"]
    confidence_threshold: 0.85

# Priority levels
priority_levels:
  urgent:
    response_time: "within 1 hour"
    escalate_immediately: true
  high:
    response_time: "within 4 hours"
    escalate_after: 2
  medium:
    response_time: "within 8 hours"
    escalate_after: 4
  low:
    response_time: "within 24 hours"
    escalate_after: 8
```

### ai-context/fallback-responses.yaml - Fallback Responses

```yaml
# Fallback responses when AI is unavailable
customer_acknowledgments:
  support: |
    Thank you for contacting our support team. We've received your inquiry
    and will respond within 4 hours during business hours.

  billing: |
    Thank you for your billing inquiry. Our team will review your request
    within 24 hours.

team_analysis:
  support: |
    Email classified as SUPPORT inquiry (fallback classification).
    Please review and provide technical assistance.

  billing: |
    Email classified as BILLING inquiry (fallback classification).
    Please review for payment/billing issues.

# Error handling
error_messages:
  ai_service_down: "AI classification service unavailable. Using fallback rules."
  config_load_error: "Configuration load error. Using system defaults."
```

---

## 🔧 Configuration Validation

### Pydantic Model Structure

```python
class ClientConfig(BaseModel):
    """Consolidated client configuration model."""
    client: ClientInfo
    domains: DomainConfig
    branding: BrandingConfig          # ← Includes consolidated colors
    response_times: ResponseTimeConfig
    contacts: ContactsConfig
    settings: SettingsConfig
    business_hours: Optional[BusinessHoursConfig]
    sla: Optional[SLAConfig]

    # Consolidated routing (from routing-rules.yaml)
    routing: Optional[Dict[str, EmailStr]]
    escalation: Optional[EscalationConfig]
    backup_routing: Optional[Dict[str, EmailStr]]
    special_rules: Optional[SpecialRules]

class BrandingConfig(BaseModel):
    """Extended branding with consolidated colors."""
    company_name: str
    email_signature: str
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    logo_url: Optional[str] = ""
    footer_text: Optional[str] = ""
    colors: Optional[Dict[str, Any]] = None  # ← Consolidated color palette
```

### Validation Features

- **Automatic validation** on configuration load
- **Email address validation** for all contact fields
- **Hex color validation** for branding colors
- **Business hours validation** with timezone support
- **Routing rule validation** with escalation paths
- **Comprehensive error reporting** with field-level details

---

## 📊 Configuration Consolidation Results

### File Reduction Summary

| **Before** | **After** | **Change** |
|------------|-----------|------------|
| 5 files | 3 files | **-40%** |
| 355 lines total | 275 lines total | **-23%** |
| 3 directories | 1 directory | **-67%** |

### Performance Improvements

- **Reduced I/O operations**: Single file load vs. multiple file reads
- **Improved caching**: Consolidated configuration caching
- **Better maintainability**: Single source of truth for client settings
- **Enhanced validation**: Unified Pydantic model validation

### Backward Compatibility

- **Service integration**: All existing services work without changes
- **API compatibility**: No breaking changes to client management APIs
- **Configuration loading**: Transparent migration from separate files
- **Template support**: Enhanced color support in email templates

---

## 🔄 Migration Guide

### For Existing Clients

1. **Backup existing configuration files**
2. **Run consolidation script** (automated migration)
3. **Validate consolidated configuration** with Pydantic
4. **Test routing and branding** functionality
5. **Remove legacy files** after validation

### For New Clients

1. **Copy configuration template** from `docs/templates/`
2. **Customize client-specific values** in single file
3. **Validate configuration** using validation tests
4. **Deploy and test** email processing pipeline

---

**Last Updated**: December 13, 2024
**Milestone**: 5 - Configuration Management Consolidation
**Status**: ✅ Complete
