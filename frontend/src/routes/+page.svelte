<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isAuthenticated, isLoading } from '$lib/stores/authStore';

  // Redirect based on authentication status
  onMount(() => {
    // Wait for auth to initialize
    const unsubscribe = isLoading.subscribe(loading => {
      if (!loading) {
        if ($isAuthenticated) {
          goto('/dashboard');
        } else {
          goto('/login');
        }
        unsubscribe();
      }
    });
  });
</script>

<svelte:head>
  <title>Email Router - AI-Powered Email Automation</title>
  <meta name="description" content="Intelligent email classification and routing with AI-powered automation." />
</svelte:head>

<!-- Show loading while determining redirect -->
<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
  <div class="text-center">
    <div class="mx-auto h-16 w-16 bg-blue-600 rounded-xl flex items-center justify-center mb-6">
      <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
      </svg>
    </div>
    
    <h1 class="text-3xl font-bold text-gray-900 mb-2">
      Email Router
    </h1>
    
    <p class="text-gray-600 mb-6">
      AI-Powered Email Automation Platform
    </p>
    
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
    <p class="mt-4 text-sm text-gray-500">Loading...</p>
  </div>
</div>

<style>
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>