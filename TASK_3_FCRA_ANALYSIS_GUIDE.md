# Task 3: FCRA Analysis Workflow Guide

## 🎯 Overview

This guide explains how to run FCRA analysis on the 26+ successful credit reports you have, including the newly fixed MyFreeScoreNow imports.

---

## ⚠️ IMPORTANT: Pull Latest Changes First

Before testing, pull the latest score extraction fix on Replit:

```bash
git pull origin main
```

**This pulls:**
- ✅ CSRF token selector fix
- ✅ Score extraction fix with flow-aware logic
- ✅ Test scripts and documentation

---

## 🧪 Step 1: Verify MyFreeScoreNow Score Extraction

Test client 125 to confirm scores are now extracted:

```bash
python3 test_client_125.py
```

**Expected Output:**
```
================================================================================
 TESTING MYFREESCORENOW IMPORT - CLIENT 125 (SHAUN SMITH)
================================================================================

1️⃣  Testing browser availability...
✅ Browser available

2️⃣  Querying database for client 125 credentials...
✅ Client found: Shaun Smith

3️⃣  Decrypting credentials...
✅ Credentials decrypted successfully

4️⃣  Running import with updated MyFreeScoreNow automation...
   This may take 60-90 seconds...

⏱️  Import completed in 67.3 seconds

5️⃣  Analyzing results...
✅ IMPORT SUCCESSFUL!

📄 Report saved:
   Path: uploads/credit_reports/125_Shaun_Smith_20251210_HHMMSS.html

📊 Credit Scores Extracted:
   TransUnion: 650
   Experian:   655
   Equifax:    648
   ✅ All 3 bureau scores extracted

💳 Accounts Found: 15

================================================================================
 TEST SUMMARY
================================================================================
✅ MyFreeScoreNow import SUCCESSFUL for client 125
   The fix is working correctly!
```

**If scores are extracted:** ✅ Proceed to FCRA analysis!

**If scores still fail:** Check logs for "Using MyFreeScoreNow extraction method"

---

## 📊 Understanding FCRA Analysis Workflow

### What is FCRA Analysis?

The platform uses Claude API to analyze credit reports for:
1. **FCRA Violations** - Identifies reporting errors
2. **Standing** - Determines legal standing for litigation
3. **Damages** - Calculates potential exposure/settlement
4. **Score Impact** - Projects credit score improvements

### Two-Stage Process:

**Stage 1:** Violation Detection & Analysis
- Automatically runs when report is uploaded/imported
- Creates `Analysis` record in database
- Status: `pending_review` → needs staff approval

**Stage 2:** Document Generation
- Runs after Stage 1 approval
- Generates client reports, internal memos, dispute letters
- Status: `completed` → ready for delivery

---

## 🚀 Method 1: Trigger Analysis via UI (Recommended)

### Option A: Processing Queue

1. **Navigate to Dashboard:**
   ```
   https://your-replit-url/dashboard
   ```

2. **View Processing Queue:**
   - Look for "Pending Review" section
   - Shows all Stage 1 completed analyses awaiting approval

3. **Click "Review" on any analysis:**
   - Opens: `/analysis/<analysis_id>/review`
   - Shows violations, standing, damages breakdown

4. **Approve or Edit:**
   - Review the Claude AI analysis
   - Edit if needed
   - Click "Approve" to move to Stage 2

### Option B: Direct Upload (New Reports)

1. **Navigate to Dashboard:**
   ```
   https://your-replit-url/dashboard
   ```

2. **Click "New Client Analysis" or "Intake" button**

3. **Fill Client Info:**
   - Client name (required)
   - Email (optional)
   - Credit provider
   - Dispute round

4. **Upload Credit Report:**
   - **For PDFs:** Upload PDF file
   - **For HTML:** Paste HTML content directly (MyFreeScoreNow reports)

