# âš¡ FCRA CASE WORKFLOW CHEAT SHEET
**Quick Reference Guide for Daily Operations**

---

## ðŸŽ¯ PHASE 1: INITIAL CONTACT (0-10 Minutes)

### THE 5 CRITICAL INTAKE QUESTIONS

â“ **Q1: "What's inaccurate on your credit report?"**
- Looking for: Mixed file, wrong account, incorrect payment history, identity theft
- Red flags: "Everything is wrong" (needs specifics), vague complaints

â“ **Q2: "Did you dispute it with the credit bureau?"**
- âœ… YES â†’ Potential Â§ 1681i claim (reinvestigation failure)
- âŒ NO â†’ May need to dispute first (some circuits require exhaustion)
- **Get:** Copies of dispute letters, CRA responses

â“ **Q3: "Were you denied credit, a job, insurance, or housing?"**
- **CRITICAL FOR STANDING** - Need concrete harm + dissemination
- âœ… YES â†’ Strong standing (TransUnion satisfied)
- âŒ NO â†’ Weak standing (may be fatal to case)
- **Get:** Denial letters, adverse action notices

â“ **Q4: "When did this happen?"**
- **STATUTE OF LIMITATIONS CHECK**
- Discovery rule: 2 years from when they learned of violation
- Absolute limit: 5 years from violation date
- âš ï¸ If close to deadline â†’ URGENT INTAKE

â“ **Q5: "Do you have documentation?"**
- Need: Credit reports (3 bureaus), denial letters, dispute letters, certified mail receipts
- Missing docs = schedule follow-up to obtain

### IMMEDIATE DECISION TREE

```
Does client have:
â”œâ”€ Concrete harm (denial, higher rate, lost job)? 
â”‚  â”œâ”€ NO â†’ DECLINE (standing issue)
â”‚  â””â”€ YES â†’ Continue â†“
â”‚
â”œâ”€ Dissemination to third party?
â”‚  â”œâ”€ NO â†’ DECLINE (TransUnion problem)
â”‚  â””â”€ YES â†’ Continue â†“
â”‚
â”œâ”€ Clear FCRA violation?
â”‚  â”œâ”€ MAYBE â†’ Schedule full intake
â”‚  â””â”€ YES â†’ Continue â†“
â”‚
â”œâ”€ Within statute of limitations?
â”‚  â”œâ”€ NO â†’ DECLINE (time-barred)
â”‚  â””â”€ YES â†’ Continue â†“
â”‚
â””â”€ ACCEPT FOR FULL INTAKE
```

---

## ðŸ“‹ PHASE 2: FULL INTAKE (30-60 Minutes)

### DOCUMENTS TO REQUEST IMMEDIATELY

**Credit Reports (all 3 bureaus):**
- [ ] Equifax (most recent)
- [ ] Experian (most recent)
- [ ] TransUnion (most recent)
- [ ] Any specialty CRA reports (employment, tenant screening)

**Dispute Documentation:**
- [ ] All dispute letters sent (copies)
- [ ] Certified mail receipts (green cards) - CRITICAL
- [ ] CRA investigation response letters
- [ ] Online dispute confirmations/screenshots

**Adverse Action Evidence:**
- [ ] Credit denial letters
- [ ] Employment adverse action notices
- [ ] Pre-adverse action notices (if employment)
- [ ] Insurance rate increase notices
- [ ] Rental/housing denials

**Supporting Documentation:**
- [ ] Payment receipts (if disputing late payments)
- [ ] Bank statements
- [ ] Bankruptcy discharge orders (if applicable)
- [ ] Identity theft reports/police reports
- [ ] Settlement/payment agreements

### USE THESE PROJECT DOCUMENTS

1. **Complete:** `FCRA-Case-Intake-Template.md`
   - Fill in every section
   - Calculate preliminary damages
   - Identify all defendants

2. **Run:** `FCRA-Violation-Spotter-Checklist.md`
   - Go through credit reports systematically
   - Check every box that applies
   - Document evidence for each violation

3. **Calculate:** Settlement range using Quick Reference formulas

