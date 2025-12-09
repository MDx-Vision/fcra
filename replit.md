# Brightpath Ascend FCRA Platform

## Overview
The Brightpath Ascend FCRA Platform is a production-ready system for consumer protection litigation, specifically targeting FCRA violations. It automates credit report analysis and generates all necessary legal documentation, functioning as a complete litigation management tool. The platform aims to facilitate robust legal action against credit reporting agencies and drive significant revenue through a tiered pricing model.

## User Preferences
- Cost-conscious but values AI quality (accepts $1-3 per analysis)
- Wants automation for clear cases, manual review for complex ones
- Building full litigation platform (not just credit repair)
- Target: 50 clients waiting, $600K-900K year-1 revenue with 3-tier pricing model
- Prefers analytical, data-driven decisions with clear case metrics
- Always provide testing URLs when adding new features or suggesting changes so user can view and test

## System Architecture
The platform is built on Flask and employs a two-stage, section-based analysis approach to manage token limits and enhance analytical depth.

### UI/UX Decisions
- **Admin Dashboard**: Professional case management at `/dashboard` for pipeline visualization, client lists, and case details.
- **Client Portal**: Branded client-facing portal at `/portal/<token>` for case status and self-service.
- **Review Checkpoints**: Interfaces (`/analysis/<id>/review`) for manual review and editing of AI-extracted data.
- **PDF Generation**: Brightpath Ascend branding for client-facing documents; unbranded for external correspondence.

