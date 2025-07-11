<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/authStore';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import ClientList from '$lib/components/clients/ClientList.svelte';
  import type { ClientSummary } from '$lib/types/client';
  import { Building2 } from 'lucide-svelte';

  // Event handlers
  function handleClientSelect(event: CustomEvent<ClientSummary>) {
    const client = event.detail;
    goto(`/dashboard/clients/${client.id}`);
  }

  function handleCreateClient(event: CustomEvent) {
    goto('/dashboard/clients/new');
  }
</script>

<svelte:head>
  <title>Client Management - Email Router</title>
  <meta name="description" content="Manage clients and their email automation configurations." />
</svelte:head>

<AuthGuard requireAuth={true}>
  <div class="min-h-screen bg-gray-50">
    <!-- Page Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Building2 class="h-4 w-4 text-white" />
              </div>
            </div>
            <div class="ml-4">
              <h1 class="text-xl font-semibold text-gray-900">Email Router</h1>
            </div>
          </div>

          <!-- User info -->
          <div class="flex items-center space-x-4">
            {#if $currentUser}
              <span class="text-sm text-gray-700">
                Welcome, {$currentUser.full_name}
              </span>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <!-- Client List Component -->
        <ClientList
          showFilters={true}
          showActions={true}
          on:client-select={handleClientSelect}
          on:create-client={handleCreateClient}
        />
      </div>
    </main>
  </div>
</AuthGuard>
