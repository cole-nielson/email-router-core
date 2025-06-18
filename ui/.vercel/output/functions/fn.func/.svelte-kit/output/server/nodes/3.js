

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/dashboard/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/3.CKYR5c-S.js","_app/immutable/chunks/Um1MPQnS.js","_app/immutable/chunks/cjHRRdVj.js","_app/immutable/chunks/CSEEA0gy.js","_app/immutable/chunks/CfmmjSnu.js","_app/immutable/chunks/CkoP-xeV.js"];
export const stylesheets = ["_app/immutable/assets/2.BUF4Zhd3.css"];
export const fonts = [];
