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

### ~~Priority 15: Invoice Generator~~ ✅ COMPLETE

**Completed: 2026-01-03**

Auto-generate professional client invoices.
- [x] Create `Invoice`, `InvoiceItem`, `InvoicePayment` models
- [x] Create `InvoiceService` with full CRUD operations
- [x] PDF invoice template (WeasyPrint)
- [x] Invoice history in client portal
- [x] Auto-email on generation
- [x] Staff invoice management UI
- [x] Partial payments support
- [x] Convenience functions (round, analysis, settlement invoices)

### Files Created/Modified
- `database.py` - Added Invoice, InvoiceItem, InvoicePayment models
- `services/invoice_service.py` - NEW (850+ lines, full service)
- `app.py` - Added 18 invoice API endpoints
- `templates/invoices.html` - Staff management UI
- `templates/portal/invoices.html` - Client portal page
- `routes/portal.py` - Portal invoice endpoints
- `tests/test_invoice_service.py` - NEW (37 tests)

---

### ~~Priority 16: Document Viewer~~ ✅ COMPLETE

**Completed: 2026-01-03**

In-browser PDF preview (no download needed).
- [x] PDF.js integration (CDN)
- [x] Document preview modal with dark overlay
- [x] Zoom and page navigation controls
- [x] Add to portal documents page
- [x] Add to staff documents page
- [x] Image preview support (JPG, PNG, GIF, etc.)
- [x] Keyboard shortcuts (Escape, arrows, +/-)
- [x] Download button in viewer
- [x] Mobile responsive design
- [x] Dark mode support

### Files Created/Modified
- `static/js/document-viewer.js` - NEW (Document viewer component)
- `templates/portal/documents.html` - Added preview buttons + PDF.js
- `templates/documents.html` - Added preview buttons + PDF.js
- `routes/portal.py` - Added preview endpoint

---

### ~~Priority 17: Push Notifications~~ ✅ COMPLETE

**Completed: 2026-01-03**

Browser notifications for case updates.
- [x] Web Push API + VAPID key generation
- [x] Create `PushSubscription` model
- [x] Create `PushNotificationLog` model
- [x] Create `PushNotificationService` (650+ lines)
- [x] Service worker for receiving notifications
- [x] Client-side subscription management
- [x] Integrate with workflow triggers
- [x] Portal profile page notification settings
- [x] Notification preferences (case, messages, documents, deadlines, payments)
- [x] Convenience functions for common notification types

### Files Created/Modified
- `database.py` - Added PushSubscription, PushNotificationLog models
- `services/push_notification_service.py` - NEW (650+ lines)
- `services/workflow_triggers_service.py` - Added send_push action
- `static/sw.js` - NEW (Service worker)
- `static/js/push-notifications.js` - NEW (Client library)
- `templates/portal/profile.html` - Added notification settings UI
- `app.py` - Added 8 push notification API endpoints

### API Endpoints
- GET /api/push/vapid-public-key
- POST /api/push/subscribe
- POST /api/push/unsubscribe
- GET /api/push/subscriptions
- PUT /api/push/subscriptions/<id>/preferences
- POST /api/push/test
- POST /api/push/send-to-client/<id>
- GET /api/push/logs

### Environment Variables Required
```
VAPID_PUBLIC_KEY=<base64-key>
VAPID_PRIVATE_KEY=<base64-key>
VAPID_SUBJECT=mailto:admin@example.com
```

---

### ~~Priority 18: Batch Processing~~ ✅ COMPLETE

**Completed: 2026-01-03**

Process multiple clients at once.
- [x] Multi-select on client list
- [x] Batch action menu (status, round, email, SMS, notes, export, delete)
- [x] Create `BatchProcessingService` (600+ lines)
- [x] Progress indicator modal with real-time updates
- [x] Batch history log page (`/dashboard/batch-jobs`)

#### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `BatchJob` - Job metadata, progress tracking, timing, audit
   - [x] `BatchJobItem` - Individual items with status, before/after state
   - [x] Migration entries for both tables

2. **BatchProcessingService** (`services/batch_processing_service.py` - 600+ lines):
   - [x] 10 action types: update_status, update_dispute_round, send_email, send_sms, assign_staff, add_tag, remove_tag, add_note, export, delete
   - [x] Job CRUD: create_job, get_job, list_jobs, cancel_job
   - [x] Execution: execute_job, retry_failed_items
   - [x] Progress tracking: get_job_progress
   - [x] Stats & history: get_stats, get_job_history

3. **API Endpoints** (`app.py` - 11 endpoints):
   - [x] `GET /api/batch/action-types` - Available actions
   - [x] `GET /api/batch/jobs` - List jobs
   - [x] `POST /api/batch/jobs` - Create and execute job
   - [x] `GET /api/batch/jobs/<id>` - Get job details
   - [x] `GET /api/batch/jobs/<id>/progress` - Real-time progress
   - [x] `POST /api/batch/jobs/<id>/execute` - Execute pending job
   - [x] `POST /api/batch/jobs/<id>/cancel` - Cancel job
   - [x] `POST /api/batch/jobs/<id>/retry` - Retry failed items
   - [x] `GET /api/batch/stats` - Processing statistics
   - [x] `GET /api/batch/history` - Job history
   - [x] `GET /dashboard/batch-jobs` - History page

4. **UI Enhancements** (`templates/clients.html`):
   - [x] Enhanced bulk toolbar with action dropdown
   - [x] Progress modal with bar, success/fail counts
   - [x] Input modals for email, SMS, notes
   - [x] CSV export functionality
   - [x] Link to batch jobs history

5. **Batch Jobs History Page** (`templates/batch_jobs.html`):
   - [x] Stats cards (total, completed, items processed, success rate)
   - [x] Jobs table with status, progress, actions
   - [x] Retry failed items button
   - [x] Auto-refresh every 30 seconds

#### Files Created/Modified
- `database.py` - Added BatchJob, BatchJobItem models + migrations
- `services/batch_processing_service.py` - NEW (600+ lines)
- `app.py` - Added 11 batch processing endpoints
- `templates/clients.html` - Enhanced bulk toolbar + modals
- `templates/batch_jobs.html` - NEW (history page)

---

### ~~Priority 19: Staff Performance~~ ✅ COMPLETE

**Completed: 2026-01-03**

Track cases handled, response times per staff.
- [x] Cases per staff member
- [x] Response time tracking
- [x] Performance dashboard
- [x] Staff leaderboard

#### What Was Implemented

