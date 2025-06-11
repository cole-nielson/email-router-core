// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces

import type { Navigation } from '@sveltejs/kit';

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

// Declare SvelteKit modules that might be missing
declare module '$app/stores' {
	import { Readable } from 'svelte/store';
	export const page: Readable<{
		url: URL;
		params: Record<string, string>;
		route: { id: string | null };
		data: Record<string, any>;
	}>;
	export const navigating: Readable<Navigation | null>;
	export const updated: Readable<boolean>;
}

declare module '$app/navigation' {
	export function goto(url: string | URL, opts?: { 
		replaceState?: boolean; 
		noscroll?: boolean; 
		keepfocus?: boolean; 
		state?: any 
	}): Promise<void>;
	export function invalidate(dependency: string | URL | ((url: URL) => boolean)): Promise<void>;
	export function invalidateAll(): Promise<void>;
	export function preloadData(href: string): Promise<void>;
	export function preloadCode(...urls: string[]): Promise<void>;
	export function beforeNavigate(fn: (navigation: Navigation) => void): void;
	export function afterNavigate(fn: (navigation: Navigation) => void): void;
}

declare module '$app/environment' {
	export const browser: boolean;
	export const dev: boolean;
	export const building: boolean;
	export const version: string;
}

export {};