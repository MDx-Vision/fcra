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

## ~~Priority 9: Light/Dark Mode Toggle~~ ✅ COMPLETE

**Completed: 2026-01-02**

### What Was Implemented

1. **CSS Variables System** (`static/css/theme-variables.css` - 280 lines):
   - [x] Base color palette (grays, navy, teal, green, status colors)
   - [x] Semantic theme variables for light mode (default)
   - [x] Dark mode overrides via `[data-theme="dark"]`
   - [x] Portal-specific accent colors (client=teal, staff/affiliate=green)
   - [x] Utility classes (.bg-theme-primary, .text-theme-primary, etc.)
   - [x] Smooth transitions for theme switching

2. **Theme Service** (`static/js/theme-service.js` - 200 lines):
   - [x] `ThemeService.init()` - Initialize on page load
   - [x] `ThemeService.toggle()` - Switch between light/dark
   - [x] `ThemeService.getSystemPreference()` - Detect OS preference
   - [x] `ThemeService.getSavedTheme()` - Read from localStorage
   - [x] `watchSystemPreference()` - Auto-switch on system change
   - [x] `updateMetaThemeColor()` - Update mobile browser UI color

3. **Template Includes**:
   - [x] `templates/includes/theme_head.html` - Flash prevention script + CSS
   - [x] `templates/includes/theme_toggle.html` - Reusable toggle button

4. **Client Portal Updates**:
   - [x] `templates/portal/base_portal.html` - Added theme includes + toggle
   - [x] `static/css/portal-redesign.css` - Converted to theme variables
   - [x] Updated nav, cards, forms, mobile nav with theme vars

5. **Staff Dashboard Updates**:
   - [x] `templates/includes/dashboard_sidebar_styles.html` - Theme head + vars
   - [x] `templates/includes/dashboard_sidebar.html` - Toggle button + script
   - [x] Sidebar stays dark in both themes (professional look)

6. **Affiliate Portal Updates**:
   - [x] `templates/affiliate_portal/base.html` - Full theme variable conversion
   - [x] Toggle button in sidebar header
   - [x] All elements use semantic theme variables

### Files Created
- `static/css/theme-variables.css` (280 lines)
- `static/js/theme-service.js` (200 lines)
- `templates/includes/theme_head.html`
- `templates/includes/theme_toggle.html`
- `cypress/e2e/theme_toggle.cy.js` (200 lines)

### Files Modified
- `templates/portal/base_portal.html`
- `static/css/portal-redesign.css`
- `templates/includes/dashboard_sidebar_styles.html`
- `templates/includes/dashboard_sidebar.html`
- `templates/affiliate_portal/base.html`

### Features
- Light mode default
- Respects `prefers-color-scheme` system preference
- localStorage persistence across sessions
- Smooth CSS transitions on theme change
- Portal-specific accent colors
- Mobile meta theme-color support

---

## ~~Priority 10: White Label Partner Portal~~ ✅ COMPLETE

**Completed: 2026-01-02**

### What Was Implemented

1. **Database Changes** (`database.py`):
   - [x] Added `admin_email` to WhiteLabelTenant (unique, for partner login)
   - [x] Added `admin_password_hash` to WhiteLabelTenant
   - [x] Added `last_login`, `password_reset_token`, `password_reset_expires`
   - [x] Added migration entries for all new columns

2. **Partner Portal Routes** (`routes/partner.py` - 700+ lines):
   - [x] Authentication: `/partner/login`, `/partner/logout`, `/partner/forgot-password`, `/partner/reset-password/<token>`
   - [x] Dashboard: `/partner/dashboard` with stats and quick actions
   - [x] Branding: `/partner/branding` + API endpoints for logo/favicon upload
   - [x] Clients: `/partner/clients` with search, filter, CSV export
   - [x] Team: `/partner/team` with invite/remove member functionality
   - [x] Analytics: `/partner/analytics` with charts and metrics
   - [x] Settings: `/partner/settings` with password change, API key management
   - [x] CI auth bypass for testing (creates test partner automatically)

