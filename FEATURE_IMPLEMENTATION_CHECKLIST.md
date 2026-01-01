# Feature Implementation Checklist

> Master checklist for all planned features. Each feature follows the workflow:
> 1. Plan → 2. Implement → 3. Write Tests → 4. Run Tests → 5. Finalize

---

## Completed Features

### Priority 1-4 (Complete)
- [x] Priority 1: Client Communication Automation
- [x] Priority 2: Gmail Integration (Replace SendGrid)
- [x] Priority 3: Post-Analysis Q&A Booking + Live Messaging
- [x] Priority 4: Simple Report Upload Flow

### Deadline Approaching Scheduler (Just Completed)
- [x] Create `DeadlineCheckerService` (`services/deadline_checker_service.py`)
- [x] Add scheduled job "Check All Approaching Deadlines" (daily 8 AM)
- [x] Add workflow triggers for secondary bureau deadlines
- [x] Add workflow triggers for CRA response deadlines
- [x] Write unit tests (22 tests passing)

---

## Phase 5: Client Acquisition & Onboarding

### 5.1 Affiliate Dashboard
> Track referral signups, commissions, payout history

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan implementation | | Database models, API endpoints, UI |
| [ ] Create `Affiliate` model | | name, email, code, commission_rate |
| [ ] Create `AffiliateReferral` model | | affiliate_id, client_id, status |
| [ ] Create `AffiliatePayout` model | | affiliate_id, amount, status, date |
| [ ] API: `/api/affiliates` CRUD | | Staff management |
| [ ] API: `/api/affiliates/referrals` | | Track referrals |
| [ ] API: `/api/affiliates/payouts` | | Payout management |
| [ ] Template: `affiliate_dashboard.html` | | Stats, referrals, payouts |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 5.2 Lead Scoring
> Auto-prioritize leads based on credit report severity

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan scoring algorithm | | Factors: account count, derogatory items, score range |
| [ ] Add `lead_score` field to Client | | Integer 0-100 |
| [ ] Create `LeadScoringService` | | Calculate and update scores |
| [ ] Add scoring trigger on report upload | | Auto-score when report analyzed |
| [ ] Update client list to show score | | Color-coded priority |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 5.3 Onboarding Wizard
> Step-by-step client setup with progress tracking

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan onboarding steps | | ID upload, address verify, payment, etc. |
| [ ] Create `OnboardingProgress` model | | client_id, step, completed_at |
| [ ] Create `OnboardingService` | | Track and update progress |
| [ ] Template: `portal/onboarding.html` | | Step-by-step wizard UI |
| [ ] Add progress indicator to portal nav | | Show completion % |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 5.4 E-Sign Integration
> DocuSign/HelloSign for service agreements

| Step | Status | Notes |
|------|--------|-------|
| [ ] Research API (DocuSign vs HelloSign) | | Cost, features, complexity |
| [ ] Create `ESignService` | | Send, track, complete documents |
| [ ] Add `ServiceAgreement` model | | client_id, status, signed_at |
| [ ] API: `/api/agreements/send` | | Trigger e-sign request |
| [ ] API: `/api/agreements/webhook` | | Handle completion callback |
| [ ] Add agreement status to client view | | Show pending/signed |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

---

## Phase 6: Client Portal Enhancements

### 6.1 Progress Timeline
> Visual journey from signup → disputes → resolution

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan timeline events | | Signup, docs, analysis, disputes, responses |
| [ ] Create `TimelineEvent` model | | client_id, event_type, date, details |
| [ ] Auto-create events on actions | | Hook into existing workflows |
| [ ] Template: `portal/timeline.html` | | Visual timeline UI |
| [ ] Add timeline preview to dashboard | | Recent events summary |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 6.2 Document Viewer
> In-browser PDF preview (no download needed)

| Step | Status | Notes |
|------|--------|-------|
| [ ] Research PDF.js integration | | Client-side PDF rendering |
| [ ] Add document preview modal | | Open PDF in browser |
| [ ] Add zoom and page navigation | | Basic viewer controls |
| [ ] Add to portal documents page | | Preview button on each doc |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 6.3 Push Notifications
> Browser notifications for updates

| Step | Status | Notes |
|------|--------|-------|
| [ ] Research Web Push API | | Service worker, VAPID keys |
| [ ] Create `PushSubscription` model | | client_id, endpoint, keys |
| [ ] Add notification permission request | | Portal settings or onboarding |
| [ ] Create `PushNotificationService` | | Send notifications |
| [ ] Integrate with workflow triggers | | Send on status changes |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 6.4 Mobile App (PWA)
> Installable app from portal