1. **Database Model** (`database.py`):
   - [x] `StaffActivity` - Track all staff activities
   - [x] Fields: activity_type, description, metadata, response_time_minutes
   - [x] Quality tracking: quality_score, was_escalated, required_revision
   - [x] Timestamps: request_received_at, response_completed_at
   - [x] Migration entries

2. **StaffPerformanceService** (`services/staff_performance_service.py` - 600+ lines):
   - [x] 11 activity types with point values
   - [x] `log_activity()` - Log staff activities with response time
   - [x] `get_staff_metrics()` - Per-staff metrics (points, activities, avg response)
   - [x] `get_team_metrics()` - Team overview and totals
   - [x] `get_leaderboard()` - Rankings by points, activities, response_time, cases
   - [x] `get_performance_trend()` - Activity trends over time
   - [x] `get_recent_activities()` - Activity feed
   - [x] `get_dashboard_summary()` - All metrics for dashboard

3. **Activity Types with Points**:
   - case_assigned (5), case_completed (20), document_reviewed (3)
   - letter_sent (10), response_processed (8), message_sent (2)
   - call_completed (5), note_added (1), status_changed (2)
   - analysis_reviewed (15), dispute_filed (12)

4. **API Endpoints** (`app.py` - 10 endpoints):
   - [x] `GET /api/staff-performance/activity-types` - Available types
   - [x] `POST /api/staff-performance/log` - Log activity
   - [x] `GET /api/staff-performance/dashboard` - Dashboard summary
   - [x] `GET /api/staff-performance/leaderboard` - Staff rankings
   - [x] `GET /api/staff-performance/staff/<id>/metrics` - Individual metrics
   - [x] `GET /api/staff-performance/staff/<id>/activities` - Activity history
   - [x] `GET /api/staff-performance/team/metrics` - Team metrics
   - [x] `GET /api/staff-performance/trend` - Performance trend
   - [x] `GET /api/staff-performance/recent` - Recent activities
   - [x] `GET /dashboard/staff-performance` - Dashboard page

5. **Staff Performance Dashboard** (`templates/staff_performance.html`):
   - [x] Stats cards: Points Today, Activities Today, Active Staff, Avg Response
   - [x] Performance trend chart (Chart.js line chart)
   - [x] Leaderboard with ranking badges (gold, silver, bronze)
   - [x] Team overview table with all staff
   - [x] Recent activity feed
   - [x] Period selector (day/week/month/quarter/year)
   - [x] Auto-refresh every 60 seconds

6. **Sidebar Navigation**:
   - [x] Added "Staff Performance" link under Analytics section

#### Files Created/Modified
- `database.py` - Added StaffActivity model + migrations
- `services/staff_performance_service.py` - NEW (600+ lines)
- `app.py` - Added 10 staff performance API endpoints
- `templates/staff_performance.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

### ~~Priority 20: Client Success Metrics~~ ✅ COMPLETE

**Completed: 2026-01-03**

Track items deleted, score improvements.
- [x] Before/after item counts
- [x] Score improvement tracking
- [x] Per-client success summary
- [x] Aggregate report

#### What Was Implemented

1. **Database Model** (`database.py`):
   - [x] `ClientSuccessMetric` - Track success metrics per client
   - [x] Initial vs current state tracking (negatives, scores by bureau)
   - [x] Items breakdown: deleted, verified, updated, in_progress
   - [x] Bureau-specific deletion counts
   - [x] Score changes by bureau
   - [x] Success metrics: deletion_rate, days_in_program, estimated_value
   - [x] Migration entries

2. **ClientSuccessService** (`services/client_success_service.py` - 600+ lines):
   - [x] `calculate_client_metrics()` - Calculate metrics from data
   - [x] `create_snapshot()` - Create periodic snapshots
   - [x] `get_client_summary()` - Per-client success summary with grade
   - [x] `get_aggregate_report()` - Aggregate across all clients
   - [x] `get_top_performers()` - Rankings by deletion rate, score, etc.
   - [x] `get_success_trend()` - Trend over time
   - [x] `get_bureau_breakdown()` - Per-bureau statistics
   - [x] `get_dashboard_summary()` - All metrics for dashboard
   - [x] `update_all_clients()` - Batch update all client metrics
   - [x] `export_success_data()` - CSV export

3. **Success Grading System**:
   - A+ to F grades based on deletion rate + score improvement + items deleted
   - Grade distribution tracking

4. **API Endpoints** (`app.py` - 11 endpoints):
   - [x] `GET /api/client-success/dashboard` - Dashboard summary
   - [x] `GET /api/client-success/aggregate` - Aggregate report
   - [x] `GET /api/client-success/client/<id>` - Client summary
   - [x] `POST /api/client-success/client/<id>/snapshot` - Create snapshot
   - [x] `GET /api/client-success/client/<id>/history` - Snapshot history
   - [x] `GET /api/client-success/top-performers` - Top performers
   - [x] `GET /api/client-success/trend` - Success trend
   - [x] `GET /api/client-success/bureau-breakdown` - Bureau stats
   - [x] `POST /api/client-success/update-all` - Update all clients
   - [x] `GET /api/client-success/export` - CSV export
   - [x] `GET /dashboard/client-success` - Dashboard page

5. **Client Success Dashboard** (`templates/client_success.html`):
   - [x] Stats cards: Total Clients, Completed Cases, Items Deleted, etc.
   - [x] Success trend chart (Chart.js dual-axis line chart)
   - [x] Top performers by deletion rate and score improvement
   - [x] Bureau breakdown (Equifax, Experian, TransUnion)
   - [x] Success grade distribution
   - [x] Period selector (week/month/quarter/year)
   - [x] Export CSV button
   - [x] Update all metrics button
   - [x] Auto-refresh every 60 seconds

6. **Sidebar Navigation**:
   - [x] Added "Client Success" link in Analytics section
   - [x] Added "Staff Performance" link in Analytics section

#### Files Created/Modified
- `database.py` - Added ClientSuccessMetric model + migrations
- `services/client_success_service.py` - NEW (600+ lines)
- `app.py` - Added 11 client success API endpoints
- `templates/client_success.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar links

---

## ~~Priority 21: AI Dispute Writer~~ ✅ COMPLETE

**Completed: 2026-01-03**

Generate customized FCRA dispute letters using AI based on credit reports and CRA responses.
- [x] Credit report analysis integration
- [x] CRA response context awareness
- [x] Round-specific strategies (R1-R4)
- [x] Multi-bureau letter generation

