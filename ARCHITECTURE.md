# Architecture Documentation

> Technical architecture for Brightpath Ascend FCRA Litigation Platform
>
> Last Updated: 2025-12-31

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Flask 3.0 | Python web framework |
| **Database** | PostgreSQL (Neon) | Primary data store |
| **ORM** | SQLAlchemy | Database abstraction |
| **AI** | Anthropic Claude | Credit report analysis, dispute letter generation |
| **Email** | SendGrid → Gmail | Transactional emails (migrating to Gmail) |
| **SMS** | Twilio | Text notifications (opt-in) |
| **Payments** | Stripe | Subscription billing |
| **PDF** | WeasyPrint, ReportLab, FPDF2 | Document generation |
| **OCR** | Custom + pdfplumber | Credit report parsing |
| **Certified Mail** | SendCertified (SFTP) | Mailing dispute letters |
| **E-Signature** | Custom implementation | Document signing |
| **Testing** | Pytest + Cypress | Unit + E2E tests |

---

## Project Structure

```
/
├── app.py                 # Main Flask app (~32k lines)
├── database.py            # SQLAlchemy models (~4.5k lines)
├── services/              # Business logic (56 services)
├── routes/                # Blueprint routes
│   ├── portal.py          # Client portal routes
│   └── staff.py           # Staff admin routes
├── templates/             # Jinja2 templates (78 dashboard + 6 portal)
│   ├── portal/            # Client portal templates
│   └── includes/          # Shared components
├── static/                # CSS, JS, images
├── tests/                 # Pytest unit tests (56 files)
├── cypress/               # E2E tests
│   └── e2e/               # Test specs (51 exhaustive + core)
├── migrations/            # Database migrations
└── docs/                  # Documentation
```

---

## Database Models (100 total)

### Core Models

| Model | Purpose |
|-------|---------|
| `Staff` | Team member accounts (admin, attorney, paralegal, viewer) |
| `Client` | Client records with contact info, case status |
| `CreditReport` | Uploaded/pulled credit reports |
| `Analysis` | AI-generated credit report analyses |
| `DisputeLetter` | Generated dispute letters |
| `Case` | Legal case tracking |

### Dispute Flow Models

| Model | Purpose |
|-------|---------|
| `DisputeItem` | Individual items being disputed |
| `LetterQueue` | Letters queued for mailing |
| `CRAResponse` | Bureau response tracking |
| `CRAResponseOCR` | OCR'd response documents |
| `Violation` | FCRA violations found |

### Communication Models

| Model | Purpose |
|-------|---------|
| `SMSLog` | SMS message history |
| `EmailLog` | Email send history |
| `EmailTemplate` | Custom email templates |
| `Notification` | In-app notifications |

### Billing Models

| Model | Purpose |
|-------|---------|
| `BillingPlan` | Subscription plans |
| `ClientSubscription` | Active subscriptions |
| `Settlement` | Settlement tracking |
| `Commission` | Affiliate commissions |

### Automation Models

| Model | Purpose |
|-------|---------|
| `WorkflowTrigger` | Automation trigger definitions |
| `WorkflowExecution` | Trigger execution logs |
| `BackgroundTask` | Async task queue |
| `ScheduledJob` | Cron-like scheduled jobs |

### Multi-Tenancy Models

| Model | Purpose |
|-------|---------|
| `WhiteLabelTenant` | White-label customer orgs |
| `FranchiseOrganization` | Franchise locations |
| `APIKey` | API access credentials |

### CRM Models

| Model | Purpose |
|-------|---------|
| `CallLog` | Call logging with outcomes and follow-ups |
| `StaffTask` | Task assignment to staff members |
| `StaffTaskComment` | Comments/notes on tasks |

### Full Model List

<details>
<summary>All 100 models (click to expand)</summary>

