import adapter from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// Vercel adapter for production deployment
		adapter: adapter({
			runtime: 'nodejs18.x',
			regions: ['iad1'], // US East for low latency to backend
			functions: {
				'src/routes/api/+server.ts': {
					maxDuration: 30
				}
			}
		}),
		
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