# Client Journey Workflow - Implementation Plan

> **Status**: Planning
> **Created**: 2026-01-02
> **Priority**: HIGH - Core Business Flow

---

## Overview

Implement a staged client journey from free analysis to full portal access, with CROA compliance and automated payment collection.

---

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: LEAD CAPTURE (/get-started)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  User provides:                                                             │
│    - Name, Email, Phone                                                     │
│    - OPTION A: Upload credit report PDF                                     │
│    - OPTION B: Enter credit monitoring credentials                          │
│    - OPTION C: "Don't have one?" → Affiliate link ($1 trial, $39.99/mo)     │
│                                                                             │
│  System creates: Client record with dispute_status = 'lead'                 │
│  NO login required yet                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: FREE ANALYSIS PAGE (/analysis/<token>)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Displays (teaser - NOT full breakdown):                                    │
│    - "14 negative items found"                                              │
│    - "6 potential FCRA violations detected"                                 │
│    - "Estimated value: $8,000 - $24,000"                                    │
│    - Bureau analyzed (just one for free)                                    │
│                                                                             │
│  CTAs:                                                                      │
│    - [Book Free Consultation] → Calendly                                    │
│    - [Ready to Start] → Triggers portal invite flow                         │
│                                                                             │
│  NO portal access yet - just this single page                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                        (Call with sales/intake team)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: PORTAL INVITE + $150 HOLD                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Staff clicks "Send Portal Invite" or client clicks "Ready to Start"       │
│                                                                             │
│  Client receives email:                                                     │
│    - Link to create portal password                                         │
│    - Explains next steps                                                    │
│                                                                             │
│  Client creates password and enters portal                                  │
│                                                                             │
│  First screen: Payment hold page                                            │
│    - "To reserve your spot, we place a $150 hold (not charged yet)"         │
│    - Enter card details → Stripe creates authorization hold                 │
│    - On success → proceed to onboarding                                     │
│                                                                             │
│  Client status: dispute_status = 'onboarding'                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: ONBOARDING (Limited Portal Access)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Client can ONLY see:                                                       │
│    ✅ Onboarding wizard                                                     │
│    ✅ CROA Agreement signing (7 documents)                                  │
│    ✅ Profile page (to update info)                                         │
│    ✅ Logout                                                                │
│                                                                             │
│  Client CANNOT see:                                                         │
│    ❌ Dashboard                                                             │
│    ❌ Full analysis                                                         │
│    ❌ Case status                                                           │
│    ❌ Documents                                                             │
│    ❌ Timeline                                                              │
│                                                                             │
│  Onboarding steps:                                                          │
│    1. Personal Information                                                  │
│    2. ID Documents (front/back)                                             │
│    3. SSN Card                                                              │
│    4. Proof of Address                                                      │
│    5. Credit Monitoring Credentials (for ongoing access)                    │
│    6. CROA Agreements (7 docs) ← Links to /portal/agreements                │
│    7. Payment Confirmation (shows hold, explains day 3 charge)              │
│                                                                             │
│  After CROA signed: dispute_status = 'pending_payment'                      │
│  cancellation_period_ends_at = NOW + 3 business days                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                        (3 Business Day CROA Period)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: AUTO-CHARGE + FULL ACCESS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Day 3 (automated):                                                         │
│    - Capture the $150 hold                                                  │
│    - Charge remaining balance (or setup subscription)                       │
│    - Update dispute_status = 'active'                                       │
│    - Send "Welcome! Your case is now active" email                          │
│                                                                             │
│  Client can now see EVERYTHING:                                             │
│    ✅ Dashboard                                                             │
│    ✅ Full 3-bureau analysis                                                │
│    ✅ Case status & progress                                                │
│    ✅ Documents                                                             │
│    ✅ Timeline/Journey                                                      │
│    ✅ All portal features                                                   │
│                                                                             │
│  If card declines:                                                          │
│    - dispute_status = 'payment_failed'                                      │
│    - Access reverts to limited (onboarding view)                            │
│    - Send "Payment failed" email with retry link                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `templates/free_analysis.html` | Teaser analysis page (no login required) |
| `services/free_analysis_service.py` | Generate teaser from PDF/report |
| `services/payment_hold_service.py` | Stripe hold/capture logic |
| `templates/portal/payment_hold.html` | $150 hold capture page |

