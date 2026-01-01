# Feature Backlog

> Priority features and enhancements for Brightpath Ascend FCRA Platform
>
> Created: 2025-12-31

---

## ~~Priority 1: Client Communication Automation~~ ✅ COMPLETE

**Completed: 2025-12-31**

### What Was Implemented

1. **Database Fields**:
   - [x] Added `sms_opt_in` (Boolean, default False) to Client model
   - [x] Added `email_opt_in` (Boolean, default True) to Client model
   - [x] Created migration entries

2. **Workflow Triggers Wired Up**:
   - [x] `dispute_sent` - Fires when certified mail is sent to bureaus
   - [x] `response_received` - Fires when CRA response is uploaded in portal
   - [x] `document_uploaded` - Fires for all document uploads in portal
   - [x] `status_changed` - Fires on dispute_status updates and round changes
   - [ ] `deadline_approaching` - Scheduler job (future enhancement)

3. **SMS Opt-in Compliance**:
   - [x] Added `check_sms_opt_in()` helper function
   - [x] All 9 SMS trigger functions check opt-in before sending
   - [x] Workflow triggers service checks opt-in for SMS actions

4. **Signup Forms**:
   - [x] Added SMS opt-in checkbox to get_started.html (default unchecked)
   - [x] Added email opt-in checkbox (default checked)
   - [x] API endpoint captures and stores opt-in preferences

### Files Modified
- `database.py` - Added `sms_opt_in`, `email_opt_in` fields + migrations
- `app.py` - Added trigger calls for dispute_sent, status_changed
- `routes/portal.py` - Added triggers for response_received, document_uploaded
- `services/sms_automation.py` - Added opt-in checks to all SMS functions
- `services/workflow_triggers_service.py` - Added opt-in check for SMS action
- `templates/get_started.html` - Added opt-in checkboxes

### Test Status
- 4,644 unit tests passing
- 162/162 SMS & workflow trigger tests
- 55/55 get_started Cypress tests

---

## ~~Priority 2: Gmail Integration (Replace SendGrid)~~ ✅ COMPLETE

**Completed: 2025-12-31**

### What Was Implemented

1. **Email Service Rewrite** (`services/email_service.py`):
   - [x] Replaced SendGrid with Gmail SMTP (smtplib)
   - [x] Uses `GMAIL_USER` and `GMAIL_APP_PASSWORD` env vars
   - [x] All existing function signatures preserved for compatibility
   - [x] Added `is_email_configured()` function (alias: `is_sendgrid_configured()`)
   - [x] Supports HTML emails, plain text, and attachments

2. **Config Updates** (`services/config.py`):
   - [x] Added `GMAIL_USER`, `GMAIL_APP_PASSWORD` properties
   - [x] Added `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME` properties
   - [x] Service checks now use "gmail" (with "sendgrid" as legacy alias)
   - [x] `get_status()` returns "gmail" instead of "sendgrid"

3. **Dependencies** (`requirements.txt`):
   - [x] Commented out `sendgrid` package (no longer needed)

4. **Tests Updated**:
   - [x] `tests/test_email_service.py` - 53 tests for Gmail SMTP
   - [x] `tests/test_config.py` - 143 tests updated for Gmail config

### Files Modified
- `services/email_service.py` - Complete rewrite for Gmail SMTP
- `services/config.py` - Gmail config properties + service checks
- `requirements.txt` - Removed sendgrid
- `tests/test_email_service.py` - 53 Gmail tests
- `tests/test_config.py` - Updated for Gmail

### Environment Variables
```
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_FROM_NAME=Brightpath Ascend Group (optional)
```

### Gmail SMTP Settings
```
Host: smtp.gmail.com
Port: 587 (TLS)
Auth: App Password (requires 2FA enabled)
```

### Test Status
- 4,650 unit tests passing
- 53/53 email service tests
- 143/143 config tests

---

## ~~Priority 3: Post-Analysis Q&A Booking + Live Messaging~~ ✅ COMPLETE

**Completed: 2025-12-31**

### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `BookingSlot` - Available time slots (date, time, duration, staff_id)
   - [x] `Booking` - Client bookings (slot_id, client_id, status, notes)
   - [x] `ClientMessage` - Live support messages (client_id, staff_id, message, sender_type)
   - [x] Created migration entries for all 3 tables

