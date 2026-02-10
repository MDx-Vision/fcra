# FCRA Platform - Gaps Roadmap

> **Created:** 2026-02-08
> **Last Updated:** 2026-02-09
> **Total Issues:** 21
> **Completed:** 10/21

---

## Progress Overview

| Priority | Total | Open | In Progress | Completed |
|----------|-------|------|-------------|-----------|
| Critical | 4 | 3 | 0 | 1 |
| High | 7 | 1 | 0 | 6 |
| Medium | 6 | 3 | 0 | 3 |
| Low | 4 | 4 | 0 | 0 |

---

## Critical Issues (Blocking Production)

### ~~ISSUE-001: Configure Anthropic API Key~~ ✅ ALREADY WORKING
- **Priority:** ~~Critical~~ N/A
- **Status:** Completed
- **Category:** Configuration
- **Completed:** 2026-02-08

**Notes:**
API key is configured in system environment. Server confirms: `✅ Anthropic API client initialized`

5-Day Knockout and Inquiry Dispute letter generation are functional.

---

### ISSUE-002: SendCertifiedMail SFTP Credentials
- **Priority:** Critical
- **Status:** Open
- **Category:** External Integration
- **Effort:** External dependency
- **Blocking:** Certified mail delivery to bureaus

**Description:**
Phase 4 (Send Certified Mail) is code complete but awaiting SFTP credentials from SendCertifiedMail.com. Currently falls back to mock mode.

**Files:**
- `services/sendcertified_sftp_service.py`
- `services/certified_mail_service.py`

**Acceptance Criteria:**
- [ ] Contact SendCertifiedMail.com for SFTP credentials
- [ ] Add `SENDCERTIFIED_SFTP_HOST`, `SENDCERTIFIED_SFTP_USER`, `SENDCERTIFIED_SFTP_PASSWORD` to `.env`
- [ ] Add `SENDCERTIFIEDMAIL_API_KEY` to `.env`
- [ ] Test certified mail order creation
- [ ] Verify tracking number retrieval
- [ ] Remove mock mode fallback warnings

**Contact:**
- Website: https://sendcertifiedmail.com
- Purpose: SFTP access for automated certified mail

---

### ISSUE-003: Twilio A2P 10DLC Campaign Approval
- **Priority:** Critical
- **Status:** Open
- **Category:** External Integration
- **Effort:** External dependency
- **Blocking:** SMS delivery (carriers may block unregistered numbers)

**Description:**
SMS automation requires A2P 10DLC campaign registration for business messaging. Without approval, SMS messages may be filtered by carriers.

**Files:**
- `services/sms_service.py`
- `services/sms_automation.py`

**Acceptance Criteria:**
- [ ] A2P 10DLC campaign submitted to Twilio
- [ ] Campaign approved by carriers
- [ ] `TWILIO_MESSAGING_SERVICE_SID` updated with approved campaign
- [ ] Test SMS delivery confirmed

**Notes:**
Check status at: https://console.twilio.com/

---

### ISSUE-004: WhatsApp Template Approval
- **Priority:** Critical
- **Status:** Open
- **Category:** External Integration
- **Effort:** External dependency
- **Blocking:** WhatsApp business messaging

**Description:**
WhatsApp Business API requires pre-approved message templates for outbound messaging.

**Files:**
- `services/whatsapp_automation.py`

**Acceptance Criteria:**
- [ ] WhatsApp message templates submitted to Meta
- [ ] Templates approved
- [ ] Template SIDs updated in configuration
- [ ] WhatsApp messaging tested

---

## High Priority Issues

### ~~ISSUE-005: Credit Account Extraction from HTML Reports~~ ✅ FIXED
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Feature Gap
- **Completed:** 2026-02-08

