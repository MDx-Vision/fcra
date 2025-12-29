# FCRA Credit Repair Application

[![CI](https://github.com/mdxvision/fcra/actions/workflows/ci.yml/badge.svg)](https://github.com/mdxvision/fcra/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mdxvision/fcra/graph/badge.svg)](https://codecov.io/gh/mdxvision/fcra)

A comprehensive credit repair management system built with Flask.

## Features

- Client management and onboarding
- Credit report analysis and dispute tracking
- Document generation (letters, reports)
- E-signature integration
- Attorney case management
- Affiliate portal
- White-label support

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

## CI/CD

All PRs run through:
- Unit tests with coverage threshold (20% minimum)
- Cypress E2E tests (88 specs)
- Linting (flake8)
- Security scanning (bandit, npm audit)
- Code formatting checks (black, isort)

## License

Proprietary - All rights reserved.