| Step | Status | Notes |
|------|--------|-------|
| [ ] Create `manifest.json` | | App name, icons, colors |
| [ ] Create service worker | | Offline caching |
| [ ] Add install prompt | | "Add to Home Screen" |
| [ ] Test on iOS and Android | | Verify PWA behavior |
| [ ] Add offline page | | Show when disconnected |
| [ ] Finalize & document | | |

---

## Phase 7: Automation & Efficiency

### 7.1 Auto-Pull Credit Reports
> Scheduled pulls from IdentityIQ/SmartCredit

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan credential storage | | Secure encryption for login info |
| [ ] Create `CreditPullSchedule` model | | client_id, frequency, next_pull |
| [ ] Create `AutoPullService` | | Login, download, process |
| [ ] Add scheduled job | | Daily/weekly pulls |
| [ ] Handle pull failures | | Retry logic, notifications |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 7.2 Letter Template Builder
> Drag-drop custom dispute letter creator

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan template structure | | Variables, sections, formatting |
| [ ] Create `LetterTemplate` model | | name, content, variables |
| [ ] Create template editor UI | | Rich text + variable insertion |
| [ ] Add preview functionality | | Show rendered letter |
| [ ] Integrate with letter generation | | Use custom templates |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 7.3 Batch Processing
> Process multiple clients at once

| Step | Status | Notes |
|------|--------|-------|
| [ ] Add multi-select to client list | | Checkbox selection |
| [ ] Create batch action menu | | Generate letters, update status, etc. |
| [ ] Create `BatchProcessingService` | | Handle bulk operations |
| [ ] Add progress indicator | | Show batch progress |
| [ ] Add batch history log | | Track completed batches |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 7.4 AI Dispute Writer
> Generate custom dispute reasons from report

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan AI prompt templates | | Account type, error type, context |
| [ ] Create `AIDisputeService` | | Call Anthropic API |
| [ ] Add "Generate Reason" button | | Per-account action |
| [ ] Add bulk generation | | Generate for all disputed items |
| [ ] Store generated text | | Editable before use |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

---

## Phase 8: Revenue & Payments

### 8.1 Stripe Subscriptions
> Monthly recurring billing

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan subscription tiers | | Basic, Pro, Enterprise |
| [ ] Create `Subscription` model | | client_id, stripe_id, status, plan |
| [ ] Integrate Stripe Billing API | | Create, update, cancel subs |
| [ ] Create subscription checkout flow | | Portal signup |
| [ ] Handle webhook events | | Payment success/failure |
| [ ] Add subscription status to portal | | Show current plan |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 8.2 Payment Plans
> Split payments over time

| Step | Status | Notes |
|------|--------|-------|
| [ ] Create `PaymentPlan` model | | client_id, total, installments, schedule |
| [ ] Create `PaymentInstallment` model | | plan_id, amount, due_date, status |
| [ ] Create payment plan setup flow | | Choose plan, schedule payments |
| [ ] Add auto-charge for installments | | Scheduled job |
| [ ] Add plan status to client view | | Show payment progress |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 8.3 Invoice Generator
> Auto-generate client invoices

| Step | Status | Notes |
|------|--------|-------|
| [ ] Create `Invoice` model | | client_id, amount, items, status |
| [ ] Create `InvoiceService` | | Generate, send, track |
| [ ] Create invoice PDF template | | Professional format |
| [ ] Add invoice history to portal | | Client can view invoices |
| [ ] Add invoice email trigger | | Auto-send on generation |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 8.4 Revenue Dashboard
> MRR, churn, LTV metrics

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan metrics to track | | MRR, ARR, churn, LTV, CAC |
| [ ] Create `RevenueMetricsService` | | Calculate all metrics |
| [ ] Template: `revenue_dashboard.html` | | Charts, trends, KPIs |
| [ ] Add historical tracking | | Store daily snapshots |
| [ ] Add export functionality | | CSV/Excel export |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

---

## Phase 9: Communication

### 9.1 Email Templates Library
> Pre-built emails for common scenarios

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan template categories | | Welcome, updates, reminders, etc. |
| [ ] Create `EmailTemplate` model | | name, subject, body, category |
| [ ] Create template management UI | | CRUD for templates |
| [ ] Add variable system | | {client_name}, {status}, etc. |
| [ ] Integrate with email sending | | Select template to send |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 9.2 Drip Campaigns
> Automated follow-up sequences