2. **Booking System**:
   - [x] Staff API: `/api/booking-slots` (GET/POST), `/api/booking-slots/<id>` (PUT/DELETE)
   - [x] Staff API: `/api/bookings` (GET), `/api/bookings/<id>/status` (PUT)
   - [x] Portal API: `/api/portal/booking-slots` (GET), `/api/portal/bookings` (GET/POST/DELETE)
   - [x] Bulk slot creation with date range, time range, and days of week
   - [x] Confirmation email sent on booking

3. **Portal Booking UI** (`templates/portal/booking.html`):
   - [x] Hero section with booking CTA
   - [x] "Your Scheduled Calls" section showing upcoming bookings
   - [x] Available time slots grid with date filter (7/14/30 days)
   - [x] Booking confirmation modal with notes field
   - [x] Cancel booking with confirmation modal

4. **Staff Booking Management** (`templates/booking_management.html`):
   - [x] Stats: Total slots, Available, Booked, Today's calls
   - [x] Tabs: Bookings list + Time slots list
   - [x] Quick create for single slot
   - [x] Bulk slot creation modal (date range, days of week, time range)
   - [x] Booking details modal with complete/cancel actions

5. **Live Support Messaging**:
   - [x] Portal API: `/api/portal/messages` (GET/POST), `/api/portal/messages/unread-count`
   - [x] Staff API: `/api/messages/clients`, `/api/messages/client/<id>` (GET/POST)
   - [x] Staff API: `/api/messages/unread-total`
   - [x] Portal messaging page (`templates/portal/messages.html`) with chat UI
   - [x] Staff messaging page (`templates/messaging.html`) with inbox + chat

6. **Navigation Updates**:
   - [x] Portal: Added "Messages" and "Book Call" tabs
   - [x] Staff Sidebar: Added "Bookings" and "Messages" links

### Files Modified/Created
- `database.py` - Added BookingSlot, Booking, ClientMessage models
- `app.py` - Added ~400 lines of booking + messaging API endpoints
- `routes/portal.py` - Added booking and messages routes
- `templates/portal/booking.html` - Client booking page (new)
- `templates/portal/messages.html` - Client messaging page (new)
- `templates/portal/base_portal.html` - Updated navigation
- `templates/booking_management.html` - Staff booking page (new)
- `templates/messaging.html` - Staff messaging page (new)
- `templates/includes/dashboard_sidebar.html` - Added sidebar links

---

## ~~Priority 4: Simple Report Upload Flow~~ ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **Simple Upload Page** (`/upload-report`):
   - [x] Minimal form: Name, Email, File upload
   - [x] Drag & drop file upload with visual feedback
   - [x] PDF, JPG, PNG support (up to 25MB)
   - [x] Mobile-responsive design
   - [x] Success state with CTA to complete profile

2. **API Endpoint** (`/api/leads/upload-report`):
   - [x] Creates client with `dispute_status='report_uploaded'`
   - [x] Saves file to `static/client_uploads/{client_id}/reports/`
   - [x] Creates ClientUpload record
   - [x] Sends confirmation email
   - [x] Triggers `document_uploaded` workflow event

3. **Features**:
   - [x] Trust badges (Bank-Level Security, FCRA Compliant, No Credit Check)
   - [x] Link to full signup form for more details
   - [x] Error handling with user-friendly messages

### Files Created/Modified
- `templates/upload_report.html` - Simple upload page (new)
- `app.py` - Added `/upload-report` route and `/api/leads/upload-report` endpoint

---

## Completed Features

- [x] Phase 1-8 Core Platform
- [x] Lead Capture Landing Page (`/get-started`)
- [x] Portal Logo Fix
- [x] Client Portal Document Upload Enhancements
- [x] Secondary Bureau Freeze Status UI
- [x] **Secondary Bureau Freeze UI Overhaul** (2026-01-01)
  - "What to Watch For in Your Mail" priority action card
  - Progress bar (X/9 complete)
  - Smart grouping: Pending first, Frozen collapsed
  - Auto-create bureau records on status page load
  - **Expected response dates**: Shows "Expected by: [date]" (30 days)
  - **Overdue tracking**: Red warning when past 30 days, ⚠️ icons on overdue bureaus
  - CTA for client to contact staff for follow-up help