5. **Submit:**
   - Route: `POST /api/credit-report/parse-and-analyze`
   - Automatically parses and runs Stage 1 analysis
   - Redirects to `/analysis/<id>/review`

### Option C: From Client Page

1. **Navigate to Client:**
   ```
   https://your-replit-url/dashboard/clients
   ```

2. **Select client** (e.g., Shaun Smith - ID 125)

3. **View Credit Reports section**

4. **Click "Analyze" on saved report**
   - Triggers analysis on existing report
   - Opens review page when complete

---

## 💻 Method 2: Trigger Analysis via API/Command Line

### Option A: Python Script (Direct)

Create `analyze_report.py`:

```python
#!/usr/bin/env python3
"""Run FCRA analysis on saved credit report"""

from database import SessionLocal, CreditReport, Client, Analysis
from app import run_stage1_for_all_sections
from datetime import datetime

# Configuration
CLIENT_ID = 125  # Shaun Smith
REPORT_FILENAME = '125_Shaun_Smith_20251210_021008.html'

db = SessionLocal()

try:
    # 1. Get client
    client = db.query(Client).filter_by(id=CLIENT_ID).first()
    if not client:
        print(f"❌ Client {CLIENT_ID} not found")
        exit(1)

    print(f"✅ Client: {client.name}")

    # 2. Get most recent credit report
    report = db.query(CreditReport).filter_by(
        client_id=CLIENT_ID
    ).order_by(CreditReport.created_at.desc()).first()

    if not report:
        print(f"❌ No credit reports found for client {CLIENT_ID}")
        exit(1)

    print(f"✅ Report found: {report.created_at}")
    print(f"   Provider: {report.credit_provider}")

    # 3. Run Stage 1 Analysis
    print("\n🤖 Running FCRA analysis with Claude API...")
    print("   This may take 2-3 minutes...\n")

    result = run_stage1_for_all_sections(
        client_name=client.name,
        cmm_id='',  # Optional CMM contact ID
        provider=report.credit_provider or 'Unknown',
        credit_report_text=report.report_html,
        analysis_mode='manual',
        dispute_round=1,
        previous_letters='',
        bureau_responses='',
        dispute_timeline=''
    )

    if not result.get('success'):
        print(f"❌ Analysis failed: {result.get('error')}")
        exit(1)

    # 4. Save Analysis record
    litigation_data = result.get('litigation_data', {})

    analysis = Analysis(
        credit_report_id=report.id,
        client_id=client.id,
        client_name=client.name,
        dispute_round=1,
        analysis_mode='manual',
        stage=1,
        stage_1_analysis=str(litigation_data),
        cost=result.get('cost', 0),
        tokens_used=result.get('tokens_used', 0),
        cache_read=result.get('cache_read', False),
        created_at=datetime.utcnow()
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 5. Display Results
    print("✅ FCRA ANALYSIS COMPLETE!")
    print(f"\n📊 Analysis ID: {analysis.id}")
    print(f"💰 Cost: ${result.get('cost', 0):.4f}")
    print(f"🎯 Tokens Used: {result.get('tokens_used', 0):,}")
    print(f"💾 Cache Read: {result.get('cache_read', False)}")

    violations = litigation_data.get('violations', [])
    print(f"\n⚖️  Violations Found: {len(violations)}")

    if violations:
        print("\nTop violations:")
        for i, v in enumerate(violations[:5], 1):
            print(f"   {i}. {v.get('type', 'Unknown')} - {v.get('description', '')[:60]}...")

    print(f"\n🔗 Review URL:")
    print(f"   https://your-replit-url/analysis/{analysis.id}/review")

    print("\n✨ Next Steps:")
    print("   1. Review analysis in browser")
    print("   2. Edit if needed")
    print("   3. Approve to generate documents")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
```

**Run it:**
```bash
python3 analyze_report.py
```

### Option B: API Call (cURL)