### CRITICAL DEADLINE CALCULATION

**Formula:**
- Discovery date: ________ (when client learned of violation)
- Violation date: ________ (when it occurred, if known)
- **Filing deadline:** Earlier of:
  - Discovery + 2 years = ________
  - Violation + 5 years = ________

**Calendar this deadline immediately!**

---

## ðŸŽ¯ PHASE 3: STANDING ANALYSIS (15 Minutes)

### POST-TRANSUNION STANDING TEST âš ï¸

**All 3 must be satisfied:**

**1. CONCRETE HARM**
- [ ] Credit denial (specific lender, specific date)
- [ ] Employment denial (with pre-adverse + adverse action notices)
- [ ] Higher interest rate (quantifiable difference)
- [ ] Lost housing opportunity
- [ ] Insurance rate increase
- [ ] Emotional distress (with treatment records)

**Examples of WEAK harm (may fail):**
- âŒ "General stress" without medical treatment
- âŒ "Would have gotten better rate" (speculative)
- âŒ "Spent time disputing" (not sufficient alone)

**2. DISSEMINATION**
- [ ] Report furnished to lender (get adverse action notice)
- [ ] Report furnished to employer (get documents)
- [ ] Report furnished to insurer
- [ ] Report furnished to landlord

**If inaccuracy never left CRA = NO STANDING**

**3. CAUSATION**
- [ ] Inaccuracy directly caused the harm
- [ ] Temporal connection (denial shortly after report pulled)
- [ ] Denial notice specifically references credit issue

**RED FLAG:** If standing is unclear, research circuit law before proceeding.

---

## ðŸš€ PHASE 4: STRATEGY SELECTION

### PATH A: LITIGATION TRACK

**Choose this if:**
- Strong standing (all 3 elements clear)
- Willfulness indicators present (3+ of below)
- Damages potential > $50,000
- Client willing to participate in litigation

**Willfulness Indicators:**
- [ ] CRA missed 30-day statutory deadline
- [ ] Multiple disputes ignored (3+)
- [ ] CRA has prior FCRA violations/consent orders
- [ ] Investigation completed in < 3 days (impossibly fast)
- [ ] CRA ignored consumer's documentary evidence
- [ ] Pattern of similar violations across consumers

**Next Steps:**
1. Send preservation letter to CRA (within 48 hours)
2. Draft demand letter (Framework Â§ 20)
3. Set 15-day deadline for response
4. Prepare complaint if demand rejected

**Use:** `FCRA_Litigation_Framework_Complete_v2.0.md` sections:
- Â§ 20: Demand Letters
- Â§ 15: Discovery Strategies  
- Â§ 21: Settlement Valuation

---

### PATH B: PRE-LITIGATION DISPUTE TRACK

**Choose this if:**
- Standing unclear but violations exist
- Damages < $50,000
- Client wants quick resolution
- Testing case strength before litigation

**Select Dispute Strategy by Violation Type:**

**LATE PAYMENTS:**
â†’ Use `Chat_GPT_Prompt_Late_Payment_R1.pdf`
- Generate individual letter for EACH inaccuracy
- Send certified mail to all 3 CRAs
- Wait 30-45 days
â†’ If "verified" â†’ Use `R2.pdf` MOV letters
- Cite Cushman v. TransUnion
- Demand tangible proof

**CHARGE-OFFS:**
â†’ Use `chargeoff_prompt.webp`
- Focus on Metro 2 compliance violations
- Attack date inconsistencies, balance errors

**IDENTITY THEFT:**
â†’ Use 3-stage escalation (Chat_History templates)
1. FTC Identity Theft Affidavit
2. CFPB Complaint (Â§ 605B) - triggers 4-day deadline
3. MOV Letter (Â§ 611(a)(7)) - litigation trap

**MIXED FILES:**
â†’ Direct CRA letters citing Â§ 1681e(b)
- Demand file segregation
- Provide SSN/DOB proof

---

## ðŸ’° PHASE 5: QUICK DAMAGES CALCULATION

### STATUTORY DAMAGES (Willful Only)