- [x] **Priority 1: Client Communication Automation** (2025-12-31)
  - SMS & email opt-in fields
  - Workflow triggers wired up (dispute_sent, response_received, document_uploaded, status_changed)
  - SMS opt-in compliance checks
- [x] **Priority 2: Gmail Integration** (2025-12-31)
  - Replaced SendGrid with Gmail SMTP
  - Uses `GMAIL_USER` and `GMAIL_APP_PASSWORD` env vars
  - All email functions work with attachments
- [x] **Priority 3: Q&A Booking + Live Messaging** (2025-12-31)
  - Client booking portal with available time slots
  - Staff booking management with bulk slot creation
  - Live support messaging in portal
  - Staff messaging inbox for responding to clients
- [x] **Priority 4: Simple Report Upload Flow** (2026-01-01)
  - Minimal upload page at `/upload-report`
  - Name, email, file upload only
  - Auto-creates lead with `dispute_status='report_uploaded'`
  - Confirmation email + staff notification

---

## Priority 5: Deadline Approaching Scheduler ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **Deadline Checker Service** (`services/deadline_checker_service.py`):
   - [x] `check_all_deadlines()` - Main entry point for scheduled job
   - [x] `check_secondary_bureau_deadlines()` - Check freeze responses
   - [x] `check_cra_response_deadlines()` - Check dispute responses
   - [x] `check_sol_deadlines()` - Check statute of limitations
   - [x] `get_deadline_summary()` - Per-client deadline summary

2. **Scheduled Job** (daily at 8 AM):
   - [x] Added to `scheduler_service.py` BUILT_IN_SCHEDULES
   - [x] Task type: `check_deadlines`

3. **Workflow Triggers Added**:
   - [x] "Secondary Bureau Response Due Soon" (25 days)
   - [x] "Secondary Bureau Response Overdue" (31+ days)
   - [x] "CRA Response Due Soon" (5 days before deadline)
   - [x] "CRA Response Overdue" (5+ days past deadline)

4. **Notifications**:
   - [x] Email notifications for all deadline types
   - [x] SMS notifications (opt-in required)
   - [x] Case notes for overdue items
   - [x] Escalation tasks for violations

### Files Created/Modified
- `services/deadline_checker_service.py` (NEW) - Main service
- `services/scheduler_service.py` - Added scheduled job
- `services/workflow_triggers_service.py` - Added 4 new triggers
- `tests/test_deadline_checker_service.py` (NEW) - 22 tests

### Test Status
- 22/22 deadline checker tests passing

---

## Priority 6: Lead Scoring ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **Database Fields** (`database.py`):
   - [x] `lead_score` (Integer 0-100) - Priority score
   - [x] `lead_score_factors` (JSON) - Breakdown of scoring factors
   - [x] `lead_scored_at` (DateTime) - When last scored

2. **LeadScoringService** (`services/lead_scoring_service.py`):
   - [x] `calculate_score()` - Calculate score without saving
   - [x] `update_client_score()` - Calculate and save score
   - [x] `score_all_clients()` - Batch score all clients
   - [x] `get_top_leads()` - Get highest priority leads
   - [x] `get_score_distribution()` - Distribution by priority

3. **Scoring Factors**:
   - Collections: +15 pts each (capped at 40)
   - Charge-offs: +12 pts each
   - Public records: +20 pts each
   - Late payments: +5 pts each
   - Inquiries: +2 pts each
   - Violations: +10 pts each (litigation potential)
   - Status bonus: up to +10 pts

4. **API Endpoints**:
   - `GET /api/clients/<id>/score` - Get client score
   - `POST /api/clients/<id>/score` - Calculate & save score
   - `POST /api/leads/score-all` - Batch score all
   - `GET /api/leads/top` - Top leads by score
   - `GET /api/leads/distribution` - Score distribution

5. **UI Updates** (`templates/clients.html`):
   - [x] Lead score column with color badges
   - [x] Click unscored clients to calculate
   - [x] HIGH (red/orange), MEDIUM (yellow), LOW (gray) badges

6. **Auto-scoring**:
   - [x] Triggered after credit report analysis

### Files Created/Modified
- `database.py` - Added lead_score fields + migration
- `services/lead_scoring_service.py` (NEW) - 400+ lines
- `app.py` - Added 5 API endpoints + auto-score hook
- `templates/clients.html` - Lead column + styles + JS
- `tests/test_lead_scoring_service.py` (NEW) - 29 tests

