import { c as create_ssr_component } from "../../chunks/ssr.js";
import "../../chunks/authStore.js";
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `${$$result.head += `<!-- HEAD_svelte-14lx0a3_START --><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet"><!-- HEAD_svelte-14lx0a3_END -->`, ""} <main>${slots.default ? slots.default({}) : ``}</main>`;
});
export {
  Layout as default
};
//# sourceMappingURL=_layout.svelte.js.map
