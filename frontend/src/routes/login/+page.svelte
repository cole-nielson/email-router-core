<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isAuthenticated } from '$lib/stores/authStore';
  import LoginForm from '$lib/components/auth/LoginForm.svelte';

  // Redirect to dashboard if already authenticated
  onMount(() => {
    if ($isAuthenticated) {
      goto('/dashboard');
    }
  });

  // Handle successful login
  function handleLoginSuccess() {
    // The LoginForm component will handle the redirect
    console.log('✅ Login successful, redirecting to dashboard');
  }
</script>

<svelte:head>
  <title>Login - Email Router</title>
  <meta name="description" content="Sign in to your Email Router dashboard to manage AI-powered email automation." />
</svelte:head>

<!-- Check if user is already authenticated -->
{#if !$isAuthenticated}
  <LoginForm on:success={handleLoginSuccess} />
{:else}
  <!-- Show loading while redirecting -->
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Redirecting to dashboard...</p>
    </div>
  </div>
{/if}

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