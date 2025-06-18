

export const index = 1;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/error.svelte.js')).default;
export const imports = ["_app/immutable/nodes/1.A6fbf14P.js","_app/immutable/chunks/Um1MPQnS.js","_app/immutable/chunks/cjHRRdVj.js","_app/immutable/chunks/CSEEA0gy.js"];
export const stylesheets = [];
export const fonts = [];
