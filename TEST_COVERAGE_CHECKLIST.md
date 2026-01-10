# Test Coverage Improvement Checklist

**Created**: 2026-01-05
**Status**: In Progress
**Goal**: Achieve comprehensive test coverage for all critical services

---

## Critical Services (No Tests - HIGHEST PRIORITY)

### Payment & Financial Services
- [ ] `test_client_payment_service.py` (~50 tests)
  - [ ] Payment intent creation (analysis, round 1-4, prepay)
  - [ ] Payment confirmation and credit application
  - [ ] Pricing calculations ($199 credit, prepay discounts)
  - [ ] Error handling (invalid client, payment failures)
  - [ ] Charge saved payment methods
  - [ ] Settlement fee calculations (30%)

- [ ] `test_stripe_webhooks_service.py` (~30 tests)
  - [ ] payment_intent.succeeded handler
  - [ ] payment_intent.payment_failed handler
  - [ ] charge.refunded handler
  - [ ] checkout.session.completed handler
  - [ ] Webhook signature verification
  - [ ] Idempotency handling
  - [ ] Error recovery scenarios

- [ ] `test_payment_plan_service.py` (~35 tests)
  - [ ] Plan creation with various frequencies
  - [ ] Installment calculations
  - [ ] Due date calculations
  - [ ] Payment processing
  - [ ] Plan status transitions
  - [ ] Overdue handling

### AI & Content Generation
- [ ] `test_ai_dispute_writer_service.py` (~40 tests)
  - [ ] Round 1 letter generation (initial disputes)
  - [ ] Round 2 letter generation (follow-up)
  - [ ] Round 3 letter generation (escalation)
  - [ ] Round 4 letter generation (legal threats)
  - [ ] Bureau-specific formatting (Equifax, Experian, TransUnion)
  - [ ] Context gathering from credit reports
  - [ ] AI API error handling
  - [ ] Invalid/missing data scenarios

### Batch & Scheduled Operations
- [ ] `test_batch_processing_service.py` (~40 tests)
  - [ ] Batch job creation
  - [ ] All 10 action types execution
  - [ ] Partial failure handling
  - [ ] Progress tracking
  - [ ] Error recovery
  - [ ] Job cancellation

- [ ] `test_scheduled_jobs_service.py` (~30 tests)
  - [ ] capture_due_payments job
  - [ ] expire_stale_holds job
  - [ ] send_payment_reminders job
  - [ ] get_pending_activations
  - [ ] run_all_jobs
  - [ ] Date/time edge cases

### Notifications & Communication
- [ ] `test_push_notification_service.py` (~30 tests)
  - [ ] VAPID key generation
  - [ ] Subscription management
  - [ ] Notification sending
  - [ ] Multiple notification types
  - [ ] Error handling
  - [ ] Subscription cleanup

### Business Logic Services
- [ ] `test_free_analysis_service.py` (~25 tests)
  - [ ] Lead creation from upload
  - [ ] Teaser analysis generation
  - [ ] Token management
  - [ ] mark_analysis_paid flow
  - [ ] proceed_to_onboarding flow

- [ ] `test_roi_calculator_service.py` (~20 tests)
  - [ ] Client ROI calculations
  - [ ] Affiliate ROI calculations
  - [ ] Time period comparisons
  - [ ] Edge cases (zero values, negative values)

- [ ] `test_client_success_service.py` (~25 tests)
  - [ ] Client lifecycle management
  - [ ] Success metrics tracking
  - [ ] Status transitions
  - [ ] Milestone tracking

- [ ] `test_staff_performance_service.py` (~25 tests)
  - [ ] Performance metrics calculation
  - [ ] Staff comparison
  - [ ] Time period analysis
  - [ ] Goal tracking

---

## Integration Tests (Multi-Service Workflows)

- [ ] `tests/integration/test_client_journey_flow.py` (~20 tests)
  - [ ] Lead capture → Analysis → Payment → Active client
  - [ ] CROA signing workflow
  - [ ] Letter generation and sending

- [ ] `tests/integration/test_payment_workflow.py` (~15 tests)
  - [ ] Analysis payment → Credit application → Round 1 payment
  - [ ] Prepay package checkout
  - [ ] Payment failure recovery

- [ ] `tests/integration/test_dispute_workflow.py` (~15 tests)
  - [ ] Credit import → Analysis → Letter generation
  - [ ] Round progression (R1 → R2 → R3 → R4)
  - [ ] Response handling

---

## Documentation Updates

- [ ] Update CLAUDE.md with test coverage status
- [ ] Update/Create CONVERSATION_LOG.md
- [ ] Commit all changes with descriptive message

---

## Progress Summary

| Category | Target Tests | Created | Passing |
|----------|--------------|---------|---------|
| Payment Services | 115 | 0 | 0 |
| AI/Content | 40 | 0 | 0 |
| Batch/Scheduled | 70 | 0 | 0 |
| Notifications | 30 | 0 | 0 |
| Business Logic | 95 | 0 | 0 |
| Integration | 50 | 0 | 0 |
| **TOTAL** | **400** | **0** | **0** |

---

## Completion Log

*Updates will be added as tests are completed*

