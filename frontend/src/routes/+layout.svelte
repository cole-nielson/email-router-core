<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { authService } from '$lib/stores/authStore';
  import '../app.css';

  // Initialize authentication when the app loads
  onMount(() => {
    if (browser) {
      // Auth service will automatically initialize from localStorage
      console.log('🚀 App initialized, auth service will handle authentication state');
    }
  });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</svelte:head>

<main>
  <slot />
</main>