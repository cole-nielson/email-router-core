import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	define: {
		// Ensure environment variables are available at build time
		__VERSION__: JSON.stringify(process.env.npm_package_version),
		__BUILD_TIME__: JSON.stringify(new Date().toISOString())
	},
	server: {
		// Development server configuration
		port: 3000,
		host: true,
		proxy: {
			// Proxy API calls to FastAPI backend during development
			'/api': {
				target: 'http://localhost:8080',
				changeOrigin: true,
				secure: false
			},
			'/ws': {
				target: 'ws://localhost:8080',
				ws: true,
				changeOrigin: true
			}
		}
	},
	build: {
		// Production build optimization
		target: 'es2022',
		sourcemap: true
	}
});