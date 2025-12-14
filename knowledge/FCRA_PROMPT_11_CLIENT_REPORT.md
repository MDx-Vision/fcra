# FCRA PROMPT 11 V2: CLIENT REPORT (APPLE-STYLE)
## Upload Report → Generate 7-Page Premium Client Report

**Version:** 2.0  
**Updated:** December 13, 2025  
**Use Case:** Generate premium Apple-style client report  
**Output:** 7-page HTML client report (NO LETTERS)  
**Audience:** Client — professional, educational, premium feel

---

## 📋 HOW TO USE:

**STEP 1:** Start new Claude chat

**STEP 2:** Upload credit report (PDF or PNG — all 3 bureaus)

**STEP 3:** Paste client info block below

**STEP 4:** Copy everything from "PROMPT STARTS HERE" and paste

**STEP 5:** Claude generates 7-page Apple-style client report

**STEP 6:** Review, convert to PDF, send to client

---

## 📝 CLIENT INFO TEMPLATE (Copy & Fill In):

```
CONSUMER INFORMATION:
- Full Name: [Name]
- Current Address: [Address]
- City, State ZIP: [City, State ZIP]
- SSN Last 4: [XXXX]
- Date of Birth: [MM/DD/YYYY]
- Phone: [Phone]
- Email: [Email]
- State: [State]

INTAKE INFORMATION:
- How did they hear about us? [Referral, web, etc.]
- Primary concern: [What brought them in?]
- Any recent denials? [Yes/No — if yes, what for?]

TODAY'S DATE: [Date]
CASE NUMBER: [Your internal case number]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

===========================================================================
FCRA CLIENT REPORT GENERATOR — APPLE-STYLE (7 PAGES)
===========================================================================

**YOUR TASK:**

Analyze the uploaded credit report and generate a premium 7-page client 
report using the Apple-style design system below.

**OUTPUT:** One HTML document — 7-page Apple-style client report

**DO NOT GENERATE ANY LETTERS.**

===========================================================================
DESIGN SYSTEM — APPLE-STYLE
===========================================================================

```css
/* FONTS */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
  /* Brand Colors */
  --brand-teal: #0d9488;
  --brand-teal-dark: #0f766e;
  --brand-teal-light: #14b8a6;
  --brand-navy: #1e3a5f;
  --brand-navy-dark: #0a2540;
  
  /* Text Colors */
  --text-primary: #1a1a2e;
  --text-secondary: #4a5568;
  --text-muted: #718096;
  
  /* Backgrounds */
  --bg-cream: #faf9f7;
  --bg-white: #ffffff;
  --border-subtle: #e8e6e3;
  
  /* Fonts */
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'DM Sans', -apple-system, sans-serif;
}

