# Broken Exhaustive Tests Checklist

> **Created**: 2025-12-30
> **Completed**: 2025-12-30
> **Total**: 41 tests fixed
> **Status**: ✅ ALL COMPLETE - 0 broken files remaining

## Fix Pattern

Each test needs:
1. Add `cy.login()` in `beforeEach()`
2. Keep `cy.visit('/route')` after login
3. Replace login page assertions with actual page assertions
4. Rename from `.broken` back to `.cy.js`

```javascript
// BEFORE (broken)
beforeEach(() => {
  cy.visit('/dashboard/feature');  // Redirects to login!
});

// AFTER (fixed)
beforeEach(() => {
  cy.login('test@example.com', 'testpass123');
  cy.visit('/dashboard/feature');
});
```

---

## Priority 1: Core Business Pages (10 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 1 | `billing_exhaustive` | `/dashboard/billing` | billing_management.html | [x] |
| 2 | `contacts_exhaustive` | `/dashboard/contacts` | contacts.html | [x] |
| 3 | `documents_exhaustive` | `/dashboard/documents` | documents.html | [x] |
| 4 | `settings_exhaustive` | `/dashboard/settings` | settings.html | [x] |
| 5 | `calendar_exhaustive` | `/dashboard/calendar` | calendar.html | [x] |
| 6 | `tasks_exhaustive` | `/dashboard/tasks` | task_queue.html | [x] |
| 7 | `signups_exhaustive` | `/dashboard/signups` | signups.html | [x] |
| 8 | `affiliates_exhaustive` | `/dashboard/affiliates` | affiliates.html | [x] |
| 9 | `settlements_exhaustive` | `/dashboard/settlements` | settlements.html | [x] |
| 10 | `admin_exhaustive` | `/admin` | admin.html | [x] |

## Priority 2: FCRA-Specific Features (12 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 11 | `letter_queue_exhaustive` | `/dashboard/letter-queue` | letter_queue.html | [x] |
| 12 | `credit_import_exhaustive` | `/dashboard/credit-import` | credit_import.html | [x] |
| 13 | `credit_tracker_exhaustive` | `/dashboard/credit-tracker` | credit_tracker.html | [x] |
| 14 | `demand_generator_exhaustive` | `/dashboard/demand-generator` | demand_generator.html | [x] |
| 15 | `furnishers_exhaustive` | `/dashboard/furnishers` | furnishers.html | [x] |
| 16 | `case_law_exhaustive` | `/dashboard/case-law` | case_law.html | [x] |
| 17 | `cfpb_exhaustive` | `/dashboard/cfpb` | cfpb_complaints.html | [x] |
| 18 | `chexsystems_exhaustive` | `/dashboard/chexsystems` | chexsystems.html | [x] |
| 19 | `specialty_bureaus_exhaustive` | `/dashboard/specialty-bureaus` | specialty_bureaus.html | [x] |
| 20 | `triage_exhaustive` | `/dashboard/triage` | triage_dashboard.html | [x] |
| 21 | `sol_exhaustive` | `/dashboard/sol` | sol_dashboard.html | [x] |
| 22 | `frivolousness_exhaustive` | `/dashboard/frivolousness` | frivolousness_tracker.html | [x] |

## Priority 3: Automation & Workflows (7 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 23 | `automation_tools_exhaustive` | `/dashboard/automation` | automation_tools.html | [x] |
| 24 | `workflows_exhaustive` | `/dashboard/workflows` | workflow_triggers.html | [x] |
| 25 | `escalation_exhaustive` | `/dashboard/escalation` | escalation_dashboard.html | [x] |
| 26 | `import_exhaustive` | `/dashboard/import` | client_import.html | [x] |
| 27 | `scanned_documents_exhaustive` | `/dashboard/scanned-documents` | scanned_documents.html | [x] |
| 28 | `va_approval_exhaustive` | `/dashboard/va-approval` | va_letter_approval.html | [x] |
| 29 | `suspense_accounts_exhaustive` | `/dashboard/suspense-accounts` | suspense_accounts.html | [x] |