#### What Was Implemented

1. **AIDisputeWriterService** (`services/ai_dispute_writer_service.py` - 600+ lines):
   - [x] `get_client_context()` - Gather violations, items, CRA responses
   - [x] `generate_letters()` - AI-powered letter generation for all bureaus
   - [x] `generate_quick_letter()` - Quick single letter generation
   - [x] `regenerate_with_feedback()` - Incorporate user feedback
   - [x] `suggest_next_action()` - AI recommendation for next steps
   - [x] `save_letter()` - Save generated letters to database
   - [x] `get_dashboard_data()` - Dashboard summary

2. **Round Strategies**:
   - Round 1: Initial dispute with RLPP bundling
   - Round 2: Cushman-style MOV demands
   - Round 3: Regulatory escalation (CFPB, state AG)
   - Round 4: Pre-litigation demands

3. **Tone Options**:
   - Professional: Firm but business-like
   - Aggressive: Emphasize legal consequences
   - Formal: Legal document style

4. **Integration with Existing Systems**:
   - Uses PromptLoader for round-specific FCRA prompts
   - Leverages knowledge folder (25+ prompt files)
   - Works with existing Violation and DisputeItem models
   - Considers CRA responses from previous rounds

5. **API Endpoints** (`app.py` - 10 endpoints):
   - [x] `GET /api/ai-dispute-writer/dashboard` - Dashboard data
   - [x] `GET /api/ai-dispute-writer/rounds` - Round info
   - [x] `GET /api/ai-dispute-writer/client/<id>/context` - Client context
   - [x] `GET /api/ai-dispute-writer/client/<id>/suggest` - AI suggestion
   - [x] `POST /api/ai-dispute-writer/generate` - Generate letters
   - [x] `POST /api/ai-dispute-writer/generate-quick` - Quick letter
   - [x] `POST /api/ai-dispute-writer/regenerate` - Regenerate with feedback
   - [x] `POST /api/ai-dispute-writer/save` - Save letter
   - [x] `GET /api/ai-dispute-writer/client/<id>/letters` - Saved letters
   - [x] `GET /dashboard/ai-dispute-writer` - Dashboard page

6. **AI Dispute Writer Dashboard** (`templates/ai_dispute_writer.html`):
   - [x] Client search and selection
   - [x] Dispute item selection with checkboxes
   - [x] Round selector (R1-R4) with descriptions
   - [x] Tone selector (Professional/Aggressive/Formal)
   - [x] Bureau checkboxes (Equifax, Experian, TransUnion)
   - [x] Custom instructions textarea
   - [x] Letter preview with bureau tabs
   - [x] Copy, Save, and Regenerate with Feedback actions
   - [x] AI suggestion banner
   - [x] Loading overlay during generation

#### Files Created/Modified
- `services/ai_dispute_writer_service.py` - NEW (600+ lines)
- `app.py` - Added 10 AI dispute writer API endpoints
- `templates/ai_dispute_writer.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

## ~~Priority 22: ROI Calculator~~ ✅ COMPLETE

**Completed: 2026-01-03**

Calculate potential settlement and recovery values based on violations, items, and historical data.
- [x] Violation-based statutory damages calculation
- [x] Actual damages tracking
- [x] Settlement estimates (conservative, moderate, aggressive, most likely)
- [x] Litigation potential scoring

#### What Was Implemented

1. **Database Model** (`database.py`):
   - [x] `ROICalculation` - Store calculation results per client
   - [x] Violation counts by type (FCRA, FDCPA, TCPA, FCBA)
   - [x] Statutory and actual damages tracking
   - [x] Settlement estimate ranges
   - [x] Litigation score and recommendation
   - [x] Score improvement and credit value estimates
   - [x] Migration entries

2. **ROICalculatorService** (`services/roi_calculator_service.py` - 750+ lines):
   - [x] `calculate_roi()` - Full client ROI calculation
   - [x] `quick_estimate()` - Quick estimate without client data
   - [x] `get_client_calculations()` - Calculation history
   - [x] `get_dashboard_summary()` - Dashboard stats
   - [x] `get_aggregate_stats()` - Period-based statistics
   - [x] `export_calculations()` - CSV export
   - [x] Statutory damages: $100-$1000 per willful FCRA violation
   - [x] Punitive damages multiplier (2.5x for willful)
   - [x] Historical deletion rates by item type
   - [x] Score improvement estimates
   - [x] Credit value improvement calculation

3. **API Endpoints** (`app.py` - 8 endpoints):
   - [x] `GET /api/roi-calculator/dashboard` - Dashboard summary
   - [x] `POST /api/roi-calculator/calculate/<id>` - Calculate client ROI
   - [x] `POST /api/roi-calculator/quick-estimate` - Quick estimate
   - [x] `GET /api/roi-calculator/client/<id>` - Client history
   - [x] `GET /api/roi-calculator/calculation/<id>` - Get specific calculation
   - [x] `GET /api/roi-calculator/stats` - Aggregate statistics
   - [x] `GET /api/roi-calculator/export` - CSV export
   - [x] `GET /dashboard/roi-calculator` - Dashboard page

4. **ROI Calculator Dashboard** (`templates/roi_calculator.html`):
   - [x] Stats cards: Total Calculations, Avg Estimate, Litigation Recommended, Total Value
   - [x] Client selector with optional actual damages inputs
   - [x] Estimate results (Conservative, Moderate, Aggressive, Most Likely)
   - [x] Violation badges by type
   - [x] Litigation potential score bar
   - [x] Recent calculations table
   - [x] Quick Estimate modal for ad-hoc calculations
   - [x] Calculation details modal
   - [x] CSV export
   - [x] Period filter (week/month/quarter/all)

5. **Calculation Factors**:
   - FCRA statutory: $100-$1,000 per willful violation
   - Punitive damages: Up to 2.5x statutory for willful
   - Attorney fees: Fee shifting estimate
   - Historical deletion rates: 30-90% by item type
   - Score improvement: 3-15 points per item type
   - Credit value: $250 per score point (lifetime savings)

6. **Sidebar Navigation**:
   - [x] Added "ROI Calculator" link in Analytics section

#### Files Created/Modified
- `database.py` - Added ROICalculation model + migrations
- `services/roi_calculator_service.py` - NEW (750+ lines)
- `app.py` - Added 8 ROI calculator API endpoints
- `templates/roi_calculator.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

## ~~Priority 23: Payment Plans~~ ✅ COMPLETE