```bash
# Upload and analyze in one request
curl -X POST https://your-replit-url/api/credit-report/parse-and-analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/report.pdf" \
  -F "clientName=Shaun Smith" \
  -F "clientEmail=shaun@example.com" \
  -F "creditProvider=MyFreeScoreNow.com" \
  -F "disputeRound=1"
```

**Response:**
```json
{
  "success": true,
  "analysis_id": 123,
  "client_id": 125,
  "violations_found": 7,
  "review_url": "/analysis/123/review",
  "parsed_data": {
    "bureau": "MyFreeScoreNow.com",
    "accounts_count": 15,
    "inquiries_count": 3
  }
}
```

### Option C: API Call for HTML Reports

For MyFreeScoreNow HTML reports saved on server:

```python
import requests

# If you have HTML content
html_content = open('uploads/credit_reports/125_Shaun_Smith_*.html', 'r').read()

response = requests.post(
    'https://your-replit-url/api/credit-report/parse-and-analyze',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    data={
        'clientName': 'Shaun Smith',
        'clientEmail': 'shaun@example.com',
        'creditProvider': 'MyFreeScoreNow.com',
        'disputeRound': 1,
        'creditReportHTML': html_content  # Pass HTML directly
    }
)

result = response.json()
print(f"Analysis ID: {result['analysis_id']}")
print(f"Review URL: {result['review_url']}")
```

---

## 🗂️ Working with Your 26+ Successful Reports

### List All Reports:

```python
from database import SessionLocal, CreditReport

db = SessionLocal()
reports = db.query(CreditReport).order_by(CreditReport.created_at.desc()).all()

print(f"Total Reports: {len(reports)}\n")

for i, report in enumerate(reports[:10], 1):
    print(f"{i}. Client ID {report.client_id}: {report.client_name}")
    print(f"   Provider: {report.credit_provider}")
    print(f"   Date: {report.created_at}")
    print(f"   Report Date: {report.report_date or 'Not extracted'}")
    print()

db.close()
```

### Batch Analyze Multiple Reports:

```python
#!/usr/bin/env python3
"""Batch analyze multiple credit reports"""

from database import SessionLocal, CreditReport, Client, Analysis
from app import run_stage1_for_all_sections
from datetime import datetime
import time

db = SessionLocal()

# Get all reports without analysis
reports = db.query(CreditReport).outerjoin(Analysis).filter(
    Analysis.id == None  # No analysis exists
).limit(10).all()

print(f"Found {len(reports)} reports without analysis\n")

for i, report in enumerate(reports, 1):
    print(f"[{i}/{len(reports)}] Analyzing {report.client_name}...")

    try:
        result = run_stage1_for_all_sections(
            client_name=report.client_name,
            cmm_id='',
            provider=report.credit_provider or 'Unknown',
            credit_report_text=report.report_html,
            analysis_mode='manual',
            dispute_round=1,
            previous_letters='',
            bureau_responses='',
            dispute_timeline=''
        )

        if result.get('success'):
            # Save analysis
            litigation_data = result.get('litigation_data', {})
            analysis = Analysis(
                credit_report_id=report.id,
                client_id=report.client_id,
                client_name=report.client_name,
                dispute_round=1,
                analysis_mode='manual',
                stage=1,
                stage_1_analysis=str(litigation_data),
                cost=result.get('cost', 0),
                tokens_used=result.get('tokens_used', 0),
                created_at=datetime.utcnow()
            )
            db.add(analysis)
            db.commit()

            violations = len(litigation_data.get('violations', []))
            print(f"  ✅ Complete! {violations} violations found")
            print(f"  💰 Cost: ${result.get('cost', 0):.4f}")
        else:
            print(f"  ❌ Failed: {result.get('error')}")

        # Rate limiting (don't overwhelm Claude API)
        time.sleep(5)

    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.rollback()

    print()

db.close()
```

---

## 📊 Analysis Routes Reference

