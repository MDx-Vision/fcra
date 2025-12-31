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

## Priority 3: Post-Analysis Q&A Booking

### Overview
After first analysis is complete, clients can book a 15-minute Q&A call if they have questions.

### Flow
1. Client receives first analysis
2. Reviews results in portal
3. Has questions? → Book 15-min call
4. Pick available time slot
5. Confirmation email sent to both parties

### Features
- 15-minute slots only
- Staff sets available times
- Client picks from open slots
- Email confirmation (Gmail)
- Simple, no Google Calendar sync needed

### Implementation Steps

1. [ ] Create `BookingSlot` model (date, time, duration=15, is_booked, client_id)
2. [ ] Create staff UI to set available slots (bulk create: "Mon-Fri 2pm-5pm")
3. [ ] Add "Book Q&A Call" button to portal after analysis complete
4. [ ] Create booking page showing open 15-min slots
5. [ ] Send confirmation email to client + staff on booking
6. [ ] Add booking to client's case notes automatically

---

## Priority 4: Simple Report Upload Flow

### Overview
Let leads upload credit reports without filling out full form.

### Concept
- Minimal form: Name, Email, Upload file
- Auto-extract info from report if possible
- Convert to lead, follow up later

### Implementation Steps

1. [ ] Create simple upload page (`/upload-report`)
2. [ ] Accept PDF/image uploads
3. [ ] Store as lead with `dispute_status='report_uploaded'`
4. [ ] Send confirmation email
5. [ ] Staff notification for new uploads

---

## Completed Features

- [x] Phase 1-8 Core Platform
- [x] Lead Capture Landing Page (`/get-started`)
- [x] Portal Logo Fix
- [x] Client Portal Document Upload Enhancements
- [x] Secondary Bureau Freeze Status UI
- [x] **Priority 1: Client Communication Automation** (2025-12-31)
  - SMS & email opt-in fields
  - Workflow triggers wired up (dispute_sent, response_received, document_uploaded, status_changed)
  - SMS opt-in compliance checks
- [x] **Priority 2: Gmail Integration** (2025-12-31)
  - Replaced SendGrid with Gmail SMTP
  - Uses `GMAIL_USER` and `GMAIL_APP_PASSWORD` env vars
  - All email functions work with attachments

---

## Notes

- **Email**: Gmail SMTP (SendGrid removed)
- **SMS**: Twilio (no alternative), requires client opt-in
- Booking (Priority 3) can be done independently
- Priority 1 is the biggest value-add for client experience
