# Payment Options Research

> Research on Stripe alternatives and BNPL integration for Brightpath Ascend Group
>
> **Created**: 2026-01-18

---

## Current Setup: Stripe

| Fee Type | Rate |
|----------|------|
| Online card transactions | 2.9% + $0.30 |
| ACH bank transfers | 0.8% (max $5) |
| Recurring/subscriptions | 2.9% + $0.30 |
| Dispute fee | $15 + $15 counter fee = $30 |

**On a $497 Round 1 payment:**
- Stripe fee: $14.71 (2.96%)
- You receive: $482.29

---

## Stripe Alternatives Comparison

### 1. Square
| Fee Type | Rate | vs Stripe |
|----------|------|-----------|
| Online | 2.9% + $0.30 | Same |
| Keyed-in | 3.5% + $0.15 | Worse |
| Chargebacks | $0 | **Better** |
| Recurring | 2.9% + $0.30 | Same |

**Verdict:** Similar fees, but no chargeback fees. Less developer-friendly.

### 2. Stax (formerly Fattmerchant)
| Fee Type | Rate |
|----------|------|
| Monthly fee | $99-$199/month |
| Per transaction | Interchange + 0% markup |
| Typical effective rate | 1.5-2.2% |

**Best for:** $10k+/month volume. Break-even at ~$5k/month.

**On $497 payment:** ~$9.94 (2%) = Save ~$5/transaction

### 3. Helcim
| Fee Type | Rate |
|----------|------|
| Online | Interchange + 0.4% + $0.25 |
| Volume discounts | Yes, automatic |
| Monthly fee | $0 |

**Typical effective rate:** 2.2-2.5%

**Best for:** Growing businesses, no monthly commitment.

### 4. PayPal / Braintree
| Fee Type | Rate |
|----------|------|
| Standard | 2.99% + $0.49 |
| With Braintree | 2.59% + $0.49 |

**Verdict:** Higher per-transaction fee, but brand recognition helps conversions.

### 5. Authorize.net
| Fee Type | Rate |
|----------|------|
| Monthly | $25/month |
| Per transaction | 2.9% + $0.30 |

**Verdict:** Similar to Stripe with monthly fee. Good for established businesses.

---

## Recommendation: Keep Stripe + Add Options

**Why keep Stripe:**
1. Already integrated and tested
2. Excellent recurring billing (critical for your model)
3. Strong API, webhook support
4. Instant payouts available
5. Good fraud protection

**How to reduce effective fees:**
1. **Add ACH option** - Only 0.8% (max $5) vs 2.9%
2. **Volume negotiations** - At $100k+/month, Stripe negotiates custom rates
3. **Add BNPL** - Shifts fee to BNPL provider, increases conversions

---

## BNPL Integration Options

### Why BNPL for Credit Restoration?

Your clients are rebuilding credit - they often can't afford $497 upfront. BNPL:
- Increases conversion rates 20-30%
- Increases average order value
- You get paid immediately, in full
- Customer pays over time

### Top BNPL Providers

#### 1. Affirm (Recommended)
| Feature | Details |
|---------|---------|
| Merchant fee | ~6% + $0.30 |
| Terms | 3, 6, 12, 36 months |
| Ticket size | $50 - $17,500 |
| Credit check | Soft pull, won't hurt client's score |
| Integration | API or Shopify/WooCommerce plugin |

**Why Affirm for BAG:**
- Handles higher ticket items ($497, $1,295 packages)
- Longer payment terms (clients need flexibility)
- Clear, honest fees (no late fees to customers)
- Reports to Experian (helps clients build credit!)

**$497 Round 1 with Affirm:**
- Merchant fee: ~$30.12 (6.06%)
- You receive: $466.88
- Client pays: $497 split over 3-12 months

#### 2. Klarna
| Feature | Details |
|---------|---------|
| Merchant fee | Custom pricing (~3.5-6%) |
| Terms | Pay in 4, or financing |
| Ticket size | Up to $10,000 |
| Best for | Fashion, retail |

**Considerations:**
- Requires $3M+ annual volume for best rates
- More focused on retail/e-commerce

#### 3. Afterpay
| Feature | Details |
|---------|---------|
| Merchant fee | ~4-6% |
| Terms | Pay in 4 (6 weeks) |
| Ticket size | Up to $2,000 |
| Best for | Smaller purchases |

**Considerations:**
- Shorter terms only (6 weeks)
- Better for smaller ticket items

#### 4. Sezzle
| Feature | Details |
|---------|---------|
| Merchant fee | 6% + $0.30 |
| Terms | Pay in 4 |
| Ticket size | No minimum |
| Integration | Easy API |

**Good for:** Smaller businesses, easy setup.

---

## Recommended Payment Stack for BAG

```
Primary: Stripe (current)
├── Credit/Debit cards (2.9% + $0.30)
├── ACH bank transfer (0.8%, max $5) ← ADD THIS
└── Recurring subscriptions

BNPL: Affirm (add this)
├── 3-month financing
├── 6-month financing
└── 12-month financing

Future consideration:
├── Square (backup processor)
└── Stax (if volume exceeds $50k/month)
```

---

## Implementation Plan

### Phase 1: Add ACH Payments (Quick Win)
Already supported by Stripe. Just need to:
1. Add bank account option to checkout
2. Offer small discount for ACH (save ~2% on fees)

**Savings:** $10+ per transaction on $497 payments

### Phase 2: Add Affirm BNPL
1. Apply for Affirm merchant account
2. Integrate Affirm API into checkout
3. Display "Pay over time" option
4. Test thoroughly

**Timeline:** 2-3 weeks for integration

### Phase 3: Monitor & Optimize
1. Track conversion rates by payment method
2. Calculate effective fees per method
3. Consider Stax if volume exceeds $50k/month

---

## Fee Comparison Summary

| Payment Method | Fee on $497 | You Receive | Client Pays |
|----------------|-------------|-------------|-------------|
| Stripe (card) | $14.71 (2.96%) | $482.29 | $497 now |
| Stripe (ACH) | $3.98 (0.8%) | $493.02 | $497 now |
| Affirm (BNPL) | ~$30.12 (6%) | $466.88 | $497 over time |
| Square (card) | $14.71 (2.96%) | $482.29 | $497 now |

**Best strategy:**
- Offer 2% discount for ACH → You still save ~1%
- Offer Affirm for clients who need payment plans
- Keep Stripe cards as default

---

## Next Steps

1. [ ] Add ACH payment option to checkout (Stripe already supports)
2. [ ] Apply for Affirm merchant account
3. [ ] Design "Payment Options" UI showing all methods
4. [ ] Test BNPL integration
5. [ ] Monitor conversion rates

---

## Sources

- [Stripe Fees Guide 2025](https://www.swipesum.com/insights/guide-to-stripe-fees-rates-for-2025)
- [Square vs Stripe Comparison](https://tailoredpay.com/blog/stripe-vs-square/)
- [Affirm vs Klarna Comparison](https://withcherry.com/blog/klarna-vs-affirm)
- [Best BNPL Providers 2025](https://www.onrampfunds.com/resources/8-best-bnpl-providers-for-ecommerce-2025)
- [BNPL Merchant Fees](https://www.chargeblast.com/blog/affirm-vs-afterpay-klarna-which-has-lower-merchant-fees)

---

*Last Updated: 2026-01-18*
