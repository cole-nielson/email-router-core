/**
 * Client management types for the Email Router application
 */

export interface ClientSummary {
  id: string;
  name: string;
  industry: string;
  status: 'active' | 'inactive' | 'suspended';
  domain_count: number;
  last_activity: string;
  health_status: 'healthy' | 'warning' | 'error';
  email_volume_24h: number;
  created_at: string;
  updated_at: string;
}

export interface ClientConfig {
  id: string;
  name: string;
  industry: string;
  status: 'active' | 'inactive' | 'suspended';
  timezone: string;
  business_hours: string;
  domains: string[];
  domain_aliases?: string[];
  created_at: string;
  updated_at: string;
  settings: {
    auto_reply_enabled: boolean;
    classification_threshold: number;
    response_time_sla: number;
    escalation_enabled: boolean;
  };
}

export interface RoutingRule {
  category: string;
  email: string;
  fallback_email?: string;
  priority: number;
  conditions?: {
    keywords?: string[];
    sender_domains?: string[];
    time_based?: {
      start_time: string;
      end_time: string;
      timezone: string;
    };
  };
}

export interface RoutingConfig {
  rules: Record<string, RoutingRule>;
  default_route: string;
  escalation_route?: string;
  after_hours_route?: string;
}

export interface BrandingConfig {
  company_name: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  accent_color?: string;
  font_family?: string;
  email_signature: string;
  footer_text?: string;
  custom_css?: string;
}

export interface AIPromptConfig {
  type: 'classification' | 'response_generation' | 'escalation';
  name: string;
  prompt: string;
  variables?: Record<string, string>;
  temperature?: number;
  max_tokens?: number;
  enabled: boolean;
}

export interface ClientValidationResult {
  client_id: string;
  valid: boolean;
  issues: Array<{
    type: 'error' | 'warning';
    category: 'configuration' | 'routing' | 'branding' | 'ai_prompts';
    message: string;
    field?: string;
  }>;
  suggestions?: string[];
}

export interface DomainResolutionResult {
  domain: string;
  client_id?: string;
  confidence: number;
  match_type: 'exact' | 'hierarchy' | 'fuzzy' | 'similarity' | 'none';
  matched_domain?: string;
  alternatives?: Array<{
    client_id: string;
    confidence: number;
    domain: string;
  }>;
}

// Request types for client management
export interface CreateClientRequest {
  name: string;
  industry: string;
  timezone: string;
  business_hours: string;
  domains: string[];
  settings?: Partial<ClientConfig['settings']>;
}

export interface UpdateClientRequest extends Partial<CreateClientRequest> {
  status?: 'active' | 'inactive' | 'suspended';
}

export interface UpdateRoutingRequest {
  category: string;
  email: string;
  fallback_email?: string;
  priority?: number;
  conditions?: RoutingRule['conditions'];
}

export interface UpdateBrandingRequest extends Partial<BrandingConfig> {}

export interface CreateAIPromptRequest {
  type: AIPromptConfig['type'];
  name: string;
  prompt: string;
  variables?: Record<string, string>;
  temperature?: number;
  max_tokens?: number;
}
