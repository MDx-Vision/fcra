# Admin Operations Guide

> Day-to-day administrative operations for the Brightpath Ascend FCRA Platform
>
> Created: 2026-01-09

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Weekly Tasks](#weekly-tasks)
3. [Monthly Tasks](#monthly-tasks)
4. [New Feature Operations (P13-P28)](#new-feature-operations)
5. [Troubleshooting Common Issues](#troubleshooting-common-issues)
6. [Environment Setup](#environment-setup)
7. [Backup & Recovery](#backup--recovery)

---

## Daily Operations

### Morning Checklist

| Task | URL | Priority |
|------|-----|----------|
| Check overdue bureau responses | `/dashboard/bureau-tracking` | High |
| Review pending analyses | `/dashboard/analyses` | High |
| Process letter queue | `/dashboard/letter-queue` | High |
| Check scheduled jobs status | `/dashboard/task-queue` | Medium |
| Review unread messages | `/dashboard/messages` | Medium |
| Check today's bookings | `/dashboard/bookings` | Medium |

### Processing Bureau Responses

1. Navigate to **Bureau Tracking** (`/dashboard/bureau-tracking`)
2. Review "Due Soon" sidebar for upcoming deadlines
3. Check "Overdue" sidebar for FCRA violations
4. Record responses as they arrive:
   - Click "Record Response" on a dispute
   - Select response type (deleted, verified, updated, frivolous)
   - Enter item counts
   - Upload response document

### Managing the Letter Queue

1. Navigate to **Letter Queue** (`/dashboard/letter-queue`)
2. Filter by status: Pending, Ready, Sent
3. For pending letters:
   - Review content for accuracy
   - Click "Approve" or "Edit"
4. For ready letters:
   - Batch download as ZIP
   - Send via certified mail
   - Update tracking numbers

### Staff Messaging

1. Navigate to **Messages** (`/dashboard/messages`)
2. Unread conversations appear with badge count
3. Click on a client to view conversation
4. Reply and mark as read
5. Use templates for common responses

---

## Weekly Tasks

### Monday - Week Start Review

| Task | Action |
|------|--------|
| Revenue check | Review `/dashboard/revenue` for week-over-week |
| Staff performance | Check `/dashboard/staff-performance` leaderboard |
| Client success | Review `/dashboard/client-success` metrics |
| Drip campaign stats | Check `/dashboard/drip-campaigns` enrollment |

### Wednesday - Mid-Week Processing

| Task | Action |
|------|--------|
| Batch processing | Run bulk status updates if needed |
| Credit pulls | Review `/dashboard/auto-pull` for failed pulls |
| Payment plans | Check `/dashboard/payment-plans` for overdue |

### Friday - Week End Tasks

| Task | Action |
|------|--------|
| Export reports | Download CSV from Analytics dashboards |
| Review escalations | Check cases needing attorney review |
| Update templates | Review letter templates for improvements |

---

## Monthly Tasks

### First Week of Month

1. **Revenue Reconciliation**
   - Export `/api/revenue/export`
   - Compare with Stripe dashboard
   - Update commissions for affiliates

2. **Client Success Snapshots**
   - Run `/api/client-success/update-all`
   - Generate success report
   - Identify top performers for testimonials

3. **Staff Performance Review**
   - Export staff metrics
   - Review response times
   - Adjust workload distribution

### Mid-Month

1. **Template Review**
   - Audit email templates for compliance
   - Update letter templates with new case law
   - Test drip campaign sequences

2. **System Health Check**
   - Review audit logs
   - Check API usage and rate limits
   - Verify backup status

### End of Month

1. **Reporting**
   - Generate monthly client success report
   - Calculate affiliate payouts
   - Document any compliance issues

2. **Planning**
   - Review feature backlog
   - Prioritize next month's work
   - Schedule staff training

---

## New Feature Operations

### Revenue Dashboard (P13)

**URL**: `/dashboard/revenue`

**Key Metrics**:
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- Churn Rate
- LTV (Lifetime Value)
- ARPU (Average Revenue Per User)

**Actions**:
- View revenue trends with Chart.js
- Filter by time period
- Export CSV for accounting

### Stripe Subscriptions (P14)

**URL**: `/dashboard/subscriptions` (via client detail)

**Plan Tiers**:
| Plan | Price | Features |
|------|-------|----------|
| Basic | $49/mo | 1 bureau monitoring |
| Pro | $99/mo | 3 bureau monitoring |
| Enterprise | $199/mo | Full service + priority |

**Operations**:
1. View client subscription status
2. Upgrade/downgrade plans
3. Handle cancellations
4. Process refunds via Stripe dashboard

### Invoice Generator (P15)

**URL**: `/dashboard/invoices`

**Creating Invoices**:
1. Click "New Invoice"
2. Select client
3. Add line items
4. Set due date
5. Click "Generate"

**Invoice Types**:
- Analysis fee
- Round fee
- Settlement fee (30%)
- Custom services

### Document Viewer (P16)

**Usage**:
- Click preview icon on any document
- PDF renders in browser
- Use zoom controls (+/-)
- Navigate pages with arrows
- Download if needed

### Push Notifications (P17)

**URL**: `/dashboard/settings` → Push Notifications

**Setup**:
1. Generate VAPID keys (if not set)
2. Configure notification preferences
3. Test with `/api/push/test`

**Notification Types**:
- Case updates
- New messages
- Document uploads
- Payment reminders
- Deadline alerts

### Batch Processing (P18)

**URL**: `/dashboard/batch-jobs`

**Available Actions**:
| Action | Description |
|--------|-------------|
| update_status | Change dispute status |
| update_dispute_round | Advance round |
| send_email | Send templated email |
| send_sms | Send SMS (opt-in required) |
| assign_staff | Assign case manager |
| add_tag | Add client tag |
| remove_tag | Remove client tag |
| add_note | Add case note |
| export | Export to CSV |
| delete | Delete clients |

**Running a Batch Job**:
1. Go to `/dashboard/client-manager`
2. Select clients with checkboxes
3. Click "Batch Actions" dropdown
4. Choose action
5. Fill in parameters
6. Click "Execute"
7. Monitor progress in modal

### Staff Performance (P19)

**URL**: `/dashboard/staff-performance`

**Tracked Activities**:
| Activity | Points |
|----------|--------|
| case_assigned | 5 |
| case_completed | 20 |
| document_reviewed | 3 |
| letter_sent | 10 |
| response_processed | 8 |
| message_sent | 2 |
| call_completed | 5 |
| note_added | 1 |
| status_changed | 2 |
| analysis_reviewed | 15 |
| dispute_filed | 12 |

**Leaderboard**:
- Top staff by points
- Gold/Silver/Bronze badges
- Response time rankings

### Client Success Metrics (P20)

**URL**: `/dashboard/client-success`

**Metrics Tracked**:
- Items deleted (total and by bureau)
- Score improvements
- Deletion rate percentage
- Success grades (A+ to F)

**Creating Snapshots**:
- Automatic: Monthly via scheduled job
- Manual: `/api/client-success/client/<id>/snapshot`

### AI Dispute Writer (P21)

**URL**: `/dashboard/ai-dispute-writer`

**Using the AI Writer**:
1. Search and select client
2. Check dispute items to include
3. Select round (R1-R4)
4. Choose tone (Professional, Aggressive, Formal)
5. Select target bureaus
6. Add custom instructions (optional)
7. Click "Generate Letters"
8. Review and edit
9. Save or copy

**Round Strategies**:
| Round | Strategy |
|-------|----------|
| R1 | Initial dispute with RLPP bundling |
| R2 | Cushman-style MOV demands |
| R3 | Regulatory escalation (CFPB, AG) |
| R4 | Pre-litigation demands |

### ROI Calculator (P22)

**URL**: `/dashboard/roi-calculator`

**Calculation Factors**:
- FCRA statutory damages ($100-$1,000/violation)
- Punitive damages (2.5x for willful)
- Attorney fees estimate
- Score improvement value

**Using the Calculator**:
1. Select client
2. Enter actual damages (optional)
3. Click "Calculate ROI"
4. View estimates (Conservative, Moderate, Aggressive)
5. Check litigation score

### Payment Plans (P23)

**URL**: `/dashboard/payment-plans`

**Creating a Plan**:
1. Click "New Plan"
2. Select client
3. Enter total amount
4. Set number of installments
5. Choose frequency (Weekly, Bi-Weekly, Monthly)
6. Set down payment (optional)
7. Configure late fees (optional)
8. Click "Create Plan"

**Managing Plans**:
- Record payments
- Pause/Resume plans
- Handle late payments
- Export reports

### Bureau Response Tracking (P24)

**URL**: `/dashboard/bureau-tracking`

**FCRA Deadlines**:
- Standard: 30 days from dispute
- Complex: 45 days (marked at creation)

**Tracking Process**:
1. Track dispute when sent
2. Confirm delivery (recalculates deadline)
3. Record response when received
4. System auto-checks for overdue

### Auto-Pull Credit Reports (P25)

**URL**: `/dashboard/auto-pull`

**Supported Services**:
- IdentityIQ
- MyScoreIQ
- SmartCredit
- Privacy Guard
- Credit Karma

**Setting Up Auto-Pull**:
1. Add client credentials
2. Set pull frequency
3. Validate credentials
4. System pulls automatically

**Pull Frequencies**:
- Manual (on-demand only)
- Daily
- Weekly
- Bi-Weekly
- Monthly
- With Letter Send

### Letter Template Builder (P26)

**URL**: `/dashboard/letter-templates`

**Template Categories**:
- Initial Dispute
- MOV Demand
- Escalation
- Follow-Up
- Pre-Litigation
- Furnisher
- Collector
- General

**Creating Templates**:
1. Click "New Template"
2. Fill in details (name, category, round)
3. Write content with variables
4. Preview with sample data
5. Save

**Common Variables**:
```
{client_name}, {first_name}, {last_name}
{address}, {city}, {state}, {zip}
{ssn_last_4}, {dob}
{bureau}, {account_name}, {account_number}
{current_date}, {deadline_date}
```

### Mobile App (PWA) (P27)

**No admin action required** - automatic for portal users

**User Instructions**:
- iOS: Safari → Share → "Add to Home Screen"
- Android: Chrome → Menu → "Install App"

### Voicemail Drops (P28)

**URL**: `/dashboard/voicemail`

**Managing Recordings**:
1. Upload audio files (MP3, WAV)
2. Categorize (welcome, reminder, update, etc.)
3. Preview before use

**Sending Drops**:
1. Select recording
2. Choose target (single client or campaign)
3. Schedule or send immediately
4. Monitor delivery status

**Providers Supported**:
- Slybroadcast
- Drop Cowboy
- Twilio (with AMD)

---

## Troubleshooting Common Issues

### Issue: Client Can't Login to Portal

1. Check `client_stage` - must be `onboarding` or `active`
2. Verify password hash is set
3. Check for session issues - have them clear cookies
4. Try magic link: `/portal/login?token=<client.portal_token>`

### Issue: Letters Not Generating

1. Check AI service (Anthropic API key)
2. Verify client has required data (address, etc.)
3. Review error logs in `/dashboard/audit-logs`
4. Check PDF generation service (WeasyPrint)

### Issue: Emails Not Sending

1. Verify Gmail credentials in environment
2. Check email opt-in status on client
3. Review email service logs
4. Test with `/api/email/test`

### Issue: SMS Not Delivering

1. Check Twilio credentials
2. Verify A2P 10DLC campaign status
3. Check SMS opt-in status on client
4. Review rate limits

### Issue: Scheduled Jobs Not Running

1. Check cron endpoint accessibility
2. Verify `CRON_SECRET` environment variable
3. Review task queue for errors
4. Manual trigger: `/api/jobs/run-all`

### Issue: Stripe Payments Failing

1. Check Stripe API key
2. Verify webhook endpoint
3. Review Stripe dashboard for errors
4. Test with Stripe test mode

---

## Environment Setup

### Required Environment Variables

```bash
# Core
DATABASE_URL=postgresql://user:pass@host:5432/db
FLASK_SECRET_KEY=<random-key>

# AI
ANTHROPIC_API_KEY=sk-ant-...

# Email
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# SMS
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# Payments
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Certified Mail (when credentials received)
SENDCERTIFIED_SFTP_HOST=sftp.sendcertifiedmail.com
SENDCERTIFIED_SFTP_USERNAME=...
SENDCERTIFIED_SFTP_PASSWORD=...

# Push Notifications
VAPID_PUBLIC_KEY=<base64-key>
VAPID_PRIVATE_KEY=<base64-key>
VAPID_SUBJECT=mailto:admin@example.com

# Encryption
FCRA_ENCRYPTION_KEY=<fernet-key>

# Scheduled Jobs
CRON_SECRET=<random-secret>
```

### Starting the Server

```bash
# Development
python3 app.py

# Production (Gunicorn)
gunicorn app:app --workers 4 --bind 0.0.0.0:5000

# With environment file
source .env && python3 app.py
```

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20260109.sql
```

### File Backup

Key directories to backup:
- `static/client_uploads/` - Client documents
- `static/signatures/` - CROA signatures
- `static/voicemail_recordings/` - Voicemail audio
- `logs/` - Application logs

### Recovery Procedures

1. **Database Recovery**:
   - Stop application
   - Restore from backup
   - Run migrations if needed
   - Restart application

2. **File Recovery**:
   - Restore file directories
   - Verify permissions
   - Check file references in database

---

## Quick Reference

### Key URLs

| Page | URL |
|------|-----|
| Dashboard | `/dashboard` |
| Clients | `/dashboard/clients` |
| Client Manager | `/dashboard/client-manager` |
| Bureau Tracking | `/dashboard/bureau-tracking` |
| Letter Queue | `/dashboard/letter-queue` |
| Revenue | `/dashboard/revenue` |
| Staff Performance | `/dashboard/staff-performance` |
| Settings | `/dashboard/settings` |

### API Endpoints for Automation

```bash
# Run all scheduled jobs
curl -X POST $BASE_URL/api/jobs/run-all \
  -H "X-Cron-Secret: $CRON_SECRET"

# Check overdue disputes
curl -X POST $BASE_URL/api/bureau-tracking/check-overdue \
  -H "Authorization: Bearer $API_KEY"

# Export revenue data
curl $BASE_URL/api/revenue/export?period=month \
  -H "Authorization: Bearer $API_KEY"
```

---

*Last Updated: 2026-01-09*