3. **API Endpoints**:
   - [x] `PUT /partner/api/branding` - Update branding settings
   - [x] `POST /partner/api/branding/logo` - Upload logo
   - [x] `POST /partner/api/branding/favicon` - Upload favicon
   - [x] `GET /partner/api/clients` - Get clients as JSON
   - [x] `GET /partner/api/clients/export` - Export clients as CSV
   - [x] `GET/POST /partner/api/team` - List/invite team members
   - [x] `DELETE /partner/api/team/<id>` - Remove team member
   - [x] `GET /partner/api/analytics/summary` - Analytics data
   - [x] `PUT /partner/api/settings` - Update settings
   - [x] `PUT /partner/api/settings/password` - Change password
   - [x] `POST /partner/api/settings/regenerate-api-key` - Regenerate API key

4. **Templates Created** (`templates/partner_portal/`):
   - [x] `base.html` - Base template with sidebar, theme support
   - [x] `login.html` - Login page with branding
   - [x] `forgot_password.html` - Password reset request
   - [x] `reset_password.html` - Password reset form
   - [x] `dashboard.html` - Stats, quick actions, recent clients
   - [x] `branding.html` - Logo upload, colors, company info, custom CSS
   - [x] `clients.html` - Client list with search/filter/export
   - [x] `team.html` - Team management with invite modal
   - [x] `analytics.html` - Stats, chart (Chart.js), metrics
   - [x] `settings.html` - Account settings, password change, API keys

5. **Features**:
   - [x] Session-based authentication for partners
   - [x] Password reset with secure tokens
   - [x] Self-service branding (logo, favicon, colors, CSS)
   - [x] Team member invitation with role assignment
   - [x] Client filtering by tenant (only see their clients)
   - [x] CSV export of client data
   - [x] Analytics with Chart.js visualization
   - [x] API key management and webhook configuration
   - [x] Light/dark mode theme support

6. **Cypress Tests** (`cypress/e2e/partner_portal.cy.js` - 40+ tests):
   - [x] Login page tests
   - [x] Forgot password tests
   - [x] Dashboard tests (CI auth)
   - [x] Clients page tests
   - [x] Branding page tests
   - [x] Team page tests
   - [x] Analytics page tests
   - [x] Settings page tests
   - [x] Navigation tests
   - [x] Theme support tests
   - [x] API endpoint tests

### Files Created
- `routes/partner.py` (700+ lines)
- `templates/partner_portal/base.html`
- `templates/partner_portal/login.html`
- `templates/partner_portal/forgot_password.html`
- `templates/partner_portal/reset_password.html`
- `templates/partner_portal/dashboard.html`
- `templates/partner_portal/branding.html`
- `templates/partner_portal/clients.html`
- `templates/partner_portal/team.html`
- `templates/partner_portal/analytics.html`
- `templates/partner_portal/settings.html`
- `cypress/e2e/partner_portal.cy.js`

### Files Modified
- `database.py` - Added auth fields to WhiteLabelTenant + migrations
- `app.py` - Registered partner blueprint

---

## ~~Priority 11: CROA Document Signing Workflow~~ ✅ COMPLETE

**Completed: 2026-01-01**

### What Was Implemented

1. **CROAProgress Model** (`database.py`):
   - [x] Tracks client progress through 7 CROA documents
   - [x] Fields for each document's `signed_at` timestamp
   - [x] Cancellation period tracking (starts_at, ends_at, waived, cancelled_at)
   - [x] Overall progress: current_document, documents_completed, is_complete

2. **CROASigningService** (`services/croa_signing_service.py` - 650 lines):
   - [x] 7 CROA documents defined with order, required status
   - [x] Methods: `get_or_create_progress`, `get_progress_summary`, `get_document`
   - [x] `get_current_document` - next document to sign
   - [x] `sign_document` - signs with signature capture (drawn/typed)
   - [x] `skip_optional_document` - skip HIPAA (optional)
   - [x] `get_cancellation_status`, `cancel_service` - 3-day cancellation period
   - [x] `waive_cancellation_period`, `can_begin_services`
   - [x] `_calculate_cancellation_end` - 3 business days (excludes weekends)
   - [x] Signature image saving to static/signatures/

3. **CROA API Endpoints** (`routes/portal.py`):
   - [x] `GET /portal/agreements` - Signing page
   - [x] `GET /portal/api/croa/progress` - Get signing progress
   - [x] `GET /portal/api/croa/document/<code>` - Get document template
   - [x] `GET /portal/api/croa/current-document` - Get next to sign
   - [x] `POST /portal/api/croa/sign` - Sign a document
   - [x] `POST /portal/api/croa/skip-optional` - Skip optional doc
   - [x] `GET /portal/api/croa/cancellation-status` - Cancellation info
   - [x] `POST /portal/api/croa/cancel` - Cancel during 3-day period
   - [x] `GET /portal/api/croa/can-begin-services` - Check if ready