## Priority 4: Analytics & AI (5 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 30 | `ml_insights_exhaustive` | `/dashboard/ml-insights` | ml_insights.html | [x] |
| 31 | `predictive_exhaustive` | `/dashboard/predictive` | predictive_analytics.html | [x] |
| 32 | `patterns_exhaustive` | `/dashboard/patterns` | violation_patterns.html | [x] |
| 33 | `performance_exhaustive` | `/dashboard/performance` | performance_dashboard.html | [x] |
| 34 | `audit_exhaustive` | `/dashboard/audit` | audit_dashboard.html | [x] |

## Priority 5: Knowledge & Integrations (4 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 35 | `knowledge_base_exhaustive` | `/dashboard/knowledge-base` | knowledge_base.html | [x] |
| 36 | `sops_exhaustive` | `/dashboard/sops` | sops.html | [x] |
| 37 | `integrations_exhaustive` | `/dashboard/integrations` | integrations_hub.html | [x] |
| 38 | `franchise_exhaustive` | `/dashboard/franchise` | franchise_dashboard.html | [x] |

## Priority 6: Other Pages (3 tests) ✅ COMPLETE

| # | Test File | Route | Template | Status |
|---|-----------|-------|----------|--------|
| 39 | `white_label_exhaustive` | `/dashboard/white-label` | white_label_dashboard.html | [x] |
| 40 | `preview_exhaustive` | `/preview` | instant_preview.html | [x] |
| 41 | `scanner_exhaustive` | `/scanner` | document_scanner.html | [x] |

---

## Progress

- [x] Priority 1: 10/10 complete ✅
- [x] Priority 2: 12/12 complete ✅
- [x] Priority 3: 7/7 complete ✅
- [x] Priority 4: 5/5 complete ✅
- [x] Priority 5: 4/4 complete ✅
- [x] Priority 6: 3/3 complete ✅

**Total: 41/41 complete (100%)**

---

## Deleted Tests (22 total)

### Redirect Routes (12)
- `cases_exhaustive` → `/dashboard/clients`
- `email_exhaustive` → `/dashboard/settings/email`
- `sms_exhaustive` → `/dashboard/settings/sms`
- `messages_exhaustive` → `/dashboard/settings/sms`
- `reports_exhaustive` → `/dashboard/analytics`
- `generator_exhaustive` → `/dashboard/demand-generator`
- `queue_exhaustive` → `/dashboard/letter-queue`
- `automation_exhaustive` → `/dashboard/automation-tools`
- `staff_exhaustive` → `/staff/admin?section=team`
- `auth_exhaustive` → `/staff/login`
- `analysis_exhaustive` → `/dashboard/analyses`
- `welcome_exhaustive` → `/signup/welcome`

### Already Covered (5)
- `clients_exhaustive` - covered by `clients.cy.js`
- `dashboard_exhaustive` - covered by `dashboard.cy.js`
- `signup_exhaustive` - covered by `signup_flow.cy.js`
- `success_exhaustive` - covered by `signup_flow.cy.js`
- `create_password_exhaustive` - covered by `client_portal.cy.js`

### Invalid Routes (5)
- `logout_exhaustive` - route doesn't exist (use `/staff/logout`)
- `history_exhaustive` - JSON API endpoint
- `test_exhaustive` - JSON API endpoint
- `other_exhaustive` - route doesn't exist
- `whitelabel_exhaustive` - duplicate of `white-label`

---

## Final Summary

**Started**: 63 broken `.cy.js.broken` files
**Deleted**: 22 redundant/invalid tests
**Fixed**: 41 tests across 6 priority levels
**Remaining**: 0 broken files

**Total Exhaustive Test Files**: 46 (all passing)
