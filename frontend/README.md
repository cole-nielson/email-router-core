# Email Router Frontend

SvelteKit-based frontend application for the Email Router system.

## Project Structure

```
frontend/
├── src/                          # Source code
│   ├── lib/                     # Library code
│   │   ├── api/                 # API client
│   │   ├── components/          # Reusable components
│   │   ├── stores/              # State management
│   │   └── utils/               # Utilities
│   ├── routes/                  # SvelteKit routes
│   └── static/                  # Static assets
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
└── static/                      # Static files
```

## Development

### Setup

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
```

### Running

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Interactive test UI
npm run test:ui
```

### Code Quality

```bash
# Linting
npm run lint

# Formatting
npm run format

# Type checking
npm run type-check
```

## Features

- **Dashboard**: Real-time email processing metrics
- **Client Management**: Multi-tenant client configuration
- **Authentication**: JWT-based authentication with role management
- **Monitoring**: System health and performance monitoring