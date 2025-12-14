# FCRA PROMPT 13 V2: LAWYER-READY PACKAGE GENERATOR
## WITH EMBEDDED APPLE-STYLE + TRADITIONAL TEMPLATES

**Version:** 2.0  
**Updated:** December 13, 2025  
**Author:** Brightpath Ascend Group  
**Purpose:** Generate complete 4-document lawyer-ready litigation packages with premium styling

---

## OVERVIEW

This prompt generates a complete **4-document FCRA litigation package** with professional styling:
- **Apple-style** for client-facing documents (modern, premium feel)
- **Traditional Law Firm** for attorney documents (credible, formal)

### DOCUMENTS GENERATED

| # | Document | Style | Audience | Pages | Purpose |
|---|----------|-------|----------|-------|---------|
| 1 | Internal Analysis | Apple-style | Staff/BAG Team | 5-6 | Quick-scan case review, go/no-go decision |
| 2 | Client Email | Apple-style | Client (email body) | 1 | Overview with key stats and CTA |
| 3 | Client Report | Apple-style | Client (PDF) | 7 | Streamlined professional report |
| 4 | Legal Memorandum | Traditional | Attorneys | 3-4 | Case law analysis, litigation strategy |

---

## DESIGN SYSTEM

### Apple-Style (Documents 1, 2, 3)

```css
/* FONTS */
--font-display: 'Playfair Display', Georgia, serif;
--font-body: 'DM Sans', -apple-system, sans-serif;

/* COLORS */
--brand-teal: #0d9488;
--brand-teal-dark: #0f766e;
--brand-teal-light: #14b8a6;
--brand-navy: #1e3a5f;
--brand-navy-dark: #0a2540;
--text-primary: #1a1a2e;
--text-secondary: #4a5568;
--bg-cream: #faf9f7;

/* CHARACTERISTICS */
- Clean whitespace
- Gradient accent boxes
- Rounded corners (3px)
- Subtle shadows
- Premium feel
```

### Traditional Law Firm (Document 4)

```css
/* FONTS */
font-family: 'Times New Roman', Times, Georgia, serif;
font-size: 12pt;
line-height: 2; /* Double-spaced */

/* COLORS */
- Black text on white
- Gray table headers (#e8e8e8)
- Green/Yellow/Red assessment boxes

/* CHARACTERISTICS */
- Double-ruled borders
- Uppercase section headers
- Proper Bluebook citations
- Dense, formal paragraphs
- 0.5in first-line indent
```

---

## FILE NAMING CONVENTION

```
[DocumentType]_[LASTNAME]_[INITIALS]_[MMDDYYYY].[ext]
```

### Examples:
- `Internal_Analysis_PERDOMO_WE_12132025.html`
- `Email_Client_PERDOMO_WE_12132025.html`
- `Client_Report_PERDOMO_WE_12132025.html`
- `Legal_Memo_PERDOMO_WE_12132025.html`

---

## WORKFLOW

```
STEP 1: Import credit report
    ↓
STEP 2: Run violation detection + standing analysis
    ↓
STEP 3: Generate Internal Analysis (Document 1)
    ↓
STEP 4: Human review checkpoint
    ↓
STEP 5: If approved → Generate Documents 2, 3, 4
    ↓
STEP 6: Deliver to client + file for attorney
```

---

## =======================================================================
## DOCUMENT 1: INTERNAL ANALYSIS (Apple-Style)
## =======================================================================