### Test Status
- 29/29 lead scoring tests passing

---

## Priority 7: Email Templates Library ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **Enhanced EmailTemplate Model** (`database.py`):
   - [x] Added `name` (human-readable name)
   - [x] Added `category` (8 categories: welcome, updates, reminders, notifications, payment, legal, marketing, general)
   - [x] Added `description` (what template is for)
   - [x] Added `plain_text_content` (fallback for non-HTML clients)
   - [x] Added `variables` (JSON array of supported variables)
   - [x] Added `is_active` (can disable without deleting)

2. **EmailTemplateService** (`services/email_template_service.py`):
   - [x] `create_template()` - Create new templates
   - [x] `update_template()` - Update existing templates
   - [x] `delete_template()` - Delete custom templates (system templates protected)
   - [x] `get_template()` - Get by ID or type
   - [x] `list_templates()` - List with filtering
   - [x] `render_template()` - Variable substitution
   - [x] `duplicate_template()` - Clone templates
   - [x] `get_template_stats()` - Statistics
   - [x] `seed_default_templates()` - Seed 11 system templates

3. **API Endpoints**:
   - [x] `GET /api/email-templates/library` - List all templates
   - [x] `GET /api/email-templates/library/<id>` - Get template by ID
   - [x] `POST /api/email-templates/library` - Create template
   - [x] `PUT /api/email-templates/library/<id>` - Update template
   - [x] `DELETE /api/email-templates/library/<id>` - Delete template
   - [x] `POST /api/email-templates/library/<id>/duplicate` - Clone template
   - [x] `POST /api/email-templates/library/<id>/render` - Render with variables
   - [x] `GET /api/email-templates/stats` - Template statistics
   - [x] `GET /api/email-templates/categories` - List categories
   - [x] `GET /api/email-templates/variables` - Common variables
   - [x] `POST /api/email-templates/seed` - Seed defaults

4. **Template Management UI** (`templates/email_templates.html`):
   - [x] Stats dashboard (total, active, custom, system)
   - [x] Template grid with filtering (category, status, type, search)
   - [x] Create/Edit modal with tabs (Details, Content, Preview)
   - [x] Variable insertion helper
   - [x] Live preview with variable substitution
   - [x] Duplicate and delete actions

5. **Common Variables**:
   - `{client_name}`, `{first_name}`, `{email}`, `{phone}`
   - `{portal_url}`, `{company_name}`, `{current_date}`
   - `{dispute_round}`, `{bureau}`, `{status}`

6. **Default System Templates** (11 templates):
   - Welcome Email, Document Reminder, Case Status Update
   - Dispute Letter Sent, Bureau Response Received
   - Payment Reminder, Analysis Complete, Dispute Letters Ready
   - Deadline Approaching, FCRA Violation Alert, Call Booking Confirmation

### Files Created/Modified
- `database.py` - Enhanced EmailTemplate model + migrations
- `services/email_template_service.py` (NEW) - 600+ lines
- `app.py` - Added 11 API endpoints + dashboard route
- `templates/email_templates.html` (NEW) - Full management UI
- `templates/includes/dashboard_sidebar.html` - Added sidebar link
- `tests/test_email_template_service.py` (NEW) - 48 tests

### Test Status
- 48/48 email template service tests passing

---

## Priority 8: Drip Campaigns (Automated Follow-up Sequences) ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `DripCampaign` - Campaign settings (name, trigger, send window)
   - [x] `DripStep` - Individual email steps with delays
   - [x] `DripEnrollment` - Track client progress through campaigns
   - [x] `DripEmailLog` - Log sent emails for tracking
   - [x] Created migration entries for all 4 tables

2. **DripCampaignService** (`services/drip_campaign_service.py`):
   - [x] Campaign CRUD (create, update, delete, get, list)
   - [x] Step management (add, update, delete, reorder)
   - [x] Enrollment management (enroll, pause, resume, cancel)
   - [x] Email processing for scheduled job
   - [x] Campaign statistics