**Completed: 2026-01-03**

Installment payment plans for clients with flexible scheduling and tracking.
- [x] Create `PaymentPlan`, `PaymentPlanInstallment`, `PaymentPlanPayment` models
- [x] Create `PaymentPlanService` with full plan management
- [x] Staff management dashboard
- [x] Client portal view
- [x] Automatic installment generation
- [x] Late fee tracking

#### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `PaymentPlan` - Plan settings, totals, status, late fees
   - [x] `PaymentPlanInstallment` - Individual installments with due dates
   - [x] `PaymentPlanPayment` - Payment records with method and notes
   - [x] Migration entries for all 3 tables

2. **PaymentPlanService** (`services/payment_plan_service.py` - 600+ lines):
   - [x] `create_plan()` - Create plan with auto-generated installments
   - [x] `get_plan()` - Get plan with installments and payments
   - [x] `get_client_plans()` - Get all plans for a client
   - [x] `record_payment()` - Record payment and auto-apply to oldest unpaid
   - [x] `pause_plan()` - Pause active plan
   - [x] `resume_plan()` - Resume paused plan
   - [x] `cancel_plan()` - Cancel plan with reason
   - [x] `mark_defaulted()` - Mark plan as defaulted
   - [x] `check_late_payments()` - Apply late fees (for scheduler)
   - [x] `get_due_soon()` - Get installments due within N days
   - [x] `get_overdue()` - Get overdue installments
   - [x] `get_dashboard_summary()` - Dashboard statistics
   - [x] `export_plans()` - CSV export

3. **API Endpoints** (`app.py` - 17 endpoints):
   - [x] `GET /api/payment-plans` - List plans (with filtering)
   - [x] `POST /api/payment-plans` - Create new plan
   - [x] `GET /api/payment-plans/<id>` - Get plan details
   - [x] `PUT /api/payment-plans/<id>` - Update plan
   - [x] `POST /api/payment-plans/<id>/payment` - Record payment
   - [x] `POST /api/payment-plans/<id>/pause` - Pause plan
   - [x] `POST /api/payment-plans/<id>/resume` - Resume plan
   - [x] `POST /api/payment-plans/<id>/cancel` - Cancel plan
   - [x] `POST /api/payment-plans/<id>/default` - Mark as defaulted
   - [x] `GET /api/payment-plans/dashboard` - Dashboard summary
   - [x] `GET /api/payment-plans/due-soon` - Due soon list
   - [x] `GET /api/payment-plans/overdue` - Overdue list
   - [x] `GET /api/payment-plans/export` - CSV export
   - [x] `GET /dashboard/payment-plans` - Dashboard page

4. **Portal API Endpoints** (`routes/portal.py` - 3 endpoints):
   - [x] `GET /portal/payment-plans` - Portal page
   - [x] `GET /portal/api/payment-plans` - Client's plans
   - [x] `GET /portal/api/payment-plans/<id>` - Plan details

5. **Staff Management UI** (`templates/payment_plans.html`):
   - [x] Stats cards: Active Plans, Collected, Pending, Due Soon, Overdue
   - [x] Create plan modal with installment preview
   - [x] Plans table with status tabs (All, Active, Paused, Completed, Cancelled)
   - [x] Record payment modal
   - [x] Plan details modal with installment schedule
   - [x] Pause/Resume/Cancel actions
   - [x] Due soon and overdue sidebars
   - [x] Quick stats panel
   - [x] CSV export

6. **Client Portal UI** (`templates/portal/payment_plans.html`):
   - [x] Summary cards: Active Plans, Total Paid, Remaining Balance
   - [x] Upcoming payment alert (with urgency badges)
   - [x] Payment plans list with progress bars
   - [x] Plan details modal with installment schedule
   - [x] Payment history display

7. **Navigation Updates**:
   - [x] Staff sidebar: "Payment Plans" link in Analytics section
   - [x] Client portal: "Plans" link in navigation

8. **Features**:
   - [x] Flexible frequency: Weekly, Bi-Weekly, Monthly
   - [x] Plan types: Custom, Dispute Round, Prepay, Settlement
   - [x] Down payment support
   - [x] Late fee configuration with grace period
   - [x] Automatic installment calculation
   - [x] Auto-apply payments to oldest unpaid
   - [x] Plan status: Active, Paused, Completed, Cancelled, Defaulted
   - [x] Payment methods: Manual, Stripe, Check, Cash, Bank Transfer

#### Files Created/Modified
- `database.py` - Added 3 payment plan models + migrations
- `services/payment_plan_service.py` - NEW (600+ lines)
- `app.py` - Added 17 payment plan API endpoints
- `templates/payment_plans.html` - NEW (staff dashboard)
- `templates/portal/payment_plans.html` - NEW (client portal)
- `routes/portal.py` - Added 3 portal endpoints
- `templates/includes/dashboard_sidebar.html` - Added sidebar link
- `templates/portal/base_portal.html` - Added portal nav link

---

## ~~Priority 24: Bureau Response Tracking~~ ✅ COMPLETE

**Completed: 2026-01-03**

### What Was Implemented

Track dispute letters sent to credit bureaus and monitor their response status against FCRA deadlines.

1. **Database Model** (`database.py`):
   - [x] `BureauDisputeTracking` model with comprehensive tracking fields
   - [x] Client and case relationships
   - [x] Sent date, expected response date, actual response date
   - [x] Bureau tracking (Equifax, Experian, TransUnion)
   - [x] Response types: deleted, updated, verified, mixed, frivolous
   - [x] Status tracking: sent, delivered, awaiting_response, overdue, closed
   - [x] Item counts: disputed, deleted, updated, verified
   - [x] Overdue detection and alert tracking
   - [x] Follow-up scheduling and completion

2. **BureauResponseService** (`services/bureau_response_service.py` - 864 lines):
   - [x] `track_dispute_sent()` - Track new dispute with auto-calculated FCRA deadline
   - [x] `confirm_delivery()` - Confirm mail delivery and recalculate deadline
   - [x] `record_response()` - Record bureau response with item counts
   - [x] `check_overdue_disputes()` - Batch check and mark overdue disputes
   - [x] `get_pending()` - Get all pending disputes awaiting response
   - [x] `get_due_soon()` - Get disputes due within N days
   - [x] `get_overdue()` - Get overdue disputes
   - [x] `get_dashboard_summary()` - Stats for dashboard
   - [x] `get_bureau_breakdown()` - Stats by bureau (Equifax/Experian/TransUnion)
   - [x] `get_response_type_breakdown()` - Count responses by type
   - [x] `schedule_follow_up()` - Schedule follow-up actions
   - [x] `export_data()` - Export tracking data for CSV/reporting