### Technical Implementations
- **Two-Stage Analysis**: Section-by-section analysis of credit reports (Stage 1) for violations, standing, and damages, then merged for document generation (Stage 2).
- **Automated Data Extraction**: Claude outputs structured JSON.
- **PDF Generation**: Modular generators for reports and letters.
- **Security**: Password encryption using Fernet.
- **Rapid Legal Protection Protocol (RLPP)**: Bundles violations and escalates disputes.
- **Automation Tools Dashboard**: 6-tab interface including Freeze Letters, Validation Letters, Settlement Calculator.
- **Action Plan Generator**: Creates branded action plan PDFs.
- **Mobile Document Scanner** (`/scanner`): Multi-page scanning with OCR via Claude Vision, links to client cases.
- **E-Signature System**: Client-facing signature capture.
- **Metro2 Violation Detection API**: Identifies 10 types of Metro2 violations with auto-generated dispute language.
- **PWA Support**: For offline caching and push notifications.
- **Email/SMS Automation**: SendGrid and Twilio for client communications.
- **Document Center**: Unified upload system with admin review.
- **Flexible Signup System**: Configurable fields and multi-payment options.
- **Credit Score Improvement Tracker** (`/dashboard/credit-tracker`): Comprehensive score tracking and impact calculations.
- **Client Avatar/Photo Feature**: Personalized client profiles.
- **Client Password Login System** (`/portal/login`): Secure email+password authentication with reset and rate limiting.
- **Analytics Dashboard** (`/dashboard/analytics`): Business intelligence for client stats, revenue, and case metrics.
- **Calendar View** (`/dashboard/calendar`): FullCalendar integration for deadline management.
- **Dispute Round Automation**: Automated progression of dispute rounds and status updates.
- **Visual CRA Response Timeline**: Per-client dispute history visualization.
- **Credit Report PDF Parser**: Enhanced PDF extraction with bureau detection and confidence scoring.
- **Multi-User Staff Roles System** (`/staff/login`): Enterprise authentication with configurable roles and permission-based access.
- **Settlement Tracking Module** (`/dashboard/settlements`): Manages case outcomes and revenue.
- **Automated CRA Response Analysis**: AI-powered processing of bureau responses via Claude Vision OCR, item matching, and reinsertion detection.
- **Furnisher Intelligence Database** (`/dashboard/furnishers`): Tracks creditor profiles and performance.
- **Statute of Limitations Calculator** (`/dashboard/sol`): Calculates FCRA deadlines with alerts.
- **CFPB Complaint Generator** (`/dashboard/cfpb`): AI-powered generation of CFPB complaints.
- **Two-Level Affiliate Commission System** (`/dashboard/affiliates`): Parent/child referral tracking and payout processing.
- **AI Case Triage System** (`/dashboard/triage`): Intelligent 1-5 star case prioritization and queue management.
- **Case Law Citation Database** (`/dashboard/case-law`): 20+ pre-loaded FCRA cases with smart suggestions.
- **Smart Letter Escalation Engine** (`/dashboard/escalation`): AI-powered dispute strategy recommendations.
- **Legal Strategy Knowledge Base** (`/dashboard/knowledge-base`): Comprehensive searchable reference for FCRA statutes, Reg Z, RESPA, FDCPA, Metro 2® codes, and dispute timelines.
- **Dispute Escalation Pathway Tracker**: Workflow tracking for disputes through various stages.
- **Advanced Dispute Letter Templates**: 7 new letter types with legal citations.
- **DOFD/Obsolescence Calculator** (`/api/obsolescence/calculate`): Calculates 7-year reporting periods.
- **Smart Letter Queue Automation** (`/dashboard/letter-queue`): Intelligent letter suggestion system based on trigger conditions.
- **Instant Violation Preview** (`/preview`): Public landing page with 60-second AI analysis for lead conversion.
- **AI Settlement Demand Letter Generator** (`/dashboard/demand-generator`): One-click professional demand letter generation.
- **Enhanced Client ROI Dashboard** (`/api/client/<id>/roi-summary`): Visual financial projections with settlement probability.
- **Background Task Queue** (`/dashboard/tasks`): Database-backed async job processing.
- **ML Outcome Learning** (`/dashboard/ml-insights`): Machine learning for predictive settlement values.
- **Predictive Analytics Engine** (`/dashboard/predictive`): Revenue forecasting, client lifetime value, and case timeline predictions.
- **Automated Workflow Triggers** (`/dashboard/workflows`): Event-based automation for case management.
- **White-Label Support** (`/dashboard/whitelabel`): Multi-tenant branding for partner law firms.
- **Franchise Mode** (`/dashboard/franchise`): Multi-office management with organizational hierarchy.
- **Public API Access** (`/dashboard/api-keys`): RESTful API with scope-based authentication.
- **Comprehensive Audit Logging** (`/dashboard/audit`): Complete action history with compliance reporting.
- **Performance Optimization** (`/dashboard/performance`): In-memory caching, database query optimization.
- **API Documentation** (`/api-docs`): Comprehensive public API documentation.
- **Enhanced Sidebar Navigation**: Collapsible accordion-style sections.
- **Enhanced Knowledge Base with Training Content** (`/dashboard/knowledge-base`): Legal education system with credit repair and Metro 2® courses.
- **Standard Operating Procedures (SOPs)** (`/dashboard/sops`): Step-by-step workflow guides for staff.
- **ChexSystems/EWS Dispute Helper** (`/dashboard/chexsystems`): Specialty bureau dispute tracking.
- **Unified Specialty Bureau Disputes Dashboard** (`/dashboard/specialty-bureaus`): Comprehensive dispute tracking across all 9 specialty consumer reporting agencies (Innovis, ChexSystems, Clarity Services, LexisNexis, CoreLogic Teletrack, Factor Trust, MicroBilt/PRBC, LexisNexis Risk Solutions, DataX Ltd) with bureau cards, response tracking, and escalation management.
- **Credit Monitoring Auto-Import System** (`/dashboard/credit-import`): Credential-based automatic credit report import from 11 monitoring services (IdentityIQ, MyScoreIQ, SmartCredit, MyFreeScoreNow, HighScoreNow, IdentityClub, PrivacyGuard, IDClub, MyThreeScores, MyScore750, CreditHeroScore) with encrypted credential storage (username, password, SSN last 4), Playwright browser automation for automated login and report scraping, manual/scheduled import triggers, and status tracking. Browser automation service at `services/credit_import_automation.py`.
- **Metro 2® Field Validation System** (`metro2_validator.py`): Comprehensive 2025 CRRG compliance validation with AI prompt integration.
- **Frivolousness Defense Tracker** (`/dashboard/frivolousness`): Track CRA frivolous claim defenses with evidence requirements, legal theory documentation, and re-dispute workflow management.
- **Suspense Account Detection** (`/dashboard/suspense-accounts`): Mortgage payment ledger analysis identifying misapplied payments in suspense accounts that cause false late payment reporting.
- **Violation Pattern Documentation** (`/dashboard/patterns`): Cross-client pattern tracking for systemic FCRA violations with evidence packet PDF generation for class action preparation.
- **VA Letter Automation System** (`/dashboard/va-approval`): Complete certified mail automation workflow with SFTP integration to SendCertifiedMail.com ($11/letter). Features client-grouped letter display with avatars, filter by round/bureau/client, batch approval with live cost calculations, real-time SFTP status monitoring, 3 API routes (pending letters, approve batch, SFTP status), 3 database tables (AutomationMetrics, LetterBatch, TradelineStatus), 4 workflow automation triggers (30-day deadlines, auto-analyze CRA responses, 35-day escalation, reinsertion alerts), 6 new communication templates (3 email + 3 SMS), 2 scheduled jobs (daily tracking updates at 6 AM, deadline checks at 9 AM), and analytics dashboard integration with 10 automation metrics.

