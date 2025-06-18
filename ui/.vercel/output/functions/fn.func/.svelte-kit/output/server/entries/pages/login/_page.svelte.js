import { c as create_ssr_component, v as validate_component, b as subscribe, d as createEventDispatcher, f as add_attribute, e as escape } from "../../../chunks/ssr.js";
import "../../../chunks/client.js";
import { a as isLoading, b as authError, i as isAuthenticated } from "../../../chunks/authStore.js";
import { I as Icon, M as Mail } from "../../../chunks/mail.js";
const Alert_circle = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    [
      "line",
      {
        "x1": "12",
        "x2": "12",
        "y1": "8",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "12",
        "x2": "12.01",
        "y1": "16",
        "y2": "16"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "alert-circle" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Eye = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"
      }
    ],
    ["circle", { "cx": "12", "cy": "12", "r": "3" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "eye" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Lock = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "18",
        "height": "11",
        "x": "3",
        "y": "11",
        "rx": "2",
        "ry": "2"
      }
    ],
    ["path", { "d": "M7 11V7a5 5 0 0 1 10 0v4" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "lock" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Log_in = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"
      }
    ],
    ["polyline", { "points": "10 17 15 12 10 7" }],
    [
      "line",
      {
        "x1": "15",
        "x2": "3",
        "y1": "12",
        "y2": "12"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "log-in" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const css$1 = {
  code: "input.svelte-n2jpm7:focus{box-shadow:0 0 0 3px rgba(59, 130, 246, 0.1)}button.svelte-n2jpm7:focus{box-shadow:0 0 0 3px rgba(59, 130, 246, 0.1)}",
  map: '{"version":3,"file":"LoginForm.svelte","sources":["LoginForm.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { createEventDispatcher } from \\"svelte\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport { authService, isLoading, authError } from \\"$lib/stores/authStore\\";\\nimport { LogIn, Mail, Lock, AlertCircle, Eye, EyeOff } from \\"lucide-svelte\\";\\nconst dispatch = createEventDispatcher();\\nlet formData = {\\n  username: \\"\\",\\n  password: \\"\\",\\n  client_id: \\"\\"\\n};\\nlet showPassword = false;\\nlet localError = \\"\\";\\nlet isSubmitting = false;\\n$: isFormValid = formData.username.trim().length >= 3 && formData.password.length >= 8;\\nasync function handleSubmit() {\\n  if (!isFormValid) return;\\n  localError = \\"\\";\\n  isSubmitting = true;\\n  try {\\n    const result = await authService.login(formData);\\n    if (result.success) {\\n      dispatch(\\"success\\", { user: result });\\n      goto(\\"/dashboard\\");\\n    } else {\\n      localError = result.error || \\"Login failed\\";\\n    }\\n  } catch (error) {\\n    localError = \\"An unexpected error occurred\\";\\n    console.error(\\"Login error:\\", error);\\n  } finally {\\n    isSubmitting = false;\\n  }\\n}\\nfunction clearErrors() {\\n  localError = \\"\\";\\n}\\nfunction togglePasswordVisibility() {\\n  showPassword = !showPassword;\\n}\\n<\/script>\\n\\n<div class=\\"min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8\\">\\n  <div class=\\"max-w-md w-full space-y-8\\">\\n    <!-- Header -->\\n    <div class=\\"text-center\\">\\n      <div class=\\"mx-auto h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center\\">\\n        <Mail class=\\"h-6 w-6 text-white\\" />\\n      </div>\\n      <h2 class=\\"mt-6 text-3xl font-extrabold text-gray-900\\">\\n        Email Router Dashboard\\n      </h2>\\n      <p class=\\"mt-2 text-sm text-gray-600\\">\\n        Sign in to manage your AI email automation\\n      </p>\\n    </div>\\n\\n    <!-- Login Form -->\\n    <form class=\\"mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg\\" on:submit|preventDefault={handleSubmit}>\\n      <div class=\\"space-y-4\\">\\n        <!-- Username Field -->\\n        <div>\\n          <label for=\\"username\\" class=\\"block text-sm font-medium text-gray-700 mb-1\\">\\n            Username\\n          </label>\\n          <div class=\\"relative\\">\\n            <input\\n              id=\\"username\\"\\n              name=\\"username\\"\\n              type=\\"text\\"\\n              autocomplete=\\"username\\"\\n              required\\n              bind:value={formData.username}\\n              on:input={clearErrors}\\n              class=\\"appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm\\"\\n              placeholder=\\"Enter your username\\"\\n              disabled={isSubmitting || $isLoading}\\n            />\\n            <div class=\\"absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none\\">\\n              <Mail class=\\"h-4 w-4 text-gray-400\\" />\\n            </div>\\n          </div>\\n        </div>\\n\\n        <!-- Password Field -->\\n        <div>\\n          <label for=\\"password\\" class=\\"block text-sm font-medium text-gray-700 mb-1\\">\\n            Password\\n          </label>\\n          <div class=\\"relative\\">\\n            {#if showPassword}\\n              <input\\n                id=\\"password\\"\\n                name=\\"password\\"\\n                type=\\"text\\"\\n                autocomplete=\\"current-password\\"\\n                required\\n                bind:value={formData.password}\\n                on:input={clearErrors}\\n                class=\\"appearance-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm\\"\\n                placeholder=\\"Enter your password\\"\\n                disabled={isSubmitting || $isLoading}\\n              />\\n            {:else}\\n              <input\\n                id=\\"password\\"\\n                name=\\"password\\"\\n                type=\\"password\\"\\n                autocomplete=\\"current-password\\"\\n                required\\n                bind:value={formData.password}\\n                on:input={clearErrors}\\n                class=\\"appearance-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm\\"\\n                placeholder=\\"Enter your password\\"\\n                disabled={isSubmitting || $isLoading}\\n              />\\n            {/if}\\n            <div class=\\"absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none\\">\\n              <Lock class=\\"h-4 w-4 text-gray-400\\" />\\n            </div>\\n            <button\\n              type=\\"button\\"\\n              class=\\"absolute inset-y-0 right-0 pr-3 flex items-center\\"\\n              on:click={togglePasswordVisibility}\\n              disabled={isSubmitting || $isLoading}\\n            >\\n              {#if showPassword}\\n                <EyeOff class=\\"h-4 w-4 text-gray-400 hover:text-gray-600\\" />\\n              {:else}\\n                <Eye class=\\"h-4 w-4 text-gray-400 hover:text-gray-600\\" />\\n              {/if}\\n            </button>\\n          </div>\\n        </div>\\n\\n        <!-- Client ID Field (Optional) -->\\n        <div>\\n          <label for=\\"client_id\\" class=\\"block text-sm font-medium text-gray-700 mb-1\\">\\n            Client ID \\n            <span class=\\"text-gray-400 text-xs\\">(optional)</span>\\n          </label>\\n          <input\\n            id=\\"client_id\\"\\n            name=\\"client_id\\"\\n            type=\\"text\\"\\n            bind:value={formData.client_id}\\n            on:input={clearErrors}\\n            class=\\"appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm\\"\\n            placeholder=\\"Leave blank for auto-detection\\"\\n            disabled={isSubmitting || $isLoading}\\n          />\\n        </div>\\n      </div>\\n\\n      <!-- Error Display -->\\n      {#if localError || $authError}\\n        <div class=\\"bg-red-50 border border-red-200 rounded-lg p-3\\">\\n          <div class=\\"flex items-center\\">\\n            <AlertCircle class=\\"h-4 w-4 text-red-600 mr-2\\" />\\n            <p class=\\"text-sm text-red-700\\">\\n              {localError || $authError}\\n            </p>\\n          </div>\\n        </div>\\n      {/if}\\n\\n      <!-- Submit Button -->\\n      <div>\\n        <button\\n          type=\\"submit\\"\\n          disabled={!isFormValid || isSubmitting || $isLoading}\\n          class=\\"group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200\\"\\n        >\\n          {#if isSubmitting || $isLoading}\\n            <svg class=\\"animate-spin -ml-1 mr-3 h-4 w-4 text-white\\" xmlns=\\"http://www.w3.org/2000/svg\\" fill=\\"none\\" viewBox=\\"0 0 24 24\\">\\n              <circle class=\\"opacity-25\\" cx=\\"12\\" cy=\\"12\\" r=\\"10\\" stroke=\\"currentColor\\" stroke-width=\\"4\\"></circle>\\n              <path class=\\"opacity-75\\" fill=\\"currentColor\\" d=\\"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z\\"></path>\\n            </svg>\\n            Signing in...\\n          {:else}\\n            <LogIn class=\\"h-4 w-4 mr-2\\" />\\n            Sign In\\n          {/if}\\n        </button>\\n      </div>\\n\\n      <!-- Additional Links -->\\n      <div class=\\"text-center\\">\\n        <p class=\\"text-sm text-gray-600\\">\\n          Need help? Contact your system administrator\\n        </p>\\n      </div>\\n    </form>\\n\\n    <!-- Footer -->\\n    <div class=\\"text-center\\">\\n      <p class=\\"text-xs text-gray-500\\">\\n        © 2024 Email Router. All rights reserved.\\n      </p>\\n    </div>\\n  </div>\\n</div>\\n\\n<style>\\n  /* Custom focus styles for better accessibility */\\n  input:focus {\\n    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);\\n  }\\n  \\n  button:focus {\\n    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);\\n  }\\n</style> "],"names":[],"mappings":"AA4ME,mBAAK,MAAO,CACV,UAAU,CAAE,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,KAAK,EAAE,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAC9C,CAEA,oBAAM,MAAO,CACX,UAAU,CAAE,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,KAAK,EAAE,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAC9C"}'
};
const LoginForm = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let isFormValid;
  let $isLoading, $$unsubscribe_isLoading;
  let $authError, $$unsubscribe_authError;
  $$unsubscribe_isLoading = subscribe(isLoading, (value) => $isLoading = value);
  $$unsubscribe_authError = subscribe(authError, (value) => $authError = value);
  createEventDispatcher();
  let formData = {
    username: "",
    password: "",
    client_id: ""
  };
  let isSubmitting = false;
  $$result.css.add(css$1);
  isFormValid = formData.username.trim().length >= 3 && formData.password.length >= 8;
  $$unsubscribe_isLoading();
  $$unsubscribe_authError();
  return `<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"><div class="max-w-md w-full space-y-8"> <div class="text-center"><div class="mx-auto h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center">${validate_component(Mail, "Mail").$$render($$result, { class: "h-6 w-6 text-white" }, {}, {})}</div> <h2 class="mt-6 text-3xl font-extrabold text-gray-900" data-svelte-h="svelte-yjlh8z">Email Router Dashboard</h2> <p class="mt-2 text-sm text-gray-600" data-svelte-h="svelte-bfl4ep">Sign in to manage your AI email automation</p></div>  <form class="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg"><div class="space-y-4"> <div><label for="username" class="block text-sm font-medium text-gray-700 mb-1" data-svelte-h="svelte-1flnbk7">Username</label> <div class="relative"><input id="username" name="username" type="text" autocomplete="username" required class="appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm svelte-n2jpm7" placeholder="Enter your username" ${$isLoading ? "disabled" : ""}${add_attribute("value", formData.username)}> <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Mail, "Mail").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}</div></div></div>  <div><label for="password" class="block text-sm font-medium text-gray-700 mb-1" data-svelte-h="svelte-kas767">Password</label> <div class="relative">${`<input id="password" name="password" type="password" autocomplete="current-password" required class="appearance-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm svelte-n2jpm7" placeholder="Enter your password" ${$isLoading ? "disabled" : ""}${add_attribute("value", formData.password)}>`} <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Lock, "Lock").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}</div> <button type="button" class="absolute inset-y-0 right-0 pr-3 flex items-center svelte-n2jpm7" ${$isLoading ? "disabled" : ""}>${`${validate_component(Eye, "Eye").$$render(
    $$result,
    {
      class: "h-4 w-4 text-gray-400 hover:text-gray-600"
    },
    {},
    {}
  )}`}</button></div></div>  <div><label for="client_id" class="block text-sm font-medium text-gray-700 mb-1" data-svelte-h="svelte-1w3o316">Client ID 
            <span class="text-gray-400 text-xs">(optional)</span></label> <input id="client_id" name="client_id" type="text" class="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:z-10 sm:text-sm svelte-n2jpm7" placeholder="Leave blank for auto-detection" ${$isLoading ? "disabled" : ""}${add_attribute("value", formData.client_id)}></div></div>  ${$authError ? `<div class="bg-red-50 border border-red-200 rounded-lg p-3"><div class="flex items-center">${validate_component(Alert_circle, "AlertCircle").$$render($$result, { class: "h-4 w-4 text-red-600 mr-2" }, {}, {})} <p class="text-sm text-red-700">${escape($authError)}</p></div></div>` : ``}  <div><button type="submit" ${!isFormValid || isSubmitting || $isLoading ? "disabled" : ""} class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 svelte-n2jpm7">${$isLoading ? `<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            Signing in...` : `${validate_component(Log_in, "LogIn").$$render($$result, { class: "h-4 w-4 mr-2" }, {}, {})}
            Sign In`}</button></div>  <div class="text-center" data-svelte-h="svelte-1ivdgtp"><p class="text-sm text-gray-600">Need help? Contact your system administrator</p></div></form>  <div class="text-center" data-svelte-h="svelte-170z3xg"><p class="text-xs text-gray-500">© 2024 Email Router. All rights reserved.</p></div></div> </div>`;
});
const css = {
  code: ".animate-spin.svelte-1q01t3c{animation:svelte-1q01t3c-spin 1s linear infinite}@keyframes svelte-1q01t3c-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}",
  map: '{"version":3,"file":"+page.svelte","sources":["+page.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { onMount } from \\"svelte\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport { isAuthenticated } from \\"$lib/stores/authStore\\";\\nimport LoginForm from \\"$lib/components/auth/LoginForm.svelte\\";\\nonMount(() => {\\n  if ($isAuthenticated) {\\n    goto(\\"/dashboard\\");\\n  }\\n});\\nfunction handleLoginSuccess() {\\n  console.log(\\"\\\\u2705 Login successful, redirecting to dashboard\\");\\n}\\n<\/script>\\n\\n<svelte:head>\\n  <title>Login - Email Router</title>\\n  <meta name=\\"description\\" content=\\"Sign in to your Email Router dashboard to manage AI-powered email automation.\\" />\\n</svelte:head>\\n\\n<!-- Check if user is already authenticated -->\\n{#if !$isAuthenticated}\\n  <LoginForm on:success={handleLoginSuccess} />\\n{:else}\\n  <!-- Show loading while redirecting -->\\n  <div class=\\"min-h-screen bg-gray-50 flex items-center justify-center\\">\\n    <div class=\\"text-center\\">\\n      <div class=\\"animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto\\"></div>\\n      <p class=\\"mt-4 text-gray-600\\">Redirecting to dashboard...</p>\\n    </div>\\n  </div>\\n{/if}\\n\\n<style>\\n  .animate-spin {\\n    animation: spin 1s linear infinite;\\n  }\\n  \\n  @keyframes spin {\\n    from {\\n      transform: rotate(0deg);\\n    }\\n    to {\\n      transform: rotate(360deg);\\n    }\\n  }\\n</style> "],"names":[],"mappings":"AAiCE,4BAAc,CACZ,SAAS,CAAE,mBAAI,CAAC,EAAE,CAAC,MAAM,CAAC,QAC5B,CAEA,WAAW,mBAAK,CACd,IAAK,CACH,SAAS,CAAE,OAAO,IAAI,CACxB,CACA,EAAG,CACD,SAAS,CAAE,OAAO,MAAM,CAC1B,CACF"}'
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $isAuthenticated, $$unsubscribe_isAuthenticated;
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => $isAuthenticated = value);
  $$result.css.add(css);
  $$unsubscribe_isAuthenticated();
  return `${$$result.head += `<!-- HEAD_svelte-lbf287_START -->${$$result.title = `<title>Login - Email Router</title>`, ""}<meta name="description" content="Sign in to your Email Router dashboard to manage AI-powered email automation."><!-- HEAD_svelte-lbf287_END -->`, ""}  ${!$isAuthenticated ? `${validate_component(LoginForm, "LoginForm").$$render($$result, {}, {}, {})}` : ` <div class="min-h-screen bg-gray-50 flex items-center justify-center" data-svelte-h="svelte-11nx2k2"><div class="text-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto svelte-1q01t3c"></div> <p class="mt-4 text-gray-600">Redirecting to dashboard...</p></div></div>`}`;
});
export {
  Page as default
};
//# sourceMappingURL=_page.svelte.js.map
