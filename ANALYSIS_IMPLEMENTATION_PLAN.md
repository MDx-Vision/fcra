# Analysis Feature Implementation Plan

## Overview

The Analysis feature is the foundation for the entire dispute workflow. When a credit report is analyzed, it should:
1. Identify FCRA violations (already working)
2. Extract individual negative items (tradelines, inquiries, collections, public records)
3. Auto-populate the `DisputeItem` table
4. Make items immediately available to AI Dispute Writer, Goodwill Letters, 5-Day Knockout, etc.

## Current State (What Exists)

### Working Components
- `run_stage1_for_all_sections()` - Splits report and sends to Claude AI for analysis
- `auto_populate_litigation_database()` - Creates `Violation`, `Standing`, `Damages` records
- Credit report parsing in `credit_report_parser.py` - Extracts accounts, inquiries, collections
- `DisputeItem` model exists with full schema

### The Gap
- Stage 1 analysis identifies **legal violations** but NOT **individual disputable items**
- `DisputeItem` table is never auto-populated from analysis
- AI Dispute Writer has to pull raw accounts from credit report JSON files as a workaround
- Items aren't categorized (inquiry, collection, late_payment, charge_off, etc.)

## Implementation Plan

### Phase 1: Negative Item Extraction Service
**Goal**: Create a service that extracts all negative items from credit reports

**File**: `services/negative_item_extractor.py` (NEW)

```python
class NegativeItemExtractor:
    """Extract negative items from credit reports for dispute generation"""

    def extract_negative_items(self, parsed_report: dict) -> List[Dict]:
        """Main entry point - returns list of negative items"""
        items = []
        items.extend(self._extract_negative_tradelines(parsed_report))
        items.extend(self._extract_hard_inquiries(parsed_report))
        items.extend(self._extract_collections(parsed_report))
        items.extend(self._extract_public_records(parsed_report))
        return items

    def _extract_negative_tradelines(self, parsed_report) -> List[Dict]:
        """Extract tradelines with negative indicators"""
        # Look for: late payments, charge-offs, closed accounts, high utilization

    def _extract_hard_inquiries(self, parsed_report) -> List[Dict]:
        """Extract hard inquiries (soft inquiries excluded)"""

    def _extract_collections(self, parsed_report) -> List[Dict]:
        """Extract collection accounts"""

    def _extract_public_records(self, parsed_report) -> List[Dict]:
        """Extract bankruptcies, judgments, liens"""
```

**Item Structure**:
```python
{
    "creditor_name": "Capital One",
    "account_id": "****1234",
    "item_type": "late_payment",  # inquiry, collection, late_payment, charge_off, public_record
    "bureaus": ["Equifax", "Experian", "TransUnion"],  # Which bureaus report this
    "status": "Derogatory",
    "balance": 1500.00,
    "date_opened": "2020-01-15",
    "date_reported": "2024-06-01",
    "negative_reason": "30 days late x3",  # Why it's negative
    "dispute_basis": "Inaccurate reporting dates",  # Suggested dispute reason
}
```

### Phase 2: Auto-Populate DisputeItem Table
**Goal**: After analysis, automatically create DisputeItem records

**File**: `app.py` - Update `auto_populate_litigation_database()` function

**Changes**:
1. Add call to `NegativeItemExtractor` after extracting violations
2. Create `DisputeItem` record for each negative item
3. Link to analysis via `analysis_id`
4. Set appropriate `item_type`, `bureau`, `creditor_name`, `account_id`

```python
def auto_populate_litigation_database(analysis_id, client_id, litigation_data, db, parsed_report=None):
    # ... existing violation/standing/damages population ...

    # NEW: Populate DisputeItem table
    if parsed_report:
        extractor = NegativeItemExtractor()
        negative_items = extractor.extract_negative_items(parsed_report)

        for item in negative_items:
            for bureau in item["bureaus"]:
                dispute_item = DisputeItem(
                    client_id=client_id,
                    analysis_id=analysis_id,
                    bureau=bureau,
                    dispute_round=1,
                    item_type=item["item_type"],
                    creditor_name=item["creditor_name"],
                    account_id=item["account_id"],
                    status="to_do",
                    reason=item.get("dispute_basis", ""),
                )
                db.add(dispute_item)
```

### Phase 3: Update Analysis Endpoints
**Goal**: Pass parsed credit report data through to auto-population

**Files to Update**:

1. `/api/credit-report/parse-and-analyze` (line ~5189)
   - Already has `parse_result` with accounts/inquiries/collections
   - Pass to `auto_populate_litigation_database()`

2. `/api/analyze` (line ~5373)
   - Need to parse HTML and extract structured data first
   - Then pass to auto-population

3. Credit Import automation (`services/credit_import_automation.py`)
   - Already extracts structured data to JSON
   - Trigger analysis auto-population when import completes

### Phase 4: AI Dispute Writer Integration
**Goal**: AI Dispute Writer loads pre-analyzed items from DisputeItem table