| Step | Status | Notes |
|------|--------|-------|
| [ ] Create `DripCampaign` model | | name, trigger, steps |
| [ ] Create `DripStep` model | | campaign_id, delay_days, template |
| [ ] Create `DripEnrollment` model | | campaign_id, client_id, step |
| [ ] Create campaign builder UI | | Define steps and delays |
| [ ] Add scheduled job for sending | | Process due messages |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 9.3 SMS Templates
> Quick-send common messages

| Step | Status | Notes |
|------|--------|-------|
| [ ] Create `SMSTemplate` model | | name, message, category |
| [ ] Create template management UI | | CRUD for templates |
| [ ] Add quick-send buttons | | Client view actions |
| [ ] Integrate with SMS service | | Use templates for automation |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 9.4 Voicemail Drops
> Pre-recorded messages via Twilio

| Step | Status | Notes |
|------|--------|-------|
| [ ] Research Twilio Programmable Voice | | API capabilities |
| [ ] Create `VoicemailTemplate` model | | name, audio_url |
| [ ] Add audio upload/recording | | Store voicemail files |
| [ ] Create `VoicemailService` | | Send via Twilio |
| [ ] Add to client actions | | "Leave Voicemail" button |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

---

## Phase 10: Reporting & Analytics

### 10.1 Client Success Metrics
> Items deleted, score improvements

| Step | Status | Notes |
|------|--------|-------|
| [ ] Track items deleted per client | | Before/after counts |
| [ ] Track score improvements | | Initial vs current scores |
| [ ] Create success summary view | | Per-client metrics |
| [ ] Add to client portal | | Show their progress |
| [ ] Create aggregate report | | All clients summary |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 10.2 Staff Performance
> Cases handled, response times

| Step | Status | Notes |
|------|--------|-------|
| [ ] Track cases per staff member | | Assignment and completion |
| [ ] Track response times | | Time to respond to clients |
| [ ] Create performance dashboard | | Staff leaderboard |
| [ ] Add individual staff reports | | Detailed metrics |
| [ ] Write unit tests | | |
| [ ] Write Cypress tests | | |
| [ ] Finalize & document | | |

### 10.3 Bureau Response Tracking
> Which bureaus respond fastest

| Step | Status | Notes |
|------|--------|-------|
| [ ] Track response times by bureau | | Days from send to response |
| [ ] Track deletion rates by bureau | | Success percentages |
| [ ] Create bureau analytics view | | Compare bureau performance |
| [ ] Add trends over time | | Historical analysis |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

### 10.4 ROI Calculator
> Show clients their savings

| Step | Status | Notes |
|------|--------|-------|
| [ ] Plan ROI formula | | Score improvement, debt reduction |
| [ ] Create calculator service | | Compute client savings |
| [ ] Add to client portal | | Show potential/actual savings |
| [ ] Create shareable report | | PDF for client |
| [ ] Write unit tests | | |
| [ ] Finalize & document | | |

---

## Pending Infrastructure

### Phase 4: Send Certified Mail
> Awaiting SFTP credentials

| Step | Status | Notes |
|------|--------|-------|
| [ ] Receive SFTP credentials | | From mail vendor |
| [ ] Configure SFTP connection | | Test connectivity |
| [ ] Test letter upload | | Verify format accepted |
| [ ] Test tracking download | | Verify status updates |
| [ ] Enable scheduled jobs | | Activate automation |
| [ ] Document process | | |

### Twilio SMS Delivery
> A2P 10DLC campaign pending approval

| Step | Status | Notes |
|------|--------|-------|
| [ ] A2P campaign approved | | Check Twilio console |
| [ ] Add `TWILIO_MESSAGING_SERVICE_SID` secret | | MG6206ea74bd1b776c53a879c0862c68d5 |
| [ ] Test SMS delivery | | Verify messages arrive |
| [ ] Enable SMS automations | | Activate workflows |

---

## How to Use This Checklist

1. **Pick a feature** from the list above
2. **Check off steps** as you complete them
3. **Run tests** after implementation
4. **Update this file** with status and notes
5. **Move to next feature**

### Commit Convention
When completing a feature:
```
feat: [Phase X.Y] Feature Name - brief description
```

Example:
```
feat: [Phase 5.1] Affiliate Dashboard - track referrals and payouts
```

---

*Last updated: 2026-01-01*