### Feature Specifications
- Full FCRA violation detection with section identification.
- Post-TransUnion standing analysis, willfulness assessment, and statute of limitations verification.
- Comprehensive damages calculation (statutory, actual, punitive).
- Case scoring (1-10 scale).
- Cost tracking for token usage and cache savings.

### System Design Choices
- **Scalability**: Section-based analysis supports large credit report sizes and client bases.
- **Cost Efficiency**: Prompt caching reduces API costs.
- **Data Integrity**: Intelligent sectioning and analysis prevent data loss.
- **Workflow Optimization**: Verification checkpoints ensure accuracy and control.

## Testing Infrastructure

### Cypress E2E Testing
The platform includes a complete end-to-end testing infrastructure using Cypress 13.17.0.

**Test Files:**
- `cypress/e2e/smoke.cy.js` - Basic page load verification tests
- `cypress/e2e/login.cy.js` - Staff login authentication tests
- `cypress/e2e/dashboard.cy.js` - Main dashboard component tests
- `cypress/e2e/clients.cy.js` - Clients page tests
- `cypress/e2e/clients_crud.cy.js` - Comprehensive client CRUD operations
- `cypress/e2e/settlements.cy.js` - Settlements page tests
- `cypress/e2e/settlements_crud.cy.js` - Comprehensive settlement CRUD operations
- `cypress/e2e/staff_crud.cy.js` - Staff management tests
- `cypress/e2e/analytics.cy.js` - Analytics dashboard tests
- `cypress/e2e/portal_login.cy.js` - Client portal login tests
- `cypress/e2e/create_item.cy.js` - Item creation workflow tests

**Running Tests (Replit/NixOS):**
```bash
# Run all tests
CI=true CYPRESS_SKIP_VERIFY=true CYPRESS_RUN_BINARY=/nix/store/0ydb4ml5crpmir6nyv7xz2m63plby0cq-cypress-13.17.0/opt/cypress/Cypress npx cypress run

# Run specific test file
CI=true CYPRESS_SKIP_VERIFY=true CYPRESS_RUN_BINARY=/nix/store/0ydb4ml5crpmir6nyv7xz2m63plby0cq-cypress-13.17.0/opt/cypress/Cypress npx cypress run --spec "cypress/e2e/login.cy.js"

# npm shortcuts
npm run test:e2e              # Run all E2E tests
npm run db:seed               # Reset database with test user
```

**Test User Credentials:**
- Email: `test@example.com`
- Password: `password123`
- Role: `admin`

**Custom Cypress Commands:**
- `cy.login(email, password)` - Robust login command with proper waits (defined in `cypress/support/commands.js`)

**Configuration:**
- `cypress.config.js` - Cypress configuration with baseUrl http://localhost:5000
- `cypress/support/e2e.js` - Support file with beforeEach hook for database seeding
- `cypress/support/commands.js` - Custom login command with explicit waits
- `seed.py` - Database seeding script that clears tables and creates test user

**NixOS/Replit Environment Notes:**
- CRITICAL: Must set `CYPRESS_SKIP_VERIFY=true` to bypass read-only Nix store permission errors
- Binary location: `/nix/store/0ydb4ml5crpmir6nyv7xz2m63plby0cq-cypress-13.17.0/opt/cypress/Cypress`
- CI authentication bypass activates when `CI=true` AND not in production
- All tests use `cy.login()` command for consistent login behavior

## External Dependencies
- **Flask**: Python web framework.
- **Anthropic Claude 3 Sonnet 4**: Primary AI analysis engine.
- **PostgreSQL**: Database solution (backed by Neon).
- **SQLAlchemy**: ORM for database interactions.
- **Fernet**: For symmetric encryption.
- **Stripe**: Payment processing.
- **Twilio**: SMS automation.
- **SendGrid**: Email automation.
- **Cypress**: E2E testing framework (v13.17.0).