**File**: `services/ai_dispute_writer_service.py`

**Changes to `get_client_context()`**:
```python
def get_client_context(self, client_id: int) -> Dict:
    # Load items from DisputeItem table (already analyzed)
    dispute_items = self.db.query(DisputeItem).filter(
        DisputeItem.client_id == client_id,
        DisputeItem.status == "to_do"
    ).all()

    # If no items exist, fall back to credit report extraction
    if not dispute_items:
        dispute_items = self._extract_accounts_from_credit_report(client_id)
```

**Remove workaround code**:
- `_extract_accounts_from_credit_report()` becomes fallback only
- Primary source is now `DisputeItem` table

### Phase 5: Analysis Dashboard UI Updates
**Goal**: Show extracted items in analysis review UI

**Files**:
- `templates/analysis_review.html` - Show items found
- `app.py` - `/analysis/<id>/review` endpoint - Return items data

**UI Changes**:
1. After analysis completes, show "Items Found" section
2. List all negative items grouped by type (Inquiries, Collections, Late Payments, etc.)
3. Allow staff to review and approve before proceeding to letters
4. "Generate Letters" button enables after approval

## Item Type Classification Logic

```python
def classify_item_type(account: dict) -> str:
    """Determine the item type based on account data"""

    status = account.get("status", "").lower()
    account_type = account.get("account_type", "").lower()

    # Inquiries
    if account.get("is_inquiry") or "inquiry" in account_type:
        return "inquiry"

    # Collections
    if "collection" in status or "collection" in account_type:
        return "collection"

    # Charge-offs
    if "charge" in status and "off" in status:
        return "charge_off"

    # Public Records
    if any(x in account_type for x in ["bankruptcy", "judgment", "lien", "tax"]):
        return "public_record"

    # Late Payments
    if any(x in status for x in ["late", "delinquent", "past due", "30 day", "60 day", "90 day"]):
        return "late_payment"

    # Default to tradeline issue
    return "tradeline"
```

## Bureau Detection Logic

```python
def detect_bureaus(account: dict) -> List[str]:
    """Determine which bureaus report this account"""

    bureaus = []

    # Check for bureau-specific fields
    if account.get("equifax") or account.get("ef_balance"):
        bureaus.append("Equifax")
    if account.get("experian") or account.get("ex_balance"):
        bureaus.append("Experian")
    if account.get("transunion") or account.get("tu_balance"):
        bureaus.append("TransUnion")

    # If no bureau info, assume all three
    if not bureaus:
        bureaus = ["Equifax", "Experian", "TransUnion"]

    return bureaus
```

## Testing Plan

### Unit Tests
- `test_negative_item_extractor.py`
  - Test extraction of each item type
  - Test bureau detection
  - Test item classification

### Integration Tests
- `test_analysis_workflow.py`
  - Upload credit report
  - Run analysis
  - Verify DisputeItem records created
  - Verify AI Dispute Writer loads items

### Manual Testing
1. Import a credit report via Credit Import
2. Navigate to AI Dispute Writer
3. Select client
4. Verify items appear without manual selection
5. Generate letters
6. Verify letters reference correct accounts

## Migration Notes

### Existing Clients
- Clients with existing credit reports but no DisputeItem records
- Need migration script to backfill items
- Run negative item extraction on stored credit reports

### Backwards Compatibility
- Keep `_extract_accounts_from_credit_report()` as fallback
- Gradually migrate to database-first approach
- Remove fallback after all clients migrated

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `services/negative_item_extractor.py` | NEW | Extract negative items from reports |
| `app.py` | MODIFY | Update auto_populate_litigation_database() |
| `app.py` | MODIFY | Update /api/analyze endpoint |
| `app.py` | MODIFY | Update /api/credit-report/parse-and-analyze |
| `services/ai_dispute_writer_service.py` | MODIFY | Load from DisputeItem table |
| `templates/analysis_review.html` | MODIFY | Show items found |
| `tests/test_negative_item_extractor.py` | NEW | Unit tests |
| `scripts/backfill_dispute_items.py` | NEW | Migration script |

## Success Criteria

1. After analysis, `DisputeItem` table has records for all negative items
2. AI Dispute Writer shows items without needing credit report file access
3. Items are correctly categorized by type
4. Items show which bureaus report them
5. Goodwill Letters, 5-Day Knockout, Inquiry Disputes all work with pre-analyzed items
6. No more "No items found" errors when items exist in credit report

## Timeline

- Phase 1: Negative Item Extraction Service - Core functionality
- Phase 2: Auto-Populate DisputeItem - Database integration
- Phase 3: Update Analysis Endpoints - Wire up the flow
- Phase 4: AI Dispute Writer Integration - Use the data
- Phase 5: UI Updates - Show results to staff

## Dependencies

- Existing `credit_report_parser.py` for parsing logic
- `DisputeItem` model (already exists)
- Claude AI for violation detection (already working)
- Credit Import automation for auto-pulled reports
