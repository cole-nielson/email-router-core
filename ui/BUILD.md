# Frontend Build Guide

## Development Setup

```bash
cd ui/
npm install
npm run dev
```

## Build Commands

```bash
# Development build
npm run build:dev

# Production build
npm run build

# Type checking
npm run check

# Linting
npm run lint
npm run lint:fix

# Testing
npm run test
npm run test:ui
```

## Environment Configuration

Create a `.env.local` file in the `ui/` directory:

```env
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080/ws
```

## Deployment

The UI is built as a static site and can be deployed to:
- Vercel (recommended)
- Netlify
- GitHub Pages
- Any static hosting service

## Architecture

- **Framework**: SvelteKit
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Package Manager**: npm

## Directory Structure

```
ui/
├── src/
│   ├── lib/           # Reusable components and utilities
│   ├── routes/        # Page routes (SvelteKit)
│   └── app.html       # HTML template
├── static/            # Static assets
└── build/            # Build output (ignored by git)
```