**What was wrong:**
The parser WAS extracting accounts to JSON files correctly (17 accounts found). The bug was in the 5-Day Knockout API endpoint - it checked for wrong keys when detecting bureaus:
- ❌ `acct.get("equifax")` - top-level key (doesn't exist)
- ✅ `acct.get("bureaus", {}).get("equifax", {}).get("present")` - nested structure

**Fix applied:**
Updated bureau detection in `app.py` (3 locations in `api_5day_knockout_client_items`):
- Analysis source (~line 42872)
- CreditReport source (~line 42938)
- CreditMonitoringCredential source (~line 43009)

**Result:**
- 17 accounts now correctly load in 5-Day Knockout Step 2
- Bureau assignments are accurate (not defaulting to all 3)
- AMERICAN EXPRESS shows "Equifax" only (correct)
- CITICARDS CBNA shows "Equifax, Experian, TransUnion" (correct)

---

### ~~ISSUE-006: Goodwill Letter Template & Workflow~~ ✅ COMPLETE
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Credit Repair Warfare Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Prompt Template:** `knowledge/FCRA_PROMPT_19_GOODWILL_LETTER.md`
   - Full letter template with customization options
   - Hardship scenarios (job loss, medical, divorce)
   - Creditor-specific tips (Capital One, Chase, Amex, etc.)
   - Clear distinction from dispute letters

2. **Prompt Loader:** `services/prompt_loader.py`
   - Added "goodwill" shortcut
   - Added `get_goodwill_letter_prompt()` convenience method

3. **AI Dispute Writer:** `services/ai_dispute_writer_service.py`
   - Added to SPECIAL_STRATEGIES dictionary
   - Available via `get_special_strategies_info()`

4. **Unit Tests:** 12 tests in `tests/test_ai_dispute_writer_service.py`
   - TestGoodwillStrategy (6 tests)
   - TestGoodwillPromptLoader (6 tests)

---

### ~~ISSUE-007: Pay-for-Delete Negotiation Tracking~~ ✅ COMPLETE
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Credit Repair Warfare Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Database Model:** `database.py` - PayForDeleteNegotiation
   - Full tracking: collector info, balances, offers, counter-offers
   - Status lifecycle: pending → offered → countered → agreed → paid → deleted
   - Payment tracking: amount, method, confirmation, deadlines
   - Deletion verification: bureau, date, proof tracking
   - Staff assignment and notes

2. **Service:** `services/pay_for_delete_service.py` (~500 lines)
   - CRUD operations for negotiations
   - Status transition methods: make_offer, record_counter_offer, accept_agreement, record_payment, verify_deletion
   - Statistics: success rate, total saved, avg settlement percent
   - Letter generation: P4D offer letter with full terms
   - Common collectors database with P4D-friendly ratings

3. **Dashboard Template:** `templates/pay_for_delete.html`
   - Stats cards: Pending, In Negotiation, Agreed, Awaiting Deletion, Deleted, Total Saved
   - Filterable table with status tabs
   - Create/Edit modal with all fields
   - Detail modal with timeline view
   - Offer modal with percentage calculator
   - CSV export functionality

4. **API Endpoints:** 13 endpoints in `app.py`
   - `GET/POST /api/pay-for-delete/negotiations` - List/create
   - `GET/PUT/DELETE /api/pay-for-delete/negotiations/<id>` - CRUD
   - `POST .../offer` - Make initial offer
   - `POST .../counter` - Record/make counter offer
   - `POST .../agree` - Accept agreement
   - `POST .../payment` - Record payment
   - `POST .../verify-deletion` - Verify deletion
   - `GET .../letter` - Generate offer letter
   - `GET /api/pay-for-delete/stats` - Statistics
   - `GET /api/pay-for-delete/common-collectors` - Collector database

5. **Unit Tests:** 53 tests in `tests/test_pay_for_delete_service.py`
   - TestP4DConstants (6 tests)
   - TestPayForDeleteServiceCRUD (13 tests)
   - TestPayForDeleteStatusTransitions (14 tests)
   - TestPayForDeleteStatistics (4 tests)
   - TestPayForDeleteLetterGeneration (8 tests)
   - TestPayForDeleteServiceContextManager (6 tests)
   - TestPayForDeleteFactoryFunction (2 tests)

**Acceptance Criteria:**
- [x] Database model for tracking negotiations
- [x] Service for CRUD operations
- [x] Dashboard UI for managing negotiations
- [x] Letter template for P4D offers
- [x] Status tracking (offered, countered, accepted, paid, deleted)
- [x] Integration with collection account disputes

---

### ~~ISSUE-008: Debt Validation Workflow UI~~ ✅ COMPLETE
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Feature Incomplete
- **Completed:** 2026-02-08

**What was added:**

1. **Database Model:** `database.py` - DebtValidationRequest
   - Full tracking: collector info, dates, deadlines, responses
   - Document receipt tracking (agreement, statements, chain of title)
   - FDCPA violation flagging with type and notes
   - Collection activity monitoring during validation period

2. **Dashboard Template:** `templates/debt_validation.html`
   - Stats cards: Pending, Awaiting, Overdue, Violations, Validated
   - Filterable table with status tabs
   - Create/Edit modal with all fields
   - Detail modal with violation flagging
   - CSV export functionality

3. **API Endpoints:** 9 new endpoints in `app.py`
   - `GET /api/debt-validation/requests` - List with filters
   - `POST /api/debt-validation/requests` - Create new
   - `GET/PUT/DELETE /api/debt-validation/requests/<id>` - CRUD
   - `POST /api/debt-validation/requests/<id>/violation` - Flag/unflag
   - `POST /api/debt-validation/requests/<id>/response` - Mark response
   - `POST /api/debt-validation/requests/<id>/close` - Close request
   - `GET /api/debt-validation/stats` - Statistics

4. **Unit Tests:** 34 tests in `tests/test_debt_validation_workflow.py`
   - Model field validation
   - API endpoint tests
   - FDCPA compliance tests
   - Integration tests

**Acceptance Criteria:**
- [x] Dashboard page at `/dashboard/debt-validation`
- [x] List of pending validation requests
- [x] Track 30-day response deadline
- [x] Mark validation received/failed
- [x] Link to client disputes
- [x] FDCPA violation flagging (no response = violation)

---

### ~~ISSUE-009: Cease & Desist Letter Template~~ ✅ COMPLETE
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Credit Repair Warfare Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Prompt Template:** `knowledge/FCRA_PROMPT_20_CEASE_DESIST.md`
   - Full FDCPA §1692c(c) citation
   - Letter template with legal sections
   - Harassment documentation section
   - State SOL reference table
   - Customization for workplace/third-party contact violations

2. **Prompt Loader:** `services/prompt_loader.py`
   - Added "ceasedesist" shortcut
   - Added `get_cease_desist_prompt()` method

3. **AI Dispute Writer:** `services/ai_dispute_writer_service.py`
   - Added to SPECIAL_STRATEGIES with warning note

4. **Unit Tests:** 11 tests in `tests/test_ai_dispute_writer_service.py`
   - TestCeaseDesistStrategy (5 tests)
   - TestCeaseDesistPromptLoader (6 tests)

---

### ~~ISSUE-010: Bureau Response Service Completion~~ ✅ COMPLETE
- **Priority:** ~~High~~ N/A
- **Status:** Completed
- **Category:** Technical Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Error Handling:** `services/bureau_response_service.py`
   - Added `BureauResponseServiceError` custom exception class
   - Added `_error_response()` and `_success_response()` helper methods
   - All methods now return structured error responses with error codes
   - Error codes: `TRACKING_NOT_FOUND`, `FILE_NOT_FOUND`, `OCR_FAILED`, `PARSE_FAILED`, `DATABASE_ERROR`, `INVALID_INPUT`

2. **Response Parsing:** New methods for parsing bureau letters
   - `parse_response_letter(file_path)` - Parse PDF/image response letters
   - `_parse_response_text(text)` - Extract info from raw text
   - `_identify_bureau(text)` - Identify Equifax/Experian/TransUnion
   - `_extract_item_counts(text)` - Extract deleted/updated/verified counts
   - `_extract_account_numbers(text)` - Extract account numbers from text
   - `_extract_dates(text)` - Extract dates from response

3. **OCR Integration:**
   - Integrates with existing `services/ocr_service.py`
   - Supports PDF text extraction and Claude vision for images
   - `auto_parse_upload(upload_id)` - Parse ClientUpload documents

4. **Status Extraction:**
   - Keyword-based detection for: deleted, verified, updated, mixed, frivolous, investigating
   - Confidence scoring based on keyword matches
   - Follow-up required detection
   - Bureau identifier patterns for all 3 bureaus

5. **Additional Methods:**
   - `extract_status_from_text(text)` - Parse plain text
   - `batch_parse_responses(file_paths)` - Batch parsing
   - `get_parse_summary(client_id, days)` - Summary statistics

6. **Unit Tests:** 22 new tests (34 → 56 total)
   - TestResponseTextParsing (11 tests)
   - TestExtractStatusFromText (3 tests)
   - TestParseResponseLetter (1 test)
   - TestBatchParseResponses (2 tests)
   - TestGetParseSummary (2 tests)
   - TestErrorHandlingImprovements (3 tests)

**Acceptance Criteria:**
- [x] Proper error handling with informative messages
- [x] Response parsing from bureau letters
- [x] OCR integration for scanned responses
- [x] Status extraction (verified, deleted, updated, etc.)
- [x] Unit tests for all methods

---

## Medium Priority Issues

### ~~ISSUE-011: State Attorney General Complaint Integration~~ ✅ COMPLETE
- **Priority:** ~~Medium~~ N/A
- **Status:** Completed
- **Category:** Credit Repair Warfare Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Database Models:** `database.py`
   - `StateAGContact` - All 50 states + DC AG contact info
   - `StateAGComplaint` - Complaint tracking with full lifecycle

2. **State AG Contact Database:** `services/state_ag_service.py`
   - All 50 states + DC consumer protection offices
   - Address, phone, website, online complaint URLs
   - Filing method support (online, mail, email)
   - FCRA enforcement notes for active states

3. **Service:** `services/state_ag_service.py` (~900 lines)
   - `seed_ag_contacts()` - Populate/update contact database
   - `get_all_ag_contacts()` - List all states
   - `get_ag_contact_by_state(state_code)` - Lookup by state
   - `create_complaint()` - Create new complaint
   - `update_complaint_status()` - Status transitions
   - `file_complaint()` - Mark as filed with tracking
   - `resolve_complaint()` - Mark resolution with damages
   - `generate_complaint_letter()` - AI/template letter generation
   - `get_complaint_statistics()` - Dashboard stats
   - `get_overdue_complaints()` - Find overdue complaints
   - `get_escalation_candidates()` - Clients ready for AG escalation

4. **API Endpoints:** 15 endpoints in `app.py`
   - `GET /api/state-ag/contacts` - List all AG contacts
   - `GET /api/state-ag/contacts/<state>` - Get state contact
   - `POST /api/state-ag/seed` - Seed contact database
   - `GET/POST /api/state-ag/complaints` - List/create complaints
   - `GET/PUT /api/state-ag/complaints/<id>` - CRUD
   - `POST .../status` - Update status
   - `POST .../file` - Mark as filed
   - `POST .../resolve` - Resolve complaint
   - `GET .../letter` - Generate letter
   - `GET /api/state-ag/stats` - Statistics
   - `GET /api/state-ag/overdue` - Overdue complaints
   - `GET /api/state-ag/escalation-candidates` - Ready for AG
   - `GET /api/clients/<id>/ag-complaints` - Client complaints

5. **Dashboard:** Added sidebar link at `/dashboard/state-ag-complaints`

6. **Unit Tests:** 47 tests in `tests/test_state_ag_service.py`
   - TestStateAGConstants (4 tests)
   - TestStateAGServiceInit (4 tests)
   - TestStateAGContactOperations (6 tests)
   - TestComplaintCRUD (8 tests)
   - TestComplaintStatusWorkflow (9 tests)
   - TestLetterGeneration (2 tests)
   - TestStatisticsAndReporting (3 tests)
   - TestResponseHelpers (2 tests)
   - TestComplaintModel (5 tests)
   - TestStateAGContactModel (1 test)
   - TestEdgeCases (4 tests)

**Acceptance Criteria:**
- [x] State AG contact database (all 50 states + DC)
- [x] Complaint letter template (AI + fallback template)
- [x] Integration in escalation workflow
- [x] Tracking for complaint filed/response received

---

### ~~ISSUE-012: Attorney Referral Handoff Workflow~~ ✅ COMPLETE
- **Priority:** ~~Medium~~ N/A
- **Status:** Completed
- **Category:** Credit Repair Warfare Gap
- **Completed:** 2026-02-08

**What was added:**

1. **Database Models:** `database.py`
   - `AttorneyNetworkMember` - Attorney network with bar info, practice areas, fee structures
   - Enhanced `AttorneyReferral` - Full referral lifecycle tracking, damages, fees

2. **Service:** `services/attorney_referral_service.py` (~800 lines)
   - `create_attorney()` / `update_attorney()` - Attorney CRUD
   - `get_all_attorneys()` / `get_attorney()` - Listing and lookup
   - `find_matching_attorneys()` - Match by state, violation type, acceptance rate
   - `create_referral()` / `update_referral()` - Referral CRUD
   - `update_referral_status()` - Status transitions
   - `mark_attorney_response()` - Accept/decline tracking
   - `record_case_filed()` - Court filing with case number
   - `record_settlement()` - Settlement with damages breakdown
   - `record_fee_received()` - Referral fee tracking
   - `generate_case_package()` - Evidence, timeline, violations package
   - `get_referral_statistics()` - Dashboard stats

3. **API Endpoints:** 20 endpoints in `app.py`
   - `GET/POST /api/attorney-network` - List/create attorneys
   - `GET/PUT /api/attorney-network/<id>` - Attorney CRUD
   - `GET /api/attorney-network/search` - Find matching attorneys
   - `GET /api/attorney-network/<id>/referrals` - Attorney's referrals
   - `GET/POST /api/referrals` - List/create referrals
   - `GET/PUT /api/referrals/<id>` - Referral CRUD
   - `POST /api/referrals/<id>/status` - Update status
   - `POST /api/referrals/<id>/response` - Record attorney response
   - `POST /api/referrals/<id>/file` - Record case filed
   - `POST /api/referrals/<id>/settle` - Record settlement
   - `POST /api/referrals/<id>/fee` - Record referral fee
   - `POST /api/referrals/<id>/case-package` - Generate case package
   - `GET /api/referrals/stats` - Statistics
   - `GET /api/referrals/pending` - Pending referrals
   - `GET /api/referrals/active` - Active cases
   - `GET /api/clients/<id>/referrals` - Client's referrals
   - `GET /api/referrals/options` - Form dropdown options

4. **Dashboard:** `templates/attorney_referrals.html`
   - Stats cards: Total, Pending, Active, Settled, Recovered
   - Tabs: Referrals, Attorney Network, Pending Action, Active Cases
   - Add Attorney modal with full form
   - New Referral modal with client/attorney selection
   - Status update actions
   - Case package generation

5. **Sidebar:** Added link at `/dashboard/attorney-referrals`

6. **Unit Tests:** 39 tests in `tests/test_attorney_referral_service.py`
   - TestAttorneyReferralConstants (10 tests)
   - TestAttorneyReferralServiceInit (7 tests)
   - TestAttorneyReferralServiceError (6 tests)
   - TestHelperMethods (4 tests)
   - TestValidStatusTransitions (3 tests)
   - TestViolationTypes (3 tests)
   - TestFeeArrangements (3 tests)
   - TestPracticeAreas (3 tests)

**Acceptance Criteria:**
- [x] Attorney network database
- [x] Case package generation (evidence, timeline, violations)
- [x] Referral tracking (referred, accepted, filed, settled)
- [x] Attorney fee agreement tracking
- [x] Commission/referral fee tracking

---

### ~~ISSUE-013: RESPA QWR Response Tracking~~ ✅ COMPLETE
- **Priority:** Medium
- **Status:** Completed
- **Category:** Feature Incomplete
- **Completed:** 2026-02-08

**Description:**
RESPA QWR template exists but response tracking is incomplete.

**Implementation:**
- Created `RESPAQWRRequest` database model with full tracking fields
- Created `services/respa_qwr_service.py` (~900 lines) with:
  - CRUD operations for QWR requests
  - Workflow operations (send, confirm delivery, acknowledgment, response)
  - RESPA deadline calculation (5 business days ack, 30 days response)
  - Automatic violation flagging for missed deadlines
  - Escalation tracking (CFPB, State AG, Attorney)
  - Resolution and damages tracking
- Added 22 API endpoints for complete QWR lifecycle
- Created `/dashboard/respa-qwr` with full management UI
- Added sidebar link in Legal Tools section
- 49 unit tests passing

**Acceptance Criteria:**
- [x] Track QWR sent date
- [x] 30-day response deadline calculation
- [x] Response received tracking
- [x] RESPA violation flagging (no response)
- [x] Payment history document storage

---

### ISSUE-014: Reg Z Dispute Workflow
- **Priority:** Medium
- **Status:** Open
- **Category:** Feature Incomplete
- **Effort:** 2-3 hours

**Description:**
Reg Z template exists but no dedicated workflow.

**Acceptance Criteria:**
- [ ] Credit card dispute tracking
- [ ] Provisional credit tracking
- [ ] Investigation outcome tracking
- [ ] Reg Z violation detection

---

### ISSUE-015: Reinsertion Alert System
- **Priority:** Medium
- **Status:** Open
- **Category:** Credit Repair Warfare Gap
- **Effort:** 3-4 hours

**Description:**
§611(a)(5)(B) requires bureaus to notify consumers before reinserting deleted items. Need automated detection.

**Acceptance Criteria:**
- [ ] Compare new credit reports to previous
- [ ] Detect reinserted items
- [ ] Auto-generate reinsertion challenge letter
- [ ] Track notification compliance
- [ ] Flag violations (no notice given)

---

### ISSUE-016: Franchise Service Error Handling
- **Priority:** Medium
- **Status:** Open
- **Category:** Technical Gap
- **Effort:** 1-2 hours

**Description:**
`franchise_service.py` returns empty `{}` on multiple error paths.

**Files:**
- `services/franchise_service.py`

**Acceptance Criteria:**
- [ ] Proper error responses with messages
- [ ] Logging for errors
- [ ] Unit tests for error cases

---

## Low Priority Issues

### ISSUE-017: Client Education Portal
- **Priority:** Low
- **Status:** Open
- **Category:** Credit Repair Warfare Gap
- **Effort:** 6-8 hours

**Description:**
Client-facing FCRA rights explainer mentioned in roadmap as future enhancement.

**Acceptance Criteria:**
- [ ] `/portal/learn/fcra-rights` page
- [ ] Plain-English FCRA explanations
- [ ] Interactive timeline of dispute process
- [ ] FAQ section
- [ ] Video content integration

---

### ISSUE-018: Suspense Account Detection Enhancement
- **Priority:** Low
- **Status:** Open
- **Category:** Feature Enhancement
- **Effort:** 2-3 hours

**Description:**
Suspense account detection exists but could use ML-based pattern recognition.

**Acceptance Criteria:**
- [ ] Pattern learning from confirmed suspense cases
- [ ] Confidence scoring
- [ ] Automated flagging suggestions

---

### ISSUE-019: Mobile PWA Enhancements
- **Priority:** Low
- **Status:** Open
- **Category:** UX Enhancement
- **Effort:** 4-6 hours

**Description:**
PWA exists but offline support is limited.

**Acceptance Criteria:**
- [ ] Offline dispute viewing
- [ ] Background sync for form submissions
- [ ] Push notification improvements
- [ ] Better offline fallback UI

---

### ISSUE-020: Class Action Pattern Evidence Packets
- **Priority:** Low
- **Status:** Open
- **Category:** Feature Enhancement
- **Effort:** 4-6 hours

**Description:**
Violation pattern tracking exists but evidence packet generation could be enhanced.

**Acceptance Criteria:**
- [ ] PDF evidence packet generation
- [ ] Statistical analysis of patterns
- [ ] Attorney-ready format
- [ ] Multi-client aggregation

---

### ISSUE-021: Historical Credit Report Comparison (Month-to-Month Tracking)
- **Priority:** High
- **Status:** Open
- **Category:** Credit Repair Warfare Gap
- **Effort:** 8-12 hours
- **Added:** 2026-02-09

**Description:**
Credit monitoring services store historical credit reports. Currently we only pull the current report. Need to pull ALL historical reports and compare them month-to-month to:
1. Detect exact deletion dates (when item disappeared)
2. Detect exact reinsertion dates (when item came back = §611 violation)
3. Build accurate timeline for litigation documentation

**Supported Credit Monitoring Services:**
- MyFreeScoreNow
- IdentityIQ
- MyScoreIQ
- SmartCredit

Each service has different UI patterns for accessing historical reports - need per-service implementation.

**Current Gap:**
- Deletion dates are estimated from audit comparison, not actual report dates
- No way to track when items were actually removed/reinserted
- Missing documentation for §611(a)(5)(B) violations

**Technical Approach:**
1. Add `pull_historical_reports()` method to credit import automation
2. Per-service logic to find and navigate historical report UI
3. Loop through all available dates and pull each report
4. Store each report with its keyDate and service source
5. Create comparison service to diff accounts between reports
6. Auto-update DisputeItem.deleted_at and reinserted_at with real dates
7. Flag §611 violations when reinsertion detected without proper notice

**Files to Modify:**
- `services/credit_import_automation.py` - Add per-service historical report pulling
- `services/credit_report_parser.py` - Parse with date context
- `services/credit_report_comparison_service.py` - NEW: Compare reports across dates
- `database.py` - Store historical report metadata (CreditReportSnapshot model)
- `app.py` - API endpoints for comparison data and timeline

**Acceptance Criteria:**
- [ ] MyFreeScoreNow: Pull all historical reports
- [ ] IdentityIQ: Pull all historical reports
- [ ] MyScoreIQ: Pull all historical reports
- [ ] SmartCredit: Pull all historical reports
- [ ] Store each report with report date and service source
- [ ] Compare accounts across report dates (same client, different dates)
- [ ] Auto-detect deletion dates (item present in report A, gone in report B)
- [ ] Auto-detect reinsertion dates (item gone in report B, back in report C)
- [ ] Update DisputeItem.deleted_at and reinserted_at with real dates
- [ ] Generate timeline visualization of account changes per client
- [ ] Flag §611(a)(5)(B) violations for reinsertions without notice

**Related Issues:**
- ISSUE-015: Reinsertion Alert System (depends on this)

---

## Issue Tracking Legend

| Status | Description |
|--------|-------------|
| Open | Not started |
| In Progress | Currently being worked on |
| Review | Code complete, awaiting review |
| Blocked | Waiting on external dependency |
| Completed | Done and tested |

| Priority | Description |
|----------|-------------|
| Critical | Blocking production use |
| High | Core functionality gap |
| Medium | Important enhancement |
| Low | Nice to have |

---

## How to Close an Issue

1. Read the issue description and acceptance criteria
2. Implement the solution
3. Check ALL acceptance criteria boxes
4. Add unit tests
5. Update this file:
   - Change status to `Completed`
   - Add completion date
   - Update progress counts at top
6. Commit with message: `fix(ISSUE-XXX): Description`

---

## Quick Reference

```bash
# Start working on an issue
# 1. Read this file
# 2. Tell Claude: "Let's work on ISSUE-XXX"

# After completion
# 1. Update status in this file
# 2. Commit changes
```

---

## Changelog

| Date | Issue | Change |
|------|-------|--------|
| 2026-02-09 | ISSUE-021 | Added - Historical Credit Report Comparison (Month-to-Month Tracking) |
| 2026-02-08 | ISSUE-013 | Complete - RESPA QWR Tracking + 22 API endpoints + 49 tests |
| 2026-02-08 | ISSUE-012 | Complete - Attorney Referral Handoff + 20 API endpoints + 39 tests |
| 2026-02-08 | ISSUE-011 | Complete - State AG Complaint Integration + 50 states + 15 API endpoints + 47 tests |
| 2026-02-08 | ISSUE-010 | Complete - Bureau Response Service + OCR integration + 22 new tests |
| 2026-02-08 | ISSUE-007 | Complete - Pay-for-Delete Tracking + 13 API endpoints + 53 tests |
| 2026-02-08 | ISSUE-008 | Complete - Debt Validation UI + 9 API endpoints + 34 tests |
| 2026-02-08 | ISSUE-009 | Complete - Cease & Desist letter prompt + 11 tests |
| 2026-02-08 | ISSUE-006 | Complete - Goodwill letter prompt + 12 tests |
| 2026-02-08 | ISSUE-005 | Fixed - Bureau detection bug in 5KO API + 5 tests |
| 2026-02-08 | ISSUE-001 | Closed - API key already configured in environment |
| 2026-02-08 | - | Initial roadmap created with 20 issues |