/* DESIGN CHARACTERISTICS */
- Clean whitespace (generous padding)
- Gradient accent boxes (navy-dark to navy)
- Teal accents for highlights
- Rounded corners (3px for subtle, 8px for cards)
- Subtle shadows (0 4px 20px rgba(0,0,0,0.08))
- Premium, modern, trustworthy feel
```

===========================================================================
HTML TEMPLATE STRUCTURE
===========================================================================

Generate this complete HTML document:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Credit Analysis Report - [CLIENT_NAME]</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
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
      font-family: 'DM Sans', -apple-system, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: var(--text-primary);
      background: var(--bg-cream);
    }
    
    .page {
      max-width: 8.5in;
      min-height: 11in;
      margin: 20px auto;
      background: var(--bg-white);
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      position: relative;
    }
    
    /* ========================================
       PAGE 1: COVER
       ======================================== */
    .cover {
      min-height: 11in;
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 60px;
      position: relative;
    }
    
    .cover::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: radial-gradient(ellipse at 30% 20%, rgba(13, 148, 136, 0.15) 0%, transparent 50%);
    }
    
    .cover-content {
      position: relative;
      z-index: 1;
    }
    
    .cover-brand {
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 4px;
      color: var(--brand-teal);
      text-transform: uppercase;
      margin-bottom: 60px;
    }
    
    .cover-title {
      font-family: 'Playfair Display', serif;
      font-size: 42px;
      font-weight: 700;
      color: white;
      margin-bottom: 20px;
      line-height: 1.2;
    }
    
    .cover-subtitle {
      font-size: 18px;
      color: rgba(255,255,255,0.7);
      margin-bottom: 80px;
    }
    
    .cover-client {
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      color: white;
      margin-bottom: 10px;
    }
    
    .cover-meta {
      font-size: 14px;
      color: rgba(255,255,255,0.5);
    }
    
    .cover-footer {
      position: absolute;
      bottom: 40px;
      left: 0;
      right: 0;
      text-align: center;
    }
    
    .cover-confidential {
      font-size: 11px;
      letter-spacing: 2px;
      color: var(--brand-teal);
      text-transform: uppercase;
    }
    
    /* ========================================
       PAGE HEADER (Pages 2-7)
       ======================================== */
    .page-header {
      background: var(--brand-navy-dark);
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .page-header-brand {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--brand-teal);
      text-transform: uppercase;
    }
    
    .page-header-title {
      font-family: 'Playfair Display', serif;
      font-size: 14px;
      color: rgba(255,255,255,0.7);
    }
    
    /* ========================================
       CONTENT AREA
       ======================================== */
    .content {
      padding: 40px;
    }
    
    .section {
      margin-bottom: 35px;
    }
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--brand-teal);
    }
    
    .section-number {
      width: 32px;
      height: 32px;
      background: var(--brand-navy);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 700;
    }
    
    .section-title {
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      font-weight: 600;
      color: var(--brand-navy);
    }
    
    /* ========================================
       EXECUTIVE SUMMARY BOX
       ======================================== */
    .exec-box {
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      border-radius: 8px;
      padding: 30px;
      margin-bottom: 30px;
    }
    
    .exec-title {
      font-family: 'Playfair Display', serif;
      font-size: 14px;
      color: rgba(255,255,255,0.6);
      text-align: center;
      margin-bottom: 25px;
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
    
    /* ========================================
       KEY FINDING BOX
       ======================================== */
    .key-finding {
      background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%);
      border-radius: 6px;
      padding: 25px 30px;
      border-left: 4px solid var(--brand-teal);
      margin: 25px 0;
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
      font-size: 15px;
      color: var(--text-primary);
      line-height: 1.6;
    }
    
    /* ========================================
       STATS GRID
       ======================================== */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin: 25px 0;
    }
    
    .stat-card {
      background: var(--bg-cream);
      border-radius: 6px;
      padding: 20px;
      text-align: center;
    }
    
    .stat-number {
      font-family: 'Playfair Display', serif;
      font-size: 32px;
      font-weight: 700;
      color: var(--brand-teal);
    }
    
    .stat-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-top: 5px;
    }
    
    /* ========================================
       TABLES
       ======================================== */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin: 20px 0;
    }
    
    th {
      background: var(--brand-navy);
      color: white;
      padding: 12px 15px;
      text-align: left;
      font-weight: 600;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    th:first-child { border-radius: 6px 0 0 0; }
    th:last-child { border-radius: 0 6px 0 0; }
    
    td {
      padding: 12px 15px;
      border-bottom: 1px solid var(--border-subtle);
    }
    
    tr:hover { background: var(--bg-cream); }
    
    tr:last-child td:first-child { border-radius: 0 0 0 6px; }
    tr:last-child td:last-child { border-radius: 0 0 6px 0; }
    
    /* ========================================
       BADGES
       ======================================== */
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    
    .badge-critical { background: #fef2f2; color: #dc2626; }
    .badge-high { background: #fff7ed; color: #ea580c; }
    .badge-medium { background: #fefce8; color: #ca8a04; }
    .badge-low { background: #f0fdf4; color: #16a34a; }
    
    /* ========================================
       ACCOUNT CARDS
       ======================================== */
    .account-card {
      background: var(--bg-white);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 15px;
    }
    
    .account-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }
    
    .account-name {
      font-weight: 600;
      color: var(--brand-navy);
      font-size: 14px;
    }
    
    .account-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      text-align: center;
    }
    
    .bureau-col {
      padding: 10px;
      background: var(--bg-cream);
      border-radius: 4px;
    }
    
    .bureau-name {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 8px;
    }
    
    .bureau-status {
      font-weight: 600;
      font-size: 13px;
    }
    
    .status-open { color: #16a34a; }
    .status-paid { color: #2563eb; }
    .status-closed { color: #6b7280; }
    .status-error { color: #dc2626; background: #fef2f2; padding: 2px 6px; border-radius: 3px; }
    
    /* ========================================
       RIGHTS SECTION
       ======================================== */
    .rights-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      margin: 20px 0;
    }
    
    .right-card {
      display: flex;
      gap: 15px;
      padding: 20px;
      background: var(--bg-cream);
      border-radius: 6px;
    }
    
    .right-icon {
      width: 40px;
      height: 40px;
      background: var(--brand-teal);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 18px;
      flex-shrink: 0;
    }
    
    .right-title {
      font-weight: 600;
      color: var(--brand-navy);
      margin-bottom: 5px;
    }
    
    .right-desc {
      font-size: 13px;
      color: var(--text-secondary);
    }
    
    /* ========================================
       TIMELINE
       ======================================== */
    .timeline {
      display: flex;
      justify-content: space-between;
      margin: 30px 0;
      position: relative;
    }
    
    .timeline::before {
      content: '';
      position: absolute;
      top: 20px;
      left: 10%;
      right: 10%;
      height: 3px;
      background: linear-gradient(90deg, var(--brand-teal), var(--brand-navy));
    }
    
    .timeline-step {
      text-align: center;
      position: relative;
      z-index: 1;
      flex: 1;
    }
    
    .timeline-dot {
      width: 40px;
      height: 40px;
      background: var(--brand-teal);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      margin: 0 auto 15px;
      box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
    }
    
    .timeline-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--brand-navy);
    }
    
    .timeline-days {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 3px;
    }
    
    /* ========================================
       CTA SECTION
       ======================================== */
    .cta-box {
      background: linear-gradient(135deg, var(--brand-teal) 0%, var(--brand-teal-dark) 100%);
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      margin: 30px 0;
    }
    
    .cta-title {
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      font-weight: 700;
      color: white;
      margin-bottom: 10px;
    }
    
    .cta-text {
      font-size: 15px;
      color: rgba(255,255,255,0.9);
      margin-bottom: 25px;
    }
    
    .cta-button {
      display: inline-block;
      background: white;
      color: var(--brand-teal-dark);
      padding: 15px 40px;
      font-size: 14px;
      font-weight: 700;
      border-radius: 6px;
      text-decoration: none;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* ========================================
       PAGE FOOTER
       ======================================== */
    .page-footer {
      background: var(--brand-navy-dark);
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
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
      color: rgba(255,255,255,0.4);
    }
    
    /* ========================================
       PRINT STYLES
       ======================================== */
    @media print {
      body { background: white; }
      .page { 
        box-shadow: none; 
        margin: 0;
        page-break-after: always;
      }
    }
  </style>
</head>
<body>

<!-- ================================================
     PAGE 1: COVER
     ================================================ -->
<div class="page cover">
  <div class="cover-content">
    <div class="cover-brand">Brightpath Ascend Group</div>
    <h1 class="cover-title">Credit Analysis<br>Report</h1>
    <p class="cover-subtitle">Fair Credit Reporting Act Violation Assessment</p>
    <div class="cover-client">Prepared for [CLIENT_NAME]</div>
    <div class="cover-meta">[REPORT_DATE] • Case #[CASE_NUMBER]</div>
  </div>
  <div class="cover-footer">
    <div class="cover-confidential">Confidential — Prepared Exclusively for Client</div>
  </div>
</div>

<!-- ================================================
     PAGE 2: EXECUTIVE SUMMARY
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Executive Summary</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">1</div>
        <div class="section-title">Executive Summary</div>
      </div>
      
      <div class="exec-box">
        <div class="exec-title">Case Assessment</div>
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
      
      <div class="key-finding">
        <div class="key-finding-label">Key Finding</div>
        <p class="key-finding-text">[KEY_FINDING_TEXT]</p>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">[VIOLATION_COUNT]</div>
          <div class="stat-label">Total Violations</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">[DEFENDANT_COUNT]</div>
          <div class="stat-label">Defendants</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">[ACCOUNT_COUNT]</div>
          <div class="stat-label">Affected Accounts</div>
        </div>
      </div>
      
      <h3 style="color: var(--brand-navy); margin: 25px 0 15px;">What This Means</h3>
      <p style="color: var(--text-secondary); line-height: 1.8;">[WHAT_THIS_MEANS_TEXT]</p>
    </div>
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 2 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

<!-- ================================================
     PAGE 3: YOUR RIGHTS
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Understanding Your Rights</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">2</div>
        <div class="section-title">Your Rights Under the FCRA</div>
      </div>
      
      <p style="color: var(--text-secondary); margin-bottom: 25px; line-height: 1.8;">
        The Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681, is a federal law that protects 
        the accuracy, fairness, and privacy of consumer information in credit reports. When 
        credit bureaus or furnishers violate this law, you have the right to seek damages.
      </p>
      
      <div class="rights-grid">
        <div class="right-card">
          <div class="right-icon">✓</div>
          <div>
            <div class="right-title">Right to Accuracy</div>
            <div class="right-desc">Credit bureaus must follow reasonable procedures to ensure maximum possible accuracy.</div>
          </div>
        </div>
        <div class="right-card">
          <div class="right-icon">✓</div>
          <div>
            <div class="right-title">Right to Dispute</div>
            <div class="right-desc">You can dispute inaccurate information and bureaus must investigate within 30 days.</div>
          </div>
        </div>
        <div class="right-card">
          <div class="right-icon">✓</div>
          <div>
            <div class="right-title">Right to Investigation</div>
            <div class="right-desc">Furnishers must investigate disputes and correct inaccurate information.</div>
          </div>
        </div>
        <div class="right-card">
          <div class="right-icon">✓</div>
          <div>
            <div class="right-title">Right to Notification</div>
            <div class="right-desc">You must be notified when information in your report is used against you.</div>
          </div>
        </div>
        <div class="right-card">
          <div class="right-icon">$</div>
          <div>
            <div class="right-title">Right to Damages</div>
            <div class="right-desc">Recover $100-$1,000 per willful violation plus punitive damages and attorney fees.</div>
          </div>
        </div>
        <div class="right-card">
          <div class="right-icon">⚖</div>
          <div>
            <div class="right-title">Right to Sue</div>
            <div class="right-desc">You can file a lawsuit in federal court against violators.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 3 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

<!-- ================================================
     PAGE 4: VIOLATION SUMMARY
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Violation Summary</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">3</div>
        <div class="section-title">Violations Identified</div>
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
      
      <h3 style="color: var(--brand-navy); margin: 30px 0 15px;">Critical Violations</h3>
      <p style="color: var(--text-secondary); margin-bottom: 20px;">
        The following accounts show impossible contradictions — the same account cannot have 
        mutually exclusive statuses across bureaus:
      </p>
      
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
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 4 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

<!-- ================================================
     PAGE 5: ACCOUNT ANALYSIS
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Account Analysis</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">4</div>
        <div class="section-title">Account-by-Account Review</div>
      </div>
      
      [ACCOUNT_CARDS]
      
    </div>
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 5 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

<!-- ================================================
     PAGE 6: DAMAGES & STRATEGY
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Damages & Strategy</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">5</div>
        <div class="section-title">Potential Recovery</div>
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
      
      <h3 style="color: var(--brand-navy); margin: 30px 0 15px;">Our Process</h3>
      
      <div class="timeline">
        <div class="timeline-step">
          <div class="timeline-dot">1</div>
          <div class="timeline-label">Round 1</div>
          <div class="timeline-days">Days 1-30</div>
        </div>
        <div class="timeline-step">
          <div class="timeline-dot">2</div>
          <div class="timeline-label">Round 2</div>
          <div class="timeline-days">Days 31-60</div>
        </div>
        <div class="timeline-step">
          <div class="timeline-dot">3</div>
          <div class="timeline-label">Round 3</div>
          <div class="timeline-days">Days 61-90</div>
        </div>
        <div class="timeline-step">
          <div class="timeline-dot">4</div>
          <div class="timeline-label">Resolution</div>
          <div class="timeline-days">Days 90-120</div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 6 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

<!-- ================================================
     PAGE 7: NEXT STEPS
     ================================================ -->
<div class="page">
  <div class="page-header">
    <div class="page-header-brand">Brightpath Ascend Group</div>
    <div class="page-header-title">Next Steps</div>
  </div>
  
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">6</div>
        <div class="section-title">Moving Forward</div>
      </div>
      
      <h3 style="color: var(--brand-navy); margin-bottom: 15px;">What We Need From You</h3>
      <ul style="color: var(--text-secondary); padding-left: 25px; line-height: 2;">
        <li>Your approval to proceed (reply "APPROVED")</li>
        <li>Any denial letters or adverse action notices you've received</li>
        <li>Documentation of any harm caused by inaccurate reporting</li>
      </ul>
      
      <h3 style="color: var(--brand-navy); margin: 30px 0 15px;">What Happens Next</h3>
      <ul style="color: var(--text-secondary); padding-left: 25px; line-height: 2;">
        <li>We send formal dispute letters to all [DEFENDANT_COUNT] defendants via certified mail</li>
        <li>They have 30 days to investigate and respond</li>
        <li>We escalate based on their responses</li>
        <li>Target resolution in 60-120 days</li>
      </ul>
      
      <div class="cta-box">
        <div class="cta-title">Ready to Protect Your Rights?</div>
        <p class="cta-text">Reply "APPROVED" to begin the dispute process immediately.</p>
        <a href="mailto:support@brightpathascend.com?subject=APPROVED" class="cta-button">I'm Ready to Start →</a>
      </div>
      
      <div style="text-align: center; margin-top: 40px; padding-top: 30px; border-top: 1px solid var(--border-subtle);">
        <div style="font-weight: 600; color: var(--brand-navy); margin-bottom: 5px;">Brightpath Ascend Group</div>
        <div style="color: var(--text-muted); font-size: 13px;">
          support@brightpathascend.com • (917) 909-4051
        </div>
      </div>
    </div>
  </div>
  
  <div class="page-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Page 7 of 7 • Case #[CASE_NUMBER]</div>
  </div>
</div>

</body>
</html>
```

