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

### 5.1 Affiliate Dashboard ✅ COMPLETE
> Track referral signups, commissions, payout history

| Step | Status | Notes |
|------|--------|-------|
| [x] Plan implementation | ✅ | Database models, API endpoints, UI |
| [x] Create `Affiliate` model | ✅ | Already existed in database.py |
| [x] Create `Commission` model | ✅ | Already existed in database.py |
| [x] Create `AffiliatePayout` model | ✅ | Added to database.py |
| [x] Create `AffiliateService` | ✅ | services/affiliate_service.py (550+ lines) |
| [x] API: `/api/affiliates` CRUD | ✅ | Already existed with full CRUD |
| [x] API: `/api/affiliates/commissions` | ✅ | Track commissions per affiliate |
| [x] API: `/api/affiliates/payouts` | ✅ | Payout management |
| [x] Template: `affiliate_dashboard.html` | ✅ | Stats, referrals, payouts, tabs |
| [x] Write unit tests | ✅ | 48 tests passing |
| [ ] Write Cypress tests | | Optional |
| [x] Finalize & document | ✅ | Sidebar link already present |

### 5.2 Lead Scoring ✅ COMPLETE
> Auto-prioritize leads based on credit report severity

| Step | Status | Notes |
|------|--------|-------|
| [x] Plan scoring algorithm | ✅ | Collections, charge-offs, public records, violations |
| [x] Add `lead_score` field to Client | ✅ | Integer 0-100 + factors JSON |
| [x] Create `LeadScoringService` | ✅ | 400+ lines, 5 main methods |
| [x] Add scoring trigger on report upload | ✅ | Auto-score after analysis |
| [x] Update client list to show score | ✅ | Color-coded badges (HIGH/MED/LOW) |
| [x] Write unit tests | ✅ | 29 tests passing |
| [ ] Write Cypress tests | | Optional |
| [x] Finalize & document | ✅ | FEATURE_BACKLOG.md updated |

### 5.3 Onboarding Wizard ✅ COMPLETE
> Step-by-step client setup with progress tracking

| Step | Status | Notes |
|------|--------|-------|
| [x] Plan onboarding steps | ✅ | 7 steps: personal_info, id_documents, ssn_card, proof_of_address, credit_monitoring, agreement, payment |
| [x] Create `OnboardingProgress` model | ✅ | Tracks completion of each step with timestamps |
| [x] Create `OnboardingService` | ✅ | services/onboarding_service.py (280+ lines) |
| [x] Template: `portal/onboarding.html` | ✅ | Step-by-step wizard with modals for each step |
| [x] Add progress indicator to portal nav | ✅ | "Setup" tab with rocket icon |
| [x] Write unit tests | ✅ | 26 tests passing |
| [ ] Write Cypress tests | | Optional |
| [x] Finalize & document | ✅ | API endpoints in routes/portal.py |

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

### 9.1 Email Templates Library ✅ COMPLETE
> Pre-built emails for common scenarios

| Step | Status | Notes |
|------|--------|-------|
| [x] Plan template categories | ✅ | 8 categories: welcome, updates, reminders, notifications, payment, legal, marketing, general |
| [x] Create `EmailTemplate` model | ✅ | Enhanced with name, category, description, variables, is_active fields |
| [x] Create template management UI | ✅ | `/dashboard/email-templates` - Full CRUD UI |
| [x] Add variable system | ✅ | 10 common variables with {name} substitution |
| [x] Create EmailTemplateService | ✅ | CRUD + render + duplicate + seed |
| [x] Add API endpoints | ✅ | GET/POST/PUT/DELETE + render + duplicate + seed |
| [x] Write unit tests | ✅ | 48 tests passing |
| [ ] Write Cypress tests | | Optional |
| [x] Finalize & document | ✅ | Sidebar link added, checklist updated |

### 9.2 Drip Campaigns ✅ COMPLETE
> Automated follow-up sequences

| Step | Status | Notes |
|------|--------|-------|
| [x] Create `DripCampaign` model | ✅ | name, trigger, steps, send window |
| [x] Create `DripStep` model | ✅ | campaign_id, delay_days, template_id |
| [x] Create `DripEnrollment` model | ✅ | campaign_id, client_id, current_step, status |
| [x] Create `DripEmailLog` model | ✅ | Track sent emails for opens/clicks |
| [x] Create `DripCampaignService` | ✅ | 1,090 lines, full CRUD + enrollment |
| [x] Add 22 API endpoints | ✅ | Campaign, step, enrollment management |
| [x] Create campaign builder UI | ✅ | `/dashboard/drip-campaigns` |
| [x] Add scheduled job for sending | ✅ | "Process Drip Campaign Emails" - hourly |
| [x] Write unit tests | ✅ | 40 tests passing |
| [ ] Write Cypress tests | | Optional |
| [x] Finalize & document | ✅ | FEATURE_BACKLOG.md updated |

### 9.3 SMS Templates ✅ COMPLETE
> Quick-send common messages

| Step | Status | Notes |
|------|--------|-------|
| [x] Create `SMSTemplate` model | ✅ | template_type, name, message, category, variables, is_custom, is_active |
| [x] Create `SMSTemplateService` | ✅ | Full CRUD + render + duplicate + seed |
| [x] Add 15 API endpoints | ✅ | GET/POST/PUT/DELETE + categories, variables, stats, render, seed, send |
| [x] Create template management UI | ✅ | `/dashboard/sms-templates` - Full CRUD + char counter + preview |
| [x] Integrate with SMS service | ✅ | `/api/sms-templates/send` endpoint |
| [x] Write unit tests | ✅ | 65 tests passing |
| [x] Finalize & document | ✅ | Sidebar link added, 10 default templates seeded |

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
