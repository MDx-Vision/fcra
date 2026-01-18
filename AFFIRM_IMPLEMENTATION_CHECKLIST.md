# Affirm BNPL Implementation Checklist

> Buy Now, Pay Later integration for Brightpath Ascend Group
>
> **Created**: 2026-01-18
> **Status**: 🔄 IN PROGRESS

---

## Overview

Affirm allows clients to pay over 3-12 months while you get paid immediately.

**Example - $497 Round 1:**
| Plan | Monthly Payment | Client Pays | You Receive |
|------|-----------------|-------------|-------------|
| 3 months | ~$166/mo | $497 | $466.88 |
| 6 months | ~$83/mo | $497 | $466.88 |
| 12 months | ~$42/mo | $497 | $466.88 |

**Merchant Fee:** ~6% + $0.30 (~$30 on $497)

**Benefits:**
- Clients can afford services they couldn't pay upfront
- You get paid immediately (Affirm takes the risk)
- Affirm reports to Experian (helps clients build credit!)
- Higher conversion rates (20-30% increase typical)

---

## Phase 1: Affirm Merchant Account Setup

### 1.1 Apply for Affirm Merchant Account
- [ ] Go to https://www.affirm.com/business
- [ ] Click "Get Started" or "Contact Sales"
- [ ] Fill out merchant application:
  - Business name: Brightpath Ascend Group
  - Industry: Financial Services / Credit Restoration
  - Average order value: $497-$2,000
  - Monthly volume estimate: $_____
  - Website: https://brightpathascendgroup.com
- [ ] Submit application
- [ ] Wait for approval (typically 1-3 business days)

### 1.2 Receive Affirm Credentials
- [ ] Receive email with merchant portal access
- [ ] Log into Affirm Merchant Portal
- [ ] Get API credentials:
  - [ ] Public API Key: `_____________`
  - [ ] Private API Key: `_____________`
  - [ ] Sandbox keys for testing: `_____________`
- [ ] Note your Merchant ID: `_____________`

### 1.3 Configure Affirm Settings
- [ ] Set minimum order amount ($50 recommended)
- [ ] Set maximum order amount ($17,500 max)
- [ ] Configure financing options (3, 6, 12 months)
- [ ] Set up webhook URL for payment notifications
- [ ] Upload business logo for Affirm checkout

---

## Phase 2: Backend Integration

### 2.1 Install Affirm SDK
```bash
pip install affirm-python  # or use requests for REST API
```
- [ ] Add to requirements.txt
- [ ] Test import works

### 2.2 Create Affirm Service
- [ ] Create `services/affirm_service.py`
- [ ] Implement functions:
  - [ ] `create_checkout()` - Create Affirm checkout for order
  - [ ] `capture_charge()` - Capture authorized payment
  - [ ] `void_charge()` - Void uncaptured authorization
  - [ ] `refund_charge()` - Process refund
  - [ ] `get_charge_status()` - Check payment status

### 2.3 Environment Variables
- [ ] Add to `.env`:
```bash
AFFIRM_PUBLIC_KEY=your_public_key
AFFIRM_PRIVATE_KEY=your_private_key
AFFIRM_ENVIRONMENT=sandbox  # or 'production'
```
- [ ] Add to `services/config.py`

### 2.4 Database Updates
- [ ] Add to Client model or create AffirmPayment model:
  - [ ] `affirm_checkout_token` - Checkout session ID
  - [ ] `affirm_charge_id` - Captured charge ID
  - [ ] `affirm_status` - pending, captured, voided, refunded
- [ ] Create migration

### 2.5 API Endpoints
- [ ] `POST /api/payment/affirm/create` - Create Affirm checkout
- [ ] `POST /api/payment/affirm/confirm` - Confirm after user approval
- [ ] `POST /api/payment/affirm/capture` - Capture authorized charge
- [ ] `POST /api/webhooks/affirm` - Handle Affirm webhooks
- [ ] `GET /api/payment/affirm/status/:charge_id` - Check status

---

## Phase 3: Frontend Integration

### 3.1 Add Affirm.js Script
- [ ] Add to `templates/portal/base_portal.html`:
```html
<script src="https://cdn1.affirm.com/js/v2/affirm.js"></script>
<script>
  affirm.ui.ready(function() {
    affirm.ui.refresh();
  });
</script>
```

### 3.2 Update Payment UI
- [ ] Update `templates/portal/onboarding.html`:
  - [ ] Add "Pay over time with Affirm" option
  - [ ] Show monthly payment estimates
  - [ ] Add Affirm promotional messaging

