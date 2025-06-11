import { c as create_ssr_component, v as validate_component, b as subscribe$1, e as each, d as escape } from "../../chunks/ssr.js";
import "../../chunks/client.js";
import { d as derived, w as writable } from "../../chunks/index.js";
import { I as Icon, A as Alert_triangle, X as X_circle, C as Check_circle } from "../../chunks/x-circle.js";
const browser$1 = typeof window !== "undefined";
const createThemeStore = () => {
  const getInitialTheme = () => {
    if (!browser$1) return "light";
    const stored = localStorage.getItem("theme");
    if (stored && (stored === "light" || stored === "dark")) {
      return stored;
    }
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  };
  const { subscribe: subscribe2, set, update: update2 } = writable(getInitialTheme());
  return {
    subscribe: subscribe2,
    // Toggle between light and dark themes
    toggle: () => {
      update2((theme2) => {
        const newTheme = theme2 === "light" ? "dark" : "light";
        if (browser$1) {
          localStorage.setItem("theme", newTheme);
          document.documentElement.setAttribute("data-theme", newTheme);
          if (newTheme === "dark") {
            document.documentElement.classList.add("dark");
          } else {
            document.documentElement.classList.remove("dark");
          }
        }
        return newTheme;
      });
    },
    // Set specific theme
    setTheme: (newTheme) => {
      set(newTheme);
      if (browser$1) {
        localStorage.setItem("theme", newTheme);
        document.documentElement.setAttribute("data-theme", newTheme);
        if (newTheme === "dark") {
          document.documentElement.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
        }
      }
    },
    // Initialize theme on app start
    init: () => {
      if (!browser$1) return;
      const current = getInitialTheme();
      set(current);
      document.documentElement.setAttribute("data-theme", current);
      if (current === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = (e) => {
        const stored = localStorage.getItem("theme");
        if (!stored) {
          const newTheme = e.matches ? "dark" : "light";
          set(newTheme);
          document.documentElement.setAttribute("data-theme", newTheme);
          if (newTheme === "dark") {
            document.documentElement.classList.add("dark");
          } else {
            document.documentElement.classList.remove("dark");
          }
        }
      };
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener("change", handleChange);
      } else {
        mediaQuery.addListener(handleChange);
      }
    }
  };
};
const theme = createThemeStore();
derived(theme, ($theme) => $theme === "dark");
derived(theme, ($theme) => $theme === "light");
const prefersReducedMotion = writable(false);
if (browser$1) {
  const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  prefersReducedMotion.set(mediaQuery.matches);
  const handleMotionChange = (e) => {
    prefersReducedMotion.set(e.matches);
  };
  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", handleMotionChange);
  } else {
    mediaQuery.addListener(handleMotionChange);
  }
}
const browser = typeof window !== "undefined";
const { subscribe, update } = writable([]);
const timeouts = /* @__PURE__ */ new Map();
const toasts = {
  subscribe,
  // Add a new toast
  add: (toast) => {
    const id = crypto?.randomUUID() || Math.random().toString(36).substring(2);
    const newToast = {
      id,
      timestamp: Date.now(),
      duration: 5e3,
      // Default 5 seconds
      dismissible: true,
      ...toast
    };
    update((toasts2) => [...toasts2, newToast]);
    if (newToast.duration && newToast.duration > 0) {
      const timeout = setTimeout(() => {
        toasts.dismiss(id);
      }, newToast.duration);
      timeouts.set(id, timeout);
    }
    return id;
  },
  // Dismiss a specific toast
  dismiss: (id) => {
    update((toasts2) => toasts2.filter((toast) => toast.id !== id));
    const timeout = timeouts.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeouts.delete(id);
    }
  },
  // Clear all toasts
  clear: () => {
    update(() => []);
    timeouts.forEach((timeout) => clearTimeout(timeout));
    timeouts.clear();
  },
  // Convenience methods
  success: (message, options) => {
    return toasts.add({
      type: "success",
      message,
      ...options
    });
  },
  error: (message, options) => {
    return toasts.add({
      type: "error",
      message,
      duration: 8e3,
      // Errors stay longer
      ...options
    });
  },
  warning: (message, options) => {
    return toasts.add({
      type: "warning",
      message,
      duration: 6e3,
      ...options
    });
  },
  info: (message, options) => {
    return toasts.add({
      type: "info",
      message,
      ...options
    });
  },
  // Promise helper - shows loading, then success/error
  promise: async (promise, options) => {
    const loadingId = toasts.add({
      type: "info",
      message: options.loading,
      duration: 0,
      // Don't auto-dismiss
      dismissible: false
    });
    try {
      const result = await promise;
      toasts.dismiss(loadingId);
      const successMessage = typeof options.success === "function" ? options.success(result) : options.success;
      toasts.success(successMessage);
      return result;
    } catch (error) {
      toasts.dismiss(loadingId);
      const errorMessage = typeof options.error === "function" ? options.error(error) : options.error;
      toasts.error(errorMessage);
      throw error;
    }
  }
};
if (browser) {
  try {
    const stored = sessionStorage.getItem("toasts");
    if (stored) {
      const persistedToasts = JSON.parse(stored);
      const recent = persistedToasts.filter(
        (toast) => Date.now() - toast.timestamp < 6e4
      );
      if (recent.length > 0) {
        update(() => recent);
      }
    }
  } catch (e) {
    console.warn("Failed to load persisted toasts:", e);
  }
  subscribe((toasts2) => {
    try {
      sessionStorage.setItem("toasts", JSON.stringify(toasts2));
    } catch (e) {
      console.warn("Failed to persist toasts:", e);
    }
  });
}
const Info = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "M12 16v-4" }],
    ["path", { "d": "M12 8h.01" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "info" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const X = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M18 6 6 18" }], ["path", { "d": "m6 6 12 12" }]];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "x" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const css = {
  code: ".toast-item.svelte-8tm6jd{transform-origin:center}@keyframes svelte-8tm6jd-progress{from{transform:scaleX(1)}to{transform:scaleX(0)}}.animate-progress.svelte-8tm6jd{animation:svelte-8tm6jd-progress linear forwards;transform-origin:left}.toast-item.svelte-8tm6jd:not(:last-child){transform:translateY(0) scale(1);transition:transform 0.3s ease}.toast-item.svelte-8tm6jd:nth-last-child(2){transform:translateY(-2px) scale(0.98)}.toast-item.svelte-8tm6jd:nth-last-child(3){transform:translateY(-4px) scale(0.96)}.toast-item.svelte-8tm6jd:nth-last-child(4){transform:translateY(-6px) scale(0.94)}.toast-item.svelte-8tm6jd:nth-last-child(n+5){transform:translateY(-8px) scale(0.92);opacity:0.7}",
  map: `{"version":3,"file":"ToastContainer.svelte","sources":["ToastContainer.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { toasts } from \\"$lib/stores/toast\\";\\nimport { fly, scale } from \\"svelte/transition\\";\\nimport { CheckCircle, XCircle, AlertTriangle, Info, X } from \\"lucide-svelte\\";\\nexport let position = \\"top-right\\";\\nexport let maxToasts = 5;\\n$: visibleToasts = $toasts.slice(-maxToasts);\\nconst positionClasses = {\\n  \\"top-right\\": \\"top-4 right-4\\",\\n  \\"top-left\\": \\"top-4 left-4\\",\\n  \\"bottom-right\\": \\"bottom-4 right-4\\",\\n  \\"bottom-left\\": \\"bottom-4 left-4\\",\\n  \\"top-center\\": \\"top-4 left-1/2 transform -translate-x-1/2\\"\\n};\\nfunction getIcon(type) {\\n  switch (type) {\\n    case \\"success\\":\\n      return CheckCircle;\\n    case \\"error\\":\\n      return XCircle;\\n    case \\"warning\\":\\n      return AlertTriangle;\\n    case \\"info\\":\\n      return Info;\\n    default:\\n      return Info;\\n  }\\n}\\nfunction getColors(type) {\\n  switch (type) {\\n    case \\"success\\":\\n      return {\\n        bg: \\"bg-success/10 border-success/20\\",\\n        icon: \\"text-success\\",\\n        title: \\"text-success-content\\",\\n        message: \\"text-base-content/80\\"\\n      };\\n    case \\"error\\":\\n      return {\\n        bg: \\"bg-error/10 border-error/20\\",\\n        icon: \\"text-error\\",\\n        title: \\"text-error-content\\",\\n        message: \\"text-base-content/80\\"\\n      };\\n    case \\"warning\\":\\n      return {\\n        bg: \\"bg-warning/10 border-warning/20\\",\\n        icon: \\"text-warning\\",\\n        title: \\"text-warning-content\\",\\n        message: \\"text-base-content/80\\"\\n      };\\n    case \\"info\\":\\n      return {\\n        bg: \\"bg-info/10 border-info/20\\",\\n        icon: \\"text-info\\",\\n        title: \\"text-info-content\\",\\n        message: \\"text-base-content/80\\"\\n      };\\n    default:\\n      return {\\n        bg: \\"bg-base-200 border-base-300\\",\\n        icon: \\"text-base-content\\",\\n        title: \\"text-base-content\\",\\n        message: \\"text-base-content/80\\"\\n      };\\n  }\\n}\\nfunction handleDismiss(id) {\\n  toasts.dismiss(id);\\n}\\nfunction handleAction(toast) {\\n  if (toast.action) {\\n    toast.action.handler();\\n    toasts.dismiss(toast.id);\\n  }\\n}\\n<\/script>\\n\\n<!-- Toast container -->\\n<div class=\\"fixed {positionClasses[position]} z-50 space-y-2 max-w-sm w-full pointer-events-none\\">\\n  {#each visibleToasts as toast (toast.id)}\\n    {@const colors = getColors(toast.type)}\\n    {@const Icon = getIcon(toast.type)}\\n    \\n    <div\\n      class=\\"toast-item pointer-events-auto\\"\\n      in:fly={{\\n        x: position.includes('right') ? 300 : position.includes('left') ? -300 : 0,\\n        y: position.includes('top') ? -100 : position.includes('bottom') ? 100 : 0,\\n        duration: 300\\n      }}\\n      out:scale={{ duration: 200, start: 0.95 }}\\n    >\\n      <div class=\\"relative overflow-hidden rounded-2xl {colors.bg} border backdrop-blur-md shadow-soft\\">\\n        <!-- Main content -->\\n        <div class=\\"p-4\\">\\n          <div class=\\"flex items-start space-x-3\\">\\n            <!-- Icon -->\\n            <div class=\\"flex-shrink-0 mt-0.5\\">\\n              <Icon class=\\"w-5 h-5 {colors.icon}\\" />\\n            </div>\\n            \\n            <!-- Content -->\\n            <div class=\\"flex-1 min-w-0\\">\\n              {#if toast.title}\\n                <h4 class=\\"text-sm font-semibold {colors.title} mb-1\\">\\n                  {toast.title}\\n                </h4>\\n              {/if}\\n              \\n              <p class=\\"text-sm {colors.message}\\">\\n                {toast.message}\\n              </p>\\n              \\n              <!-- Action button -->\\n              {#if toast.action}\\n                <button\\n                  class=\\"mt-2 text-xs font-medium {colors.icon} hover:underline focus:outline-none focus:underline\\"\\n                  on:click={() => handleAction(toast)}\\n                >\\n                  {toast.action.label}\\n                </button>\\n              {/if}\\n            </div>\\n            \\n            <!-- Dismiss button -->\\n            {#if toast.dismissible}\\n              <button\\n                class=\\"flex-shrink-0 p-1 rounded-lg hover:bg-base-content/10 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50\\"\\n                on:click={() => handleDismiss(toast.id)}\\n                aria-label=\\"Dismiss notification\\"\\n              >\\n                <X class=\\"w-4 h-4 text-base-content/60\\" />\\n              </button>\\n            {/if}\\n          </div>\\n        </div>\\n        \\n        <!-- Progress bar for auto-dismiss -->\\n        {#if toast.duration && toast.duration > 0}\\n          <div class=\\"absolute bottom-0 left-0 right-0 h-1 bg-base-content/10\\">\\n            <div \\n              class=\\"h-full bg-gradient-to-r from-primary-400 to-primary-600 origin-left animate-progress\\"\\n              style=\\"animation-duration: {toast.duration}ms\\"\\n            ></div>\\n          </div>\\n        {/if}\\n        \\n        <!-- Subtle glow effect -->\\n        <div class=\\"absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-50 pointer-events-none\\"></div>\\n      </div>\\n    </div>\\n  {/each}\\n</div>\\n\\n<style>\\n  .toast-item {\\n    transform-origin: center;\\n  }\\n  \\n  @keyframes progress {\\n    from {\\n      transform: scaleX(1);\\n    }\\n    to {\\n      transform: scaleX(0);\\n    }\\n  }\\n  \\n  .animate-progress {\\n    animation: progress linear forwards;\\n    transform-origin: left;\\n  }\\n  \\n  /* Stacking animation */\\n  .toast-item:not(:last-child) {\\n    transform: translateY(0) scale(1);\\n    transition: transform 0.3s ease;\\n  }\\n  \\n  .toast-item:nth-last-child(2) {\\n    transform: translateY(-2px) scale(0.98);\\n  }\\n  \\n  .toast-item:nth-last-child(3) {\\n    transform: translateY(-4px) scale(0.96);\\n  }\\n  \\n  .toast-item:nth-last-child(4) {\\n    transform: translateY(-6px) scale(0.94);\\n  }\\n  \\n  .toast-item:nth-last-child(n+5) {\\n    transform: translateY(-8px) scale(0.92);\\n    opacity: 0.7;\\n  }\\n</style>"],"names":[],"mappings":"AA2JE,yBAAY,CACV,gBAAgB,CAAE,MACpB,CAEA,WAAW,sBAAS,CAClB,IAAK,CACH,SAAS,CAAE,OAAO,CAAC,CACrB,CACA,EAAG,CACD,SAAS,CAAE,OAAO,CAAC,CACrB,CACF,CAEA,+BAAkB,CAChB,SAAS,CAAE,sBAAQ,CAAC,MAAM,CAAC,QAAQ,CACnC,gBAAgB,CAAE,IACpB,CAGA,yBAAW,KAAK,WAAW,CAAE,CAC3B,SAAS,CAAE,WAAW,CAAC,CAAC,CAAC,MAAM,CAAC,CAAC,CACjC,UAAU,CAAE,SAAS,CAAC,IAAI,CAAC,IAC7B,CAEA,yBAAW,gBAAgB,CAAC,CAAE,CAC5B,SAAS,CAAE,WAAW,IAAI,CAAC,CAAC,MAAM,IAAI,CACxC,CAEA,yBAAW,gBAAgB,CAAC,CAAE,CAC5B,SAAS,CAAE,WAAW,IAAI,CAAC,CAAC,MAAM,IAAI,CACxC,CAEA,yBAAW,gBAAgB,CAAC,CAAE,CAC5B,SAAS,CAAE,WAAW,IAAI,CAAC,CAAC,MAAM,IAAI,CACxC,CAEA,yBAAW,gBAAgB,GAAG,CAAE,CAC9B,SAAS,CAAE,WAAW,IAAI,CAAC,CAAC,MAAM,IAAI,CAAC,CACvC,OAAO,CAAE,GACX"}`
};
function getColors(type) {
  switch (type) {
    case "success":
      return {
        bg: "bg-success/10 border-success/20",
        icon: "text-success",
        title: "text-success-content",
        message: "text-base-content/80"
      };
    case "error":
      return {
        bg: "bg-error/10 border-error/20",
        icon: "text-error",
        title: "text-error-content",
        message: "text-base-content/80"
      };
    case "warning":
      return {
        bg: "bg-warning/10 border-warning/20",
        icon: "text-warning",
        title: "text-warning-content",
        message: "text-base-content/80"
      };
    case "info":
      return {
        bg: "bg-info/10 border-info/20",
        icon: "text-info",
        title: "text-info-content",
        message: "text-base-content/80"
      };
    default:
      return {
        bg: "bg-base-200 border-base-300",
        icon: "text-base-content",
        title: "text-base-content",
        message: "text-base-content/80"
      };
  }
}
const ToastContainer = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let visibleToasts;
  let $toasts, $$unsubscribe_toasts;
  $$unsubscribe_toasts = subscribe$1(toasts, (value) => $toasts = value);
  let { position = "top-right" } = $$props;
  let { maxToasts = 5 } = $$props;
  const positionClasses = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-center": "top-4 left-1/2 transform -translate-x-1/2"
  };
  function getIcon(type) {
    switch (type) {
      case "success":
        return Check_circle;
      case "error":
        return X_circle;
      case "warning":
        return Alert_triangle;
      case "info":
        return Info;
      default:
        return Info;
    }
  }
  if ($$props.position === void 0 && $$bindings.position && position !== void 0) $$bindings.position(position);
  if ($$props.maxToasts === void 0 && $$bindings.maxToasts && maxToasts !== void 0) $$bindings.maxToasts(maxToasts);
  $$result.css.add(css);
  visibleToasts = $toasts.slice(-maxToasts);
  $$unsubscribe_toasts();
  return ` <div class="${"fixed " + escape(positionClasses[position], true) + " z-50 space-y-2 max-w-sm w-full pointer-events-none svelte-8tm6jd"}">${each(visibleToasts, (toast) => {
    let colors = getColors(toast.type), Icon2 = getIcon(toast.type);
    return `  <div class="toast-item pointer-events-auto svelte-8tm6jd"><div class="${"relative overflow-hidden rounded-2xl " + escape(colors.bg, true) + " border backdrop-blur-md shadow-soft svelte-8tm6jd"}"> <div class="p-4"><div class="flex items-start space-x-3"> <div class="flex-shrink-0 mt-0.5">${validate_component(Icon2, "Icon").$$render($$result, { class: "w-5 h-5 " + colors.icon }, {}, {})}</div>  <div class="flex-1 min-w-0">${toast.title ? `<h4 class="${"text-sm font-semibold " + escape(colors.title, true) + " mb-1 svelte-8tm6jd"}">${escape(toast.title)} </h4>` : ``} <p class="${"text-sm " + escape(colors.message, true) + " svelte-8tm6jd"}">${escape(toast.message)}</p>  ${toast.action ? `<button class="${"mt-2 text-xs font-medium " + escape(colors.icon, true) + " hover:underline focus:outline-none focus:underline svelte-8tm6jd"}">${escape(toast.action.label)} </button>` : ``}</div>  ${toast.dismissible ? `<button class="flex-shrink-0 p-1 rounded-lg hover:bg-base-content/10 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50" aria-label="Dismiss notification">${validate_component(X, "X").$$render($$result, { class: "w-4 h-4 text-base-content/60" }, {}, {})} </button>` : ``} </div></div>  ${toast.duration && toast.duration > 0 ? `<div class="absolute bottom-0 left-0 right-0 h-1 bg-base-content/10"><div class="h-full bg-gradient-to-r from-primary-400 to-primary-600 origin-left animate-progress svelte-8tm6jd" style="${"animation-duration: " + escape(toast.duration, true) + "ms"}"></div> </div>` : ``}  <div class="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-50 pointer-events-none"></div></div> </div>`;
  })} </div>`;
});
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let isAuthenticated = false;
  let user = null;
  return `${$$result.head += `<!-- HEAD_svelte-14lx0a3_START --><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet"><!-- HEAD_svelte-14lx0a3_END -->`, ""}  <div class="min-h-screen bg-gradient-to-br from-base-100 via-base-200 to-base-100 transition-all duration-300">${slots.default ? slots.default({ isAuthenticated, user }) : ``}  ${validate_component(ToastContainer, "ToastContainer").$$render($$result, { position: "top-right", maxToasts: 5 }, {}, {})}</div>`;
});
export {
  Layout as default
};
//# sourceMappingURL=_layout.svelte.js.map
