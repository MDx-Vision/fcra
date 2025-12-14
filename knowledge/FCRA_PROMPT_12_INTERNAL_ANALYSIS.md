# FCRA PROMPT 12 V2: INTERNAL ANALYSIS (APPLE-STYLE)
## Upload Report → Generate Staff Case Review

**Version:** 2.0  
**Updated:** December 13, 2025  
**Use Case:** Quick internal review for case assessment  
**Output:** 5-6 page HTML internal analysis  
**Audience:** Staff only — NOT for client

---

## 📋 HOW TO USE:

**STEP 1:** Start new Claude chat

**STEP 2:** Upload credit report (PDF or PNG)

**STEP 3:** Paste client info block below

**STEP 4:** Copy everything from "PROMPT STARTS HERE" and paste

**STEP 5:** Claude generates Apple-style internal analysis

**STEP 6:** Use for case decision (accept/decline/need more info)

---

## 📝 CLIENT INFO TEMPLATE (Copy & Fill In):

```
CONSUMER INFORMATION:
- Full Name: [Name]
- SSN Last 4: [XXXX]
- DOB: [MM/DD/YYYY]
- State: [State]

INTAKE INFO:
- How did they hear about us? [Source]
- Primary concern: [Why they came in]
- Any recent denials? [Yes/No + details]

TODAY'S DATE: [Date]
CASE NUMBER: [Your case number]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

===========================================================================
FCRA INTERNAL ANALYSIS GENERATOR — APPLE-STYLE
===========================================================================

Analyze the uploaded credit report and generate INTERNAL staff analysis 
using the Apple-style design system below.

**OUTPUT:** One HTML document (5-6 pages) for staff case review.

**DO NOT generate any client-facing documents or letters.**

===========================================================================
DESIGN SYSTEM — APPLE-STYLE (INTERNAL)
===========================================================================

```css
/* Same design system as client documents but with STAFF ONLY markers */

