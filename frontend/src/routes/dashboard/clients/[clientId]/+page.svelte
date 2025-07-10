<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/authStore';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import ClientDetail from '$lib/components/clients/ClientDetail.svelte';
  import type { ClientConfig } from '$lib/types/client';
  import { Building2, ArrowLeft } from 'lucide-svelte';

  // Get client ID from URL params
  $: clientId = $page.params.clientId;

  // Get tab from query params
  $: activeTab = ($page.url.searchParams.get('tab') as any) || 'overview';

  // Event handlers
  function handleBack() {
    goto('/dashboard/clients');
  }

  function handleTabChange(event: CustomEvent<string>) {
    const tab = event.detail;
    const url = new URL($page.url);
    url.searchParams.set('tab', tab);
    goto(url.pathname + url.search, { replaceState: true });
  }

  function handleClientUpdated(event: CustomEvent<ClientConfig>) {
    // Client was updated, could show success message or refresh
    console.log('Client updated:', event.detail);
  }
</script>

<svelte:head>
  <title>Client Details - Email Router</title>
  <meta name="description" content="View and manage client configuration and settings." />
</svelte:head>

<AuthGuard requireAuth={true}>
  <div class="min-h-screen bg-gray-50">
    <!-- Page Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <!-- Back Button -->
            <button
              on:click={handleBack}
              class="mr-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
            >
              <ArrowLeft class="h-4 w-4 mr-1" />
              Back to Clients
            </button>

            <div class="flex-shrink-0">
              <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Building2 class="h-4 w-4 text-white" />
              </div>
            </div>
            <div class="ml-4">
              <h1 class="text-xl font-semibold text-gray-900">Client Details</h1>
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
        <!-- Client Detail Component -->
        {#if clientId}
          <ClientDetail
            {clientId}
            {activeTab}
            on:tab-change={handleTabChange}
            on:client-updated={handleClientUpdated}
          />
        {:else}
          <div class="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 class="text-sm font-medium text-red-800">Invalid Client ID</h3>
            <p class="mt-1 text-sm text-red-700">
              The client ID in the URL is missing or invalid.
            </p>
            <button
              on:click={handleBack}
              class="mt-2 text-sm text-red-600 hover:text-red-500"
            >
              Return to client list
            </button>
          </div>
        {/if}
      </div>
    </main>
  </div>
</AuthGuard>
