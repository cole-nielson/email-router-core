/**
 * Client Management Service
 * Handles client configuration, routing rules, branding, and domain management.
 */

import { BaseService, type ServiceResponse, type PaginationParams, type PaginationResponse } from './base.service';
import type {
  ClientSummary,
  ClientConfig,
  RoutingConfig,
  RoutingRule,
  BrandingConfig,
  AIPromptConfig,
  ClientValidationResult,
  DomainResolutionResult,
  CreateClientRequest,
  UpdateClientRequest,
  UpdateRoutingRequest,
  UpdateBrandingRequest,
  CreateAIPromptRequest,
} from '$lib/types/client';

export interface ClientFilters {
  search?: string;
  status?: 'active' | 'inactive' | 'suspended';
  industry?: string;
  health_status?: 'healthy' | 'warning' | 'error';
}

export interface ClientListResponse {
  clients: ClientSummary[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

/**
 * ClientService handles all client management operations
 */
export class ClientService extends BaseService {

  // =============================================================================
  // CLIENT OPERATIONS
  // =============================================================================

  /**
   * Get paginated list of clients with filtering
   */
  async getClients(
    pagination: PaginationParams = {},
    filters: ClientFilters = {}
  ): Promise<ServiceResponse<PaginationResponse<ClientSummary>>> {

    const queryParams = this.buildQueryParams({
      ...pagination,
      ...filters,
      limit: pagination.limit ?? 20,
      offset: pagination.offset ?? 0,
    });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<ClientListResponse>(`/api/v1/clients${queryParams}`);

      return {
        items: response.clients,
        total: response.pagination.total,
        limit: response.pagination.limit,
        offset: response.pagination.offset,
        has_more: response.pagination.has_more,
      };
    }, 'Get clients list');
  }