```
Staff, Client, ClientTag, ClientTagAssignment, UserQuickLink,
CreditReport, Analysis, DisputeLetter, Violation, Standing,
Damages, CaseScore, Case, CaseEvent, Document, Notification,
Settlement, AnalysisQueue, CRAResponse, DisputeItem, LetterQueue,
SecondaryBureauFreeze, ClientReferral, Affiliate, Commission,
SignupDraft, Task, ClientNote, ClientDocument, ClientUpload,
SignupSettings, SMSLog, EmailLog, EmailTemplate, CaseDeadline,
NotarizationOrder, FreezeLetterBatch, CertifiedMailOrder,
SettlementEstimate, AttorneyReferral, LimitedPOA, Metro2DisputeLog,
CRAResponseOCR, ESignatureRequest, DocumentTemplate,
ClientDocumentSignature, CaseTriage, CreditScoreSnapshot,
CreditScoreProjection, CFPBComplaint, Furnisher, FurnisherStats,
EscalationRecommendation, CaseLawCitation, IntegrationConnection,
IntegrationEvent, CertifiedMailingRecord, NotarizeTransaction,
CreditPullRequest, CreditMonitoringCredential, BillingPlan,
ClientSubscription, BackgroundTask, ScheduledJob, CaseOutcome,
OutcomePrediction, FurnisherPattern, RevenueForecast,
ClientLifetimeValue, AttorneyPerformance, WorkflowTrigger,
WorkflowExecution, WhiteLabelTenant, TenantUser, TenantClient,
FranchiseOrganization, OrganizationMembership, OrganizationClient,
InterOrgTransfer, WhiteLabelConfig, APIKey, APIRequest, APIWebhook,
AuditLog, PerformanceMetric, CacheEntry, KnowledgeContent,
Metro2Code, SOP, ChexSystemsDispute, SpecialtyBureauDispute,
FrivolousDefense, FrivolousDefenseEvidence, MortgagePaymentLedger,
SuspenseAccountFinding, ViolationPattern, PatternInstance,
AutomationMetrics, LetterBatch, TradelineStatus, CallLog,
StaffTask, StaffTaskComment
```

</details>

---

## Services (58 total)

### Core Services

| Service | Purpose |
|---------|---------|
| `credit_report_parser` | Parse credit report text/PDF |
| `credit_report_ocr_parser` | OCR credit reports |
| `credit_score_calculator` | Calculate/project scores |
| `pattern_analyzer_service` | Detect furnisher patterns |
| `sol_calculator` | Statute of limitations calc |

### Communication Services

| Service | Purpose |
|---------|---------|
| `email_service` | Send emails (SendGrid → Gmail) |
| `email_automation` | Triggered email flows |
| `email_templates` | Email template rendering |
| `sms_service` | Send SMS (Twilio) |
| `sms_automation` | Triggered SMS flows |
| `sms_templates` | SMS template text |

### CRM Services

| Service | Purpose |
|---------|---------|
| `call_log_service` | Call logging with follow-ups |
| `task_service` | Staff task assignment & tracking |

### Document Services

| Service | Purpose |
|---------|---------|
| `pdf_service` | Generate PDF documents |
| `pdf_parser_service` | Parse PDF documents |
| `ocr_service` | Optical character recognition |
| `freeze_letter_service` | Generate freeze letters |
| `letter_queue_service` | Queue letters for mailing |

### External Integrations

| Service | Purpose |
|---------|---------|
| `stripe_client` | Stripe payment processing |
| `stripe_plans_service` | Manage subscription plans |
| `sendcertified_service` | Certified mail API |
| `sendcertified_sftp_service` | SFTP file transfers |
| `notarize_service` | Document notarization |
| `credit_pull_service` | Auto-pull credit reports |

### Automation Services

| Service | Purpose |
|---------|---------|
| `workflow_triggers_service` | Event-based automation |
| `task_queue_service` | Background job processing |
| `scheduler_service` | Scheduled jobs |
| `deadline_service` | Deadline tracking/alerts |

### Security Services

| Service | Purpose |
|---------|---------|
| `encryption` | Data encryption/decryption |
| `api_auth` | API authentication |
| `rate_limiter` | Request rate limiting |
| `security_headers` | HTTP security headers |
| `input_validator` | Input sanitization |

### Analytics Services

| Service | Purpose |
|---------|---------|
| `predictive_analytics_service` | Case outcome predictions |
| `attorney_analytics_service` | Attorney performance metrics |
| `ml_learning_service` | ML model training |
| `performance_service` | System performance metrics |

### Full Service List

