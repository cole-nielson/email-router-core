<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { theme } from '$lib/stores/theme';
  import ToastContainer from '$lib/components/UI/ToastContainer.svelte';
  import '../app.css';

  // Global authentication state
  let isAuthenticated = false;
  let user: any = null;

  onMount(() => {
    // Initialize theme system
    theme.init();
    
    // Check authentication status
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        isAuthenticated = true;
        user = JSON.parse(userData);
      } catch (error) {
        console.error('Failed to parse user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
  });

  // Handle authentication changes
  function handleAuthChange(event: CustomEvent) {
    isAuthenticated = event.detail.isAuthenticated;
    user = event.detail.user;
  }
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</svelte:head>

<!-- Removed custom auth-change event handler for now -->

<div class="min-h-screen bg-gradient-to-br from-base-100 via-base-200 to-base-100 transition-all duration-300">
  <slot {isAuthenticated} {user} />
  
  <!-- Global toast notifications -->
  <ToastContainer position="top-right" maxToasts={5} />
</div>