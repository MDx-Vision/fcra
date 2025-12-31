# Feature Backlog

> Priority features and enhancements for Brightpath Ascend FCRA Platform
>
> Created: 2025-12-31

---

## Priority 1: Client Communication Automation

### Overview
Complete the workflow automation system to notify clients at key points in their case lifecycle.

### Current State
- Infrastructure exists in `services/workflow_triggers_service.py`
- Only `case_created` and `payment_received` triggers are wired up
- Email/SMS actions work but most triggers never fire

### Triggers Needing Wire-Up

| Trigger | Fire When | Location to Add |
|---------|-----------|-----------------|
| `dispute_sent` | Letters mailed to bureaus | Letter queue / certified mail flow |
| `response_received` | CRA response uploaded | Portal upload + staff upload routes |
| `status_changed` | Case status updates | Anywhere `dispute_status` changes |
| `document_uploaded` | Client uploads document | Portal document upload route |
| `deadline_approaching` | SOL/response deadline near | Scheduler/cron job |

### Email Templates Needed

| Template | Subject | When Sent |
|----------|---------|-----------|
| `welcome` | Welcome to Brightpath! | On signup (exists) |
| `round_sent` | Round {N} Letters Sent | After dispute letters mailed |
| `response_received` | Update: {Bureau} Responded | When CRA response uploaded |
| `status_update` | Your Case Status Update | On status change |
| `deadline_reminder` | Action Required: Deadline Approaching | 7 days before deadline |

### Implementation Steps

1. [ ] Add `evaluate_triggers("dispute_sent", {...})` call in letter queue send flow
2. [ ] Add `evaluate_triggers("response_received", {...})` in portal CRA upload route
3. [ ] Add `evaluate_triggers("status_changed", {...})` where `dispute_status` updates
4. [ ] Add `evaluate_triggers("document_uploaded", {...})` in portal document routes
5. [ ] Create scheduler job for `deadline_approaching` trigger
6. [ ] Create default email templates for each trigger type
7. [ ] Test full automation flow end-to-end

### Files to Modify
- `app.py` - Add trigger calls at event points
- `routes/portal.py` - Add triggers for portal uploads
- `services/email_templates.py` - Add new templates
- `services/scheduler_service.py` - Add deadline check job

---

## Priority 2: Gmail Integration (Replace SendGrid)

### Overview
Switch from SendGrid to Gmail/Google Workspace for transactional emails.

### Why
- Already paying for Google Workspace
- Volume is low (<100 emails/day)
- Simpler setup, replies go to real inbox

### Current State
- `services/email_service.py` uses SendGrid API
- Environment vars: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME`

### Implementation Steps

1. [ ] Create Gmail App Password (requires 2FA on Google account)
2. [ ] Rewrite `services/email_service.py` to use `smtplib` with Gmail SMTP
3. [ ] Update environment variables to `GMAIL_USER`, `GMAIL_APP_PASSWORD`
4. [ ] Update `services/config.py` for new config vars
5. [ ] Test email sending with new implementation
6. [ ] Update all tests in `tests/test_email_service.py`

### Gmail SMTP Settings
```
Host: smtp.gmail.com
Port: 587 (TLS) or 465 (SSL)
Auth: App Password (not regular password)
```

### Limits to Remember
- Google Workspace: 2,000 emails/day
- Personal Gmail: 500 emails/day

---

## Priority 3: Simple Booking System

### Overview
Allow leads/clients to book consultations without Calendly.

### Options

**Option A: Simple DB-based booking (Recommended to start)**
- Staff sets available time slots manually
- Clients pick from available slots
- No Google Calendar sync
- Confirmation emails via Gmail

**Option B: Full Google Calendar integration**
- Reads staff calendar for availability
- Creates events on booking
- Requires OAuth2 setup
- More complex, more maintenance

### Recommendation
Start with Option A. Add Google Calendar sync later only if needed.

### Implementation Steps (Option A)

1. [ ] Create `AvailableSlot` model (date, time, duration, is_booked)
2. [ ] Create staff UI to manage available slots
3. [ ] Create public booking page showing open slots
4. [ ] Create booking confirmation flow
5. [ ] Send confirmation email to client + staff
6. [ ] Add to lead capture page (`/get-started`)

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

---

## Notes

- All email sending should work with Gmail once Priority 2 is done
- Automation (Priority 1) depends on email working
- Booking (Priority 3) can be done independently