### Key Routes from app.py:

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/credit-report/parse-and-analyze` | POST | Upload & analyze report (auto Stage 1) |
| `/analysis/<id>/review` | GET | View analysis results |
| `/api/analysis/<id>/data` | GET | Get analysis JSON data |
| `/api/analysis/<id>/violations` | GET/POST | Get/update violations |
| `/api/analysis/<id>/standing` | GET/POST | Get/update standing |
| `/api/analysis/<id>/damages` | GET/POST | Get/update damages |
| `/api/analysis/<id>/complete` | POST | Mark analysis complete |
| `/api/generate/client-report/<id>` | POST | Generate PDF client report (Stage 2) |
| `/api/generate/internal-memo/<id>` | POST | Generate internal memo (Stage 2) |
| `/api/generate/round-letters/<id>` | POST | Generate dispute letters (Stage 2) |
| `/dashboard` | GET | Main dashboard with pipeline |
| `/dashboard/queue` | GET | Processing queue |

---

## 🎯 Next Steps After Analysis

### 1. Review Analysis Results

Navigate to: `https://your-replit-url/analysis/<analysis_id>/review`

**What you'll see:**
- **Violations Tab:** All FCRA violations detected
- **Standing Tab:** Legal standing analysis
- **Damages Tab:** Exposure calculation
- **Score Impact Tab:** Credit score improvement projection

### 2. Edit if Needed

- Click any section to edit
- Update violations, standing, damages
- Save changes

### 3. Approve Analysis

- Click "Approve" button
- Moves to Stage 2
- Ready for document generation

### 4. Generate Documents (Stage 2)

**From analysis review page:**
- **Client Report:** Full 40-50 page comprehensive report
- **Internal Memo:** 3-5 page staff analysis
- **Dispute Letters:** Bureau-specific letters

**OR via API:**
```bash
# Generate all documents
curl -X POST https://your-replit-url/api/generate/client-report/123
curl -X POST https://your-replit-url/api/generate/internal-memo/123
curl -X POST https://your-replit-url/api/generate/round-letters/123
```

---

## 💡 Tips & Best Practices

### 1. Rate Limiting
- Claude API has rate limits
- Space out batch analyses by 5-10 seconds
- Monitor API costs

### 2. Cost Management
- Stage 1 analysis: ~$0.50-$2.00 per report
- Uses Claude Opus/Sonnet models
- Cache hits reduce cost significantly

### 3. Quality Control
- Always review Stage 1 before approval
- Edit violations/damages as needed
- Verify legal standing is accurate

### 4. MyFreeScoreNow Reports
- Now fully supported with score extraction
- HTML format works same as PDF
- Scores mapped: TU → EXP → EQF

---

## 🐛 Troubleshooting

### Analysis Fails with "No API key"
```bash
# Check environment variable
echo $ANTHROPIC_API_KEY
```

### Analysis Takes Too Long
- Normal: 2-3 minutes per report
- Check Claude API status
- Increase timeout if needed

### Scores Not Showing
- Verify MyFreeScoreNow fix was pulled
- Check logs for "Using MyFreeScoreNow extraction method"
- Re-run import if needed

### "Insufficient standing" for all cases
- Review credit report text quality
- Ensure full report HTML was saved
- Check if report has sufficient violations

---

## ✅ Success Criteria

After completing Task 3:

- ✅ Latest changes pulled on Replit
- ✅ Client 125 test passes with scores extracted
- ✅ FCRA analysis runs successfully on at least 1 report
- ✅ Violations, standing, damages calculated
- ✅ Can review analysis in UI
- ✅ Documents can be generated

---

## 📞 Need Help?

If you encounter issues:

1. **Check logs:** Look for error messages in console
2. **Verify API key:** Ensure `ANTHROPIC_API_KEY` is set
3. **Test with one report first:** Don't batch until confirmed working
4. **Review analysis quality:** Edit if AI analysis needs refinement

---

**Status:** Ready to test! Pull changes and run analysis on your 26+ reports. 🚀
