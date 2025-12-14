# Force Regeneration Testing Guide

## Problem Fixed
Analysis 106 (and others) were already at stage 2 with old documents. The endpoint was returning cached results instead of regenerating with the new Apple-style generators.

## Solution Added
Added `force=true` parameter to `/api/approve/{id}` endpoint that:
1. Deletes all old documents (files + database records)
2. Resets analysis to stage 1
3. Regenerates all 3 Apple-style documents from scratch

## How to Test

### Method 1: Query Parameter (Recommended)
```bash
curl -X POST "http://localhost:5000/api/approve/106?force=true"
```

### Method 2: POST Body
```bash
curl -X POST http://localhost:5000/api/approve/106 \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

### Method 3: Via Replit Webview
If using Replit's web interface, add `?force=true` to the approval button URL.

## Expected Result

### Before (Old Behavior)
```json
{
  "success": true,
  "message": "Client documents already generated",
  "documents": [
    {"type": "comprehensive_analysis", ...}  // Old format
  ]
}
```

### After (New Behavior with force=true)
```json
{
  "success": true,
  "message": "Apple-style documents generated successfully (no Claude API cost)",
  "cost": 0,
  "tokens": 0,
  "documents": [
    {"document_id": 123, "type": "internal_analysis", "filepath": "..."},
    {"document_id": 124, "type": "client_report", "filepath": "..."},
    {"document_id": 125, "type": "client_email", "filepath": "..."}
  ],
  "total_cost": 2.50,  // Only Stage 1 cost
  "total_tokens": 15000
}
```

## Console Output You Should See
```
🔄 FORCE REGENERATION: Deleting old documents and resetting to stage 1...
  🗑️  Deleted: static/generated_letters/old_file_1.pdf
  🗑️  Deleted: static/generated_letters/old_file_2.pdf
  ✅ Deleted 2 old documents
  ✅ Reset analysis to stage 1

🚀 STAGE 2: Generating client documents for analysis 106...
📄 Generating Apple-style documents (database-driven, no Claude API)...
  📊 Generating Internal Analysis...
  ✅ Internal Analysis saved: static/generated_letters/...
  📄 Generating 7-Page Client Report...
  ✅ Client Report saved: static/generated_letters/...
  📧 Generating Client Email...
  ✅ Client Email saved: static/generated_letters/...
✅ Stage 2 complete! Analysis 106 ready for delivery
```

## Verification Steps

1. **Check PDFs Generated:**
```bash
ls -lh static/generated_letters/*_20*.pdf | tail -3
```

2. **Check PDF Sizes (should be < 5 pages each, < 15 pages total):**
```bash
for f in static/generated_letters/*_20*.pdf; do
  echo "$f: $(pdfinfo "$f" 2>/dev/null | grep Pages || echo 'N/A')"
done | tail -3
```

3. **Check Database Records:**
```bash
sqlite3 fcra_platform.db "SELECT id, bureau, round_number, created_at FROM dispute_letters WHERE analysis_id=106 ORDER BY id DESC LIMIT 3;"
```

## Troubleshooting

### Error: "Analysis is not in Stage 1"
- You're trying to regenerate without `force=true`
- Add `?force=true` to the URL

### Error: "'Violation' object has no attribute 'furnisher'"
- This was fixed in commit 298109a
- Make sure you pulled the latest code: `git pull`

### No PDFs Generated
- Check that violations exist: `SELECT COUNT(*) FROM violations WHERE analysis_id=106;`
- Check for Python errors in console output
- Verify WeasyPrint is installed: `pip list | grep weasyprint`

### PDFs Too Large
- This shouldn't happen with new generators (target < 15 pages total)
- Old documents may still exist - use `force=true` to delete them

## Changes Made

**Commits:**
- `8d5831c` - Add force regeneration parameter (this fix)
- `298109a` - Fix Violation model attribute error (furnisher)
- `d55f0d9` - Fix WeasyPrint import and date formatting
- `316486e` - Improve Stage 2 document handling (main implementation)

**Files Modified:**
- `app.py` - Added force parameter logic, old document deletion
- `document_generators.py` - Fixed attribute errors, added conditional imports

## Success Criteria
✅ 3 PDFs generated (Internal Analysis, Client Report, Client Email)
✅ Total pages < 15
✅ Cost = $0 for Stage 2
✅ Documents have Apple-style design (Playfair Display fonts, navy/teal colors)
✅ Old documents deleted when using force=true