Generate this HTML structure for internal staff review:

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
      --bg-cream: #faf9f7;
      --bg-white: #ffffff;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: var(--text-primary);
      background: var(--bg-cream);
    }
    
    .page {
      max-width: 8.5in;
      margin: 0 auto;
      background: var(--bg-white);
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* HEADER */
    .header {
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      padding: 30px 40px;
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
      font-size: 18px;
      font-weight: 700;
      color: var(--brand-teal);
      letter-spacing: 2px;
      text-transform: uppercase;
    }
    
    .doc-type {
      font-family: 'Playfair Display', serif;
      font-size: 14px;
      color: rgba(255,255,255,0.7);
    }
    
    .confidential {
      background: #dc2626;
      color: white;
      padding: 6px 14px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 3px;
    }
    
    /* CLIENT INFO BAR */
    .client-bar {
      background: var(--bg-cream);
      padding: 20px 40px;
      border-bottom: 1px solid #e5e5e5;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }
    
    .info-item label {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
    }
    
    .info-item p {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-top: 2px;
    }
    
    /* EXECUTIVE SUMMARY */
    .exec-summary {
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      margin: 30px 40px;
      border-radius: 8px;
      padding: 30px;
    }
    
    .exec-title {
      font-family: 'Playfair Display', serif;
      font-size: 16px;
      color: rgba(255,255,255,0.7);
      margin-bottom: 20px;
      text-align: center;
    }
    
    .exec-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }
    
    .exec-item {
      text-align: center;
      padding: 15px;
      background: rgba(255,255,255,0.05);
      border-radius: 6px;
    }
    
    .exec-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--brand-teal);
      margin-bottom: 8px;
    }
    
    .exec-value {
      font-family: 'Playfair Display', serif;
      font-size: 28px;
      font-weight: 700;
      color: white;
    }
    
    /* DECISION BOX */
    .decision-box {
      margin: 0 40px 30px;
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
      font-size: 24px;
      font-weight: 700;
      color: white;
    }
    
    .decision-sub {
      font-size: 13px;
      color: rgba(255,255,255,0.8);
      margin-top: 4px;
    }
    
    /* CONTENT */
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
      width: 28px;
      height: 28px;
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
      font-size: 18px;
      font-weight: 600;
      color: var(--brand-navy);
    }
    
    /* TABLES */
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
    
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #e5e5e5;
    }
    
    tr:hover {
      background: var(--bg-cream);
    }
    
    /* BADGES */
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
    .badge-confirmed { background: #f0fdf4; color: #16a34a; }
    .badge-conditional { background: #fefce8; color: #ca8a04; }
    
    /* FOOTER */
    .footer {
      background: var(--brand-navy-dark);
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .footer-brand {
      font-size: 11px;
      font-weight: 600;
      color: var(--brand-teal);
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    
    .footer-info {
      font-size: 10px;
      color: rgba(255,255,255,0.5);
    }
    
    @media print {
      body { background: white; }
      .page { box-shadow: none; }
    }
  </style>
</head>
<body>
  <div class="page">
    
    <!-- HEADER -->
    <div class="header">
      <div class="brand">
        <div>
          <div class="brand-name">Brightpath Ascend Group</div>
          <div class="doc-type">Internal Case Analysis</div>
        </div>
      </div>
      <div class="confidential">Staff Only — Not for Client</div>
    </div>
    
    <!-- CLIENT INFO BAR -->
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
    
    <!-- EXECUTIVE SUMMARY -->
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
    
    <!-- DECISION BOX -->
    <div class="decision-box [DECISION_CLASS]">
      <div>
        <div class="decision-text">[DECISION_TEXT]</div>
        <div class="decision-sub">[DECISION_REASON]</div>
      </div>
      <div style="text-align: right; color: white;">
        <div style="font-size: 12px; opacity: 0.8;">Settlement Probability</div>
        <div style="font-size: 24px; font-weight: 700;">[SETTLEMENT_PROB]%</div>
      </div>
    </div>
    
    <!-- CONTENT SECTIONS -->
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
          </tr>
          <tr>
            <td><strong>Dissemination</strong></td>
            <td><span class="badge badge-[DISS_STATUS]">[DISS_STATUS]</span></td>
            <td>[DISS_SCORE]/10</td>
            <td>[DISS_EVIDENCE]</td>
          </tr>
          <tr>
            <td><strong>Concrete Harm</strong></td>
            <td><span class="badge badge-[HARM_STATUS]">[HARM_STATUS]</span></td>
            <td>[HARM_SCORE]/10</td>
            <td>[HARM_EVIDENCE]</td>
          </tr>
          <tr>
            <td><strong>Causation</strong></td>
            <td><span class="badge badge-[CAUSE_STATUS]">[CAUSE_STATUS]</span></td>
            <td>[CAUSE_SCORE]/10</td>
            <td>[CAUSE_EVIDENCE]</td>
          </tr>
        </table>
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
          </tr>
          [CONTRADICTION_ROWS]
        </table>
      </div>
      
      <!-- SECTION 4: DAMAGES -->
      <div class="section">
        <div class="section-header">
          <div class="section-number">4</div>
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
          <tr style="background: var(--brand-navy); color: white;">
            <td><strong>TOTAL</strong></td>
            <td><strong>$[TOTAL_CONS]</strong></td>
            <td><strong>$[TOTAL_MOD]</strong></td>
            <td><strong>$[TOTAL_AGG]</strong></td>
          </tr>
        </table>
      </div>
      
      <!-- SECTION 5: DEFENDANTS -->
      <div class="section">
        <div class="section-header">
          <div class="section-number">5</div>
          <div class="section-title">Defendant Targeting</div>
        </div>
        <table>
          <tr>
            <th>Priority</th>
            <th>Defendant</th>
            <th>Violations</th>
            <th>Settlement Target</th>
          </tr>
          [DEFENDANT_ROWS]
        </table>
      </div>
      
      <!-- SECTION 6: ACTION ITEMS -->
      <div class="section">
        <div class="section-header">
          <div class="section-number">6</div>
          <div class="section-title">Action Items</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
          <div>
            <h4 style="color: var(--brand-navy); margin-bottom: 10px;">Pre-Approval</h4>
            <ul style="padding-left: 20px; color: var(--text-secondary);">
              [PRE_APPROVAL_ITEMS]
            </ul>
          </div>
          <div>
            <h4 style="color: var(--brand-navy); margin-bottom: 10px;">Post-Approval</h4>
            <ul style="padding-left: 20px; color: var(--text-secondary);">
              [POST_APPROVAL_ITEMS]
            </ul>
          </div>
        </div>
      </div>
      
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
      <div class="footer-brand">Brightpath Ascend Group</div>
      <div class="footer-info">Case: [CASE_NUMBER] | Confidential — Internal Use Only</div>
    </div>
    
  </div>
</body>
</html>
```

---

## =======================================================================
## DOCUMENT 2: CLIENT EMAIL (Apple-Style)
## =======================================================================

Generate this HTML structure for client email:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Analysis is Ready - [CLIENT_NAME]</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --brand-teal: #0d9488;
      --brand-teal-dark: #0f766e;
      --brand-teal-light: #14b8a6;
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
      font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 16px;
      line-height: 1.7;
      color: var(--text-primary);
      background: linear-gradient(180deg, #f0f0f0 0%, #e8e6e3 100%);
      padding: 40px 20px;
    }
    
    .email-wrapper { max-width: 600px; margin: 0 auto; }
    
    .email-container {
      background: var(--bg-white);
      border-radius: 3px;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(10, 37, 64, 0.12);
    }
    
    .email-hero {
      position: relative;
      background: var(--brand-navy-dark);
      padding: 48px 40px;
      text-align: center;
    }
    
    .email-hero::after {
      content: '';
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--brand-teal), var(--brand-teal-light), var(--brand-teal));
    }
    
    .brand-name {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 6px;
      color: var(--brand-teal-light);
      text-transform: uppercase;
      margin-bottom: 12px;
    }
    
    .hero-title {
      font-family: 'Playfair Display', serif;
      font-size: 17px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .email-body { padding: 45px 40px; }
    
    .greeting {
      font-family: 'Playfair Display', serif;
      font-size: 20px;
      color: var(--brand-navy);
      margin-bottom: 24px;
    }
    
    .intro-text {
      font-size: 16px;
      color: var(--text-secondary);
      margin-bottom: 16px;
      line-height: 1.75;
    }
    
    .intro-text strong {
      color: var(--brand-navy);
      font-weight: 600;
    }
    
    .key-finding {
      background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%);
      border-radius: 3px;
      padding: 28px 30px;
      margin: 32px 0;
      border-left: 4px solid var(--brand-teal);
    }
    
    .key-finding-label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      color: var(--brand-teal);
      margin-bottom: 10px;
    }
    
    .key-finding-text {
      font-size: 16px;
      color: var(--text-primary);
      line-height: 1.65;
    }
    
    .stats-container {
      background: var(--bg-cream);
      border-radius: 3px;
      padding: 12px;
      margin: 32px 0;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
    
    .stat-card {
      text-align: center;
      padding: 18px 6px;
      background: var(--bg-white);
      border-radius: 2px;
    }
    
    .stat-number {
      font-size: 22px;
      font-weight: 700;
      color: var(--brand-teal);
      margin-bottom: 6px;
    }
    
    .stat-label {
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      color: var(--text-muted);
    }
    
    .value-card {
      background: var(--brand-navy-dark);
      border-radius: 3px;
      padding: 40px;
      margin: 32px 0;
      text-align: center;
    }
    
    .value-label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: var(--brand-teal-light);
      margin-bottom: 12px;
    }
    
    .value-amount {
      font-family: 'Playfair Display', serif;
      font-size: 42px;
      font-weight: 700;
      color: white;
    }
    
    .cta-section {
      text-align: center;
      margin: 40px 0 32px;
    }
    
    .cta-title {
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      font-weight: 700;
      color: var(--brand-navy);
      margin-bottom: 8px;
    }
    
    .cta-text {
      font-size: 15px;
      color: var(--text-muted);
      margin-bottom: 24px;
    }
    
    .cta-button {
      display: inline-block;
      background: var(--brand-teal);
      color: white;
      padding: 18px 48px;
      text-decoration: none;
      font-size: 15px;
      font-weight: 700;
      border-radius: 4px;
      box-shadow: 0 4px 14px rgba(13, 148, 136, 0.4);
    }
    
    .signature {
      margin-top: 40px;
      padding-top: 28px;
      border-top: 1px solid var(--border-subtle);
      text-align: center;
    }
    
    .signature-name {
      font-family: 'Playfair Display', serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--brand-navy);
    }
    
    .signature-contact {
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 8px;
    }
    
    .email-footer {
      background: var(--brand-navy-dark);
      padding: 30px 40px;
      text-align: center;
    }
    
    .footer-brand {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--brand-teal-light);
      text-transform: uppercase;
    }
    
    .footer-disclaimer {
      font-size: 10px;
      color: rgba(255, 255, 255, 0.3);
      margin-top: 10px;
    }
  </style>
</head>
<body>

<div class="email-wrapper">
  <div class="email-container">
    
    <div class="email-hero">
      <div class="brand-name">Brightpath Ascend Group</div>
      <div class="hero-title">Your Credit Analysis is Complete</div>
    </div>
    
    <div class="email-body">
      
      <p class="greeting">[CLIENT_FIRST_NAME],</p>
      
      <p class="intro-text">Your analysis is complete. <strong>We found violations.</strong> Real ones. The kind that get results.</p>
      
      <p class="intro-text">This isn't credit repair. It's federal consumer protection — and the law is on your side.</p>
      
      <div class="key-finding">
        <div class="key-finding-label">Key Finding</div>
        <p class="key-finding-text">[KEY_FINDING_TEXT]</p>
      </div>
      
      <div class="stats-container">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">[VIOLATION_COUNT]</div>
            <div class="stat-label">Violations</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">$[EST_VALUE]K</div>
            <div class="stat-label">Case Value</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">[SETTLEMENT_RATE]%</div>
            <div class="stat-label">Settlement</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">[ACCOUNT_COUNT]</div>
            <div class="stat-label">Accounts</div>
          </div>
        </div>
      </div>
      
      <div class="value-card">
        <div class="value-label">Your Case Value</div>
        <div class="value-amount">[VALUE_RANGE]</div>
      </div>
      
      <div class="cta-section">
        <div class="cta-title">Ready?</div>
        <p class="cta-text">Reply "APPROVED" and we start immediately.</p>
        <a href="mailto:support@brightpathascend.com?subject=APPROVED" class="cta-button">I'm In →</a>
      </div>
      
      <div class="signature">
        <div class="signature-name">Brightpath Ascend Group</div>
        <div class="signature-contact">
          support@brightpathascend.com<br>
          (917) 909-4051
        </div>
      </div>
      
    </div>
    
    <div class="email-footer">
      <div class="footer-brand">Brightpath Ascend Group</div>
      <div class="footer-disclaimer">
        Confidential | Case: [CASE_NUMBER]
      </div>
    </div>
    
  </div>
</div>

</body>
</html>
```

---

## =======================================================================
## DOCUMENT 3: CLIENT REPORT (Apple-Style, 7 Pages)
## =======================================================================

Generate a 7-page client report with the following structure:

### PAGE 1: COVER
- Navy gradient background
- Brightpath logo
- "CREDIT ANALYSIS REPORT"
- Client name, date, case number
- "Confidential — Prepared for [Client]"

### PAGE 2: EXECUTIVE SUMMARY
- 4-metric box (Case Strength, Standing, Willfulness, Value)
- Key Finding highlight box (teal accent)
- 6-stat grid (Violations, Defendants, Accounts, Score Avg, Settlement %, Timeline)
- Brief "What This Means" paragraph

### PAGE 3: YOUR RIGHTS
- What is FCRA (brief)
- Your 5 Core Rights (icon list)
- What CRAs Must Do
- What Furnishers Must Do

### PAGE 4: VIOLATION SUMMARY
- Violation category table
- Top 3 Critical Violations highlighted
- Visual severity badges

### PAGE 5: ACCOUNT ANALYSIS
- Account cards showing contradictions
- Bureau comparison columns
- Color-coded status (Open=green, Paid=blue, contradiction=red highlight)

### PAGE 6: DAMAGES & STRATEGY
- Damages table (Conservative/Moderate/Aggressive)
- Defendant priority list
- Settlement targets
- Timeline (4 phases)

### PAGE 7: NEXT STEPS
- What we need from you
- What happens next
- Contact information
- CTA section

**Use the same Apple-style CSS from Document 1, adapted for print/PDF.**

---

## =======================================================================
## DOCUMENT 4: LEGAL MEMORANDUM (Traditional Law Firm)
## =======================================================================

Generate this HTML structure for attorney review:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Legal Memorandum - [CASE_CAPTION]</title>
  <style>
    @page { size: letter; margin: 1in; }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'Times New Roman', Times, Georgia, serif;
      font-size: 12pt;
      line-height: 2;
      color: #000;
      background-color: #fff;
    }
    
    .page {
      max-width: 8.5in;
      margin: 0 auto;
      padding: 1in;
      background-color: white;
    }
    
    .memo-header {
      border-bottom: 3px double #000;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    
    .memo-header-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }
    
    .firm-name {
      font-size: 14pt;
      font-weight: bold;
      letter-spacing: 1px;
    }
    
    .firm-division {
      font-size: 10pt;
      font-style: italic;
      color: #333;
    }
    
    .confidential-stamp {
      text-align: right;
      font-size: 10pt;
      font-weight: bold;
      border: 2px solid #000;
      padding: 6px 12px;
      text-transform: uppercase;
    }
    
    .memo-title {
      text-align: center;
      font-size: 14pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin: 25px 0;
      text-decoration: underline;
    }
    
    .memo-row {
      display: flex;
      margin: 4px 0;
      line-height: 1.6;
    }
    
    .memo-label {
      width: 120px;
      font-weight: bold;
    }
    
    .exec-summary {
      border: 2px solid #000;
      padding: 20px;
      margin: 30px 0;
      background-color: #f9f9f9;
    }
    
    .exec-summary-title {
      font-size: 12pt;
      font-weight: bold;
      text-transform: uppercase;
      text-align: center;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #666;
    }
    
    .exec-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      text-align: center;
    }
    
    .exec-item-label {
      font-size: 9pt;
      text-transform: uppercase;
      color: #666;
    }
    
    .exec-item-value {
      font-size: 18pt;
      font-weight: bold;
      margin-top: 5px;
    }
    
    h1 {
      font-size: 12pt;
      font-weight: bold;
      text-transform: uppercase;
      margin: 35px 0 15px 0;
      padding-bottom: 5px;
      border-bottom: 2px solid #000;
    }
    
    h2 {
      font-size: 12pt;
      font-weight: bold;
      margin: 25px 0 12px 0;
      font-style: italic;
    }
    
    h3 {
      font-size: 12pt;
      font-weight: bold;
      margin: 20px 0 10px 0;
    }
    
    p {
      margin: 12px 0;
      text-align: justify;
      text-indent: 0.5in;
    }
    
    p.no-indent { text-indent: 0; }
    
    .cite { font-style: italic; }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 11pt;
    }
    
    th {
      background-color: #e8e8e8;
      border: 1px solid #000;
      padding: 8px 10px;
      text-align: left;
      font-weight: bold;
      font-size: 10pt;
      text-transform: uppercase;
    }
    
    td {
      border: 1px solid #000;
      padding: 8px 10px;
      vertical-align: top;
    }
    
    tr.total-row {
      background-color: #d9d9d9;
      font-weight: bold;
    }
    
    tr.highlight-row {
      background-color: #ffffcc;
    }
    
    ol, ul {
      margin: 15px 0 15px 0.75in;
    }
    
    li {
      margin: 8px 0;
      line-height: 1.8;
    }
    
    .assessment-box {
      border: 1px solid #000;
      padding: 15px 20px;
      margin: 20px 0;
      background-color: #f5f5f5;
    }
    
    .assessment-box.strong { border-left: 5px solid #228b22; }
    .assessment-box.moderate { border-left: 5px solid #daa520; }
    .assessment-box.weak { border-left: 5px solid #dc143c; }
    
    .assessment-title {
      font-weight: bold;
      margin-bottom: 8px;
    }
    
    .signature-block { margin-top: 50px; }
    
    .signature-line {
      margin-top: 40px;
      padding-top: 5px;
      border-top: 1px solid #000;
      width: 250px;
    }
    
    .memo-footer {
      margin-top: 40px;
      padding-top: 15px;
      border-top: 1px solid #999;
      font-size: 10pt;
      color: #666;
      display: flex;
      justify-content: space-between;
    }
    
    @media print {
      .page-break { page-break-before: always; }
      body { padding: 0; }
    }
  </style>
</head>
<body>

<div class="page">
  
  <!-- MEMO HEADER -->
  <div class="memo-header">
    <div class="memo-header-top">
      <div>
        <div class="firm-name">BRIGHTPATH ASCEND GROUP</div>
        <div class="firm-division">FCRA Litigation Support Services</div>
      </div>
      <div class="confidential-stamp">
        Confidential<br>
        Attorney Work Product
      </div>
    </div>
    
    <div class="memo-title">Memorandum of Law</div>
    
    <div>
      <div class="memo-row">
        <span class="memo-label">TO:</span>
        <span>Reviewing Counsel</span>
      </div>
      <div class="memo-row">
        <span class="memo-label">FROM:</span>
        <span>Brightpath Ascend Group — FCRA Litigation Division</span>
      </div>
      <div class="memo-row">
        <span class="memo-label">DATE:</span>
        <span>[REPORT_DATE]</span>
      </div>
      <div class="memo-row">
        <span class="memo-label">RE:</span>
        <span><strong>[CLIENT_NAME] v. Equifax Information Services, LLC, et al.</strong></span>
      </div>
      <div class="memo-row">
        <span class="memo-label">MATTER NO.:</span>
        <span>[CASE_NUMBER]</span>
      </div>
    </div>
  </div>

  <!-- EXECUTIVE SUMMARY -->
  <div class="exec-summary">
    <div class="exec-summary-title">Executive Summary</div>
    <div class="exec-grid">
      <div>
        <div class="exec-item-label">Case Strength</div>
        <div class="exec-item-value">[CASE_STRENGTH]/10</div>
      </div>
      <div>
        <div class="exec-item-label">Standing</div>
        <div class="exec-item-value">[STANDING_SCORE]/10</div>
      </div>
      <div>
        <div class="exec-item-label">Willfulness</div>
        <div class="exec-item-value">[WILLFULNESS]%</div>
      </div>
      <div>
        <div class="exec-item-label">Est. Value</div>
        <div class="exec-item-value">$[EST_VALUE]K</div>
      </div>
    </div>
  </div>

  <!-- I. QUESTION PRESENTED -->
  <h1>I. Question Presented</h1>
  
  <p class="no-indent">Whether [CLIENT_NAME] ("Consumer") has viable claims under the Fair Credit Reporting Act, 15 U.S.C. § 1681 <em>et seq.</em>, against credit reporting agencies and furnishers based on documented inaccuracies in Consumer's credit reports, and whether such claims survive standing analysis under <span class="cite">TransUnion LLC v. Ramirez</span>, 141 S. Ct. 2190 (2021).</p>

  <!-- II. BRIEF ANSWER -->
  <h1>II. Brief Answer</h1>
  
  <p class="no-indent">Yes. Consumer has [CASE_STRENGTH_TEXT] FCRA claims based on [VIOLATION_COUNT] documented violations across [DEFENDANT_COUNT] defendants. The violations include impossible status contradictions, balance discrepancies, and date reporting errors. Standing is [STANDING_STATUS] under <span class="cite">TransUnion</span>. Willfulness probability is assessed at [WILLFULNESS]%. Estimated case value ranges from $[VALUE_LOW] to $[VALUE_HIGH], with a settlement target of $[SETTLEMENT_TARGET].</p>

  <!-- III. STATEMENT OF FACTS -->
  <h1>III. Statement of Facts</h1>
  
  <h2>A. Background</h2>
  
  <p>Consumer [CLIENT_NAME] is an individual residing in [CLIENT_STATE]. Consumer obtained tri-bureau credit reports dated [REPORT_DATE]. Review of these reports reveals significant inaccuracies affecting [ACCOUNT_COUNT] accounts.</p>

  <h2>B. Credit Bureau Scores</h2>
  
  <table>
    <tr>
      <th>Bureau</th>
      <th>Score</th>
      <th>Score Range</th>
    </tr>
    [SCORE_ROWS]
  </table>

  <h2>C. Summary of Inaccuracies</h2>
  
  <table>
    <tr>
      <th>Violation Category</th>
      <th>Count</th>
      <th>Statutory Basis</th>
      <th>Severity</th>
    </tr>
    [VIOLATION_SUMMARY_ROWS]
  </table>

  <!-- IV. ANALYSIS -->
  <h1>IV. Analysis</h1>
  
  <h2>A. Standing Under <span class="cite">TransUnion LLC v. Ramirez</span></h2>
  
  <p>Following the Supreme Court's decision in <span class="cite">TransUnion LLC v. Ramirez</span>, 141 S. Ct. 2190 (2021), FCRA plaintiffs must establish Article III standing by demonstrating: (1) a concrete injury-in-fact; (2) caused by defendant's conduct; (3) that is redressable by a favorable decision.</p>

  <div class="assessment-box [STANDING_BOX_CLASS]">
    <div class="assessment-title">Standing Assessment: [STANDING_SCORE]/10</div>
    [STANDING_CONCLUSION]
  </div>

  <h2>B. Violation Analysis</h2>
  
  <h3>1. Impossible Status Contradictions</h3>
  
  <p>The most significant violations involve accounts reported with mutually exclusive statuses across bureaus. <em>See</em> <span class="cite">Cushman v. Trans Union Corp.</span>, 115 F.3d 220, 225 (3d Cir. 1997).</p>

  <table>
    <tr>
      <th>Account</th>
      <th>Balance</th>
      <th>TransUnion</th>
      <th>Experian</th>
      <th>Equifax</th>
    </tr>
    [CONTRADICTION_ROWS]
  </table>

  <h2>C. Willfulness Analysis Under <span class="cite">Safeco</span></h2>
  
  <p>Under <span class="cite">Safeco Insurance Co. v. Burr</span>, 551 U.S. 47 (2007), willfulness requires knowing or reckless disregard of statutory duties.</p>

  <div class="assessment-box [WILLFULNESS_BOX_CLASS]">
    <div class="assessment-title">Willfulness Assessment: [WILLFULNESS]% Probability</div>
    [WILLFULNESS_CONCLUSION]
  </div>

  <h2>D. Damages Calculation</h2>

  <table>
    <tr>
      <th>Component</th>
      <th>Conservative</th>
      <th>Moderate</th>
      <th>Aggressive</th>
    </tr>
    [DAMAGES_ROWS]
    <tr class="total-row">
      <td><strong>TOTAL</strong></td>
      <td><strong>$[TOTAL_CONS]</strong></td>
      <td><strong>$[TOTAL_MOD]</strong></td>
      <td><strong>$[TOTAL_AGG]</strong></td>
    </tr>
  </table>

  <!-- V. SETTLEMENT STRATEGY -->
  <h1>V. Settlement Strategy</h1>

  <table>
    <tr>
      <th>Priority</th>
      <th>Defendant</th>
      <th>Violations</th>
      <th>Settlement Target</th>
    </tr>
    [DEFENDANT_ROWS]
    <tr class="total-row">
      <td colspan="2"><strong>TOTAL</strong></td>
      <td><strong>[VIOLATION_COUNT]</strong></td>
      <td><strong>$[SETTLEMENT_TARGET]</strong></td>
    </tr>
  </table>

  <!-- VI. CONCLUSION -->
  <h1>VI. Conclusion and Recommendations</h1>

  <p class="no-indent"><strong>Recommendations:</strong></p>

  <ol>
    <li><strong>Initiate Formal Disputes:</strong> Send detailed dispute letters to all [DEFENDANT_COUNT] defendants via certified mail.</li>
    <li><strong>Strengthen Standing Evidence:</strong> [STANDING_RECOMMENDATION]</li>
    <li><strong>Prioritize Tier 1 Defendants:</strong> Focus on defendants with most egregious violations.</li>
    <li><strong>Settlement Strategy:</strong> Target $[SETTLEMENT_TARGET] global settlement.</li>
  </ol>

  <p><strong>Anticipated Timeline:</strong> 60-120 days RLPP protocol; 12-18 months if litigation required.</p>

  <div style="text-align: center; margin-top: 50px;">* * *</div>

  <!-- SIGNATURE -->
  <div class="signature-block">
    <p>Respectfully submitted,</p>
    <div class="signature-line">
      Brightpath Ascend Group<br>
      FCRA Litigation Support Services
    </div>
  </div>

  <!-- FOOTER -->
  <div class="memo-footer">
    <div>
      <strong>BRIGHTPATH ASCEND GROUP</strong><br>
      FCRA Litigation Support Services
    </div>
    <div style="text-align: right;">
      Matter No.: [CASE_NUMBER]<br>
      Confidential — Attorney Work Product
    </div>
  </div>
  
</div>

</body>
</html>
```

---

## KEY CASE CITATIONS

Include these citations in Legal Memorandum:

**Standing:**
- TransUnion LLC v. Ramirez, 141 S. Ct. 2190 (2021)
- Spokeo, Inc. v. Robins, 578 U.S. 330 (2016)

**Accuracy:**
- Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997)
- Dalton v. Capital Associated Indus., 257 F.3d 409 (4th Cir. 2001)

**Willfulness:**
- Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)

**Punitive Limits:**
- BMW of North America, Inc. v. Gore, 517 U.S. 559 (1996)
- State Farm Mut. Auto. Ins. Co. v. Campbell, 538 U.S. 408 (2003)

---

## SHORTCUTS REFERENCE

| Shortcut | Action |
|----------|--------|
| `Full` | Generate complete 4-document package |
| `InternalAnalysis` | Document 1 only |
| `ClientEmail` | Document 2 only |
| `ClientReport` | Document 3 only |
| `LegalMemo` | Document 4 only |
| `R1` | Round 1 dispute letters |
| `R2` | MOV escalation letters |
| `R3` | Regulatory complaints |
| `R4` | Pre-arbitration demands |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 12/12/2025 | Initial release |
| 2.0 | 12/13/2025 | Added embedded Apple-style + Traditional templates |

---

*END OF PROMPT*
