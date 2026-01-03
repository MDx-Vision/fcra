# FCRA Credit Repair Application

[![CI](https://github.com/mdxvision/fcra/actions/workflows/ci.yml/badge.svg)](https://github.com/mdxvision/fcra/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mdxvision/fcra/graph/badge.svg)](https://codecov.io/gh/mdxvision/fcra)

A comprehensive credit repair management system built with Flask.

## Features

### Core Platform
- Client management and onboarding
- Credit report analysis and dispute tracking
- Document generation (letters, reports)
- E-signature integration (CROA compliance)
- Attorney case management
- Affiliate portal
- White-label partner portal

### Client Portal (PWA)
- Mobile-first responsive design
- Installable on iOS/Android/Desktop
- Live chat support
- Document upload and tracking
- Freeze status monitoring
- Journey timeline
- Booking system for calls

### Automation
- Workflow triggers and actions
- Drip campaigns
- Voicemail drops (multi-provider)
- Email/SMS automation
- Scheduled jobs

### Business Intelligence
- Revenue dashboard
- Staff performance metrics
- Lead scoring
- ROI calculator
- Bureau response tracking

### Integrations
- Gmail SMTP for email
- Twilio for SMS/WhatsApp
- Stripe for payments
- Multiple credit monitoring services

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (for Cypress tests)

## Quick Start

### Docker (Recommended)

```bash
# Start with Docker Compose (includes PostgreSQL)
docker-compose up

# Or build and run manually
docker build -t fcra-platform .
docker run -p 5000:5000 --env-file .env fcra-platform
```

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/fcra"
export SECRET_KEY="your-secret-key"

# Run the application
python app.py
```

## Development

### Code Formatting

```bash
# Format code
black app.py services/
isort app.py services/ --profile black
```

### Running Tests

```bash
# Unit tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Cypress E2E tests
npm ci
npx cypress run
```

### Database Migrations

```bash
# Create a new migration (after modifying models)
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

### Security Scanning

```bash
# Python security scan
pip install bandit
bandit -r app.py services/ --severity-level high

# JavaScript vulnerability scan
npm audit
```

## API Documentation

Interactive API documentation is available at `/api/docs/` when the app is running.

- **Swagger UI**: `/api/docs/`
- **OpenAPI Spec**: `/api/docs/apispec.json`
- **Static Spec**: `docs/openapi.yaml`

## Test Status

- **Unit Tests**: 5,300+ passing (60+ test files)
- **Cypress E2E**: 88 specs passing
- **Coverage**: All 60 services tested

## CI/CD

All PRs run through:
- Unit tests with coverage threshold (20% minimum)
- Cypress E2E tests (88 specs)
- Linting (flake8)
- Security scanning (bandit, npm audit)
- Code formatting checks (black, isort)

## Documentation

- `CLAUDE.md` - Development context and instructions
- `ARCHITECTURE.md` - Tech stack and project structure
- `FEATURE_BACKLOG.md` - Feature priorities and status
- `CONVERSATION_LOG.md` - Development session history

## License

Proprietary - All rights reserved.