---

## Files to Modify

| File | Changes |
|------|---------|
| `database.py` | Add `client_stage`, `payment_hold_id`, `payment_due_date` fields |
| `templates/get_started.html` | Add PDF upload option, affiliate link |
| `app.py` | Add `/analysis/<token>` route, modify lead capture |
| `routes/portal.py` | Add stage-based access control to all routes |
| `templates/portal/base_portal.html` | Conditionally show/hide nav based on stage |
| `templates/portal/onboarding.html` | Add payment confirmation step |
| `services/stripe_client.py` | Add `create_hold()`, `capture_hold()`, `release_hold()` |
| `CLAUDE.md` | Document new workflow |
| `ARCHITECTURE.md` | Add new models and services |

---

## Database Changes

### New Fields on Client Model

```python
# Client stage tracking
client_stage = Column(String(20), default='lead')
# Values: 'lead', 'onboarding', 'pending_payment', 'active', 'payment_failed', 'cancelled'

# Payment hold tracking
payment_hold_id = Column(String(100))  # Stripe PaymentIntent ID for hold
payment_hold_amount = Column(Integer)  # Amount in cents (15000 = $150)
payment_hold_created_at = Column(DateTime)
payment_due_date = Column(DateTime)  # 3 days after CROA signed

# Free analysis tracking
free_analysis_token = Column(String(64))  # Token for /analysis/<token> page
free_analysis_viewed_at = Column(DateTime)
```

---

## Portal Access Matrix

| Page | lead | onboarding | pending_payment | active | payment_failed |
|------|------|------------|-----------------|--------|----------------|
| `/portal/` (dashboard) | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/portal/onboarding` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `/portal/agreements` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `/portal/profile` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `/portal/status` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/portal/documents` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/portal/timeline` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/portal/learn` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/analysis/<token>` | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## API Endpoints to Add

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /api/leads/upload-report` | POST | Upload PDF for free analysis |
| `GET /analysis/<token>` | GET | View free analysis (public, token-based) |
| `POST /portal/api/payment-hold` | POST | Create $150 hold |
| `POST /api/webhooks/payment-due` | POST | Cron job to capture holds on day 3 |
| `POST /portal/api/retry-payment` | POST | Retry failed payment |

---

## Scheduled Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| `capture_due_payments` | Every hour | Find clients where `payment_due_date < NOW` and capture holds |
| `expire_stale_holds` | Daily | Release holds older than 7 days if onboarding not complete |
| `send_payment_reminders` | Daily | Email clients with upcoming payment (day 2 reminder) |

---

## Implementation Order

1. **Database changes** - Add new fields to Client model
2. **Free analysis page** - `/analysis/<token>` with teaser view
3. **Update `/get-started`** - PDF upload + affiliate link
4. **Portal access control** - Stage-based routing in `portal.py`
5. **Payment hold page** - $150 authorization before onboarding
6. **Auto-capture job** - Day 3 charge automation
7. **Update nav/UI** - Show/hide based on stage
8. **Testing** - E2E tests for full flow
9. **Documentation** - Update CLAUDE.md, ARCHITECTURE.md

---

## Questions Resolved

| Question | Decision |
|----------|----------|
| How to get report for free analysis? | Upload PDF OR enter credentials OR affiliate signup |
| When is hold placed? | After call, when they start onboarding |
| When is payment captured? | Day 3 after CROA signed (auto) |
| What if payment fails? | Revert to limited access, send retry email |
| What can onboarding clients see? | Only: onboarding, agreements, profile |

---

## Affiliate Link Details

For clients without credit monitoring:
- **Link**: Partner affiliate URL (IdentityIQ, SmartCredit, etc.)
- **Trial**: $1 for 7 days
- **After trial**: $39.99/month
- **If they sign up with us**: We cancel it for them (part of service)