### 3.3 Checkout Flow
- [ ] Create Affirm checkout button/option
- [ ] Handle Affirm popup/redirect flow
- [ ] Handle success callback
- [ ] Handle cancel callback
- [ ] Show confirmation on success

### 3.4 Monthly Payment Calculator
- [ ] Add payment calculator widget
- [ ] Show "As low as $X/month" messaging
- [ ] Use Affirm's promo messaging API

---

## Phase 4: Webhook Handling

### 4.1 Webhook Events to Handle
- [ ] `charge.created` - Authorization created
- [ ] `charge.captured` - Payment captured
- [ ] `charge.voided` - Authorization voided
- [ ] `charge.refunded` - Refund processed
- [ ] `charge.failed` - Payment failed

### 4.2 Webhook Security
- [ ] Implement signature verification
- [ ] Log all webhook events
- [ ] Handle duplicate events (idempotency)

### 4.3 Webhook Actions
- [ ] On `charge.captured`:
  - [ ] Update client payment status
  - [ ] Update client stage (if applicable)
  - [ ] Send confirmation email
  - [ ] Log to timeline

---

## Phase 5: Testing

### 5.1 Sandbox Testing
- [ ] Set `AFFIRM_ENVIRONMENT=sandbox`
- [ ] Test checkout creation
- [ ] Test successful payment flow
- [ ] Test declined payment
- [ ] Test cancellation
- [ ] Test webhook handling
- [ ] Test refund flow

### 5.2 Test Scenarios
| Scenario | Test Card/Method | Expected Result |
|----------|------------------|-----------------|
| Approved | Use sandbox credentials | Checkout succeeds |
| Declined | Trigger decline in sandbox | Error message shown |
| Cancel | User clicks cancel | Return to payment selection |
| Refund | Process refund | Charge refunded |

### 5.3 Unit Tests
- [ ] Create `tests/test_affirm_service.py`
- [ ] Test all service functions
- [ ] Test webhook handlers
- [ ] Mock Affirm API responses
- [ ] Run full regression suite

---

## Phase 6: Go Live

### 6.1 Pre-Launch Checklist
- [ ] Switch to production API keys
- [ ] Update webhook URL to production
- [ ] Test one real transaction (small amount)
- [ ] Verify funds received in merchant account
- [ ] Update documentation

### 6.2 Monitoring
- [ ] Set up error alerts for failed payments
- [ ] Monitor conversion rates by payment method
- [ ] Track average order value changes
- [ ] Monitor Affirm merchant dashboard

---

## Implementation Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Merchant Account | ⏳ Pending | Need to apply |
| Phase 2: Backend | ✅ COMPLETE | affirm_service.py, config, database, API endpoints |
| Phase 3: Frontend | ⏳ Pending | |
| Phase 4: Webhooks | ✅ COMPLETE | Included in Phase 2 backend work |
| Phase 5: Testing | ✅ COMPLETE | 33 unit tests passing |
| Phase 6: Go Live | ⏳ Pending | Need merchant account first |

---

## Files to Create/Modify

| File | Action | Description | Status |
|------|--------|-------------|--------|
| `services/affirm_service.py` | CREATE | Affirm API integration | ✅ DONE |
| `tests/test_affirm_service.py` | CREATE | Unit tests (33 tests) | ✅ DONE |
| `database.py` | MODIFY | Add Affirm payment fields | ✅ DONE |
| `app.py` | MODIFY | Add Affirm API endpoints (7 endpoints) | ✅ DONE |
| `services/config.py` | MODIFY | Add Affirm config | ✅ DONE |
| `templates/portal/onboarding.html` | MODIFY | Add Affirm payment option | ⏳ Pending |
| `templates/portal/base_portal.html` | MODIFY | Add Affirm.js script | ⏳ Pending |
| `requirements.txt` | MODIFY | Add Affirm SDK (if using) | N/A (using requests) |
| `.env.example` | MODIFY | Add Affirm env vars | ⏳ Pending |

---

## Resources

- Affirm Merchant Portal: https://www.affirm.com/business
- Affirm Developer Docs: https://docs.affirm.com/
- Affirm API Reference: https://docs.affirm.com/affirm-developers/reference
- Affirm.js Integration: https://docs.affirm.com/affirm-developers/docs/affirm-js

---

## Notes

- Affirm approval typically takes 1-3 business days
- Must have live website with SSL
- Credit restoration services should be approved (verify during application)
- Minimum ticket: $50, Maximum: $17,500
- Affirm reports to Experian - great for your clients!

---

*Last Updated: 2026-01-18*