3. **API Endpoints** (22 endpoints):
   - [x] `GET /api/drip-campaigns` - List campaigns
   - [x] `POST /api/drip-campaigns` - Create campaign
   - [x] `GET /api/drip-campaigns/<id>` - Get campaign
   - [x] `PUT /api/drip-campaigns/<id>` - Update campaign
   - [x] `DELETE /api/drip-campaigns/<id>` - Delete campaign
   - [x] `GET /api/drip-campaigns/<id>/stats` - Campaign stats
   - [x] `POST /api/drip-campaigns/<id>/steps` - Add step
   - [x] `PUT /api/drip-campaigns/steps/<id>` - Update step
   - [x] `DELETE /api/drip-campaigns/steps/<id>` - Delete step
   - [x] `POST /api/drip-campaigns/<id>/steps/reorder` - Reorder
   - [x] `GET /api/drip-campaigns/enrollments` - List enrollments
   - [x] `POST /api/drip-campaigns/<id>/enroll/<client_id>` - Enroll
   - [x] Pause, resume, cancel enrollment endpoints
   - [x] `POST /api/drip-campaigns/process` - Manual process trigger

4. **Scheduled Job**:
   - [x] Added to `scheduler_service.py` BUILT_IN_SCHEDULES
   - [x] "Process Drip Campaign Emails" runs hourly

5. **Campaign Management UI** (`templates/drip_campaigns.html`):
   - [x] Stats dashboard (Total, Active, Enrolled, Completed)
   - [x] Campaign grid with filtering (status, trigger type, search)
   - [x] Create/Edit campaign modal with step builder
   - [x] Enrollments tab with status management
   - [x] Manual process trigger button

6. **Trigger Types Supported**:
   - `signup` - New client signup
   - `status_change` - Dispute status change
   - `report_uploaded` - Credit report uploaded
   - `analysis_complete` - Analysis complete
   - `dispute_sent` - Dispute sent to bureaus
   - `response_received` - Bureau response received
   - `manual` - Manual enrollment
   - `tag_added` - Tag added to client

### Files Created/Modified
- `database.py` - Added 4 models + migrations
- `services/drip_campaign_service.py` (NEW) - 1,090 lines
- `services/scheduler_service.py` - Added scheduled job
- `app.py` - Added 22 API endpoints + page route
- `templates/drip_campaigns.html` (NEW) - Full UI
- `templates/includes/dashboard_sidebar.html` - Added sidebar link
- `tests/test_drip_campaign_service.py` (NEW) - 40 tests

### Test Status
- 40/40 drip campaign service tests passing

---

## Upcoming Features

### Priority 9: Light/Dark Mode Toggle

**Status**: Backlog

**Description**: Add theme switching capability across all portals (Staff Dashboard, Client Portal, Affiliate Portal).

**Implementation Plan**:

1. **CSS Variables for Theming**:
   - Define CSS custom properties for colors (background, text, borders, accents)
   - Create light theme and dark theme variable sets
   - Apply variables across all templates

2. **Theme Toggle Component**:
   - Sun/moon icon toggle button in header
   - Smooth transition animation between themes
   - Consistent placement across all portals

3. **Persistence**:
   - Store preference in localStorage
   - Optional: Store in user profile for cross-device sync

4. **System Preference Detection**:
   - Respect `prefers-color-scheme` media query
   - Auto-switch based on OS/browser settings
   - Manual override takes precedence

5. **Templates to Update**:
   - Staff Dashboard (`templates/includes/dashboard_sidebar.html`, all dashboard pages)
   - Client Portal (`templates/portal/base_portal.html`)
   - Affiliate Portal (`templates/affiliate_portal/base.html`)

**Estimated Scope**:
- CSS variables file (~200 lines)
- JS toggle logic (~50 lines)
- Template updates (minor)

---

### Priority 10: White Label Partner Portal

**Status**: Backlog

**Description**: Create a dedicated portal where white label partners (law firms, credit repair agencies) can log in and manage their own branding, users, and clients.

**Current State**:
- ✅ `WhiteLabelTenant` model exists with branding fields
- ✅ `WhiteLabelService` for tenant management
- ✅ Staff admin page for managing tenants
- ❌ No partner login/authentication
- ❌ No self-service branding management
- ❌ No partner dashboard

**Implementation Plan**:

1. **Partner Authentication**:
   - Add `password_hash`, `last_login` to WhiteLabelTenant or create WhiteLabelUser model
   - Login/logout routes at `/partner/login`
   - Session-based auth (similar to affiliate portal)