<details>
<summary>All 56 services (click to expand)</summary>

```
affiliate_service, api_access_service, api_auth,
attorney_analytics_service, audit_service, case_law_service,
certified_mail_service, config, credit_import_automation,
credit_pull_service, credit_report_ocr_parser, credit_report_parser,
credit_score_calculator, deadline_service, debt_validation_service,
document_scanner_service, email_automation, email_service,
email_templates, encryption, escalation_service, esignature_service,
franchise_service, freeze_letter_service, input_validator,
letter_queue_service, logging_config, lrm_import_service,
metro2_service, ml_learning_service, notarization_service,
notarize_service, ocr_service, pattern_analyzer_service,
pdf_parser_service, pdf_service, performance_service,
predictive_analytics_service, rate_limiter, scheduler_service,
security_headers, sendcertified_service, sendcertified_sftp_service,
settlement_calculator, sms_automation, sms_service, sms_templates,
sol_calculator, stripe_client, stripe_plans_service,
task_queue_service, triage_service, white_label_service,
whitelabel_service, workflow_triggers_service
```

</details>

---

## API Endpoints

### Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/staff/login` | Staff login |
| POST | `/staff/logout` | Staff logout |
| POST | `/portal/login` | Client portal login |
| POST | `/api/auth/token` | API token auth |

### Client Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/clients` | List clients |
| POST | `/api/clients` | Create client |
| GET | `/api/clients/<id>` | Get client details |
| PUT | `/api/clients/<id>` | Update client |
| DELETE | `/api/clients/<id>` | Delete client |

### Credit Reports

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/credit-reports/upload` | Upload credit report |
| POST | `/api/credit-reports/analyze` | Trigger AI analysis |
| GET | `/api/analyses/<id>` | Get analysis results |

### Dispute Letters

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/letters/generate` | Generate dispute letters |
| GET | `/api/letters/<id>` | Get letter |
| POST | `/api/letters/queue` | Queue for mailing |

### Lead Capture

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/get-started` | Lead capture page |
| POST | `/api/leads/capture` | Submit lead form |

### CRM - Call Logging

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/api/call-logs` | List/create calls |
| GET/PUT/DELETE | `/api/call-logs/<id>` | CRUD operations |
| POST | `/api/call-logs/<id>/complete-follow-up` | Mark follow-up done |
| GET | `/api/call-logs/pending-follow-ups` | Pending follow-ups |
| GET | `/api/call-logs/statistics` | Call statistics |

### CRM - Task Assignment

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/api/staff-tasks` | List/create tasks |
| GET/PUT/DELETE | `/api/staff-tasks/<id>` | CRUD operations |
| POST | `/api/staff-tasks/<id>/complete` | Mark task complete |
| POST | `/api/staff-tasks/<id>/assign` | Assign to staff |
| GET | `/api/staff-tasks/my-tasks` | My assigned tasks |
| GET | `/api/staff-tasks/team-workload` | Team workload stats |
| GET | `/api/staff-tasks/statistics` | Task statistics |

### 5-Day Knock-Out (§605B Identity Theft)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/dashboard/5day-knockout` | 5DKO dashboard UI |
| GET | `/api/5day-knockout/strategies` | Available dispute strategies |
| POST | `/api/5day-knockout/generate` | Generate §605B documents via AI |
| GET | `/api/5day-knockout/client/<id>/items` | Get accounts from credit report |

**Note**: Uses Prompt 17 for AI generation. Requires Anthropic API credits.

---

## Client Portal Routes

| Route | Template | Purpose |
|-------|----------|---------|
| `/portal/login` | `portal/login.html` | Portal login |
| `/portal/dashboard` | `portal/dashboard.html` | Client dashboard |
| `/portal/status` | `portal/status.html` | Case status + freeze tracking |
| `/portal/documents` | `portal/documents.html` | Upload documents |
| `/portal/learn` | `portal/learn.html` | Educational content |
| `/portal/profile` | `portal/profile.html` | Profile settings |

---

## Key Flows

### 1. Client Onboarding Flow

