import { c as create_ssr_component, v as validate_component, b as subscribe, e as escape } from "../../../chunks/ssr.js";
import { g as goto } from "../../../chunks/client.js";
import { c as currentUser, i as isAuthenticated, a as isLoading } from "../../../chunks/authStore.js";
import { I as Icon, M as Mail } from "../../../chunks/mail.js";
const Alert_triangle = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"
      }
    ],
    ["path", { "d": "M12 9v4" }],
    ["path", { "d": "M12 17h.01" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "alert-triangle" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Bar_chart_3 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M3 3v18h18" }],
    ["path", { "d": "M18 17V9" }],
    ["path", { "d": "M13 17V5" }],
    ["path", { "d": "M8 17v-3" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bar-chart-3" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Bell = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"
      }
    ],
    ["path", { "d": "M10.3 21a1.94 1.94 0 0 0 3.4 0" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bell" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Clock = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["polyline", { "points": "12 6 12 12 16 14" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "clock" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Log_out = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"
      }
    ],
    ["polyline", { "points": "16 17 21 12 16 7" }],
    [
      "line",
      {
        "x1": "21",
        "x2": "9",
        "y1": "12",
        "y2": "12"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "log-out" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Settings = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
      }
    ],
    ["circle", { "cx": "12", "cy": "12", "r": "3" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "settings" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Shield = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "shield" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const User = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "12", "cy": "7", "r": "4" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const css = {
  code: ".animate-spin.svelte-1q01t3c{animation:svelte-1q01t3c-spin 1s linear infinite}@keyframes svelte-1q01t3c-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}",
  map: '{"version":3,"file":"AuthGuard.svelte","sources":["AuthGuard.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { onMount } from \\"svelte\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport { page } from \\"$app/stores\\";\\nimport { isAuthenticated, currentUser, isLoading } from \\"$lib/stores/authStore\\";\\nimport { Shield, AlertTriangle } from \\"lucide-svelte\\";\\nexport let requireAuth = true;\\nexport let requiredRole = null;\\nexport let requiredPermission = null;\\nexport let fallbackPath = \\"/login\\";\\nlet isAuthorized = false;\\nlet authorizationError = \\"\\";\\n$: checkAuthorization($isAuthenticated, $currentUser);\\nfunction checkAuthorization(authenticated, user) {\\n  isAuthorized = false;\\n  authorizationError = \\"\\";\\n  if (!requireAuth) {\\n    isAuthorized = true;\\n    return;\\n  }\\n  if (!authenticated) {\\n    authorizationError = \\"Authentication required\\";\\n    if (!$isLoading) {\\n      goto(fallbackPath);\\n    }\\n    return;\\n  }\\n  if (!user) {\\n    authorizationError = \\"User data not available\\";\\n    return;\\n  }\\n  if (requiredRole) {\\n    if (user.role !== requiredRole && user.role !== \\"super_admin\\") {\\n      authorizationError = `Access denied. Required role: ${requiredRole}`;\\n      return;\\n    }\\n  }\\n  if (requiredPermission) {\\n    if (!hasPermission(user, requiredPermission)) {\\n      authorizationError = `Access denied. Required permission: ${requiredPermission}`;\\n      return;\\n    }\\n  }\\n  isAuthorized = true;\\n}\\nfunction hasPermission(user, permission) {\\n  if (!user) return false;\\n  if (user.role === \\"super_admin\\") return true;\\n  switch (user.role) {\\n    case \\"client_admin\\":\\n      return [\\n        \\"client:read\\",\\n        \\"client:write\\",\\n        \\"routing:read\\",\\n        \\"routing:write\\",\\n        \\"branding:read\\",\\n        \\"branding:write\\",\\n        \\"response_times:read\\",\\n        \\"response_times:write\\",\\n        \\"ai_prompts:read\\",\\n        \\"ai_prompts:write\\",\\n        \\"users:read\\",\\n        \\"users:write\\"\\n      ].includes(permission);\\n    case \\"client_user\\":\\n      return [\\n        \\"client:read\\",\\n        \\"routing:read\\",\\n        \\"branding:read\\",\\n        \\"response_times:read\\",\\n        \\"ai_prompts:read\\"\\n      ].includes(permission);\\n    case \\"api_user\\":\\n      return [\\"client:read\\"].includes(permission);\\n    default:\\n      return false;\\n  }\\n}\\nonMount(() => {\\n  checkAuthorization($isAuthenticated, $currentUser);\\n});\\n<\/script>\\n\\n{#if $isLoading}\\n  <!-- Loading state -->\\n  <div class=\\"min-h-screen bg-gray-50 flex items-center justify-center\\">\\n    <div class=\\"text-center\\">\\n      <div class=\\"animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto\\"></div>\\n      <p class=\\"mt-4 text-gray-600\\">Checking authentication...</p>\\n    </div>\\n  </div>\\n{:else if authorizationError}\\n  <!-- Authorization error -->\\n  <div class=\\"min-h-screen bg-gray-50 flex items-center justify-center p-4\\">\\n    <div class=\\"max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center\\">\\n      <div class=\\"mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mb-4\\">\\n        <AlertTriangle class=\\"h-6 w-6 text-red-600\\" />\\n      </div>\\n      \\n      <h2 class=\\"text-xl font-semibold text-gray-900 mb-2\\">\\n        Access Denied\\n      </h2>\\n      \\n      <p class=\\"text-gray-600 mb-4\\">\\n        {authorizationError}\\n      </p>\\n      \\n      <button\\n        on:click={() => goto(fallbackPath)}\\n        class=\\"inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500\\"\\n      >\\n        <Shield class=\\"h-4 w-4 mr-2\\" />\\n        Go to Login\\n      </button>\\n    </div>\\n  </div>\\n{:else if isAuthorized}\\n  <!-- Authorized - render children -->\\n  <slot />\\n{:else}\\n  <!-- Fallback loading -->\\n  <div class=\\"min-h-screen bg-gray-50 flex items-center justify-center\\">\\n    <div class=\\"text-center\\">\\n      <div class=\\"animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto\\"></div>\\n      <p class=\\"mt-4 text-gray-600\\">Loading...</p>\\n    </div>\\n  </div>\\n{/if}\\n\\n<style>\\n  .animate-spin {\\n    animation: spin 1s linear infinite;\\n  }\\n  \\n  @keyframes spin {\\n    from {\\n      transform: rotate(0deg);\\n    }\\n    to {\\n      transform: rotate(360deg);\\n    }\\n  }\\n</style> "],"names":[],"mappings":"AAiIE,4BAAc,CACZ,SAAS,CAAE,mBAAI,CAAC,EAAE,CAAC,MAAM,CAAC,QAC5B,CAEA,WAAW,mBAAK,CACd,IAAK,CACH,SAAS,CAAE,OAAO,IAAI,CACxB,CACA,EAAG,CACD,SAAS,CAAE,OAAO,MAAM,CAC1B,CACF"}'
};
function hasPermission(user, permission) {
  if (!user) return false;
  if (user.role === "super_admin") return true;
  switch (user.role) {
    case "client_admin":
      return [
        "client:read",
        "client:write",
        "routing:read",
        "routing:write",
        "branding:read",
        "branding:write",
        "response_times:read",
        "response_times:write",
        "ai_prompts:read",
        "ai_prompts:write",
        "users:read",
        "users:write"
      ].includes(permission);
    case "client_user":
      return [
        "client:read",
        "routing:read",
        "branding:read",
        "response_times:read",
        "ai_prompts:read"
      ].includes(permission);
    case "api_user":
      return ["client:read"].includes(permission);
    default:
      return false;
  }
}
const AuthGuard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $currentUser, $$unsubscribe_currentUser;
  let $isAuthenticated, $$unsubscribe_isAuthenticated;
  let $isLoading, $$unsubscribe_isLoading;
  $$unsubscribe_currentUser = subscribe(currentUser, (value) => $currentUser = value);
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => $isAuthenticated = value);
  $$unsubscribe_isLoading = subscribe(isLoading, (value) => $isLoading = value);
  let { requireAuth = true } = $$props;
  let { requiredRole = null } = $$props;
  let { requiredPermission = null } = $$props;
  let { fallbackPath = "/login" } = $$props;
  let isAuthorized = false;
  let authorizationError = "";
  function checkAuthorization(authenticated, user) {
    isAuthorized = false;
    authorizationError = "";
    if (!requireAuth) {
      isAuthorized = true;
      return;
    }
    if (!authenticated) {
      authorizationError = "Authentication required";
      if (!$isLoading) {
        goto();
      }
      return;
    }
    if (!user) {
      authorizationError = "User data not available";
      return;
    }
    if (requiredRole) {
      if (user.role !== requiredRole && user.role !== "super_admin") {
        authorizationError = `Access denied. Required role: ${requiredRole}`;
        return;
      }
    }
    if (requiredPermission) {
      if (!hasPermission(user, requiredPermission)) {
        authorizationError = `Access denied. Required permission: ${requiredPermission}`;
        return;
      }
    }
    isAuthorized = true;
  }
  if ($$props.requireAuth === void 0 && $$bindings.requireAuth && requireAuth !== void 0) $$bindings.requireAuth(requireAuth);
  if ($$props.requiredRole === void 0 && $$bindings.requiredRole && requiredRole !== void 0) $$bindings.requiredRole(requiredRole);
  if ($$props.requiredPermission === void 0 && $$bindings.requiredPermission && requiredPermission !== void 0) $$bindings.requiredPermission(requiredPermission);
  if ($$props.fallbackPath === void 0 && $$bindings.fallbackPath && fallbackPath !== void 0) $$bindings.fallbackPath(fallbackPath);
  $$result.css.add(css);
  {
    checkAuthorization($isAuthenticated, $currentUser);
  }
  $$unsubscribe_currentUser();
  $$unsubscribe_isAuthenticated();
  $$unsubscribe_isLoading();
  return `${$isLoading ? ` <div class="min-h-screen bg-gray-50 flex items-center justify-center" data-svelte-h="svelte-11rdv1n"><div class="text-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto svelte-1q01t3c"></div> <p class="mt-4 text-gray-600">Checking authentication...</p></div></div>` : `${authorizationError ? ` <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4"><div class="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center"><div class="mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mb-4">${validate_component(Alert_triangle, "AlertTriangle").$$render($$result, { class: "h-6 w-6 text-red-600" }, {}, {})}</div> <h2 class="text-xl font-semibold text-gray-900 mb-2" data-svelte-h="svelte-jf9kji">Access Denied</h2> <p class="text-gray-600 mb-4">${escape(authorizationError)}</p> <button class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">${validate_component(Shield, "Shield").$$render($$result, { class: "h-4 w-4 mr-2" }, {}, {})}
        Go to Login</button></div></div>` : `${isAuthorized ? ` ${slots.default ? slots.default({}) : ``}` : ` <div class="min-h-screen bg-gray-50 flex items-center justify-center" data-svelte-h="svelte-1ybd4c3"><div class="text-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto svelte-1q01t3c"></div> <p class="mt-4 text-gray-600">Loading...</p></div></div>`}`}`}`;
});
function getRoleBadgeColor(role) {
  switch (role) {
    case "super_admin":
      return "bg-purple-100 text-purple-800";
    case "client_admin":
      return "bg-blue-100 text-blue-800";
    case "client_user":
      return "bg-green-100 text-green-800";
    case "api_user":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
}
function formatDate(dateString) {
  return new Date(dateString).toLocaleString();
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $currentUser, $$unsubscribe_currentUser;
  $$unsubscribe_currentUser = subscribe(currentUser, (value) => $currentUser = value);
  $$unsubscribe_currentUser();
  return `${$$result.head += `<!-- HEAD_svelte-1q61mzl_START -->${$$result.title = `<title>Dashboard - Email Router</title>`, ""}<meta name="description" content="Email Router dashboard for managing AI-powered email automation."><!-- HEAD_svelte-1q61mzl_END -->`, ""} ${validate_component(AuthGuard, "AuthGuard").$$render($$result, { requireAuth: true }, {}, {
    default: () => {
      return `<div class="min-h-screen bg-gray-50"> <header class="bg-white shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div class="flex justify-between items-center h-16"> <div class="flex items-center"><div class="flex-shrink-0"><div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">${validate_component(Mail, "Mail").$$render($$result, { class: "h-4 w-4 text-white" }, {}, {})}</div></div> <div class="ml-4" data-svelte-h="svelte-1q0878y"><h1 class="text-xl font-semibold text-gray-900">Email Router</h1></div></div>  <div class="flex items-center space-x-4">${$currentUser ? `<div class="flex items-center space-x-3"><span class="text-sm text-gray-700">Welcome, ${escape($currentUser.full_name)}</span> <button class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">${validate_component(Log_out, "LogOut").$$render($$result, { class: "h-4 w-4 mr-2" }, {}, {})}
                  Logout</button></div>` : ``}</div></div></div></header>  <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"><div class="px-4 py-6 sm:px-0"> <div class="bg-white overflow-hidden shadow rounded-lg mb-6" data-svelte-h="svelte-5p0fh4"><div class="px-4 py-5 sm:p-6"><h2 class="text-lg leading-6 font-medium text-gray-900 mb-4">Welcome to Email Router Dashboard</h2> <p class="text-sm text-gray-600">Your AI-powered email automation platform is ready. This is the foundation for Week 1 authentication implementation.</p></div></div>  ${$currentUser ? `<div class="bg-white overflow-hidden shadow rounded-lg mb-6"><div class="px-4 py-5 sm:p-6"><div class="flex items-center mb-4">${validate_component(User, "User").$$render($$result, { class: "h-5 w-5 text-gray-400 mr-2" }, {}, {})} <h3 class="text-lg leading-6 font-medium text-gray-900" data-svelte-h="svelte-7b0mlm">User Information</h3></div> <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2"><div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-4lh61b">Full Name</dt> <dd class="mt-1 text-sm text-gray-900">${escape($currentUser.full_name)}</dd> </div><div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-1ecozuf">Username</dt> <dd class="mt-1 text-sm text-gray-900">${escape($currentUser.username)}</dd> </div><div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-qj6i1v">Email</dt> <dd class="mt-1 text-sm text-gray-900">${escape($currentUser.email)}</dd> </div><div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-1gecueb">Role</dt> <dd class="mt-1"><span class="${"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium " + escape(getRoleBadgeColor($currentUser.role), true)}">${validate_component(Shield, "Shield").$$render($$result, { class: "h-3 w-3 mr-1" }, {}, {})} ${escape($currentUser.role.replace("_", " ").toUpperCase())}</span></dd> </div><div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-xnqksl">Status</dt> <dd class="mt-1"><span class="${"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium " + escape(
        $currentUser.status === "active" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800",
        true
      )}">${escape($currentUser.status.toUpperCase())}</span></dd> </div>${$currentUser.client_id ? `<div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-63oh4r">Client ID</dt> <dd class="mt-1 text-sm text-gray-900">${escape($currentUser.client_id)}</dd></div>` : ``}<div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-1fwnerm">Account Created</dt> <dd class="mt-1 text-sm text-gray-900"><div class="flex items-center">${validate_component(Clock, "Clock").$$render($$result, { class: "h-4 w-4 text-gray-400 mr-1" }, {}, {})} ${escape(formatDate($currentUser.created_at))}</div></dd> </div>${$currentUser.last_login_at ? `<div><dt class="text-sm font-medium text-gray-500" data-svelte-h="svelte-1oazw3y">Last Login</dt> <dd class="mt-1 text-sm text-gray-900"><div class="flex items-center">${validate_component(Clock, "Clock").$$render($$result, { class: "h-4 w-4 text-gray-400 mr-1" }, {}, {})} ${escape(formatDate($currentUser.last_login_at))}</div></dd></div>` : ``}</dl></div></div>` : ``}  <div class="bg-white overflow-hidden shadow rounded-lg"><div class="px-4 py-5 sm:p-6"><h3 class="text-lg leading-6 font-medium text-gray-900 mb-4" data-svelte-h="svelte-112x5j">Quick Actions</h3> <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"> <button disabled class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"><div class="flex items-center">${validate_component(Settings, "Settings").$$render($$result, { class: "h-6 w-6 text-gray-400" }, {}, {})} <div class="ml-3" data-svelte-h="svelte-bni7v9"><p class="text-sm font-medium text-gray-900">Client Management</p> <p class="text-sm text-gray-500">Coming in Week 2</p></div></div></button> <button disabled class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"><div class="flex items-center">${validate_component(Bar_chart_3, "BarChart3").$$render($$result, { class: "h-6 w-6 text-gray-400" }, {}, {})} <div class="ml-3" data-svelte-h="svelte-gzkcdd"><p class="text-sm font-medium text-gray-900">System Monitoring</p> <p class="text-sm text-gray-500">Coming in Week 3</p></div></div></button> <button disabled class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"><div class="flex items-center">${validate_component(Bell, "Bell").$$render($$result, { class: "h-6 w-6 text-gray-400" }, {}, {})} <div class="ml-3" data-svelte-h="svelte-ypsnp2"><p class="text-sm font-medium text-gray-900">Advanced Features</p> <p class="text-sm text-gray-500">Coming in Week 4</p></div></div></button></div></div></div>  <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4"><div class="flex">${validate_component(Shield, "Shield").$$render($$result, { class: "h-5 w-5 text-blue-600 mt-0.5" }, {}, {})} <div class="ml-3" data-svelte-h="svelte-1ibqadg"><h3 class="text-sm font-medium text-blue-800">✅ Week 1: Authentication Foundation Complete!</h3> <div class="mt-2 text-sm text-blue-700"><ul class="list-disc list-inside space-y-1"><li>JWT authentication system ✅</li> <li>Login/logout flows ✅</li> <li>Route protection ✅</li> <li>User profile display ✅</li> <li>Token management with auto-refresh ✅</li></ul></div> <div class="mt-3"><p class="text-sm text-blue-700"><strong>Next:</strong> Week 2 - Client Management Dashboard</p></div></div></div></div></div></main></div>`;
    }
  })}`;
});
export {
  Page as default
};
//# sourceMappingURL=_page.svelte.js.map
