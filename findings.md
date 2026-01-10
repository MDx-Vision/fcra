# Findings & Decisions

## Requirements
- Full-featured FCRA litigation/credit repair platform
- Client portal for onboarding, document upload, case tracking
- Staff dashboard for CRM, analysis, letter generation
- Partner portal for white-label operations
- Automated workflows for communication and processing
- AI-powered credit report analysis and letter generation

## Research Findings

### Tech Stack
- **Backend:** Flask (Python), SQLAlchemy ORM
- **Database:** PostgreSQL (production), SQLite (development)
- **Frontend:** Jinja2 templates, Tailwind CSS, Chart.js
- **Testing:** Pytest (unit), Cypress (E2E)
- **AI:** Anthropic Claude API for analysis and letter generation

### Key Integrations
- **Email:** Gmail SMTP (replaced SendGrid)
- **SMS:** Twilio (A2P 10DLC pending)
- **Payments:** Stripe (subscriptions, one-time, webhooks)
- **Certified Mail:** SendCertifiedMail.com (SFTP pending)
- **Push:** Web Push API with VAPID keys

### FCRA Compliance
- 30-day dispute investigation deadline (standard)
- 45-day deadline for complex disputes
- CROA document signing with 3-day cancellation period
- Required document order: Rights Disclosure must be first

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Flask over Django | Lighter weight, more flexible for custom workflows |
| SQLAlchemy | Clean ORM, supports multiple database backends |
| Jinja2 templates | Simpler than React/Vue for internal tools |
| Tailwind CSS | Rapid styling, consistent design system |
| Gmail SMTP | Direct control, no third-party API dependency |
| PWA over native | Cross-platform, faster to implement, already works |
| Fernet encryption | Industry standard for PII, Python native |
| TOTP for 2FA | Works with all authenticator apps |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Rate limiting in CI | Added CI=true flag to disable rate limits in tests |
| SQLite PostgreSQL incompatibility | Use PostgreSQL for production testing |
| Session not navigating in Cypress | Added explicit cy.visit() after cy.login() |
| Email opt-in compliance | Added sms_opt_in and email_opt_in fields |

## Resources

### Documentation Files
- `CLAUDE.md` - Project context and session logs
- `ARCHITECTURE.md` - Technical architecture details
- `FEATURE_BACKLOG.md` - Feature specifications
- `UAT_TEST_PLAN.md` - Manual testing checklist
- `ADMIN_OPERATIONS_GUIDE.md` - Operations runbook
- `PRIORITY_29_PLUS_ROADMAP.md` - Future features
- `CLIENT_PORTAL_SOP.md` - Client journey guide

### Key Code Files
- `app.py` - Main Flask application (~26k lines)
- `database.py` - SQLAlchemy models
- `services/` - 86 service modules
- `routes/` - Route blueprints (portal, partner)
- `templates/` - Jinja2 templates

### Test Files
- `tests/` - 96 unit test files
- `cypress/e2e/` - 46 exhaustive E2E tests
- `tests/integration/` - Integration tests

## Visual/Browser Findings
- Dashboard sidebar uses accordion navigation
- Client portal has 5 main tabs (Case, Documents, Contact, Journey, Profile)
- Staff dashboard organized into 8 sidebar sections
- Theme toggle supports light/dark mode with CSS variables

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