4. **Agreements Page** (`templates/portal/agreements.html`):
   - [x] 7-step progress indicator
   - [x] Document viewer with scrollable content
   - [x] Scroll-to-bottom requirement before signing
   - [x] Signature capture: canvas (drawn) or typed name input
   - [x] Sign button enabled after scroll + signature
   - [x] Skip button for optional documents
   - [x] Cancellation notice with countdown
   - [x] Complete state with success message

5. **CROA Compliance Features**:
   - [x] Rights Disclosure MUST be signed before any contract
   - [x] 3 business day cancellation period (excludes weekends)
   - [x] Sequential document signing enforced
   - [x] IP address and user agent captured for audit
   - [x] Signature images saved with timestamps

### Files Created/Modified
- `services/croa_signing_service.py` (650 lines)
- `templates/portal/agreements.html`
- `tests/test_croa_signing_service.py` (55 tests)
- `database.py` - Added CROAProgress model
- `routes/portal.py` - Added 9 CROA API endpoints
- `templates/portal/onboarding.html` - Updated agreement step

### Test Status
- 55/55 CROA signing service tests passing

---

## ~~Priority 12: Two-Factor Authentication (2FA)~~ ✅ COMPLETE

**Completed: 2026-01-03**

### What Was Implemented

1. **TwoFactorService** (`services/two_factor_service.py` - 500+ lines):
   - [x] TOTP generation and verification with pyotp
   - [x] QR code generation for authenticator apps
   - [x] 10 backup codes with secure hashing
   - [x] Device trust management (30-day tokens)
   - [x] Staff and Partner portal 2FA support

2. **Database Changes** (`database.py`):
   - [x] `two_factor_enabled` (Boolean) on Staff model
   - [x] `two_factor_secret` (encrypted string) for TOTP
   - [x] `two_factor_method` (totp/sms/email)
   - [x] `two_factor_backup_codes` (JSON, hashed)
   - [x] `two_factor_verified_at`, `two_factor_last_used` (DateTime)
   - [x] `trusted_devices` (JSON) for device trust
   - [x] Same fields added to WhiteLabelTenant for partner portal

3. **API Endpoints** (`app.py`):
   - [x] `GET /api/2fa/status` - Check 2FA status
   - [x] `POST /api/2fa/setup` - Start setup (returns secret + QR)
   - [x] `POST /api/2fa/verify` - Verify and enable 2FA
   - [x] `POST /api/2fa/disable` - Disable 2FA
   - [x] `POST /api/2fa/backup-codes` - Regenerate backup codes
   - [x] `GET /api/2fa/devices` - List trusted devices
   - [x] `POST /api/2fa/devices/revoke-all` - Revoke all devices

4. **Login Flow** (`templates/staff_login.html`):
   - [x] 2FA challenge on login when enabled
   - [x] Backup code support
   - [x] "Trust this device" option (30 days)
   - [x] Device token cookie management

5. **Settings UI** (`templates/settings.html`):
   - [x] 2FA status display
   - [x] Enable 2FA button + QR code setup
   - [x] Backup codes display
   - [x] Trusted devices count
   - [x] Disable 2FA with code verification
   - [x] Regenerate backup codes button
   - [x] Revoke all devices button

6. **Security Features**:
   - [x] Encrypted TOTP secrets (Fernet)
   - [x] SHA256 hashed backup codes
   - [x] Device trust expiration (30 days)
   - [x] Rate limiting on login (existing)

### Files Created/Modified
- `services/two_factor_service.py` (500+ lines) - NEW
- `tests/test_two_factor_service.py` (63 tests) - NEW
- `database.py` - Added 2FA fields + migrations
- `app.py` - Added 7 2FA API endpoints, modified login
- `templates/settings.html` - Added 2FA section
- `templates/staff_login.html` - Added 2FA challenge flow
- `requirements.txt` - Added pyotp, qrcode

### Test Status
- 63/63 2FA service tests passing

---

## Prioritized Backlog (P13-P20)

### ~~Priority 13: Revenue Dashboard~~ ✅ COMPLETE
**Completed**: 2026-01-03 | **Effort**: Medium