2. **Partner Dashboard** (`/partner/dashboard`):
   - Stats: Total clients, Active disputes, Revenue, Team members
   - Recent activity feed
   - Quick actions

3. **Branding Management** (`/partner/branding`):
   - Logo upload (main + favicon)
   - Color picker (primary, secondary, accent)
   - Company info (name, address, phone, email)
   - Custom CSS/JS editor
   - Live preview

4. **Team Management** (`/partner/team`):
   - Invite team members
   - Role management (admin, staff, viewer)
   - Activity logs

5. **Client Management** (`/partner/clients`):
   - View their clients only (filtered by tenant_id)
   - Client status overview
   - Export functionality

6. **Analytics** (`/partner/analytics`):
   - Client acquisition over time
   - Dispute success rates
   - Revenue tracking

7. **Templates to Create**:
   - `templates/partner_portal/base.html`
   - `templates/partner_portal/login.html`
   - `templates/partner_portal/dashboard.html`
   - `templates/partner_portal/branding.html`
   - `templates/partner_portal/team.html`
   - `templates/partner_portal/clients.html`
   - `templates/partner_portal/analytics.html`
   - `templates/partner_portal/settings.html`

**Database Changes**:
- Add auth fields to WhiteLabelTenant or create WhiteLabelUser model
- Add `tenant_id` foreign key to Client model (if not exists)

**Estimated Scope**: Medium-Large (similar to Affiliate Portal)

---

### Priority 11: CROA Document Signing Workflow

**Status**: Backlog

**Description**: Integrate the full 7-document CROA signing workflow into the client portal onboarding process with proper sequential signing and compliance tracking.

**Current State**:
- ✅ 7 CROA HTML documents exist in `/docs/htm/`
- ✅ `DocumentTemplate` model with CROA fields
- ✅ `ESignatureRequest` model for signature tracking
- ✅ `esignature_service.py` with token-based signing
- ❌ Onboarding has single "agreement" checkbox (not full CROA flow)
- ❌ No sequential document signing in portal
- ❌ No cancellation period tracking
- ❌ Documents not loaded into database yet

**CROA Compliance Requirements**:
1. Rights Disclosure MUST be signed BEFORE any contract
2. Client has 3 business days to cancel after signing contract
3. No services can begin until cancellation period expires
4. All documents must be signed in order

**Implementation Plan**:

1. **Load Documents to Database**:
   - Run `load_croa_documents.py` to populate DocumentTemplate table
   - Verify all 7 documents load correctly

2. **Update Onboarding Wizard**:
   - Replace single "agreement" step with CROA document flow
   - Show each document in sequence with scroll-to-bottom before sign
   - Signature capture pad for each document
   - Track `signed_at` timestamp for each document

3. **CROA Progress Tracking** (new model or extend OnboardingProgress):
   - `rights_disclosure_signed_at`
   - `lpoa_signed_at`
   - `service_agreement_signed_at`
   - `cancellation_notice_signed_at`
   - `cancellation_period_ends_at` (3 business days after contract)
   - `service_completion_signed_at`
   - `hipaa_signed_at` (optional)
   - `welcome_packet_signed_at`

4. **Cancellation Period Workflow**:
   - Show "Cancellation period expires: [date]" in portal
   - Block service start until cancellation period ends
   - Client can cancel during period via button
   - After period ends, show "Service Completion Authorization" step

5. **Portal UI Updates**:
   - Document viewer with full text display
   - Signature capture canvas
   - Progress indicator (1/7, 2/7, etc.)
   - Download signed documents link

6. **Compliance Features**:
   - Audit log of all signature events
   - IP address capture with each signature
   - Timestamp verification
   - PDF generation of signed documents

**Database Changes**:
- Populate `document_templates` table with CROA docs
- Add CROA progress fields to OnboardingProgress or create CROAProgress model
- Add `cancellation_period_ends_at` to Client model

**Estimated Scope**: Medium (extend existing e-signature infrastructure)

---

## Notes

- **Email**: Gmail SMTP (SendGrid removed)
- **SMS**: Twilio (A2P campaign pending carrier approval)
- All 8 priorities complete!
- See `FEATURE_IMPLEMENTATION_CHECKLIST.md` for future feature roadmap