===========================================================================
CONTENT GENERATION INSTRUCTIONS
===========================================================================

### PAGE 1: COVER
- Use client name, report date, case number
- Keep design clean and premium

### PAGE 2: EXECUTIVE SUMMARY
- Calculate Case Strength (1-10 based on violations + standing)
- Calculate Standing Score (1-10 based on TransUnion factors)
- Calculate Willfulness % (based on Safeco factors)
- Estimate Value (settlement target range)
- Write Key Finding (most compelling violation in plain language)
- Calculate stats from analysis

### PAGE 3: YOUR RIGHTS
- Keep as template (education content is static)
- No customization needed

### PAGE 4: VIOLATION SUMMARY
- Table of violation categories with counts
- Critical contradictions table showing bureau-by-bureau status

### PAGE 5: ACCOUNT ANALYSIS
- Generate account cards for top 3-5 affected accounts
- Show status per bureau with color coding
- Highlight contradictions

### PAGE 6: DAMAGES & STRATEGY
- Calculate Conservative/Moderate/Aggressive damages
- Keep timeline as template

### PAGE 7: NEXT STEPS
- Customize defendant count
- Keep CTA section

===========================================================================
OUTPUT INSTRUCTIONS
===========================================================================

1. Generate complete HTML document
2. Replace all [PLACEHOLDERS] with actual data
3. Use proper Apple-style formatting
4. Make it print-ready (7 pages when printed)
5. Output as single HTML file

**DO NOT GENERATE ANY LETTERS.**

===========================================================================
END OF PROMPT
===========================================================================