:root {
  --brand-teal: #0d9488;
  --brand-teal-dark: #0f766e;
  --brand-navy: #1e3a5f;
  --brand-navy-dark: #0a2540;
  --text-primary: #1a1a2e;
  --text-secondary: #4a5568;
  --bg-cream: #faf9f7;
  --bg-white: #ffffff;
  
  /* Staff-specific colors */
  --staff-red: #dc2626;
  --proceed-green: #059669;
  --caution-yellow: #d97706;
  --reject-red: #dc2626;
}
```

===========================================================================
HTML TEMPLATE
===========================================================================

Generate this complete HTML document:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Internal Analysis - [CLIENT_NAME]</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --brand-teal: #0d9488;
      --brand-teal-dark: #0f766e;
      --brand-navy: #1e3a5f;
      --brand-navy-dark: #0a2540;
      --text-primary: #1a1a2e;
      --text-secondary: #4a5568;
      --text-muted: #718096;
      --bg-cream: #faf9f7;
      --bg-white: #ffffff;
      --border-subtle: #e8e6e3;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'DM Sans', -apple-system, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: var(--text-primary);
      background: var(--bg-cream);
    }
    
    .page {
      max-width: 8.5in;
      margin: 20px auto;
      background: var(--bg-white);
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* ========================================
       HEADER
       ======================================== */
    .header {
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      padding: 25px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .brand {
      display: flex;
      align-items: center;
      gap: 15px;
    }
    
    .brand-name {
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--brand-teal);
      letter-spacing: 2px;
      text-transform: uppercase;
    }
    
    .doc-type {
      font-family: 'Playfair Display', serif;
      font-size: 13px;
      color: rgba(255,255,255,0.6);
    }
    
    .staff-badge {
      background: #dc2626;
      color: white;
      padding: 6px 14px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 3px;
    }
    
    /* ========================================
       CLIENT INFO BAR
       ======================================== */
    .client-bar {
      background: var(--bg-cream);
      padding: 18px 40px;
      border-bottom: 1px solid var(--border-subtle);
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }
    
    .info-item label {
      font-size: 9px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }
    
    .info-item p {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      margin-top: 2px;
    }
    
    /* ========================================
       EXECUTIVE SUMMARY BOX
       ======================================== */
    .exec-summary {
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      margin: 25px 40px;
      border-radius: 8px;
      padding: 25px;
    }
    
    .exec-title {
      font-family: 'Playfair Display', serif;
      font-size: 14px;
      color: rgba(255,255,255,0.6);
      margin-bottom: 20px;
      text-align: center;
    }
    
    .exec-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
    }
    
    .exec-item {
      text-align: center;
      padding: 12px;
      background: rgba(255,255,255,0.05);
      border-radius: 6px;
    }
    
    .exec-label {
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--brand-teal);
      margin-bottom: 6px;
    }
    
    .exec-value {
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      font-weight: 700;
      color: white;
    }
    
    /* ========================================
       DECISION BOX
       ======================================== */
    .decision-box {
      margin: 0 40px 25px;
      padding: 25px 30px;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .decision-box.proceed {
      background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    }
    
    .decision-box.caution {
      background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
    }
    
    .decision-box.reject {
      background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
    }
    
    .decision-text {
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      font-weight: 700;
      color: white;
    }
    
    .decision-sub {
      font-size: 12px;
      color: rgba(255,255,255,0.8);
      margin-top: 4px;
    }
    
    .decision-right {
      text-align: right;
      color: white;
    }
    
    .decision-prob-label {
      font-size: 11px;
      opacity: 0.8;
    }
    
    .decision-prob-value {
      font-size: 24px;
      font-weight: 700;
    }
    
    /* ========================================
       QUICK STATS ROW
       ======================================== */
    .quick-stats {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      margin: 0 40px 25px;
    }
    
    .quick-stat {
      background: var(--bg-cream);
      padding: 15px;
      border-radius: 6px;
      text-align: center;
    }
    
    .quick-stat-value {
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      font-weight: 700;
      color: var(--brand-teal);
    }
    
    .quick-stat-label {
      font-size: 9px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    
    /* ========================================
       CONTENT
       ======================================== */
    .content {
      padding: 0 40px 40px;
    }
    
    .section {
      margin-bottom: 30px;
    }
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--brand-teal);
    }
    
    .section-number {
      width: 26px;
      height: 26px;
      background: var(--brand-navy);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 700;
    }
    
    .section-title {
      font-family: 'Playfair Display', serif;
      font-size: 17px;
      font-weight: 600;
      color: var(--brand-navy);
    }
    
    /* ========================================
       TABLES
       ======================================== */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin: 15px 0;
    }
    
    th {
      background: var(--brand-navy);
      color: white;
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    th:first-child { border-radius: 5px 0 0 0; }
    th:last-child { border-radius: 0 5px 0 0; }
    
    td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border-subtle);
    }
    
    tr:hover { background: var(--bg-cream); }
    
    /* ========================================
       BADGES
       ======================================== */
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .badge-critical { background: #fef2f2; color: #dc2626; }
    .badge-high { background: #fff7ed; color: #ea580c; }
    .badge-medium { background: #fefce8; color: #ca8a04; }
    .badge-low { background: #f0fdf4; color: #16a34a; }
    .badge-confirmed { background: #f0fdf4; color: #16a34a; }
    .badge-conditional { background: #fefce8; color: #ca8a04; }
    .badge-missing { background: #fef2f2; color: #dc2626; }
    
    .badge-tier1 { background: #dc2626; color: white; }
    .badge-tier2 { background: #f59e0b; color: white; }
    .badge-tier3 { background: #16a34a; color: white; }
    
    /* ========================================
       ASSESSMENT BOXES
       ======================================== */
    .assessment-box {
      padding: 15px 20px;
      border-radius: 6px;
      margin: 15px 0;
      border-left: 4px solid;
    }
    
    .assessment-box.strong {
      background: #f0fdf4;
      border-color: #16a34a;
    }
    
    .assessment-box.moderate {
      background: #fefce8;
      border-color: #ca8a04;
    }
    
    .assessment-box.weak {
      background: #fef2f2;
      border-color: #dc2626;
    }
    
    .assessment-title {
      font-weight: 600;
      margin-bottom: 5px;
    }
    
    .assessment-text {
      font-size: 13px;
      color: var(--text-secondary);
    }
    
    /* ========================================
       TWO COLUMN LAYOUT
       ======================================== */
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 25px;
    }
    
    .col h4 {
      color: var(--brand-navy);
      font-size: 13px;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }
    
    .col ul {
      padding-left: 20px;
      color: var(--text-secondary);
      font-size: 13px;
    }
    
    .col li {
      margin-bottom: 6px;
    }
    
    /* ========================================
       FOOTER
       ======================================== */
    .footer {
      background: var(--brand-navy-dark);
      padding: 18px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .footer-brand {
      font-size: 10px;
      font-weight: 600;
      color: var(--brand-teal);
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    
    .footer-info {
      font-size: 10px;
      color: rgba(255,255,255,0.4);
    }
    
    /* ========================================
       PRINT STYLES
       ======================================== */
    @media print {
      body { background: white; }
      .page { box-shadow: none; margin: 0; }
    }
  </style>
</head>
<body>

<div class="page">
  
  <!-- ========================================
       HEADER
       ======================================== -->
  <div class="header">
    <div class="brand">
      <div>
        <div class="brand-name">Brightpath Ascend Group</div>
        <div class="doc-type">Internal Case Analysis</div>
      </div>
    </div>
    <div class="staff-badge">Staff Only — Not for Client</div>
  </div>
  
  <!-- ========================================
       CLIENT INFO BAR
       ======================================== -->
  <div class="client-bar">
    <div class="info-item">
      <label>Client</label>
      <p>[CLIENT_NAME]</p>
    </div>
    <div class="info-item">
      <label>Case Number</label>
      <p>[CASE_NUMBER]</p>
    </div>
    <div class="info-item">
      <label>Report Date</label>
      <p>[REPORT_DATE]</p>
    </div>
    <div class="info-item">
      <label>Scores</label>
      <p>TU: [TU_SCORE] | EX: [EX_SCORE] | EQ: [EQ_SCORE]</p>
    </div>
  </div>
  
  <!-- ========================================
       EXECUTIVE SUMMARY
       ======================================== -->
  <div class="exec-summary">
    <div class="exec-title">Executive Summary</div>
    <div class="exec-grid">
      <div class="exec-item">
        <div class="exec-label">Case Strength</div>
        <div class="exec-value">[CASE_STRENGTH]/10</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Standing</div>
        <div class="exec-value">[STANDING_SCORE]/10</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Willfulness</div>
        <div class="exec-value">[WILLFULNESS]%</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Est. Value</div>
        <div class="exec-value">$[EST_VALUE]K</div>
      </div>
    </div>
  </div>
  
  <!-- ========================================
       DECISION BOX
       ======================================== -->
  <div class="decision-box [DECISION_CLASS]">
    <div>
      <div class="decision-text">[DECISION_TEXT]</div>
      <div class="decision-sub">[DECISION_REASON]</div>
    </div>
    <div class="decision-right">
      <div class="decision-prob-label">Settlement Probability</div>
      <div class="decision-prob-value">[SETTLEMENT_PROB]%</div>
    </div>
  </div>
  
  <!-- ========================================
       QUICK STATS
       ======================================== -->
  <div class="quick-stats">
    <div class="quick-stat">
      <div class="quick-stat-value">[VIOLATION_COUNT]</div>
      <div class="quick-stat-label">Violations</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">[DEFENDANT_COUNT]</div>
      <div class="quick-stat-label">Defendants</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">[CONTRADICTION_COUNT]</div>
      <div class="quick-stat-label">Contradictions</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">[AVG_SCORE]</div>
      <div class="quick-stat-label">Avg Score</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">[EST_DAYS]</div>
      <div class="quick-stat-label">Est. Days</div>
    </div>
  </div>
  
  <!-- ========================================
       CONTENT SECTIONS
       ======================================== -->
  <div class="content">
    
    <!-- SECTION 1: STANDING -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">1</div>
        <div class="section-title">Standing Analysis (TransUnion v. Ramirez)</div>
      </div>
      
      <table>
        <tr>
          <th>Element</th>
          <th>Status</th>
          <th>Score</th>
          <th>Evidence</th>
          <th>Action Needed</th>
        </tr>
        <tr>
          <td><strong>Dissemination</strong></td>
          <td><span class="badge badge-[DISS_STATUS]">[DISS_STATUS]</span></td>
          <td>[DISS_SCORE]/10</td>
          <td>[DISS_EVIDENCE]</td>
          <td>[DISS_ACTION]</td>
        </tr>
        <tr>
          <td><strong>Concrete Harm</strong></td>
          <td><span class="badge badge-[HARM_STATUS]">[HARM_STATUS]</span></td>
          <td>[HARM_SCORE]/10</td>
          <td>[HARM_EVIDENCE]</td>
          <td>[HARM_ACTION]</td>
        </tr>
        <tr>
          <td><strong>Causation</strong></td>
          <td><span class="badge badge-[CAUSE_STATUS]">[CAUSE_STATUS]</span></td>
          <td>[CAUSE_SCORE]/10</td>
          <td>[CAUSE_EVIDENCE]</td>
          <td>[CAUSE_ACTION]</td>
        </tr>
      </table>
      
      <div class="assessment-box [STANDING_BOX_CLASS]">
        <div class="assessment-title">Standing Verdict: [STANDING_VERDICT]</div>
        <div class="assessment-text">[STANDING_ANALYSIS]</div>
      </div>
    </div>
    
    <!-- SECTION 2: VIOLATIONS -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">2</div>
        <div class="section-title">Violation Summary</div>
      </div>
      
      <table>
        <tr>
          <th>Category</th>
          <th>Count</th>
          <th>Severity</th>
          <th>Defendants</th>
          <th>FCRA Section</th>
        </tr>
        [VIOLATION_ROWS]
      </table>
    </div>
    
    <!-- SECTION 3: CRITICAL VIOLATIONS -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">3</div>
        <div class="section-title">Critical Violations — Impossible Contradictions</div>
      </div>
      
      <table>
        <tr>
          <th>Account</th>
          <th>Balance</th>
          <th>TransUnion</th>
          <th>Experian</th>
          <th>Equifax</th>
          <th>Violation</th>
        </tr>
        [CONTRADICTION_ROWS]
      </table>
    </div>
    
    <!-- SECTION 4: WILLFULNESS -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">4</div>
        <div class="section-title">Willfulness Assessment (Safeco Standard)</div>
      </div>
      
      <table>
        <tr>
          <th>Factor</th>
          <th>Present?</th>
          <th>Weight</th>
          <th>Analysis</th>
        </tr>
        <tr>
          <td>Objectively Impossible Scenarios</td>
          <td>[IMPOSSIBLE_PRESENT]</td>
          <td>High</td>
          <td>[IMPOSSIBLE_ANALYSIS]</td>
        </tr>
        <tr>
          <td>Pattern of Violations</td>
          <td>[PATTERN_PRESENT]</td>
          <td>High</td>
          <td>[PATTERN_ANALYSIS]</td>
        </tr>
        <tr>
          <td>Defendant Sophistication</td>
          <td>[SOPHISTICATION_PRESENT]</td>
          <td>Medium</td>
          <td>[SOPHISTICATION_ANALYSIS]</td>
        </tr>
        <tr>
          <td>Metro 2® Certification</td>
          <td>[METRO2_PRESENT]</td>
          <td>High</td>
          <td>[METRO2_ANALYSIS]</td>
        </tr>
        <tr>
          <td>Prior Industry Knowledge</td>
          <td>[PRIOR_PRESENT]</td>
          <td>High</td>
          <td>[PRIOR_ANALYSIS]</td>
        </tr>
      </table>
      
      <div class="assessment-box [WILLFULNESS_BOX_CLASS]">
        <div class="assessment-title">Willfulness Probability: [WILLFULNESS]%</div>
        <div class="assessment-text">[WILLFULNESS_CONCLUSION]</div>
      </div>
    </div>
    
    <!-- SECTION 5: DAMAGES -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">5</div>
        <div class="section-title">Damages Calculation</div>
      </div>
      
      <table>
        <tr>
          <th>Component</th>
          <th>Conservative</th>
          <th>Moderate</th>
          <th>Aggressive</th>
        </tr>
        <tr>
          <td>Statutory Damages</td>
          <td>$[STAT_CONS]</td>
          <td>$[STAT_MOD]</td>
          <td>$[STAT_AGG]</td>
        </tr>
        <tr>
          <td>Punitive Damages</td>
          <td>$[PUN_CONS]</td>
          <td>$[PUN_MOD]</td>
          <td>$[PUN_AGG]</td>
        </tr>
        <tr>
          <td>Actual Damages</td>
          <td>$[ACT_CONS]</td>
          <td>$[ACT_MOD]</td>
          <td>$[ACT_AGG]</td>
        </tr>
        <tr>
          <td>Attorney Fees (Est.)</td>
          <td>$[FEE_CONS]</td>
          <td>$[FEE_MOD]</td>
          <td>$[FEE_AGG]</td>
        </tr>
        <tr style="background: var(--brand-navy); color: white;">
          <td><strong>TOTAL</strong></td>
          <td><strong>$[TOTAL_CONS]</strong></td>
          <td><strong>$[TOTAL_MOD]</strong></td>
          <td><strong>$[TOTAL_AGG]</strong></td>
        </tr>
      </table>
    </div>
    
    <!-- SECTION 6: DEFENDANTS -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">6</div>
        <div class="section-title">Defendant Targeting</div>
      </div>
      
      <table>
        <tr>
          <th>Priority</th>
          <th>Defendant</th>
          <th>Violations</th>
          <th>Primary Basis</th>
          <th>Settlement Target</th>
        </tr>
        [DEFENDANT_ROWS]
        <tr style="background: var(--bg-cream); font-weight: 600;">
          <td colspan="2">TOTAL</td>
          <td>[VIOLATION_COUNT]</td>
          <td></td>
          <td>$[SETTLEMENT_TARGET]</td>
        </tr>
      </table>
    </div>
    
    <!-- SECTION 7: ACTION ITEMS -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">7</div>
        <div class="section-title">Action Items</div>
      </div>
      
      <div class="two-col">
        <div class="col">
          <h4>Pre-Approval (Before Client Docs)</h4>
          <ul>
            [PRE_APPROVAL_ITEMS]
          </ul>
        </div>
        <div class="col">
          <h4>Post-Approval (After Client Signs)</h4>
          <ul>
            [POST_APPROVAL_ITEMS]
          </ul>
        </div>
      </div>
    </div>
    
    <!-- SECTION 8: TIMELINE -->
    <div class="section">
      <div class="section-header">
        <div class="section-number">8</div>
        <div class="section-title">RLPP Timeline</div>
      </div>
      
      <table>
        <tr>
          <th>Phase</th>
          <th>Days</th>
          <th>Action</th>
          <th>Expected Outcome</th>
        </tr>
        <tr>
          <td><strong>Round 1</strong></td>
          <td>1-30</td>
          <td>Formal disputes to all defendants</td>
          <td>Initial responses, some deletions</td>
        </tr>
        <tr>
          <td><strong>Round 2</strong></td>
          <td>31-60</td>
          <td>MOV demands for verified items</td>
          <td>Additional deletions, evidence gathering</td>
        </tr>
        <tr>
          <td><strong>Round 3</strong></td>
          <td>61-90</td>
          <td>Regulatory complaints (CFPB/FTC/AG)</td>
          <td>Regulatory pressure, settlement offers</td>
        </tr>
        <tr>
          <td><strong>Round 4</strong></td>
          <td>91-120</td>
          <td>Pre-arbitration demands</td>
          <td>Final deletions or litigation referral</td>
        </tr>
      </table>
    </div>
    
  </div>
  
  <!-- ========================================
       FOOTER
       ======================================== -->
  <div class="footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Case: [CASE_NUMBER] | Confidential — Internal Use Only</div>
  </div>
  
</div>

</body>
</html>
```

