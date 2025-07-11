<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/authStore';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import UserForm from '$lib/components/admin/UserForm.svelte';
  import type { UserResponse } from '$lib/types/auth';
  import { Shield, ArrowLeft } from 'lucide-svelte';

  // Get user ID from URL params
  $: userId = parseInt($page.params.userId);

  // Check if user has edit permissions
  $: hasEditAccess = $currentUser?.permissions.includes('users:write') || false;

  // Event handlers
  function handleCancel() {
    goto('/dashboard/admin/users');
  }

  function handleUserSaved(event: CustomEvent<UserResponse>) {
    // User was updated successfully
    console.log('User updated:', event.detail);
    goto('/dashboard/admin/users');
  }

  function handleBack() {
    goto('/dashboard/admin/users');
  }
</script>

<svelte:head>
  <title>Edit User - Email Router Admin</title>
  <meta name="description" content="Edit user information, role, and permissions." />
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
              Back to Users
            </button>

            <div class="flex-shrink-0">
              <div class="h-8 w-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <Shield class="h-4 w-4 text-white" />
              </div>
            </div>
            <div class="ml-4">
              <h1 class="text-xl font-semibold text-gray-900">Edit User</h1>
            </div>
          </div>

          <!-- User info -->
          <div class="flex items-center space-x-4">
            {#if $currentUser}
              <span class="text-sm text-gray-700">
                Welcome, {$currentUser.full_name}
              </span>
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                <Shield class="h-3 w-3 mr-1" />
                {$currentUser.role.replace('_', ' ').toUpperCase()}
              </span>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        {#if hasEditAccess && userId}
          <!-- User Form Component -->
          <UserForm
            mode="edit"
            {userId}
            onCancel={handleCancel}
            on:user-saved={handleUserSaved}
            on:cancel={handleCancel}
          />
        {:else if !userId}
          <!-- Invalid User ID -->
          <div class="bg-red-50 border border-red-200 rounded-lg p-6">
            <div class="flex">
              <Shield class="h-5 w-5 text-red-400" />
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">Invalid User ID</h3>
                <p class="mt-1 text-sm text-red-700">
                  The user ID in the URL is missing or invalid.
                </p>
                <button
                  on:click={handleBack}
                  class="mt-2 text-sm text-red-600 hover:text-red-500"
                >
                  Return to user list
                </button>
              </div>
            </div>
          </div>
        {:else}
          <!-- Access Denied -->
          <div class="bg-red-50 border border-red-200 rounded-lg p-6">
            <div class="flex">
              <Shield class="h-5 w-5 text-red-400" />
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">Access Denied</h3>
                <p class="mt-1 text-sm text-red-700">
                  You do not have permission to edit users.
                </p>
                <button
                  on:click={handleBack}
                  class="mt-2 text-sm text-red-600 hover:text-red-500"
                >
                  Return to user list
                </button>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </main>
  </div>
</AuthGuard>