  /**
   * Get detailed client configuration
   */
  async getClient(clientId: string): Promise<ServiceResponse<ClientConfig>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<ClientConfig>(`/api/v2/config/clients/${clientId}`);
    }, 'Get client details');
  }

  /**
   * Create a new client (super admin only)
   */
  async createClient(request: CreateClientRequest): Promise<ServiceResponse<ClientConfig>> {
    this.validateRequired(request, ['name', 'industry', 'timezone', 'domains']);

    return this.executeRequest(async () => {
      const client = await this.apiClient.request<ClientConfig>('/api/v2/config/clients', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      this.log('Client created', { clientId: client.id, name: request.name });
      return client;
    }, 'Client creation');
  }

  /**
   * Update client configuration
   */
  async updateClient(clientId: string, request: UpdateClientRequest): Promise<ServiceResponse<ClientConfig>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      const client = await this.apiClient.request<ClientConfig>(`/api/v2/config/clients/${clientId}`, {
        method: 'PUT',
        body: JSON.stringify(request),
      });

      this.log('Client updated', { clientId });
      return client;
    }, 'Client update');
  }

  /**
   * Validate client configuration
   */
  async validateClient(clientId: string): Promise<ServiceResponse<ClientValidationResult>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<ClientValidationResult>(`/api/v1/clients/${clientId}/validate`, {
        method: 'POST',
      });
    }, 'Client validation');
  }

  // =============================================================================
  // ROUTING CONFIGURATION
  // =============================================================================

  /**
   * Get client routing configuration
   */
  async getRoutingConfig(clientId: string): Promise<ServiceResponse<RoutingConfig>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<RoutingConfig>(`/api/v2/config/clients/${clientId}/routing`);
    }, 'Get routing configuration');
  }

  /**
   * Update specific routing rule
   */
  async updateRoutingRule(
    clientId: string,
    category: string,
    request: UpdateRoutingRequest
  ): Promise<ServiceResponse<RoutingRule>> {
    this.validateRequired({ clientId, category }, ['clientId', 'category']);
    this.validateRequired(request, ['email']);

    return this.executeRequest(async () => {
      const rule = await this.apiClient.request<RoutingRule>(
        `/api/v2/config/clients/${clientId}/routing/${category}`,
        {
          method: 'PUT',
          body: JSON.stringify(request),
        }
      );

      this.log('Routing rule updated', { clientId, category, email: request.email });
      return rule;
    }, 'Routing rule update');
  }

  /**
   * Delete routing rule
   */
  async deleteRoutingRule(clientId: string, category: string): Promise<ServiceResponse<void>> {
    this.validateRequired({ clientId, category }, ['clientId', 'category']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>(`/api/v2/config/clients/${clientId}/routing/${category}`, {
        method: 'DELETE',
      });

      this.log('Routing rule deleted', { clientId, category });
    }, 'Routing rule deletion');
  }

  // =============================================================================
  // BRANDING CONFIGURATION
  // =============================================================================

  /**
   * Get client branding configuration
   */
  async getBrandingConfig(clientId: string): Promise<ServiceResponse<BrandingConfig>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<BrandingConfig>(`/api/v2/config/clients/${clientId}/branding`);
    }, 'Get branding configuration');
  }

  /**
   * Update client branding configuration
   */
  async updateBrandingConfig(
    clientId: string,
    request: UpdateBrandingRequest
  ): Promise<ServiceResponse<BrandingConfig>> {
    this.validateRequired({ clientId }, ['clientId']);

    return this.executeRequest(async () => {
      const branding = await this.apiClient.request<BrandingConfig>(
        `/api/v2/config/clients/${clientId}/branding`,
        {
          method: 'PUT',
          body: JSON.stringify(request),
        }
      );

      this.log('Branding updated', { clientId, company_name: request.company_name });
      return branding;
    }, 'Branding update');
  }

  // =============================================================================
  // AI PROMPT CONFIGURATION
  // =============================================================================

  /**
   * Get AI prompts for client
   */
  async getAIPrompts(clientId: string, type?: string): Promise<ServiceResponse<AIPromptConfig[]>> {
    this.validateRequired({ clientId }, ['clientId']);

    const queryParams = type ? this.buildQueryParams({ type }) : '';

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{ prompts: AIPromptConfig[] }>(
        `/api/v2/config/clients/${clientId}/ai-prompts${queryParams}`
      );
      return response.prompts;
    }, 'Get AI prompts');
  }

  /**
   * Create new AI prompt
   */
  async createAIPrompt(
    clientId: string,
    request: CreateAIPromptRequest
  ): Promise<ServiceResponse<AIPromptConfig>> {
    this.validateRequired({ clientId }, ['clientId']);
    this.validateRequired(request, ['type', 'name', 'prompt']);

    return this.executeRequest(async () => {
      const prompt = await this.apiClient.request<AIPromptConfig>(
        `/api/v2/config/clients/${clientId}/ai-prompts`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      this.log('AI prompt created', { clientId, type: request.type, name: request.name });
      return prompt;
    }, 'AI prompt creation');
  }

  /**
   * Update AI prompt
   */
  async updateAIPrompt(
    clientId: string,
    promptType: string,
    request: Partial<CreateAIPromptRequest>
  ): Promise<ServiceResponse<AIPromptConfig>> {
    this.validateRequired({ clientId, promptType }, ['clientId', 'promptType']);

    return this.executeRequest(async () => {
      const prompt = await this.apiClient.request<AIPromptConfig>(
        `/api/v2/config/clients/${clientId}/ai-prompts/${promptType}`,
        {
          method: 'PUT',
          body: JSON.stringify(request),
        }
      );

      this.log('AI prompt updated', { clientId, promptType });
      return prompt;
    }, 'AI prompt update');
  }

  // =============================================================================
  // DOMAIN MANAGEMENT
  // =============================================================================

  /**
   * Test domain resolution
   */
  async resolveDomain(domain: string): Promise<ServiceResponse<DomainResolutionResult>> {
    this.validateRequired({ domain }, ['domain']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<DomainResolutionResult>('/api/v1/domain/resolve', {
        method: 'POST',
        body: JSON.stringify({ domain }),
      });
    }, 'Domain resolution');
  }

  /**
   * Add domain to client
   */
  async addDomain(clientId: string, domain: string): Promise<ServiceResponse<void>> {
    this.validateRequired({ clientId, domain }, ['clientId', 'domain']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>(`/api/v2/config/clients/${clientId}/domains`, {
        method: 'POST',
        body: JSON.stringify({ domain }),
      });

      this.log('Domain added', { clientId, domain });
    }, 'Domain addition');
  }

  /**
   * Remove domain from client
   */
  async removeDomain(clientId: string, domain: string): Promise<ServiceResponse<void>> {
    this.validateRequired({ clientId, domain }, ['clientId', 'domain']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>(`/api/v2/config/clients/${clientId}/domains/${encodeURIComponent(domain)}`, {
        method: 'DELETE',
      });

      this.log('Domain removed', { clientId, domain });
    }, 'Domain removal');
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  /**
   * Get client status summary for dashboard
   */
  async getClientStatusSummary(): Promise<ServiceResponse<{
    total_clients: number;
    active_clients: number;
    healthy_clients: number;
    clients_with_issues: number;
    last_updated: string;
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/clients/status-summary');
    }, 'Get client status summary');
  }

  /**
   * Check if client name is available
   */
  async checkClientNameAvailability(name: string): Promise<ServiceResponse<{ available: boolean }>> {
    this.validateRequired({ name }, ['name']);

    const queryParams = this.buildQueryParams({ name });

    return this.executeRequest(async () => {
      return await this.apiClient.request(`/api/v1/clients/check-name${queryParams}`);
    }, 'Check client name availability');
  }
}

// Export singleton instance
export const clientService = new ClientService();