===========================================================================
DECISION BOX LOGIC
===========================================================================

Based on Case Strength and Standing Score, set DECISION_CLASS and DECISION_TEXT:

**PROCEED (Green):**
- Case Strength ≥ 7 AND Standing ≥ 6
- DECISION_CLASS = "proceed"
- DECISION_TEXT = "✓ PROCEED"
- DECISION_REASON = "Strong case, proceed immediately"

**CAUTION (Yellow):**
- Case Strength ≥ 5 AND Standing ≥ 4
- DECISION_CLASS = "caution"
- DECISION_TEXT = "⚠ ACCEPT WITH CONDITIONS"
- DECISION_REASON = "Need [specific items] before proceeding"

**REJECT (Red):**
- Case Strength < 5 OR Standing < 4
- DECISION_CLASS = "reject"
- DECISION_TEXT = "✕ DECLINE"
- DECISION_REASON = "Insufficient for litigation — [reason]"

===========================================================================
STANDING ANALYSIS LOGIC
===========================================================================

**Dissemination (Was info shared with third parties?):**
- CONFIRMED: 3+ hard inquiries in last 2 years
- CONDITIONAL: 1-2 inquiries
- MISSING: 0 inquiries

**Concrete Harm (Did consumer suffer real harm?):**
- CONFIRMED: Denial letter or adverse action in hand
- CONDITIONAL: Claims harm but no documentation
- MISSING: No evidence of harm

**Causation (Link between inaccuracy and harm?):**
- CONFIRMED: Clear timeline showing cause → effect
- CONDITIONAL: Likely but needs strengthening
- MISSING: No clear connection

===========================================================================
WILLFULNESS FACTORS
===========================================================================

Score each factor as:
- ✓ Yes (supports willfulness)
- ✕ No (does not support)
- — N/A or unknown

Calculate percentage based on weighted factors.

===========================================================================
OUTPUT INSTRUCTIONS
===========================================================================

1. Generate complete HTML document
2. Replace all [PLACEHOLDERS] with actual data
3. Use correct badge classes based on status
4. Color-code the decision box correctly
5. Calculate all metrics from credit report analysis
6. Output as single HTML file

**DO NOT generate any client-facing documents or letters.**

===========================================================================
END OF PROMPT
===========================================================================