3. **API Endpoints** (16 endpoints in `app.py`):
   - [x] `GET /api/bureau-tracking/dashboard` - Dashboard summary stats
   - [x] `GET /api/bureau-tracking` - List disputes with filters
   - [x] `POST /api/bureau-tracking` - Track new dispute
   - [x] `GET /api/bureau-tracking/<id>` - Get single dispute
   - [x] `POST /api/bureau-tracking/<id>/delivery` - Confirm delivery
   - [x] `POST /api/bureau-tracking/<id>/response` - Record response
   - [x] `POST /api/bureau-tracking/<id>/link-response` - Link CRA response
   - [x] `POST /api/bureau-tracking/<id>/close` - Close dispute
   - [x] `POST /api/bureau-tracking/<id>/follow-up` - Schedule follow-up
   - [x] `POST /api/bureau-tracking/check-overdue` - Batch overdue check
   - [x] `GET /api/bureau-tracking/due-soon` - Disputes due soon
   - [x] `GET /api/bureau-tracking/overdue` - Overdue disputes
   - [x] `GET /api/bureau-tracking/bureau-breakdown` - Stats by bureau
   - [x] `GET /api/bureau-tracking/export` - Export CSV
   - [x] `GET /api/clients/<id>/bureau-tracking` - Client disputes

4. **Dashboard UI** (`templates/bureau_tracking.html`):
   - [x] Stats cards: Pending, Overdue, Due Soon, Received, Avg Response Time
   - [x] Bureau breakdown cards (Equifax, Experian, TransUnion)
   - [x] Pending disputes table with filters (bureau, status, round)
   - [x] Search by client name
   - [x] Track new dispute modal (multi-bureau selection)
   - [x] Record response modal with item counts
   - [x] Due soon sidebar panel
   - [x] Overdue sidebar panel
   - [x] Response type breakdown stats
   - [x] Export to CSV functionality
   - [x] Check overdue button

5. **Sidebar Navigation**:
   - [x] Added "Bureau Tracking" link in Case Workflow section

### FCRA Compliance Features

- **30-day deadline** for standard disputes (auto-calculated from sent date)
- **45-day deadline** for complex disputes (marked at creation)
- **Deadline recalculation** when delivery is confirmed
- **Overdue detection** with batch checking
- **Response type tracking** for compliance reporting

### Files Created/Modified
- `database.py` - Added `BureauDisputeTracking` model + migrations
- `services/bureau_response_service.py` - NEW (864 lines)
- `app.py` - Added 16 bureau tracking API endpoints + dashboard route
- `templates/bureau_tracking.html` - NEW (dashboard UI)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

## ~~Priority 25: Auto-Pull Credit Reports~~ ✅ COMPLETE

**Completed: 2026-01-03**

Automatically pull credit reports from credit monitoring services.

### What Was Implemented

1. **Database Model** (`database.py`):
   - [x] `CreditPullLog` - Track each pull attempt with status and results
   - [x] Pull type tracking (scheduled, manual, on_demand)
   - [x] Status tracking (pending, in_progress, success, failed, timeout)
   - [x] Report path and item counts
   - [x] Duration and error tracking
   - [x] Migration entries

2. **AutoPullService** (`services/auto_pull_service.py` - 600+ lines):
   - [x] Supported services: IdentityIQ, MyScoreIQ, SmartCredit, Privacy Guard, Credit Karma
   - [x] `get_credentials()` - List client credentials
   - [x] `add_credential()` - Add monitoring account (encrypted)
   - [x] `update_credential()` - Update credentials
   - [x] `delete_credential()` - Remove credential
   - [x] `execute_pull()` - Pull credit report from service
   - [x] `get_due_pulls()` - Get scheduled pulls that are due
   - [x] `run_scheduled_pulls()` - Run all due scheduled pulls
   - [x] `validate_credentials()` - Test credential validity
   - [x] `get_pull_stats()` - Dashboard statistics
   - [x] `get_pull_logs()` - Pull history with filtering

3. **API Endpoints** (`app.py` - 14 endpoints):
   - [x] `GET /api/auto-pull/stats` - Dashboard statistics
   - [x] `GET /api/auto-pull/services` - Supported services
   - [x] `GET /api/auto-pull/credentials` - List credentials
   - [x] `POST /api/auto-pull/credentials` - Add credential
   - [x] `PUT /api/auto-pull/credentials/<id>` - Update credential
   - [x] `DELETE /api/auto-pull/credentials/<id>` - Delete credential
   - [x] `POST /api/auto-pull/pull/<id>` - Pull for credential
   - [x] `POST /api/auto-pull/pull-client/<id>` - Pull for client
   - [x] `POST /api/auto-pull/run-scheduled` - Run scheduled pulls
   - [x] `GET /api/auto-pull/due` - Get due pulls
   - [x] `GET /api/auto-pull/logs` - Pull logs
   - [x] `POST /api/auto-pull/validate/<id>` - Validate credentials
   - [x] `GET /dashboard/auto-pull` - Dashboard page
   - [x] `GET/POST /api/cron/auto-pull` - Cron endpoint

4. **Dashboard UI** (`templates/auto_pull.html`):
   - [x] Stats cards: Credentials, Pulls Today, Success Rate, Due for Pull, Failed
   - [x] Service breakdown cards (per service)
   - [x] Credentials table with filters and actions
   - [x] Pull logs tab with status tracking
   - [x] Add credential modal
   - [x] Run scheduled pulls button
   - [x] Due for pull sidebar
   - [x] Supported services list
   - [x] Quick actions panel

5. **Sidebar Navigation**:
   - [x] Added "Auto-Pull" link in Processing section

6. **Features**:
   - [x] Pull frequencies: Manual, Daily, Weekly, Bi-Weekly, Monthly, With Letter Send
   - [x] Encrypted credential storage (AES-256)
   - [x] Automatic pull scheduling
   - [x] Pull logging with detailed status
   - [x] Credential validation
   - [x] Cron endpoint for automated scheduled pulls

