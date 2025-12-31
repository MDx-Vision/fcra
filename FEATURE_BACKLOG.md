# Feature Backlog

> Priority features and enhancements for Brightpath Ascend FCRA Platform
>
> Created: 2025-12-31

---

## Priority 1: Client Communication Automation

### Overview
Complete the workflow automation system to notify clients at key points in their case lifecycle via Email AND SMS (for clients who opt-in).

### Current State
- Infrastructure exists in `services/workflow_triggers_service.py`
- Only `case_created` and `payment_received` triggers are wired up
- Email/SMS actions work but most triggers never fire
- SMS templates already exist in `services/sms_templates.py`

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

### SMS Templates (Already Exist)

| Template | When Sent | Opt-in Required |
|----------|-----------|-----------------|
| `welcome_sms` | On signup | Yes |
| `dispute_sent_sms` | Letters mailed | Yes |
| `cra_response_sms` | Bureau responds | Yes |
| `case_update_sms` | Status change | Yes |
| `document_reminder_sms` | Missing docs | Yes |

### SMS Opt-In Requirements

1. [ ] Add `sms_opt_in` boolean field to Client model
2. [ ] Add SMS opt-in checkbox to signup forms
3. [ ] Add SMS preference toggle in client portal profile
4. [ ] Check `sms_opt_in` before sending any SMS
5. [ ] Honor STOP replies (Twilio handles this automatically)

### Implementation Steps

1. [ ] Add `sms_opt_in` field to Client model + migration
2. [ ] Update signup forms with SMS opt-in checkbox
3. [ ] Add `evaluate_triggers("dispute_sent", {...})` call in letter queue send flow
4. [ ] Add `evaluate_triggers("response_received", {...})` in portal CRA upload route
5. [ ] Add `evaluate_triggers("status_changed", {...})` where `dispute_status` updates
6. [ ] Add `evaluate_triggers("document_uploaded", {...})` in portal document routes
7. [ ] Create scheduler job for `deadline_approaching` trigger
8. [ ] Create default email templates for each trigger type
9. [ ] Wire up SMS sending in workflow actions (check opt-in first)
10. [ ] Test full automation flow end-to-end (email + SMS)

### Files to Modify
- `database.py` - Add `sms_opt_in` to Client model
- `app.py` - Add trigger calls at event points, update signup forms
- `routes/portal.py` - Add triggers for portal uploads, SMS preference in profile
- `services/email_templates.py` - Add new templates
- `services/workflow_triggers_service.py` - Check SMS opt-in before sending
- `services/scheduler_service.py` - Add deadline check job

---

## Priority 2: Gmail for Transactional + SendGrid for Campaigns

### Overview
Use Gmail for transactional emails (notifications, updates). Keep SendGrid for marketing campaigns.

### Email Strategy

| Email Type | Service | Why |
|------------|---------|-----|
| Welcome emails | Gmail | Replies go to real inbox |
| Status updates | Gmail | Personal feel |
| Round notifications | Gmail | Transactional |
| CRA response alerts | Gmail | Transactional |
| Marketing campaigns | SendGrid | Built for bulk, tracking, templates |
| Newsletter | SendGrid | Open/click tracking |

### Why This Approach
- Gmail: Already paying for Google Workspace, replies go to real inbox, personal feel
- SendGrid: Keep for campaigns where you need tracking, bulk sending, templates

### Current State
- `services/email_service.py` uses SendGrid API for everything
- Need to add Gmail option for transactional

### Implementation Steps

1. [ ] Create Gmail App Password (requires 2FA on Google account)
2. [ ] Create `services/gmail_service.py` for transactional emails
3. [ ] Keep `services/email_service.py` (SendGrid) for campaigns
4. [ ] Update workflow triggers to use Gmail for notifications
5. [ ] Add `EMAIL_PROVIDER` config to choose per-email-type
6. [ ] Update `services/config.py` for Gmail vars
7. [ ] Test both email paths

### Gmail SMTP Settings
```
Host: smtp.gmail.com
Port: 587 (TLS) or 465 (SSL)
Auth: App Password (not regular password)
```

### Environment Variables (New)
```
GMAIL_USER=your-email@yourdomain.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Limits to Remember
- Google Workspace: 2,000 emails/day (transactional)
- SendGrid: Use for campaigns beyond Gmail limits

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

- **Email strategy**: Gmail for transactional (notifications), SendGrid for campaigns
- **SMS**: Twilio (no alternative), requires client opt-in
- Automation (Priority 1) can start with existing SendGrid, switch to Gmail later
- Booking (Priority 3) can be done independently
- Priority 1 is the biggest value-add for client experience
