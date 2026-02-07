# FCRA Platform - Comprehensive Regression Plan

This document outlines the complete regression testing strategy for the FCRA Litigation Platform to ensure changes don't break existing functionality.

## Current Test Coverage

| Test Type | Count | Location |
|-----------|-------|----------|
| **Unit Tests** | 7,532 | `tests/*.py` |
| **Cypress E2E** | 76 files | `cypress/e2e/*.cy.js` |
| **Exhaustive Tests** | 53 files | `cypress/e2e/*_exhaustive.cy.js` |
| **Integration Tests** | 2 files | `tests/integration/` |

## Test Categories

### 1. Unit Tests (`tests/`)

Test individual services in isolation with mocked dependencies.

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run specific service tests
python -m pytest tests/test_credit_import_automation.py -v

# Run with coverage
python -m pytest tests/ --cov=services --cov-report=html
```

**Services Covered (122 total):**
- Payment services (stripe, payment plans, client payments)
- AI services (dispute writer, chat, analysis)
- Communication services (email, SMS, voicemail)
- Document services (PDF, letters, notarization)
- Credit services (import, parser, monitoring)
- Workflow services (triggers, automation, scheduling)
- Portal services (client, partner, affiliate)
- And more...

### 2. Cypress E2E Tests (`cypress/e2e/`)

Test full user flows through the browser.

```bash
# Run all Cypress tests
CI=true npx cypress run

# Run specific test file
CI=true npx cypress run --spec "cypress/e2e/login.cy.js"

# Run exhaustive tests only
CI=true npx cypress run --spec "cypress/e2e/*_exhaustive.cy.js"

# Interactive mode
npx cypress open
```

**Key E2E Test Files:**
- `login.cy.js` - Staff authentication
- `clients.cy.js` - Client management
- `portal_*.cy.js` - Client portal flows
- `payment_*.cy.js` - Payment processing
- `credit_import.cy.js` - Credit report imports

### 3. Exhaustive Tests (`cypress/e2e/*_exhaustive.cy.js`)

Comprehensive tests for each dashboard page covering:
- Page load and structure
- All interactive elements
- Form submissions
- Modal dialogs
- Responsive layouts
- JavaScript functions

### 4. Regression-Specific Tests

**Credit Import Regression** (`tests/test_credit_import_regression.py`):
- Tests extraction output format across all services
- Protects against JavaScript extraction bugs
- Validates data structure consistency

**Credit Extraction Regression** (`tests/test_credit_extraction_regression.py`):
- MyScoreIQ Personal Info extraction
- MyFreeScoreNow format support
- Per-bureau data separation

## When to Run Tests

### Before Every Commit

```bash
# Quick smoke test (fast)
python -m pytest tests/ -x -q --tb=short

# If touching credit import
python -m pytest tests/test_credit_import*.py -v
```

### Before Pull Request

```bash
# Full unit test suite
python -m pytest tests/ -v

# Cypress E2E (requires running server)
CI=true PORT=5001 python app.py &
CI=true npx cypress run
```

### Before Production Deploy

```bash
# Full QA suite
./run_full_qa.sh
```

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: fcra_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/fcra_test
          TESTING: true
        run: python -m pytest tests/ -v --tb=short

  cypress-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Cypress
        run: npm install cypress
      - name: Run Cypress
        env:
          CI: true
        run: npx cypress run
```

## Test Data Management

### Fixtures

Test fixtures are stored in:
- `tests/fixtures/` - Unit test data
- `tests/fixtures/credit_reports/` - Credit report JSON samples
- `cypress/fixtures/` - Cypress test data

### Database

- Tests use `TESTING=true` environment variable
- Test database is separate from production
- Migrations run automatically in test setup

## Adding New Tests

### For New Features

1. **Unit tests first** - Test the service in isolation
2. **Integration test** - Test with real dependencies
3. **E2E test** - Test user flow in browser

### For Bug Fixes

1. **Write failing test** - Reproduce the bug
2. **Fix the bug** - Make test pass
3. **Commit together** - Test + fix in same commit

### Template for New Service Test

```python
# tests/test_my_new_service.py
import pytest
from unittest.mock import patch, MagicMock
from services.my_new_service import MyNewService

class TestMyNewService:
    @pytest.fixture
    def service(self):
        return MyNewService()

    def test_basic_functionality(self, service):
        result = service.do_something()
        assert result is not None

    def test_error_handling(self, service):
        with pytest.raises(ValueError):
            service.do_something_invalid()
```

## Critical Paths to Always Test

### Payment Flow
- Stripe checkout creation
- Webhook handling
- Payment confirmation
- Subscription management

### Client Portal
- Login/authentication
- Document upload
- Agreement signing
- Status viewing

### Credit Import
- Credential validation
- Browser automation
- Data extraction
- JSON output format

### Document Generation
- Dispute letter creation
- PDF generation
- Template rendering
- Mail queue

### Communication
- Email sending
- SMS delivery
- Notification triggers

## Test Maintenance

### Weekly
- Review skipped tests
- Update flaky tests
- Check coverage trends

### Monthly
- Add fixtures for new clients
- Update expected values
- Clean up obsolete tests

### Per Release
- Full regression run
- Performance benchmarks
- Security scan

## Quick Reference Commands

```bash
# Full unit test suite
python -m pytest tests/ -v

# Fast smoke test
python -m pytest tests/ -x -q

# With coverage
python -m pytest tests/ --cov=services --cov-report=term-missing

# Specific test class
python -m pytest tests/test_payment_service.py::TestPaymentFlow -v

# Credit import regression
python -m pytest tests/test_credit_import_regression.py -v

# Cypress headless
CI=true npx cypress run

# Cypress specific file
CI=true npx cypress run --spec "cypress/e2e/clients.cy.js"

# All exhaustive tests
CI=true npx cypress run --spec "cypress/e2e/*_exhaustive.cy.js"
```

## Contacts

- **Test failures**: Check logs in `logs/test.log`
- **Flaky tests**: Tag with `@pytest.mark.flaky`
- **Coverage gaps**: Run coverage report and address

---

*Last Updated: 2026-02-07*
*Total Tests: 7,532 unit + 76 E2E files*
