import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// Auto adapter for development
		adapter: adapter(),

		// Environment configuration
		env: {
			dir: './',
			publicPrefix: 'PUBLIC_'
		},

		// Path aliases
		alias: {
			'$lib': './src/lib',
			'$lib/*': './src/lib/*'
		},

		// CSP for security
		csp: {
			mode: 'auto',
			directives: {
				'script-src': ['self', 'unsafe-inline', 'https://cdn.jsdelivr.net'],
				'style-src': ['self', 'unsafe-inline', 'https://fonts.googleapis.com'],
				'connect-src': ['self', process.env.PUBLIC_API_URL || 'http://localhost:8080']
			}
		}
	}
};

export default config;
