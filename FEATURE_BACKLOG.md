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

## Priority 2: Gmail Integration (Replace SendGrid)

### Overview
Switch all email sending from SendGrid to Gmail. Simpler, already paid for, replies go to real inbox.

### Current State
- `services/email_service.py` uses SendGrid API
- Environment vars: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME`

### Implementation Steps

1. [ ] Create Gmail App Password (requires 2FA on Google account)
2. [ ] Rewrite `services/email_service.py` to use `smtplib` with Gmail SMTP
3. [ ] Update environment variables to `GMAIL_USER`, `GMAIL_APP_PASSWORD`
4. [ ] Update `services/config.py` for new config vars
5. [ ] Remove SendGrid dependency from `requirements.txt`
6. [ ] Update all tests in `tests/test_email_service.py`
7. [ ] Test email sending end-to-end

### Gmail SMTP Settings
```
Host: smtp.gmail.com
Port: 587 (TLS) or 465 (SSL)
Auth: App Password (not regular password)
```

### Environment Variables
```
GMAIL_USER=your-email@yourdomain.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Limits
- Google Workspace: 2,000 emails/day
- Personal Gmail: 500 emails/day

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

---

## Notes

- **Email**: Gmail only (replacing SendGrid completely)
- **SMS**: Twilio (no alternative), requires client opt-in
- Automation (Priority 1) can start with existing SendGrid, switch to Gmail after Priority 2
- Booking (Priority 3) can be done independently
- Priority 1 is the biggest value-add for client experience