```
# of violations Ã— $100-$1,000 each
Conservative: # ___ Ã— $100 = $_______
Moderate:     # ___ Ã— $500 = $_______
Aggressive:   # ___ Ã— $1,000 = $_______
```

### ACTUAL DAMAGES

**Economic Losses:**
```
Lost credit opportunity:    $_______
Higher interest paid:       $_______
Lost employment:            $_______
Lost housing:               $_______
Time spent (hours Ã— rate):  $_______
Out-of-pocket costs:        $_______
TOTAL ECONOMIC:             $_______
```

**Emotional Distress:**
```
Severity: â–¡ Minimal ($0-$5k) â–¡ Moderate ($5k-$25k) â–¡ Severe ($25k-$75k)
Treatment: â–¡ None â–¡ Therapy â–¡ Medication â–¡ Hospitalization

Estimated: $_______
```

### PUNITIVE DAMAGES (Willful Only)

```
Compensatory (Stat + Actual): $_______
Multiplier: â–¡ 2:1 â–¡ 3:1 â–¡ 4:1
(Based on reprehensibility)

Punitive estimate: $_______
```

### ATTORNEY'S FEES

```
Estimated hours to settlement: ___ Ã— $__/hr = $_______
Estimated hours through trial:  ___ Ã— $__/hr = $_______
```

### TOTAL CASE VALUATION

```
Conservative:  $_______
Likely:        $_______  
Maximum:       $_______
```

### SETTLEMENT RANGE

```
Quick (60%): $_______
Post-Discovery (75%): $_______
Trial-Ready (90%): $_______
```

---

## ðŸ“ž PHASE 6: CLIENT COMMUNICATION

### ACCEPTANCE CALL SCRIPT

"Based on my review, you have a strong FCRA case. Here's what I found:

**Violations:** [List 2-3 main violations]
**Defendants:** [CRA names, furnisher names if applicable]
**Standing:** You have concrete harm because [denial/higher rate/lost job]
**Timeline:** We need to [file by X date / send demand / begin disputes]

**Your case value:** $X,XXX to $X,XXX based on:
- Statutory damages if we prove willfulness
- Your actual losses of approximately $X,XXX
- Attorney's fees (defendant pays if we win)

**Next steps:**
1. Sign engagement agreement
2. Provide remaining documents
3. We'll send [demand letter / preservation letter / dispute letters] within 48 hours

**Questions?"**

### DECLINE CALL SCRIPT

"I've reviewed your situation carefully. Unfortunately, I cannot take your case because:

[Choose reason:]
- [ ] **Standing issue:** Under current law (TransUnion case), you need proof the inaccurate report was furnished to a third party AND caused you concrete harm. [Explain gap]
- [ ] **Statute of limitations:** The deadline to file has passed.
- [ ] **Damages too low:** The case value doesn't justify litigation costs.
- [ ] **No clear FCRA violation:** [Explain why]

**Alternative options:**
- You can dispute directly with credit bureaus (I can provide form letters)
- Consider consulting with [credit repair specialist / other attorney]
- If situation changes [new denial, new evidence], call me back

I wish I could help, but ethically I cannot take a case I don't believe has merit."

---

## ðŸ—‚ï¸ PHASE 7: FILE ORGANIZATION

### CREATE CASE FOLDER IMMEDIATELY

```
[Client Name - Case ID]/
â”œâ”€â”€ 01_Intake/
â”‚   â”œâ”€â”€ Intake_Questionnaire.pdf
â”‚   â”œâ”€â”€ Violation_Spotter_Checklist.pdf
â”‚   â””â”€â”€ Initial_Documents/
â”œâ”€â”€ 02_Credit_Reports/
â”‚   â”œâ”€â”€ Equifax_[date].pdf
â”‚   â”œâ”€â”€ Experian_[date].pdf
â”‚   â””â”€â”€ TransUnion_[date].pdf
â”œâ”€â”€ 03_Disputes_CRA_Correspondence/
â”‚   â”œâ”€â”€ Dispute_Letter_1.pdf
â”‚   â”œâ”€â”€ Certified_Receipt_1.pdf
â”‚   â””â”€â”€ CRA_Response_1.pdf
â”œâ”€â”€ 04_Adverse_Action_Notices/
â”œâ”€â”€ 05_Supporting_Evidence/
â”œâ”€â”€ 06_Legal_Research/
â”œâ”€â”€ 07_Demand_Letter/
â”œâ”€â”€ 08_Pleadings/ (if litigation)
â””â”€â”€ 09_Settlement/ (when reached)
```