```
Lead captures form (/get-started)
    ↓
Client record created (dispute_status='lead')
    ↓
Credit report uploaded/pulled
    ↓
AI analysis triggered
    ↓
Analysis reviewed by staff
    ↓
Dispute letters generated
    ↓
Letters queued for certified mail
    ↓
Client notified (email + SMS if opted in)
```

### 2. Dispute Round Flow

```
Letters sent to bureaus (Round N)
    ↓
30-45 day waiting period
    ↓
CRA response received
    ↓
Response uploaded to portal
    ↓
OCR extracts results
    ↓
Items verified/deleted tracked
    ↓
Next round triggered if needed
    ↓
Client notified of results
```

### 3. Automation Trigger Flow

```
Event occurs (signup, letter sent, response received)
    ↓
WorkflowTriggersService.evaluate_triggers() called
    ↓
Matching triggers found
    ↓
Actions queued (email, SMS, task)
    ↓
TaskQueueService executes actions
    ↓
Execution logged
```

### 4. 5-Day Knock-Out Flow (§605B Identity Theft)

```
PHASE 1: Preparation
    Client credit report imported
        ↓
    Staff selects client in 5DKO dashboard
        ↓
    Accounts loaded from credit report (tradelines + inquiries)
        ↓
    Generate Phase 1 docs:
        - FTC Affidavit template
        - Police Report Instructions (with local PD links)
        - Third-party freeze checklist
        ↓
    Client files police report + FTC report (identitytheft.gov)

PHASE 2: Full Dispute (requires police case #)
    Staff enters police case number
        ↓
    Generate Phase 2 docs:
        - Bureau letters citing FCRA §605B
        - Identity theft declaration
        ↓
    Letters sent to FRAUD DEPARTMENTS (not regular addresses):
        - Experian: P.O. Box 9554, Allen, TX 75013
        - Equifax: P.O. Box 105069, Atlanta, GA 30348
        - TransUnion: P.O. Box 2000, Chester, PA 19016
        ↓
    Bureaus must block within 4 BUSINESS DAYS (not 30 days)
```

---

## Environment Variables

### Required

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret |
| `ANTHROPIC_API_KEY` | Claude AI API key |

### Email (Current: SendGrid, Future: Gmail)

| Variable | Purpose |
|----------|---------|
| `SENDGRID_API_KEY` | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | Sender email |
| `GMAIL_USER` | Gmail address (future) |
| `GMAIL_APP_PASSWORD` | Gmail app password (future) |

### SMS

| Variable | Purpose |
|----------|---------|
| `TWILIO_ACCOUNT_SID` | Twilio account ID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Sending phone number |

### Payments

| Variable | Purpose |
|----------|---------|
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key |
| `STRIPE_WEBHOOK_SECRET` | Webhook verification |

### Optional

| Variable | Purpose |
|----------|---------|
| `SENTRY_DSN` | Error tracking |
| `CI` | CI mode flag (disables rate limiting) |

---

## Testing

### Unit Tests
- **Location**: `tests/`
- **Framework**: Pytest
- **Coverage**: 56/56 services (100%)
- **Count**: 4,653 tests

### E2E Tests
- **Location**: `cypress/e2e/`
- **Framework**: Cypress
- **Coverage**: 51 exhaustive + core tests
- **Count**: 88+ specs

### Running Tests

```bash
# Unit tests
python -m pytest --tb=short -q

# Single Cypress test
CI=true npx cypress run --spec "cypress/e2e/login.cy.js"

# All Cypress tests
CI=true npx cypress run
```

---

## Deployment

### Current: Replit

- Auto-deploys on push to main
- PostgreSQL via Neon
- Environment variables in Replit Secrets

### CI/CD

- GitHub Actions for tests
- Cypress runs with `CI=true` (disables rate limiting)

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-31 | Initial architecture doc created |
| 2025-12-31 | Email: Planning migration from SendGrid to Gmail |
| 2025-12-31 | Added feature backlog (automation, booking, etc.) |

---

## Related Docs

- `CLAUDE.md` - Project status and current work
- `FEATURE_BACKLOG.md` - Upcoming features and priorities
- `EXHAUSTIVE_TESTS_FEATURE_BACKLOG.md` - Test-derived feature specs
- `API_REFERENCE.md` - API documentation
- `ADMIN_USER_GUIDE.md` - Staff user guide