### Files Created/Modified
- `database.py` - Added CreditPullLog model + migrations
- `services/auto_pull_service.py` - NEW (600+ lines)
- `app.py` - Added 14 auto-pull API endpoints
- `templates/auto_pull.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

## ~~Priority 26: Letter Template Builder~~ ✅ COMPLETE

**Completed: 2026-01-03**

Create and manage customizable dispute letter templates.

### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `LetterTemplate` - Store letter templates with categories, variables, versioning
   - [x] `LetterTemplateVersion` - Track template version history
   - [x] `GeneratedLetter` - Track letters generated from templates
   - [x] Migration entries for all tables

2. **LetterTemplateService** (`services/letter_template_service.py` - 900+ lines):
   - [x] Template CRUD: create, update, delete, get, list, duplicate
   - [x] Variable system with 20+ common placeholders
   - [x] Template categories: Initial Dispute, MOV Demand, Escalation, Follow-Up, Pre-Litigation, Furnisher, Collector, General
   - [x] Version history: create version, get versions, restore version
   - [x] Template rendering with variable substitution
   - [x] Client variable population from database
   - [x] Letter generation from templates
   - [x] Dashboard statistics
   - [x] Default template seeding (6 built-in templates)

3. **API Endpoints** (`app.py` - 20 endpoints):
   - [x] `GET /api/letter-templates` - List templates with filtering
   - [x] `POST /api/letter-templates` - Create template
   - [x] `GET /api/letter-templates/<id>` - Get template
   - [x] `PUT /api/letter-templates/<id>` - Update template
   - [x] `DELETE /api/letter-templates/<id>` - Delete template
   - [x] `POST /api/letter-templates/<id>/duplicate` - Duplicate template
   - [x] `GET /api/letter-templates/<id>/versions` - Get version history
   - [x] `POST /api/letter-templates/<id>/restore/<version_id>` - Restore version
   - [x] `POST /api/letter-templates/<id>/render` - Render with variables
   - [x] `POST /api/letter-templates/generate` - Generate letter for client
   - [x] `GET /api/letter-templates/generated` - List generated letters
   - [x] `GET /api/letter-templates/generated/<id>` - Get generated letter
   - [x] `PUT /api/letter-templates/generated/<id>/status` - Update letter status
   - [x] `GET /api/letter-templates/dashboard` - Dashboard stats
   - [x] `GET /api/letter-templates/categories` - List categories
   - [x] `GET /api/letter-templates/target-types` - List target types
   - [x] `GET /api/letter-templates/variables` - Common variables
   - [x] `GET /api/letter-templates/client-variables/<id>` - Client variable values
   - [x] `POST /api/letter-templates/seed` - Seed default templates
   - [x] `GET /dashboard/letter-templates` - Dashboard page

4. **Dashboard UI** (`templates/letter_templates.html`):
   - [x] Stats cards: Total, Active, Generated, Sent
   - [x] Template grid with category/round/target filtering
   - [x] Search functionality
   - [x] Create/Edit modal with tabbed interface (Details, Content, Preview)
   - [x] Variable insertion helper panel
   - [x] Live preview with sample data
   - [x] Generate letter modal
   - [x] View template modal with duplicate/edit actions
   - [x] Category sidebar with counts
   - [x] Most used templates list
   - [x] Common variables reference

5. **Sidebar Navigation**:
   - [x] Added "Letter Templates" link in Legal Tools section

6. **Default Templates** (6 built-in):
   - Initial Dispute - FCRA Section 611
   - Method of Verification Demand
   - CFPB Complaint Draft
   - Pre-Litigation Demand
   - Debt Validation Letter
   - Furnisher Direct Dispute

### Files Created/Modified
- `database.py` - Added 3 models + migrations
- `services/letter_template_service.py` - NEW (900+ lines)
- `app.py` - Added 20 API endpoints
- `templates/letter_templates.html` - NEW (dashboard page)
- `templates/includes/dashboard_sidebar.html` - Added sidebar link

---

## ~~Priority 27: Mobile App (PWA)~~ ✅ COMPLETE

**Completed: 2026-01-03**

Progressive Web App for installable mobile experience with offline support.

### What Was Implemented

1. **Web App Manifest** (`static/manifest.json`):
   - [x] App name: "Brightpath Ascend Group - Client Portal"
   - [x] Standalone display mode
   - [x] Theme colors for light/dark modes
   - [x] 8 icon sizes (72px to 512px)
   - [x] App shortcuts (Dashboard, Documents, Messages)
   - [x] Screenshots for install UI

2. **PWA Icons** (`static/images/pwa/`):
   - [x] Generated icons: 72, 96, 128, 144, 152, 192, 384, 512px
   - [x] Apple touch icon (180px)
   - [x] Shortcut icons for quick actions
   - [x] Notification and badge icons

3. **Enhanced Service Worker** (`static/sw.js`):
   - [x] Multiple caching strategies:
     - Cache First for static assets
     - Network First for API calls
     - Stale While Revalidate for pages
   - [x] Offline fallback page
   - [x] Push notification handling
   - [x] Background sync support
   - [x] Cache versioning and cleanup

4. **PWA JavaScript** (`static/js/pwa.js`):
   - [x] Service worker registration
   - [x] Install prompt capture and custom UI
   - [x] "Add to Home Screen" banner
   - [x] Update notification toast
   - [x] Online/offline status indicators
   - [x] 24-hour dismissal cooldown

5. **Portal Template Updates** (`templates/portal/base_portal.html`):
   - [x] PWA meta tags (theme-color, apple-mobile-web-app-*)
   - [x] Manifest link
   - [x] Apple touch icon links
   - [x] MS tile configuration

6. **Offline Page** (`templates/portal/offline.html`):
   - [x] Branded offline experience
   - [x] Auto-retry connection
   - [x] Tips for offline usage
   - [x] Light/dark mode support

### Features

- **Installable**: Users can add to home screen on iOS, Android, and desktop
- **Offline Support**: Previously viewed pages cached for offline access
- **Push Notifications**: Receive case updates even when app is closed
- **Fast Loading**: Static assets cached for instant load
- **Native Feel**: Standalone mode hides browser UI

### Files Created/Modified
- `static/manifest.json` - NEW (Web App Manifest)
- `static/images/pwa/*` - NEW (14 icon files)
- `static/sw.js` - Enhanced (caching strategies)
- `static/js/pwa.js` - NEW (install prompt, updates)
- `templates/portal/base_portal.html` - Added PWA meta tags
- `templates/portal/offline.html` - NEW (offline page)
- `routes/portal.py` - Added offline route

---

## ~~Priority 28: Voicemail Drops~~ ✅ COMPLETE

**Completed: 2026-01-03**

Automated ringless voicemail drops for client outreach and communication.

### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `VoicemailRecording` - Pre-recorded voicemail audio files
   - [x] `VoicemailDrop` - Individual voicemail drop tracking
   - [x] `VoicemailCampaign` - Batch voicemail campaigns

2. **VoicemailDropService** (`services/voicemail_drop_service.py`):
   - [x] Recording management (CRUD)
   - [x] Multiple provider support (Slybroadcast, Drop Cowboy, Twilio)
   - [x] Phone number validation and formatting
   - [x] Scheduled drops
   - [x] Campaign management (create, start, pause, cancel)
   - [x] Drop retry and cancellation
   - [x] Statistics and reporting

3. **API Endpoints** (~20 endpoints):
   - [x] Recordings: GET/POST/PUT/DELETE `/api/voicemail/recordings`
   - [x] Drops: GET/POST `/api/voicemail/drops`, retry, cancel
   - [x] Campaigns: GET/POST, add targets, start, pause, cancel
   - [x] Stats: GET `/api/voicemail/stats`
   - [x] Client history: GET `/api/voicemail/clients/<id>/history`

4. **Dashboard UI** (`templates/voicemail_drops.html`):
   - [x] Recording library with audio preview
   - [x] Category filtering (welcome, reminder, update, follow_up, payment, custom)
   - [x] Recent drops table with status badges
   - [x] Campaign management interface
   - [x] Quick send modal
   - [x] File upload with drag-and-drop
   - [x] Statistics cards

5. **Workflow Triggers Integration**:
   - [x] New action type: `send_voicemail`
   - [x] Can trigger voicemail drops from any workflow event
   - [x] Parameters: `recording_id`, `recording_name`

### Features

- **Multiple Providers**: Slybroadcast, Drop Cowboy, Twilio (with AMD)
- **Campaign Management**: Create, schedule, and manage batch drops
- **Recording Library**: Upload, categorize, and preview audio
- **Workflow Integration**: Trigger drops from automated workflows
- **Cost Tracking**: Per-drop cost tracking and reporting
- **Scheduling**: Schedule drops for future delivery

### Files Created/Modified
- `database.py` - Added 3 new models
- `services/voicemail_drop_service.py` - NEW (~650 lines)
- `app.py` - Added ~20 API endpoints
- `templates/voicemail_drops.html` - NEW (dashboard)
- `templates/includes/dashboard_sidebar.html` - Added nav link
- `services/workflow_triggers_service.py` - Added send_voicemail action
- `tests/test_voicemail_drop_service.py` - NEW (34 tests)

---

## ~~Priority 29: AI Chat Support~~ ✅ COMPLETE

**Completed: 2026-01-18**

AI-powered chat support for client portal.
- [x] Chat widget in portal
- [x] AI context awareness (client data, case status)
- [x] Conversation history
- [x] Staff dashboard for chat monitoring

---

## ~~Priority 30: AI Chat Support (Staff Dashboard)~~ ✅ COMPLETE

**Completed: 2026-01-18**

Staff-side chat management and AI training.

---

## ~~Priority 31: Credit Score Simulator~~ ✅ COMPLETE

**Completed: 2026-01-19**

What-if score projections for client portal.
- [x] ScoreScenario database model
- [x] Score simulation service with item-level impact
- [x] Save/load scenarios
- [x] Goal recommendations
- [x] Interactive portal UI

---

## ~~Priority 32: Unified Inbox~~ ✅ COMPLETE

**Completed: 2026-01-19**

### What Was Implemented

1. **UnifiedInboxService** (`services/unified_inbox_service.py` - ~800 lines):
   - [x] Aggregates messages from 5 channels (Email, SMS, WhatsApp, Portal, AI Chat)
   - [x] UnifiedMessage normalization pattern
   - [x] Channel filtering (All, Email, SMS, Portal, Calls)
   - [x] Search and conversation threading
   - [x] Quick reply support
   - [x] Mark as read/unread
   - [x] Assign to staff

2. **API Endpoints** (11 endpoints):
   - [x] `GET /api/unified-inbox/messages` - List messages with filters
   - [x] `GET /api/unified-inbox/message/<id>` - Get single message
   - [x] `POST /api/unified-inbox/message/<id>/read` - Mark as read
   - [x] `POST /api/unified-inbox/message/<id>/reply` - Quick reply
   - [x] `GET /api/unified-inbox/stats` - Unread counts by channel
   - Plus 6 more endpoints

3. **Dashboard UI** (`templates/unified_inbox.html`):
   - [x] Channel tabs with unread badges
   - [x] Message list with search
   - [x] Conversation thread view
   - [x] Quick reply modal
   - [x] Assign to staff dropdown

### Files Created/Modified
- `services/unified_inbox_service.py` (NEW) - ~800 lines
- `templates/unified_inbox.html` (NEW) - Dashboard UI
- `app.py` - Added 11 API endpoints
- `tests/test_unified_inbox_service.py` (NEW) - 30 tests
- `cypress/e2e/unified_inbox_exhaustive.cy.js` (NEW) - E2E tests

### Test Status
- 30/30 unit tests passing

---

## ~~Priority 33: Calendar Sync (Google/Outlook)~~ ✅ COMPLETE

**Completed: 2026-01-19**

### What Was Implemented

1. **Database Models** (`database.py`):
   - [x] `CalendarIntegration` - Staff calendar connections (Google/Outlook)
   - [x] `CalendarEvent` - Synced events with external event IDs
   - [x] Migration entries for both tables

2. **CalendarSyncService** (`services/calendar_sync_service.py` - ~700 lines):
   - [x] Google Calendar OAuth flow (auth URL, token exchange, refresh)
   - [x] Outlook Calendar OAuth flow (Microsoft Graph API)
   - [x] List available calendars
   - [x] Free/busy checking from connected calendars
   - [x] Sync bookings to calendar (create events)
   - [x] Delete calendar events on booking cancellation
   - [x] Integration management (connect, disconnect, settings)

3. **API Endpoints** (14 endpoints):
   - [x] `GET /api/calendar/integrations` - List integrations
   - [x] `GET /api/calendar/stats` - Sync statistics
   - [x] `GET /api/calendar/google/auth` - Google OAuth URL
   - [x] `GET /api/calendar/google/callback` - Google OAuth callback
   - [x] `GET /api/calendar/outlook/auth` - Outlook OAuth URL
   - [x] `GET /api/calendar/outlook/callback` - Outlook OAuth callback
   - [x] `GET /api/calendar/integrations/<id>/calendars` - List calendars
   - [x] `PUT /api/calendar/integrations/<id>/calendar` - Set calendar
   - [x] `PUT /api/calendar/integrations/<id>/settings` - Update settings
   - [x] `POST /api/calendar/integrations/<id>/disconnect` - Disconnect
   - [x] `GET /api/calendar/free-busy` - Get busy times
   - [x] `POST /api/calendar/check-availability` - Check slot availability

4. **Settings UI** (`templates/settings.html`):
   - [x] Calendar Integration section with Google/Outlook cards
   - [x] Connect/disconnect buttons
   - [x] Sync settings toggles (enable/disable, free/busy checking)
   - [x] Connection status and last sync display

5. **Booking System Integration** (`app.py`):
   - [x] Auto-sync new bookings to staff's connected calendar
   - [x] Delete calendar events when bookings are cancelled

### Files Created/Modified
- `database.py` - Added CalendarIntegration, CalendarEvent models + migrations
- `services/calendar_sync_service.py` (NEW) - ~700 lines
- `app.py` - Added 14 calendar API endpoints + booking integration
- `templates/settings.html` - Added Calendar Integration section
- `tests/test_calendar_sync_service.py` (NEW) - 30 tests

### Environment Variables
```
# Google Calendar (OAuth 2.0)
GOOGLE_CALENDAR_CLIENT_ID=your-client-id
GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5001/api/calendar/google/callback

# Outlook Calendar (Microsoft Graph API)
OUTLOOK_CALENDAR_CLIENT_ID=your-client-id
OUTLOOK_CALENDAR_CLIENT_SECRET=your-client-secret
OUTLOOK_CALENDAR_REDIRECT_URI=http://localhost:5001/api/calendar/outlook/callback
```

### Test Status
- 30/30 calendar sync service tests passing

---

## Priority 34: Call Logging

**Status**: ✅ COMPLETE | **Effort**: Low (1 week)

Manual call tracking with notes and outcomes.
- [x] CallLog model
- [x] CallLogService (~500 lines)
- [x] 11 API endpoints at `/api/call-logs/*`
- [x] Dashboard UI at `/dashboard/call-logs`
- [x] 31 unit tests
- [ ] Log call from client page
- [ ] Call history and stats

---

## Priority 35: Task Assignment

**Status**: ✅ COMPLETE | **Effort**: Medium (1-2 weeks)

Assign tasks to staff with due dates and reminders.
- [x] StaffTask + StaffTaskComment models
- [x] TaskService (~670 lines)
- [x] 18 API endpoints at `/api/staff-tasks/*`
- [x] Dashboard UI at `/dashboard/tasks`
- [x] Recurring tasks (daily, weekly, biweekly, monthly)
- [x] Team workload view
- [x] 35 unit tests

---

## Priority 36: Scheduled Reports

**Status**: Not Started | **Effort**: Low (1 week)

Auto-email reports on schedule.
- [ ] ScheduledReport model
- [ ] Report scheduler service
- [ ] Settings page configuration

---

## Priority 37: SMS Templates Library

**Status**: Not Started | **Effort**: Low (3 days)

Pre-built SMS templates like email templates.
- [ ] SMSTemplate model
- [ ] Template management UI
- [ ] Variable substitution

---

## Priority 38: Client Tags

**Status**: Not Started | **Effort**: Low (1 week)

Flexible tagging for client segmentation.
- [ ] ClientTag model
- [ ] Tag management UI
- [ ] Filter by tags

---

## Priority 39: Email Open/Click Tracking

**Status**: Not Started | **Effort**: Medium (1-2 weeks)

Track email engagement.
- [ ] Tracking pixel
- [ ] Click tracking
- [ ] Stats dashboard

---

## CRM Enhancement Roadmap

See `CRM_ENHANCEMENT_CHECKLIST.md` for detailed implementation plans and failproof testing strategy.

**Phase 1 (High Value)**: P32 Unified Inbox
**Phase 2 (Medium Value)**: P33 Calendar Sync, P34 Call Logging
**Phase 3 (Quick Wins)**: P35-P36
**Phase 4 (Nice to Have)**: P37-P39

---

## Completed Features Summary

| Priority | Feature | Completed |
|----------|---------|-----------|
| P1-P14 | Core Platform Features | 2025-12-31 to 2026-01-03 |
| P15-P28 | Advanced Features | 2026-01-03 |
| P29-P30 | AI Chat Support | 2026-01-18 |
| P31 | Credit Score Simulator | 2026-01-19 |

---

## Pending Infrastructure

- [ ] **Send Certified Mail** - Awaiting SFTP credentials
- [ ] **Twilio A2P 10DLC** - Campaign pending carrier approval

---

## Notes

- **Email**: Gmail SMTP (SendGrid removed)
- **SMS**: Twilio (A2P campaign pending carrier approval)
- **Priorities 1-12**: All complete!
- **Priority 13**: Revenue Dashboard ✅ COMPLETE (2026-01-03)
- **Priority 14**: Stripe Subscriptions ✅ COMPLETE (2026-01-03)
- **Priority 15**: Invoice Generator ✅ COMPLETE (2026-01-03)
- **Priority 16**: Document Viewer ✅ COMPLETE (2026-01-03)
- **Priority 17**: Push Notifications ✅ COMPLETE (2026-01-03)
- **Priority 18**: Batch Processing ✅ COMPLETE (2026-01-03)
- **Priority 19**: Staff Performance ✅ COMPLETE (2026-01-03)
- **Priority 20**: Client Success Metrics ✅ COMPLETE (2026-01-03)
- **Priority 21**: AI Dispute Writer ✅ COMPLETE (2026-01-03)
- **Priority 22**: ROI Calculator ✅ COMPLETE (2026-01-03)
- **Priority 23**: Payment Plans ✅ COMPLETE (2026-01-03)
- **Priority 24**: Bureau Response Tracking ✅ COMPLETE (2026-01-03)
- **Priority 25**: Auto-Pull Credit Reports ✅ COMPLETE (2026-01-03)
- **Priority 26**: Letter Template Builder ✅ COMPLETE (2026-01-03)
- **Priority 27**: Mobile App (PWA) ✅ COMPLETE (2026-01-03)
- **Priority 28**: Voicemail Drops ✅ COMPLETE (2026-01-03)
- **All P1-P28 priorities complete!**
- See `FEATURE_IMPLEMENTATION_CHECKLIST.md` for future feature roadmap

---

*Last updated: 2026-01-03*
