# FCRA Litigation Platform

**AI-Powered Credit Repair & FCRA Litigation Management System**

Comprehensive platform for credit restoration, dispute management, and FCRA litigation with AI-generated letters, automated workflows, and multi-portal architecture.

[![CI](https://github.com/MDx-Vision/fcra/actions/workflows/ci.yml/badge.svg)](https://github.com/MDx-Vision/fcra/actions/workflows/ci.yml)

## Current Status (Jan 2025)

| Component | Status | Notes |
|-----------|--------|-------|
| Staff Dashboard | Working | Full case management, analytics, ML insights |
| Client Portal | Working | PWA, onboarding, document upload, camera capture |
| Affiliate Portal | Working | Lead tracking, commission management |
| Partner Portal | Working | White-label branding, team management |
| AI Dispute Letters | Working | Claude AI, 4 dispute rounds, 210+ case citations |
| 5-Day Knock-Out | Working | §605B identity theft block (Online + Mail) |
| Credit Import | Working | IdentityIQ, MyScoreIQ, SmartCredit, MyFreeScoreNow |
| Email (Gmail SMTP) | Working | Transactional emails, portal invites |
| SMS (Twilio) | Working | A2P 10DLC compliant, templates |
| Payments (Stripe) | Working | Subscriptions, prepay packages, ACH |
| Certified Mail | Ready | SendCertifiedMail.com integration (awaiting credentials) |
| Calendar Sync | Working | Google Calendar, Outlook integration |
| 2FA Authentication | Working | TOTP, backup codes, trusted devices |

## Key Features

### AI-Powered Dispute Generation

**4-Round Dispute Strategy**
- **Round 1**: Initial FCRA §611 disputes with factual basis challenges
- **Round 2**: Method of Verification (MOV) demands under §611(a)(6)
- **Round 3**: Regulatory complaints (CFPB, State AG, FTC)
- **Round 4**: Pre-arbitration demands with 210+ case citations

**5-Day Knock-Out (§605B)** *(NEW)*
- Identity theft block requiring 4 business day response
- Online submission via bureau portals (fastest method)
- Certified mail to fraud departments (paper trail)
- FTC affidavit generation + police report instructions
- Third-party freeze guidance (LexisNexis, Teletrack, Innovis)
- Phone follow-up scripts with call navigation

**AI Features**
- Claude AI integration for letter generation
- 36K word litigation framework with 210+ FCRA cases
- Auto-detection of FCRA violations
- Medical coding: ICD-10 (90+) & CPT (100+) violation codes
- Specialty templates for different dispute types

### Client Portal (PWA)

**Onboarding Wizard**
- Personal information with USPS address validation
- ID verification with camera capture (mobile + desktop)
- SSN card upload with preview
- Proof of address document upload
- Credit monitoring credential capture
- E-signature for CROA documents (7 required)

**Camera Capture** *(NEW)*
- Mobile: Opens native camera app directly
- Desktop: getUserMedia with fallback to file upload
- Image preview before submission
- Supports ID front/back, SSN card, utility bills

**Portal Features**
- Real-time case status tracking
- Document upload/download
- Secure messaging with staff
- Appointment booking system
- Journey timeline visualization
- Secondary bureau freeze tracking
- Payment management (Stripe + Affirm)

### Staff Dashboard

**Case Management**
- Client intake and onboarding
- Credit report analysis and parsing
- Dispute letter generation and tracking
- Settlement calculator (30% fee)
- Bureau response monitoring

**Analytics & Reporting**
- Revenue dashboard (MRR, ARR, LTV, churn)
- Staff performance leaderboards
- ML insights and predictive analytics
- Violation pattern detection
- ROI calculator per client

**Automation**
- Workflow triggers (20+ event types)
- Drip email/SMS campaigns
- Voicemail drops (Slybroadcast, Drop Cowboy, Twilio)
- Scheduled jobs (payment capture, reminders)
- Task assignment and tracking

### Multi-Portal Architecture

**Staff Portal** (`/dashboard`)
- Full admin capabilities
- Client management
- Letter generation
- Analytics

**Client Portal** (`/portal`)
- Self-service onboarding
- Document uploads
- Case tracking
- Messaging

**Affiliate Portal** (`/affiliate`)
- Lead submission
- Commission tracking
- Performance metrics

**Partner Portal** (`/partner`)
- White-label branding
- Team management
- Client filtering
- Custom domains

### Payment System

**Pricing Structure**
- Free teaser analysis (upload PDF)
- Full analysis: $199 (credited toward Round 1)
- Round 1: $497 ($298 after credit)
- Round 2+: $297/round
- Settlement fee: 30%

**Prepay Packages**
- Starter: $749 (Rounds 1-2)
- Standard: $1,295 (Rounds 1-3)
- Complete: $1,795 (Rounds 1-4)
- Unlimited: $2,000 (All rounds)

**Payment Methods**
- Credit/Debit (2.9% + $0.30)
- ACH Bank Transfer (0.8%, max $5)
- Apple Pay / Google Pay
- Affirm (12-month financing)

### Compliance & Security

**CROA Compliance**
- 7 required disclosure documents
- 3 business day cancellation period
- Sequential signing enforcement
- Signature capture (drawn/typed)
- IP address and timestamp logging

**Security**
- Two-factor authentication (TOTP)
- Encrypted credential storage (AES-256)
- Rate limiting on all endpoints
- HIPAA-ready audit logging
- Session management with trusted devices

### Integrations

| Service | Purpose | Status |
|---------|---------|--------|
| Gmail SMTP | Transactional email | Working |
| Twilio | SMS/WhatsApp | Working |
| Stripe | Payments | Working |
| SendCertifiedMail | Certified mail | Ready |
| USPS | Address validation | Working |
| Google Calendar | Appointment sync | Working |
| Outlook | Appointment sync | Working |
| IdentityIQ | Credit reports | Working |
| MyScoreIQ | Credit reports | Working |
| SmartCredit | Credit reports | Working |
| MyFreeScoreNow | Credit reports | Working |

## Architecture

```
fcra/
├── app.py                  # Main Flask application (26K+ lines)
├── database.py             # SQLAlchemy models (50+ tables)
├── routes/
│   ├── portal.py           # Client portal routes
│   ├── affiliate.py        # Affiliate portal routes
│   └── partner.py          # Partner portal routes
├── services/               # Business logic (86 services)
│   ├── ai_dispute_writer_service.py
│   ├── credit_report_parser.py
│   ├── email_service.py
│   ├── sms_service.py
│   ├── stripe_client.py
│   └── ...
├── templates/              # Jinja2 HTML templates
│   ├── portal/             # Client portal templates
│   ├── includes/           # Shared components
│   └── ...
├── static/                 # CSS, JS, images
├── knowledge/              # AI prompts (17 prompt files)
├── tests/                  # Unit tests (98 files, 5,936 tests)
├── cypress/                # E2E tests (88 specs)
└── docs/                   # Documentation
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, Flask 3.x, SQLAlchemy 2.x |
| Database | PostgreSQL 16 |
| AI | Anthropic Claude API |
| Frontend | Jinja2, Tailwind CSS, vanilla JS |
| PWA | Service Worker, Web App Manifest |
| Email | Gmail SMTP (smtplib) |
| SMS | Twilio SDK |
| Payments | Stripe SDK |
| Testing | pytest, Cypress |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Node.js 18+ (for Cypress tests)

### Local Development

```bash
# Clone repository
git clone https://github.com/MDx-Vision/fcra.git
cd fcra

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://localhost/fcra?sslmode=disable
FCRA_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
PORT=5001
EOF

# Source environment
set -a && source .env && set +a

# Run database migrations
python -c "from database import init_db; init_db()"

# Start server (port 5001 - macOS uses 5000 for AirPlay)
python app.py

# Dashboard: http://localhost:5001/dashboard
# Portal: http://localhost:5001/portal/login
```

### Docker

```bash
docker-compose up
```

## API Endpoints

### Authentication
```bash
POST /api/staff/login           # Staff login
POST /portal/api/login          # Client portal login
POST /affiliate/api/login       # Affiliate login
POST /partner/api/login         # Partner login
```

### Clients
```bash
GET  /api/clients               # List all clients
POST /api/clients               # Create client
GET  /api/clients/{id}          # Get client
PUT  /api/clients/{id}          # Update client
POST /api/clients/{id}/analyze  # Analyze credit report
```

### Disputes
```bash
POST /api/disputes/generate     # Generate dispute letters
GET  /api/disputes/{id}         # Get dispute
POST /api/disputes/{id}/send    # Send to bureaus
```

### 5-Day Knock-Out
```bash
GET  /api/5day-knockout/strategies           # List strategies
GET  /api/5day-knockout/client/{id}/items    # Get disputable items
POST /api/5day-knockout/generate             # Generate documents
POST /api/5day-knockout/create-packets       # Create mail packets
POST /api/5day-knockout/queue-packets        # Queue to SendCertified
```

### Portal Onboarding
```bash
GET  /portal/api/onboarding/progress         # Get progress
POST /portal/api/onboarding/save-personal-info  # Save personal info
POST /portal/api/onboarding/complete-step    # Mark step complete
POST /portal/api/onboarding/upload           # Upload documents
```

### Payments
```bash
POST /api/clients/{id}/payment/round         # Create round payment
POST /api/clients/{id}/payment/prepay        # Create prepay checkout
POST /api/webhooks/stripe                    # Stripe webhooks
```

## Test Status

| Test Type | Count | Status |
|-----------|-------|--------|
| Unit Tests | 5,936 | Passing |
| Cypress E2E | 88 | Passing |
| Exhaustive Tests | 51 files | Passing |
| Integration Tests | 2 files | Passing |
| Service Coverage | 88/88 | 100% |

### Run Tests

```bash
# Unit tests
python -m pytest --tb=short -q

# Single test file
python -m pytest tests/test_email_service.py -v

# Cypress E2E
CI=true npx cypress run

# Single Cypress spec
CI=true npx cypress run --spec "cypress/e2e/login.cy.js"
```

## Test Credentials

| Portal | URL | Email | Password |
|--------|-----|-------|----------|
| Staff Dashboard | /staff/login | test@example.com | testpass123 |
| Client Portal | /portal/login | testclient@example.com | test123 |

## Documentation

| Document | Description |
|----------|-------------|
| CLAUDE.md | Development context and current work |
| ARCHITECTURE.md | Tech stack and project structure |
| FEATURE_BACKLOG.md | Feature priorities (P1-P35 complete) |
| PRICING_STRUCTURE.md | Pricing and payment flow |
| CLIENT_PORTAL_SOP.md | Client portal user guide |
| ADMIN_USER_GUIDE.md | Staff dashboard guide |
| API_REFERENCE.md | REST API documentation |

## Feature Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Platform | Complete |
| Phase 2 | Litigation Features | Complete |
| Phase 3 | AI Integration | Complete |
| Phase 4 | Certified Mail | Ready (awaiting credentials) |
| Phase 5 | Client Portal | Complete |
| Phase 6 | Business Intelligence | Complete |
| Phase 7 | Credit Monitoring Import | Complete |
| Phase 8 | BAG CRM Feature Parity | Complete |
| Phase 9 | 5-Day Knock-Out (§605B) | Complete |

## Compliance

- **FCRA**: Full compliance with Fair Credit Reporting Act
- **CROA**: Credit Repair Organizations Act compliant
- **A2P 10DLC**: SMS messaging compliance
- **PCI DSS**: Stripe handles card data
- **HIPAA**: Audit logging ready

## License

Proprietary - Bright Path Ascend Group. All rights reserved.
