# Pricing Structure - Brightpath Ascend

> **Last Updated**: 2026-01-02
> **Status**: CONFIRMED

---

## Overview

All dispute letters are sent via **Certified Mail** using SendCertifiedMail.com.
- **Certified Mail Cost**: $11-15 per letter
- **Settlement Fee**: 30% of any settlement won

---

## Client Journey Pricing

### Stage 1: Free Teaser Analysis
| Item | Price |
|------|-------|
| Upload credit report PDF | FREE |
| Basic analysis (1 bureau) | FREE |
| Shows: # of items, violations found, potential value | FREE |
| **TOTAL** | **$0** |

### Stage 2: Full Analysis
| Item | Price |
|------|-------|
| Complete 3-bureau analysis | Included |
| Item-by-item breakdown | Included |
| Dispute strategy & game plan | Included |
| Priority items identified | Included |
| **TOTAL** | **$199** |

*If client proceeds to full program, $199 is credited toward Round 1*

### Stage 3: Credit Repair Program

| Round | Price | Notes |
|-------|-------|-------|
| **Round 1** | $497 | MINUS $199 analysis credit = **$298 due** |
| **Round 2** | $297 | Charged when letters sent |
| **Round 3** | $297 | Charged when letters sent |
| **Round 4** | $297 | Charged when letters sent |
| **Round 5** | $297 | Charged when letters sent |
| **Round 6** | $297 | If needed |

### Settlement Fee
| Settlement Amount | Fee |
|-------------------|-----|
| Any amount | **30%** of settlement |

*Example: $15,000 settlement = $4,500 fee*

---

## Total Program Costs

| Scenario | Rounds | Calculation | Total |
|----------|--------|-------------|-------|
| **Quick case** | 2 rounds | $199 + $298 + $297 | **$794** |
| **Average case** | 4 rounds | $199 + $298 + ($297 × 3) | **$1,388** |
| **Complex case** | 6 rounds | $199 + $298 + ($297 × 5) | **$1,982** |

---

## Prepay Discount Packages

For clients who want to pay upfront and save:

| Package | Includes | Normal Price | Prepay Price | Savings |
|---------|----------|--------------|--------------|---------|
| **Starter** | Analysis + 2 rounds | $794 | $749 | $45 (6%) |
| **Standard** | Analysis + 4 rounds | $1,388 | $1,295 | $93 (7%) |
| **Complete** | Analysis + 6 rounds | $1,982 | $1,795 | $187 (9%) |
| **Unlimited** | Analysis + unlimited | N/A | $2,000 | Best value |

---

## Financing Option

For clients who want to finance the prepay packages:

| Package | Prepay Price | Financed Price | Admin Fee |
|---------|--------------|----------------|-----------|
| Standard | $1,295 | $1,495 | +$200 |
| Complete | $1,795 | $1,995 | +$200 |
| Unlimited | $2,000 | $2,200 | +$200 |

*Financing available through Affirm/Klarna or in-house payment plan*

---

## Payment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Free Teaser                                            │
│  Client uploads PDF → Sees teaser → "Want full analysis?"       │
│  Payment: $0                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Full Analysis                                          │
│  Client pays $199 → Gets complete breakdown                     │
│  Payment: $199 (Stripe charge)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Decide to Proceed                                      │
│  Client wants to work with us → Portal invite sent              │
│  $199 will be credited toward Round 1                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Onboarding + CROA Signing                              │
│  Client completes onboarding → Signs 7 CROA documents           │
│  Card on file collected (for future charges)                    │
│  3-day CROA cancellation period begins                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Round 1 Payment + Letters Sent                         │
│  Day 3 (after CROA period): Charge $298 ($497 - $199 credit)    │
│  Round 1 dispute letters sent via certified mail                │
│  Full portal access unlocked                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    (30-45 days waiting for responses)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Round 2+ Payment + Letters Sent                        │
│  Staff clicks "Send Round 2"                                    │
│  System charges $297 → If success → Letters sent                │
│  If payment fails → Letters NOT sent → Client notified          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    (Repeat until case complete)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Case Complete                                          │
│  No more disputable items OR client satisfied                   │
│  If settlement won: 30% fee charged                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Your Costs (Margin Analysis)

### Per-Letter Cost
| Expense | Cost |
|---------|------|
| SendCertifiedMail.com | $11-15/letter |
| Typical round (5 letters) | $55-75 |

### Margin by Round
| Round | Client Pays | Your Cost | Gross Margin |
|-------|-------------|-----------|--------------|
| Full Analysis | $199 | ~$10 (AI) | ~$189 (95%) |
| Round 1 | $298 | ~$75 | ~$223 (75%) |
| Round 2+ | $297 | ~$75 | ~$222 (75%) |

### Full Case Margin (4 rounds)
| Item | Revenue | Cost | Margin |
|------|---------|------|--------|
| Analysis | $199 | $10 | $189 |
| Round 1 | $298 | $75 | $223 |
| Round 2 | $297 | $75 | $222 |
| Round 3 | $297 | $75 | $222 |
| Round 4 | $297 | $75 | $222 |
| **TOTAL** | **$1,388** | **$310** | **$1,078 (78%)** |

---

## System Implementation

### Database Fields Needed
```python
# On Client model
client_stage = Column(String(20))  # lead, analysis_paid, onboarding, active, payment_failed
analysis_payment_id = Column(String(100))  # Stripe payment for $199
analysis_paid_at = Column(DateTime)
analysis_credit_applied = Column(Boolean, default=False)
round_1_amount_due = Column(Integer)  # 29800 cents ($497 - $199 = $298)
```

### Stripe Integration
- `create_analysis_payment($199)` - One-time charge for full analysis
- `create_round_payment($amount)` - Charge when round is sent
- `create_subscription()` - For prepay packages (optional)

---

## Confirmed Decisions

| Decision | Value |
|----------|-------|
| Free teaser | ✅ Yes |
| Full analysis price | **$199** |
| Analysis credit toward Round 1 | ✅ Yes |
| Round 1 price | **$497** ($298 after credit) |
| Round 2+ price | **$297** |
| Settlement fee | **30%** |
| Charge timing | When letters are sent |
| Prepay discount | 6-9% off |
| Financing upcharge | +$200 |