Track MRR, ARR, churn, LTV, CAC metrics with charts and trends.

#### What Was Implemented

1. **RevenueMetricsService** (`services/revenue_metrics_service.py` - 600 lines):
   - [x] `get_total_revenue()` - Total revenue for period
   - [x] `get_revenue_by_period()` - Revenue by day/week/month/year
   - [x] `get_revenue_by_payment_method()` - Breakdown by payment method
   - [x] `get_revenue_by_plan()` - Breakdown by signup plan
   - [x] `get_mrr()` - Monthly Recurring Revenue + ARR + ARPU
   - [x] `get_mrr_growth()` - MRR growth over months
   - [x] `get_churn_rate()` - Churn and retention rates
   - [x] `get_client_retention_cohorts()` - Retention by cohorts
   - [x] `get_ltv()` - Customer Lifetime Value
   - [x] `get_commission_metrics()` - Affiliate commission tracking
   - [x] `get_top_affiliates()` - Top performers
   - [x] `get_dashboard_summary()` - All metrics combined
   - [x] `get_revenue_chart_data()` - Chart.js formatted data
   - [x] `export_revenue_data()` - CSV export data

2. **Revenue Dashboard UI** (`templates/revenue_dashboard.html`):
   - [x] 8 metric cards (Revenue, MRR, LTV, Churn, Signups, Conversion, ARPU, Pending Commissions)
   - [x] Revenue over time line chart (Chart.js)
   - [x] Revenue by plan doughnut chart
   - [x] Top affiliates table
   - [x] Payment method breakdown
   - [x] Plan breakdown
   - [x] CSV export button
   - [x] Responsive design

3. **API Endpoints** (`app.py`):
   - [x] `GET /dashboard/revenue` - Dashboard page
   - [x] `GET /api/revenue/summary` - Dashboard summary API
   - [x] `GET /api/revenue/by-period` - Revenue by time period
   - [x] `GET /api/revenue/mrr` - MRR/ARR metrics
   - [x] `GET /api/revenue/churn` - Churn and retention
   - [x] `GET /api/revenue/export` - CSV export

4. **Sidebar Navigation**:
   - [x] Added "Revenue" link in Analytics section

5. **Unit Tests** (`tests/test_revenue_metrics_service.py` - 31 tests):
   - [x] All service methods tested
   - [x] Edge cases for zero division
   - [x] Negative growth handling

#### Files Created/Modified
- `services/revenue_metrics_service.py` - NEW (600 lines)
- `templates/revenue_dashboard.html` - NEW (500 lines)
- `tests/test_revenue_metrics_service.py` - NEW (31 tests)
- `app.py` - Added revenue endpoints
- `templates/includes/dashboard_sidebar.html` - Added revenue link

---

### ~~Priority 14: Stripe Subscriptions~~ ✅ COMPLETE
**Completed**: 2026-01-03 | **Effort**: High

Monthly recurring billing with subscription tiers.

#### What Was Implemented

1. **SubscriptionService** (`services/subscription_service.py` - 700+ lines):
   - [x] Plan tiers: Basic ($49/mo), Pro ($99/mo), Enterprise ($199/mo)
   - [x] `sync_plans_to_stripe()` - Sync plans to Stripe products/prices
   - [x] `get_or_create_stripe_customer()` - Customer management
   - [x] `create_checkout_session()` - Subscription checkout
   - [x] `create_subscription()` - Direct subscription creation
   - [x] `cancel_subscription()` - Cancel at period end or immediately
   - [x] `reactivate_subscription()` - Undo pending cancellation
   - [x] `change_plan()` - Upgrade/downgrade with proration
   - [x] `create_billing_portal_session()` - Stripe billing portal access
   - [x] Webhook handlers for all subscription events

2. **API Endpoints** (`app.py`):
   - [x] `GET /api/subscriptions/plans` - List available plans
   - [x] `POST /api/subscriptions/sync-plans` - Admin: Sync to Stripe
   - [x] `GET /api/clients/<id>/subscription` - Get client subscription
   - [x] `POST /api/clients/<id>/subscription/checkout` - Create checkout
   - [x] `POST /api/clients/<id>/subscription/create` - Direct create
   - [x] `POST /api/clients/<id>/subscription/cancel` - Cancel
   - [x] `POST /api/clients/<id>/subscription/reactivate` - Reactivate
   - [x] `POST /api/clients/<id>/subscription/change-plan` - Change plan
   - [x] `POST /api/clients/<id>/subscription/billing-portal` - Portal access
   - [x] `POST /api/webhooks/stripe/subscriptions` - Webhook handler