---

## â±ï¸ TIME TRACKING BY PHASE

**Quick Reference for Billing:**

| Phase | Time | Billable? |
|-------|------|-----------|
| Initial Contact | 10-15 min | Maybe (screen first) |
| Full Intake | 45-60 min | YES |
| Violation Analysis | 30-45 min | YES |
| Legal Research | 1-2 hours | YES |
| Demand Letter Drafting | 2-3 hours | YES |
| Discovery Requests | 3-4 hours | YES |
| Client Calls | 15-30 min each | YES |

---

## ðŸš¨ RED FLAGS - DECLINE IMMEDIATELY

**Standing Issues:**
- âŒ "I just don't like what's on my report" (no concrete harm)
- âŒ "I haven't been denied anything yet" (no dissemination)
- âŒ "I'm worried about future denials" (speculative)

**Statute of Limitations:**
- âŒ Client discovered violation > 2 years ago
- âŒ Violation occurred > 5 years ago

**Impossible Cases:**
- âŒ Client wants accurate but negative information removed
- âŒ Client is judgement proof / bankruptcy imminent
- âŒ Client has unrealistic expectations ("I want $1 million for one late payment")

**Credibility Issues:**
- âŒ Story changes multiple times
- âŒ Client admits information is accurate
- âŒ Client forged documents

---

## ðŸ“š QUICK REFERENCE - MOST USED FRAMEWORK SECTIONS

### Daily Use:
- **Â§ 2**: Standing Analysis (use every case)
- **Â§ 5**: Willfulness Indicators
- **Â§ 11**: Damages Calculation
- **Â§ 20**: Demand Letters

### Discovery Phase:
- **Â§ 15**: Discovery Strategies
- **Â§ 16**: Expert Witnesses
- **Â§ 26-27**: Document Requests & Interrogatories

### Settlement:
- **Â§ 21**: Settlement Valuation
- **Â§ 23**: Circuit-Specific Guidance

### Trial:
- **Â§ 22**: Trial Prep & Jury Instructions
- **Â§ 30**: Case Law Reference Table

---

## ðŸ”„ WEEKLY REVIEW CHECKLIST

**Every Monday Morning:**
- [ ] Review all cases approaching statute of limitations
- [ ] Check for CRA responses (30-day deadline tracking)
- [ ] Follow up on pending document requests
- [ ] Update case status in tracking system

**Every Friday Afternoon:**
- [ ] Send weekly client updates
- [ ] Calendar next week's deadlines
- [ ] Review time entries for accuracy
- [ ] Prepare next week's tasks

---

## ðŸ“ž EMERGENCY PROCEDURES

**Statute of Limitations Crisis (< 30 days to deadline):**
1. Immediately calendar filing deadline
2. Gather minimum necessary docs
3. Draft bare-bones complaint
4. File complaint to preserve claim
5. Conduct full intake after filing

**CRA Deadline Expired (missed 30-day reinvestigation):**
1. Document exact dates (dispute received, 30 days elapsed)
2. This is willfulness evidence
3. Prioritize this case for litigation

---

## ðŸŽ¯ SUCCESS METRICS

**Track These Weekly:**
- Intake conversion rate (consultations â†’ retained cases)
- Average case value
- Settlement rate (% of cases settling vs. litigation)
- Average time to settlement
- Average attorney time per case

**Good Benchmarks:**
- Conversion rate: 30-40%
- Settlement rate: 70-80%
- Average case value: $35,000-$75,000
- Time to settlement: 3-6 months

---

**END OF WORKFLOW CHEAT SHEET**

*Print this and keep at your desk for daily reference*
*Update as you develop firm-specific procedures*
