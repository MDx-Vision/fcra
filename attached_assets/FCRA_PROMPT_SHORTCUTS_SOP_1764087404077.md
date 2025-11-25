# FCRA PROMPT SHORTCUTS - STANDARD OPERATING PROCEDURE
## Brightpath Ascend Group | Version 2.0 | November 24, 2025

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Complete Shortcut Library](#complete-shortcut-library)
3. [Workflow Sequence](#workflow-sequence)
4. [Document Requirements by Stage](#document-requirements-by-stage)
5. [Usage Instructions](#usage-instructions)
6. [Common Scenarios](#common-scenarios)
7. [Quality Control Checklist](#quality-control-checklist)
8. [Troubleshooting](#troubleshooting)

---

## 📖 OVERVIEW

### Purpose
This SOP standardizes the use of 12 FCRA prompt shortcuts with Claude AI to streamline case processing, ensuring consistent quality and proper workflow sequencing.

### Key Benefits
- **Speed:** Generate comprehensive analyses in 5-7 minutes vs 50+ minutes manual
- **Consistency:** Same quality output every time
- **Scalability:** Process 150-200 cases annually with small team
- **Quality:** Built-in verification checkpoints and legal compliance
- **Efficiency:** V2.8 outputs separate files automatically (no manual extraction needed)

### Core Principle
**CRITICAL:** Round 3 and Round 4 escalations require complete paper trail (original report + letters sent + bureau responses). Never skip documentation stages.

---

## 📚 COMPLETE SHORTCUT LIBRARY

| # | Shortcut | Prompt File | Output | Lines | Use Case |
|---|----------|-------------|--------|-------|----------|
| **01** | `Full` | FULL_INTAKE_V2.8 | Complete analysis + all letters (separate files) | 2,348 | New case intake - everything |
| **02** | `R1` | ROUND1_LETTERS_ONLY | Initial dispute letters (separate files) | 641 | First contact with bureaus |
| **03** | `R2` | ROUND2_MOV | MOV demands (separate files) | 774 | After bureau response to R1 |
| **04** | `R3` | ROUND3_REGULATORY | Regulatory complaints (separate files) | 1,113 | After R1+R2 fail |
| **05** | `R4` | ROUND4_PRE_ARB | Pre-arb demands (separate files) | 861 | Final pre-litigation push |
| **06** | `Quick` | QUICK_SINGLE_LETTER | One targeted letter (single file) | 199 | Single issue disputes |
| **07** | `Secondary` | SECONDARY_BUREAUS | 9 freeze + file requests (separate files) | 991 | Innovis, ChexSystems, etc. |
| **08** | `SecDispute` | SECONDARY_DISPUTE | Secondary bureau disputes (separate files) | 393 | Dispute to specialty CRAs |
| **09** | `PII` | CRA_PII_CORRECTION | 3 PII correction letters (separate files) | 554 | Name, address, SSN errors |
| **10** | `Validation` | COLLECTION_VALIDATION | Collection validation letters (separate files) | 436 | Debt collector disputes |
| **11** | `ClientReport` | CLIENT_REPORT | 40-50pg client presentation (single file) | 509 | Client delivery (report only) |
| **12** | `InternalAnalysis` | INTERNAL_ANALYSIS | 3-5pg staff summary (single file) | 424 | Internal case review only |

---

## 🔄 WORKFLOW SEQUENCE

### Stage 1: Initial Case Intake (Days 1-7)
**Documents Required:** ✅ Credit report only  
**Action:** Upload credit report → Type `Full`  
**Output:** Complete analysis + Round 1 letters  
**Next Step:** Mail Round 1 letters via LetterStream (certified mail)

### Stage 2: Method of Verification (Days 30-45)
**Documents Required:** ✅ Credit report + ✅ Round 1 letters sent + ✅ Bureau responses  
**Action:** Upload all documents → Type `R2`  
**Output:** MOV demand letters  
**Next Step:** Mail MOV letters via LetterStream (certified mail)

### Stage 3: Regulatory Escalation (Days 60-75)
**Documents Required:** ✅ Credit report + ✅ R1 letters + ✅ R1 responses + ✅ R2 letters + ✅ R2 responses  
**Action:** Upload complete paper trail → Type `R3`  
**Output:** CFPB/FTC/AG complaint letters  
**Next Step:** File regulatory complaints + send letters

### Stage 4: Pre-Arbitration (Days 90-120)
**Documents Required:** ✅ Complete case file (all above + regulatory responses)  
**Action:** Upload entire case history → Type `R4`  
**Output:** Pre-arbitration demand letters  
**Next Step:** Attorney review → Arbitration filing or settlement negotiation

---

## 📄 DOCUMENT REQUIREMENTS BY STAGE

### Initial Disputes (R1, R2, Quick)
```
UPLOAD: Credit report only
- IdentityIQ, MyScoreIQ, or similar
- Must show all 3 bureaus (Experian, TransUnion, Equifax)
- PDF or screenshot format acceptable
```

### Escalations (R3, R4)
```
UPLOAD COMPLETE PACKAGE:
1. Original credit report
2. Round 1 letters (all 3 bureaus)
3. Bureau responses to Round 1 (proof of delivery + response letters)
4. Round 2 MOV letters (if applicable)
5. Bureau responses to Round 2 (if applicable)
6. Regulatory complaint confirmations (for R4)

⚠️ CRITICAL: Missing documents = invalid escalation
```

### Standalone Tools (Secondary, PII, Validation)
```
UPLOAD: Relevant documents only
- Secondary: Credit report + secondary bureau reports
- PII: Credit report showing incorrect personal info
- Validation: Collection letters + credit report
```

### Reports Only (ClientReport, InternalAnalysis)
```
UPLOAD: Credit report only
- Use when you only need presentation documents
- No letters generated
```

---

## 🎯 USAGE INSTRUCTIONS

### Basic Syntax
1. Upload required documents to Claude
2. Type the shortcut command
3. Wait for generation (typically 5-7 minutes for `Full`)
4. Review output before client delivery

### Examples

**Example 1: New Case Intake**
```
Staff: [Uploads client credit report]
Staff: "Full"
Claude: [Generates 40-50 page analysis + all Round 1 letters]
Staff: [Reviews verification checkpoint → Approves → Sends to client]
```

**Example 2: Round 2 MOV After Bureau Response**
```
Staff: [Uploads credit report + Round 1 letters + bureau responses]
Staff: "R2"
Claude: [Generates MOV demand letters]
Staff: [Reviews → Mails via LetterStream]
```

**Example 3: Quick Single Letter**
```
Staff: [Uploads credit report]
Staff: "Quick - Chase late payment only"
Claude: [Generates one targeted letter]
```

**Example 4: Client Presentation Only**
```
Staff: [Uploads credit report]
Staff: "ClientReport"
Claude: [Generates 40-50 page client-facing report only, no letters]
```

---

## 💼 COMMON SCENARIOS

### Scenario 1: Brand New Client - Fresh Case
**Goal:** Complete intake with client deliverables  
**Shortcut:** `Full`  
**Documents:** Credit report only  
**Timeline:** 5-7 minutes  
**Deliverable:** Analysis + Round 1 letters + client report

### Scenario 2: Client Already Sent Round 1, Got Responses
**Goal:** Escalate with MOV demands  
**Shortcut:** `R2`  
**Documents:** Report + R1 letters + bureau responses  
**Timeline:** 3-5 minutes  
**Deliverable:** MOV letters for all 3 bureaus

### Scenario 3: Client Needs Client-Facing Report Only
**Goal:** Professional presentation for client review  
**Shortcut:** `ClientReport`  
**Documents:** Credit report only  
**Timeline:** 2-3 minutes  
**Deliverable:** 40-50 page client report (no letters)

### Scenario 4: Staff Needs Quick Internal Analysis
**Goal:** Case evaluation for intake decision  
**Shortcut:** `InternalAnalysis`  
**Documents:** Credit report only  
**Timeline:** 1-2 minutes  
**Deliverable:** 3-5 page staff analysis summary

### Scenario 5: Single Account Issue - Quick Fix Needed
**Goal:** Dispute one specific account  
**Shortcut:** `Quick`  
**Documents:** Credit report  
**Timeline:** 1-2 minutes  
**Deliverable:** One targeted letter

### Scenario 6: Expanding to Secondary Bureaus
**Goal:** Hit Innovis, ChexSystems, LexisNexis  
**Shortcut:** `Secondary`  
**Documents:** Credit report + secondary reports if available  
**Timeline:** 3-4 minutes  
**Deliverable:** 9 freeze + file requests

### Scenario 7: Pre-Litigation Final Push
**Goal:** Settlement demand before arbitration  
**Shortcut:** `R4`  
**Documents:** Complete case file (report + all letters + all responses)  
**Timeline:** 5-7 minutes  
**Deliverable:** Pre-arb demand letters with damages calculation

---

## ✅ QUALITY CONTROL CHECKLIST

### Before Sending to Client
- [ ] Verification checkpoint reviewed (for `Full` analysis)
- [ ] Client name and contact information accurate
- [ ] Account numbers match credit report
- [ ] All violation citations accurate (FCRA section references)
- [ ] Standing analysis includes concrete harm evidence
- [ ] Damages calculations reasonable and defensible
- [ ] Letters addressed to correct bureaus/furnishers
- [ ] Certified mail instructions included
- [ ] All files generated and properly named (V2.8 outputs separate files automatically)

### Before Escalating to R3 or R4
- [ ] Complete paper trail assembled
- [ ] Proof of delivery for all prior letters
- [ ] Bureau responses documented (even "verified as accurate")
- [ ] Timeline meets statutory requirements (30-day response periods)
- [ ] All FCRA procedural requirements met
- [ ] Standing evidence documented (denial letters, harm proof)

### Before Client Delivery
- [ ] Human review completed (never deliver unverified AI output)
- [ ] Professional formatting consistent
- [ ] No placeholder text or [BRACKETS] remaining
- [ ] File named appropriately: `ClientName_FCRA_Analysis_Date.pdf`
- [ ] Engagement agreement signed (if new client)

---

## 🔧 TROUBLESHOOTING

### Issue: Claude doesn't recognize shortcut
**Solution:** Ensure exact spelling. Shortcuts are case-sensitive:
- Correct: `R1`, `Full`, `ClientReport`
- Incorrect: `r1`, `full`, `client report`

### Issue: Claude says it needs more documents for R3/R4
**Cause:** Missing required escalation documents  
**Solution:** Upload complete paper trail:
1. Original credit report
2. All prior letters sent
3. All bureau responses received
4. Proof of delivery (tracking numbers, green cards)

### Issue: Analysis looks incomplete or has errors
**Cause:** Credit report image quality or missing pages  
**Solution:** 
- Re-upload higher quality scan
- Ensure all 3 bureau sections visible
- Check that account details are readable

### Issue: Letters seem generic or miss specific violations
**Cause:** Insufficient detail in credit report upload  
**Solution:**
- Upload full 3-bureau report (not summary)
- Include account detail pages
- If using Quick, specify: "Quick - [specific issue]"

### Issue: Verification checkpoint shows errors
**Cause:** AI analysis needs human correction (this is by design)  
**Solution:** 
- Review verification table carefully
- Identify and note corrections needed
- Do NOT approve if significant errors present
- Regenerate with corrected instructions

### Issue: Wrong prompt file seems to be used
**Cause:** Shortcut memory may need refresh  
**Solution:** Ask Claude: "Which prompt file does [shortcut] use?"

---

## 📞 SUPPORT RESOURCES

### Internal Resources
- **FCRA Litigation Framework:** `/mnt/project/FCRA_Litigation_Framework_Complete_v2_0__3_.md`
- **Workflow Cheat Sheet:** `/mnt/project/FCRA_WORKFLOW_CHEAT_SHEET.md`
- **Violation Spotter Checklist:** `/mnt/project/FCRA-Violation-Spotter-Checklist.md`

### When to Escalate to Attorney
- Pre-arbitration demands (R4)
- Settlement negotiations over $5,000
- Any case with potential willfulness (4-6x damages)
- Standing questions after TransUnion v. Ramirez
- Circuit court splits or novel legal issues

### Training Requirements
- **New Staff:** Shadow 10 cases before independent processing
- **Quality Check:** First 5 cases reviewed by supervisor
- **Ongoing:** Monthly case reviews for accuracy and compliance

---

## 📊 PERFORMANCE METRICS

### Processing Speed Targets
- `Full` analysis: 5-7 minutes (vs 50+ minutes manual)
- `R1` letters: 2-3 minutes
- `R2` MOV: 3-5 minutes
- `Quick` letter: 1-2 minutes
- Quality review: 10-15 minutes per case

### Quality Standards
- Verification accuracy: >95%
- Standing compliance: 100% (concrete harm documented)
- Citation accuracy: 100% (proper FCRA sections)
- Client satisfaction: >90%

### Expected Outcomes
- Round 1 success rate: 15-25% (traditional)
- RLPP bundled strategy: 75-85% success
- Settlement rate: 75-85% of qualified cases
- Average case value: $12,000-$85,000

---

## 🔒 COMPLIANCE REMINDERS

### Ethical Standards
- Never promise removal of accurate negative items
- Require concrete harm evidence (denial letters) for standing
- Document all client communications
- Maintain attorney-client privilege when applicable
- No exploitation of unrelated events (deaths, disasters)

### Professional Boundaries
- Services are "case-building, not disputing"
- Position as "federal consumer protection litigation"
- Require signed representation waivers
- Strongly recommend attorney consultation for pro se clients

### FCRA Compliance
- 30-day investigation timeline (§ 1681i(a)(1))
- 5-day notice requirement for identity theft blocks (§ 1681c-2)
- Proper standing requirements (TransUnion v. Ramirez)
- Documentary proof standards (Cushman v. TransUnion)

---

## 📝 VERSION HISTORY

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Nov 24, 2025 | Initial SOP creation with 12-prompt library | Brightpath Ascend Group |
| 2.0 | Nov 24, 2025 | Updated to V2.8 with separate files output format | Brightpath Ascend Group |

---

## ✍️ ACKNOWLEDGMENT

I have read, understood, and agree to follow the FCRA Prompt Shortcuts SOP:

**Staff Name:** ________________________________  
**Signature:** ___________________________________  
**Date:** _______________________________________  
**Supervisor:** __________________________________

---

**Document Control:**  
Classification: Internal Use Only  
Review Cycle: Quarterly  
Next Review: February 24, 2026  
Owner: Operations Manager