3. **Portal Endpoints**:
   - [x] `GET /portal/api/subscription` - Get current subscription
   - [x] `POST /portal/api/subscription/checkout` - Checkout for client
   - [x] `POST /portal/api/subscription/billing-portal` - Billing portal

4. **Portal UI** (`templates/portal/subscription.html`):
   - [x] Current plan display with status badge
   - [x] Plan cards with features list
   - [x] Checkout flow integration
   - [x] Billing portal access
   - [x] Cancellation modal
   - [x] Responsive design

5. **Navigation**:
   - [x] Added "Subscription" link to portal nav
   - [x] Added "Billing" link to mobile nav

6. **Unit Tests** (`tests/test_subscription_service.py` - 31 tests):
   - [x] Service initialization
   - [x] Plan management
   - [x] Customer management
   - [x] Subscription lifecycle
   - [x] Webhook handlers
   - [x] Edge cases and error handling

#### Files Created/Modified
- `services/subscription_service.py` - NEW (700+ lines)
- `templates/portal/subscription.html` - NEW (400+ lines)
- `tests/test_subscription_service.py` - NEW (31 tests)
- `app.py` - Added 14 subscription endpoints
- `routes/portal.py` - Added subscription route
- `templates/portal/base_portal.html` - Added nav links

---

### Priority 15: Invoice Generator
**Status**: Backlog | **Effort**: Medium

Auto-generate professional client invoices.
- [ ] Create `Invoice` model
- [ ] Create `InvoiceService`
- [ ] PDF invoice template
- [ ] Invoice history in portal
- [ ] Auto-email on generation

---

### Priority 16: Document Viewer
**Status**: Backlog | **Effort**: Low-Medium

In-browser PDF preview (no download needed).
- [ ] PDF.js integration
- [ ] Document preview modal
- [ ] Zoom and page navigation
- [ ] Add to portal documents page

---

### Priority 17: Push Notifications
**Status**: Backlog | **Effort**: Medium

Browser notifications for case updates.
- [ ] Web Push API + VAPID keys
- [ ] Create `PushSubscription` model
- [ ] Create `PushNotificationService`
- [ ] Integrate with workflow triggers

---

### Priority 18: Batch Processing
**Status**: Backlog | **Effort**: Medium

Process multiple clients at once.
- [ ] Multi-select on client list
- [ ] Batch action menu
- [ ] Create `BatchProcessingService`
- [ ] Progress indicator
- [ ] Batch history log

---

### Priority 19: Staff Performance
**Status**: Backlog | **Effort**: Medium

Track cases handled, response times per staff.
- [ ] Cases per staff member
- [ ] Response time tracking
- [ ] Performance dashboard
- [ ] Staff leaderboard

---

### Priority 20: Client Success Metrics
**Status**: Backlog | **Effort**: Medium

Track items deleted, score improvements.
- [ ] Before/after item counts
- [ ] Score improvement tracking
- [ ] Per-client success summary
- [ ] Aggregate report

---

## Future Features (Not Yet Prioritized)

- [x] ~~E-Sign Integration~~ - Already implemented (CROA Signing Service with signature capture)
- [ ] Mobile App (PWA)
- [ ] Auto-Pull Credit Reports
- [ ] Letter Template Builder
- [ ] AI Dispute Writer
- [ ] Payment Plans
- [ ] Voicemail Drops
- [ ] Bureau Response Tracking
- [ ] ROI Calculator

### Pending Infrastructure

- [ ] **Send Certified Mail** - Awaiting SFTP credentials
- [ ] **Twilio A2P 10DLC** - Campaign pending carrier approval

---

## Notes

- **Email**: Gmail SMTP (SendGrid removed)
- **SMS**: Twilio (A2P campaign pending carrier approval)
- **Priorities 1-12**: All complete!
- **Priority 13**: Revenue Dashboard ✅ COMPLETE (2026-01-03)
- **Priority 14**: Stripe Subscriptions ✅ COMPLETE (2026-01-03)
- **Priority 15**: Invoice Generator - Next up
- See `FEATURE_IMPLEMENTATION_CHECKLIST.md` for future feature roadmap

---

*Last updated: 2026-01-03*
