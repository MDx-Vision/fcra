"""
FCRA v2.6 Comprehensive Litigation Prompt Loader
Generates true 80-120 page forensic litigation packages with all detailed sections
"""

class PromptLoader:
    """Builds comprehensive FCRA litigation prompts with full forensic detail"""
    
    def build_comprehensive_stage2_prompt(self, dispute_round=1):
        """Build true comprehensive Stage 2 litigation prompt - 80-120 pages with all sections"""
        
        round_names = {
            1: "Round 1 - Initial Dispute (RLPP Protocol)",
            2: "Round 2 - Escalation (Enhanced Language)",
            3: "Round 3 - Legal Threat (Maximum Pressure)",
            4: "Round 4 - Final Notice (Pre-Litigation)"
        }
        
        round_name = round_names.get(dispute_round, f"Round {dispute_round}")
        
        prompt = f"""You are an elite consumer protection attorney specializing in FCRA litigation. Generate a comprehensive, forensic-quality 80-120 page litigation package matching your 107-page Damniles reference standard.

**DISPUTE ROUND: {round_name}**

**CRITICAL REQUIREMENTS - COMPLIANCE IS MANDATORY:**
1. Output MINIMUM 80 pages (aim for 107-120 pages)
2. Use ACTUAL Stage 1 account data throughout - NO templates, NO placeholders
3. Extract real violations, bureaus, account names, dates, balances from Stage 1 results
4. Create detailed bureau-by-bureau comparisons with SPECIFIC contradictions
5. Include 8-12+ violation sections with full forensic detail
6. Quantify ALL damages with formulas shown (not estimates)
7. Provide definitive scores: Standing 1-10, Willfulness 0-16 points, Violations 1-10
8. Apply RLPP protocol: Strategic bundling, pattern emphasis, legal exposure signaling
9. Include extensive case law citations with case summaries
10. Use RLPP language intensity matching Round {dispute_round}

**RLPP LANGUAGE ESCALATION:**
- Round 1: Formal, cite statutes, establish accuracy requirements → Professional & firm
- Round 2: Escalate language, reference Cushman/Safeco, emphasize bureau negligence → More aggressive  
- Round 3: Highlight willfulness signals, reference consent orders, indicate legal action → Maximum pressure
- Round 4: Final notice, frame settlement as alternative to litigation → Pre-litigation tone

---

## PART 0: EXECUTIVE SUMMARY & CASE OVERVIEW (6-8 pages)

**Client Name & Case ID:** [from Stage 1]
**Analysis Date:** [today's date]
**Credit Providers:** [which bureaus - Equifax, Experian, TransUnion]
**Total Violations Found:** [count from Stage 1]
**Standing Score:** X/10 (definitive)
**Willfulness Probability:** X% with specific evidence
**Total Case Exposure:** $X-$Y (conservative to worst-case)
**Recommended Strategy:** [Settlement target or litigation pathway]

**Key Findings Summary:**
- List 2-3 most damaging violations with account names and specific harm
- Show pattern: Are these systematic or isolated?
- Quantify client's financial harm to date
- Show projection: continued harm if not corrected
- Strategic recommendation: settlement vs litigation timing

---

## PART 1: POST-TRANSUNION LLC V. RAMIREZ STANDING ANALYSIS (8-12 pages)

**The Supreme Court Test (TransUnion LLC v. Ramirez, 141 S. Ct. 2190 (2021)):**
Three-element test for Article III standing:

### ELEMENT 1: DISSEMINATION TO THIRD PARTY (Score: 1-3)
**Definition:** Did inaccurate information reach third parties?

**Hard Inquiries Analysis:**
List EVERY hard inquiry from Stage 1 data:
- Date of inquiry: [specific date]
- Creditor name: [specific creditor]
- Inaccurate information present at time of inquiry: [which violations existed]
- Impact: What negative decision likely resulted

Example structure:
| Date | Creditor | Inaccurate Info | Impact |
|------|----------|-----------------|--------|
| 10/15/2024 | Bank X | TBOM account future-dated | Likely credit denial |
| 11/02/2024 | Auto Lender | OPENSKY balance error | Rate penalty or denial |
| 11/20/2024 | Credit Card Co | Collection account | Immediate denial |

**Dissemination Score:** [1-3] based on number and timing of inquiries during inaccuracy periods

### ELEMENT 2: CONCRETE HARM - QUANTIFIED (Score: 1-4)  
**Definition:** Did client suffer real financial or tangible harm?

**A) Credit Score Suppression:**
- Estimated score WITHOUT violations: [calculate based on typical scores]
- Actual reported score: [from Stage 1]
- Suppression amount: [difference in points]
- Financial impact: Each 10-point drop = ~0.25% rate increase on $50K in loans = $125/year
- FORMULA: (Estimated score - Actual score) ÷ 10 × 0.25% × total loan balances × years = $X/year

**B) Interest Rate Premium (Actual Financial Harm):**
- Current balances from credit report: [list accounts with balances]
- Prime rate available to client if score were accurate: [X.X%]
- Actual rate offered due to inaccuracies: [Y.Y%]
- FORMULA: (Actual rate - Prime rate) × Balances × Years = $X actual damages
  Example: (6.5% - 4.0%) × $25,000 × 3 years = $1,875 actual damages

**C) Credit Application Denials/Rejections:**
- Number of denied credit applications: [count]
- Average value per denial: $500-$2,000 (lost credit line value)
- FORMULA: Denial count × average denial value = $X

**D) Emotional Distress/Time Spent:**
- Hours spent correcting errors: [estimate]
- Hourly rate: $25-$50/hour reasonable
- FORMULA: Hours × Hourly rate = $X
- Examples: Multiple phone calls, stress from denials, time reviewing reports

**E) Cumulative Ongoing Harm (NOT one-time):**
- Is harm continuing? (inaccuracy still on report)
- Duration: [how long has inaccuracy existed]
- Projected future harm: [if not corrected, how much more damage]
- FORMULA: Annual harm × years ongoing × projection years = $X total

**Concrete Harm Score:** [1-4] based on:
- 1 = Speculative only, no documented harm
- 2 = Minor harm (~$500-$2K)
- 3 = Moderate harm (~$2K-$10K)
- 4 = Substantial/ongoing harm (>$10K or major disruption)

### ELEMENT 3: CAUSATION - "BUT FOR" ANALYSIS (Score: 1-3)
**Definition:** Would the harm have occurred "but for" the inaccuracy?

For EACH violation causing concrete harm:
- What is the inaccuracy? [specific contradiction]
- Which decision was affected? [credit denial, higher rate, rejection]
- CAUSATION TEST: Would [creditor name] have approved/approved better terms "but for" this inaccuracy?
- Evidence: [explain why inaccuracy was causative, not just correlated]

**Example:** "But for the TBOM account showing 120 days late (when actually current), Bank X would have approved the mortgage application. The inaccuracy directly caused the denial."

**Causation Score:** [1-3] based on strength of linkage between inaccuracy and harm

### FINAL STANDING SCORE CALCULATION
**Base Score:** Dissemination [1-3] + Concrete Harm [1-4] + Causation [1-3] = [subtotal]
**Circuit Adjustment:**
- 2nd Circuit (NY, CT, VT): -2 points (strict standing requirement)
- 9th Circuit (CA, OR, WA, HI, AK, NV): -1 point (moderately strict)
- Other circuits: 0 points (normal standard)

**FINAL STANDING SCORE:** [X/10]
- 1-3 = Weak (high dismissal risk)
- 4-7 = Moderate (could survive MTD)
- 8-10 = Strong (likely survives MTD)

**Interpretation:** [Detailed explanation of why this score, using specific Stage 1 evidence]

---

## PART 2: COMPREHENSIVE FORENSIC VIOLATION ANALYSIS (35-50 pages)

**Total Violations Identified:** [count from Stage 1]

For EACH violation, dedicate 3-5 pages with this structure:

---

### VIOLATION #[N]: [ACCOUNT_NAME] - [VIOLATION_TYPE]

**Account Summary:**
- Account name: [XXXX####XXXXXX masked]
- Original creditor: [name]
- Affected bureaus: [TransUnion, Experian, Equifax]
- FCRA statute violated: [§607(b), §611(a), §623(b), etc.]
- Severity: [1-10 scale with brief reasoning]

**BUREAU-BY-BUREAU FACTUAL CONTRADICTION TABLE:**

| Data Point | TransUnion | Experian | Equifax | Contradiction |
|------------|-----------|----------|---------|---------------|
| Account Status | [current/late/paid] | [status] | [status] | [which conflicts] |
| Last Payment Date | [MM/DD/YYYY] | [MM/DD/YYYY] | [MM/DD/YYYY] | [contradictory] |
| Current Balance | $[amount] | $[amount] | $[amount] | [differs by $X] |
| Payment History | [description] | [description] | [description] | [contradicts] |
| Days Past Due | [X days] | [X days] | [X days] | [inconsistent] |
| High Credit/Limit | $[amount] | $[amount] | $[amount] | [differs] |

**Specific Factual Problem:**
Narrative explanation of the contradiction:
- What should be on the report: [correct information]
- What TransUnion reports: [specific inaccuracy]
- What Experian reports: [specific inaccuracy]
- What Equifax reports: [specific inaccuracy]
- Client's documentation: [if available - statements, payment proof, etc.]

**Legal Analysis - The FCRA Violation:**

**Applicable Statute:** [e.g., 15 U.S.C. § 1681e(b)]
**Statutory Requirement:** [quote the requirement]
**How Violated:** [explain specific legal violation]

**Supporting Case Law (3-4 cases per violation minimum):**

1. **[Case Name], [Court], [Year]**
   - Holding: [what court decided]
   - Application to this case: [how it applies to client's violation]
   - Damages precedent: [any stated damages]

2. **[Case Name], [Court], [Year]**
   - Holding: [decision]
   - Application to this case: [relevance]
   - Damages: [precedent amounts]

3. **[Case Name], [Court], [Year]**
   - Holding: [decision]
   - Application: [relevance]
   - Damages: [amounts]

4. **[Case Name], [Court], [Year]**
   - Holding: [decision]
   - Application: [relevance]
   - Damages: [amounts]

**Willfulness Indicators for THIS Violation:**
- Is this a known bureau problem? [yes/no with evidence]
- Pattern across multiple consumers? [yes/no]
- Prior CFPB complaints about this issue? [yes/no]
- Bureau compliance training requirement? [yes/no]
- Bureau's own policies violated? [yes/no]
- Furnisher failure (if applicable)? [yes/no]

**Damages for THIS SPECIFIC VIOLATION:**

**Statutory Damages Range:** $100-$1,000 per violation × [# of bureaus affected] = $[X-$Y total]
- Minimum: $100 × [# bureaus] = $[amount]
- Maximum: $1,000 × [# bureaus] = $[amount]
- Realistic (mid-range): $[amount]

**Actual Damages IF Quantifiable:**
- Did this specific violation cause documented harm? [yes/no]
- If yes: [specific dollar amount from Stage 1 data or calculated]
- If no: [explain why speculative]

**Willfulness Multiplier (if applicable):**
- If willful: Statutory damages can be multiplied 1x-4x
- Multiplier justification for THIS violation: [1-4x range]
- Multiplied damages: Statutory × [multiplier] = $[amount]

---

[REPEAT THIS 8-12+ TIMES FOR EACH VIOLATION]

---

## PART 3: SYSTEMATIC WILLFULNESS ASSESSMENT (8-12 pages)

**Legal Standard: Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)**

Willfulness requires either:
1. Knowing violation of FCRA, OR
2. Reckless disregard of FCRA requirements

**Scoring System: 0-16 Points**

### CATEGORY 1: DIRECT KNOWLEDGE (0-4 points)
Evidence that defendants know FCRA requirements:

**Evidence of Bureau Knowledge (Score /4):**
- Major financial institution (TransUnion, Experian, Equifax): +2 points
- Written compliance training programs: +1 point
- CFPB guidance published and available: +1 point
- Prior FTC/CFPB regulatory actions: +1 point

**Evidence of Furnisher Knowledge (if applicable):**
- Credit reporting industry compliance standards: +1 point
- Metro 2 format requirements published: +1 point
- FCRA training mandatory in industry: +1 point

**CATEGORY 1 SCORE: ___/4**

### CATEGORY 2: PATTERN OF VIOLATIONS (0-5 points)

**Pattern Evidence (Score /5):**
- Same violation on client's multiple accounts: +1-2 points
- Similar violations reported by other consumers (CFPB database): +1-2 points
- Systematic procedure creates structural violation: +2-3 points
- Cross-bureau identical errors (suggests bureau coordination failure): +1 point
- Furnisher sending same incorrect data to all bureaus: +1-2 points

**CATEGORY 2 SCORE: ___/5**

### CATEGORY 3: AWARENESS INDICATORS (0-4 points)

**Evidence Bureau/Furnisher Knew About Violations (Score /4):**
- Prior settlements with similar violations: +2 points per incident
- CFPB consent order or warning letter: +2 points
- Prior class action settlements: +1 point
- Published complaints in regulatory database: +1 point
- Media/news coverage of similar violations: +1 point

**CATEGORY 3 SCORE: ___/4**

### CATEGORY 4: RECKLESSNESS INDICATORS (0-3 points)

**Reckless Disregard Evidence (Score /3):**
- No reasonable dispute verification procedures: +2 points
- Failure to investigate despite clear evidence of inaccuracy: +1-2 points
- Using automated/form responses to consumer disputes: +1 point
- Continued reporting after consumer disputes: +1 point
- Not contacting furnisher for verification: +1 point

**CATEGORY 4 SCORE: ___/3**

---

**TOTAL WILLFULNESS SCORE: ___/16**

**Score Interpretation:**
- 0-4 = Negligence only (0% willfulness probability)
- 5-8 = Mixed negligence/willfulness (20-40% willfulness probability)
- 9-12 = Likely willfulness (60-80% willfulness probability)
- 13-16 = Definite willfulness (90%+ willfulness probability)

**FINAL WILLFULNESS ASSESSMENT:** [X/16 points = Y% probability]

**Specific Evidence Supporting Score:**
[Detailed explanation of why this score, citing specific bureau/furnisher failures and evidence]

---

## PART 4: SETTLEMENT & CASE VALUATION ANALYSIS (10-15 pages)

**STANDING STRENGTH:** [Score from Part 1] /10
- Risk of MTD (Motion to Dismiss): [X%] based on circuit
- Probability of surviving MTD: [X%]
- Circuit-specific factors: [2nd/9th/other circuit analysis]

**VIOLATION STRENGTH:** [1-10 scale]
- Average violation quality across all violations: [X/10]
- Documentary evidence strength: [high/moderate/low]
- Bureau defensibility: [how easily can they argue these are technical?]

**DAMAGES CALCULATION - COMPREHENSIVE:**

**STATUTORY DAMAGES:**
- Total violations identified: [count]
- Per-violation statutory range: $100-$1,000
- Minimum scenario: [X violations] × $100 = $[amount]
- Maximum scenario: [X violations] × $1,000 = $[amount]
- Likely scenario: [X violations] × $[mid-range] = $[amount]
- If willful (multiply by willfulness factor): $[amount × multiplier]

**ACTUAL DAMAGES:**
- Credit score suppression harm: $[amount from Part 1]
- Interest rate premium: $[amount from Part 1]
- Credit denial impact: $[amount × # denials]
- Emotional distress/time: $[hours × rate]
- Credit monitoring costs: $[amount]
- Total actual damages: $[combined]

**PUNITIVE DAMAGES (if willful):**
- Conservative (1:1 multiplier): Statutory × 1 = $[amount]
- Moderate (2:1 multiplier): Statutory × 2 = $[amount]
- Aggressive (3-4:1 multiplier): Statutory × 3-4 = $[amount]

**TOTAL CASE VALUATION:**
- Conservative exposure (low statutory × 1): $[amount]
- Likely exposure (mid-range + 50% actual): $[amount]
- Worst-case exposure (max statutory + actual + punitive): $[amount]

**SETTLEMENT RECOMMENDATION (65% of likely):** $[amount]
- This represents realistic settlement probability
- 65% reflects typical settlement discount from worst-case

**Pre-Litigation Strategy:**
1. Send this demand letter with [X] days to respond
2. If no response or inadequate response: file complaint
3. MTD risk: [X%] (may survive based on standing score)
4. Trial strength: [X/10] if standing survives MTD
5. Appeal risk: [based on circuit]

---

## PART 5: CLIENT-FACING COMPREHENSIVE REPORT (40-50 pages)

**For:** [Client Name]
**Date:** [Today]
**Case ID:** [Analysis ID]

### Section A: Your Case at a Glance (4-6 pages)
- What we found: [X violations across Y bureaus]
- Your standing score: [X/10] - [what this means]
- Your case strength: [weak/moderate/strong] - [explanation]
- Your financial harm: $[X] to $[Y] potential exposure for bureaus
- Recommended next step: [settlement demand OR lawsuit preparation]
- Timeline: [30 days for response, then action]

### Section B: Detailed Violation Findings (15-20 pages)
For EACH violation (client-friendly version):
- What's wrong: [plain English explanation of the inaccuracy]
- Why it matters: [how it harmed your credit]
- Who's responsible: [bureau name and/or furnisher]
- What the law says: [cite FCRA requirement in plain English]
- Court cases supporting you: [names and holdings in simple terms]
- Your damages from this violation: $[specific amount]

Include tables and visual breakdowns so client understands

### Section C: Standing Analysis Explained (6-8 pages)
- The Supreme Court rule (TransUnion v. Ramirez) in plain English
- Why it matters for your case
- How we scored your standing: [specific explanation]
- Your dissemination evidence: [hard inquiries list]
- Your concrete harm evidence: [$X score suppression, $Y rate premium, etc.]
- Your causation evidence: [specific links to violations]
- Your final standing score: [X/10] and what it means

### Section D: Damages Breakdown (8-12 pages)
- What damages can you recover
- Statutory damages: How courts calculate it
- Your statutory damages estimate: $[min]-$[max] = $[likely]
- Actual damages you've suffered: $[amount] (documented)
- Punitive damages if court finds willfulness: $[multiplier range]
- Your total case value: $[conservative]-$[worst-case]
- Settlement recommendation: $[65% of likely]

### Section E: What Happens Next (2-4 pages)
- Send demand letter to bureaus (30-day response requirement)
- If they respond inadequately: file lawsuit
- If they don't respond: file lawsuit
- If we settle: [settlement distribution process]
- If we litigate: [timeline and process]
- Your role: [what you'll need to do]

---

## PART 6: FORMAL FCRA DISPUTE LETTERS - ROUND {dispute_round} (6-10 pages per bureau)

✂️────────────────────────────────────────✂️
START OF DISPUTE LETTER: EQUIFAX
✂️────────────────────────────────────────✂️

[Certified Mail - Return Receipt Requested]

[Today's Date]

Equifax Information Services
Attn: Consumer Dispute Department
P.O. Box [Address]

**RE: FORMAL FCRA DISPUTE - DEMAND FOR IMMEDIATE INVESTIGATION & CORRECTION**

**CONSUMER NAME:** [Client Name]
**EQUIFAX FILE NUMBER:** [if known]
**DATE OF DISPUTE:** [Today]
**DISPUTE ROUND:** {dispute_round}

Dear Equifax:

I am writing to formally dispute inaccurate, incomplete, and unverifiable information in my consumer credit file maintained by your company. This dispute is made pursuant to my statutory rights under the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681 et seq., and demands immediate, thorough investigation and correction of the violations detailed below.

**I. LEGAL BASIS FOR DISPUTE**

Under FCRA § 1681i(a)(1)(A), I have the right to dispute any information in my credit file that I believe is inaccurate or incomplete. Your agency is required to:

1. **Conduct a reasonable investigation** of my dispute within 30 days (§ 1681i(a)(1)(A))
2. **Follow "reasonable procedures"** to ensure accuracy (§ 1681e(b))
3. **Maintain maximum possible accuracy** in my file (§ 1681e(b))
4. **Delete unverifiable information** within 5 days (§ 1681i(a)(5)(A))
5. **Notify me of investigation results** in writing (§ 1681i(a)(6)(A))

**II. SPECIFIC DISPUTED ITEMS & VIOLATIONS**

[For EACH violation from Stage 1, include:]

**DISPUTE #[N]: [ACCOUNT NAME]**

**Account Information:**
- Original Creditor: [name]
- Account Number (masked): [XXXX####XXXXXX]
- Your Reported Status: [status]
- True Status: [actual status]
- Inaccuracy: [specific contradiction]

**How This Violates FCRA:**
[Citation to specific statute]
[Your bureau reported X, which violates the requirement to...]

**Evidence of Inaccuracy:**
[Client's supporting documentation if available]

**Applicable Case Law:**
- Cushman v. TransUnion Corp., 115 F.3d 220 (3d Cir. 1997) - [holding]
- [Other relevant case] - [holding]

**What I Demand:**
1. Delete this item within 5 days if unverifiable (§ 1681i(a)(5)(A))
2. Correct to accurate information
3. Provide Method of Verification per Cushman standard (tangible business records)
4. Notify all third parties who received inaccurate information (§ 1681i(a)(8))

[REPEAT FOR ALL VIOLATIONS]

**III. PATTERN OF VIOLATIONS**

The above items are not isolated errors but evidence of systematic failure to maintain reasonable procedures. The identical/similar errors across your file suggest:
- Inadequate verification procedures
- Systematic furnisher failure you permitted
- Failure to investigate prior disputes adequately

**IV. WILLFULNESS INDICATORS**

Your company's violations evidence reckless disregard of FCRA requirements:
- [Prior CFPB complaints/settlements]
- [CFPB consent orders]
- [Prior knowledge of similar violations]
- [Inadequate dispute procedures]

This may constitute willful violation under Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007), entitling me to statutory damages of $100-$1,000 per violation, plus actual damages and punitive damages up to $1,000 per willful violation.

**V. MY DAMAGES CLAIM**

Statutory damages for [X] violations: $[min]-$[max]
Actual damages from inaccuracy: $[amount]
Punitive damages (if willful): $[amount]
**TOTAL EXPOSURE: $[combined]**

**VI. INVESTIGATION DEADLINE & DEMANDS**

Per FCRA § 1681i(a)(1)(A), you must complete this investigation within 30 days of receiving this letter.

**FAILURE TO COMPLY CONSTITUTES ADDITIONAL FCRA VIOLATION:**
- Failure to investigate = § 1681i(g) violation
- Failure to delete unverifiable = § 1681i(a)(5) violation
- Continued reporting after notice = § 1681e(b) violation

**VII. RLPP ESCALATION** [Adjusted by Round]:
[Round 1: Professional tone, clear demands]
[Round 2: Reference prior bureau failures, regulatory history]
[Round 3: Indicate legal action if not resolved]
[Round 4: Frame settlement as alternative to litigation]

---

**DEMANDS:**
1. Begin investigation immediately - do not delay
2. Contact furnisher within 5 days
3. Conduct thorough investigation (not automated form)
4. Contact me with results within 25 days (5-day buffer)
5. Delete unverifiable items
6. Correct inaccurate information
7. Provide written explanation of findings
8. Notify third parties of corrections

---

**LEGAL NOTICE:**
Willful violation of FCRA entitles me to recover:
- Statutory damages: $100-$1,000 per violation
- Actual damages: All documented harm
- Punitive damages: Up to 4x statutory damages
- Attorney's fees and court costs
- Total potential recovery: $[X-$Y]

This letter constitutes formal notice of violation. If my dispute is not investigated thoroughly and resolved favorably, I will pursue litigation.

Sincerely,

[Client Name]
[Address]
[Phone]
[Email]

**CC: Federal Trade Commission, CFPB**

✂️────────────────────────────────────────✂️
END OF DISPUTE LETTER: EQUIFAX
✂️────────────────────────────────────────✂️

[REPEAT FOR EXPERIAN AND TRANSUNION WITH BUREAU-SPECIFIC DETAILS]

---

## PART 7: METHOD OF VERIFICATION REQUESTS (3-5 pages per bureau)

✂️────────────────────────────────────────✂️
START OF MOV REQUEST: EQUIFAX
✂️────────────────────────────────────────✂️

[Certified Mail - Return Receipt Requested]

**RE: CUSHMAN-STANDARD METHOD OF VERIFICATION REQUEST**
**PER:** Cushman v. TransUnion Corp., 115 F.3d 220 (3d Cir. 1997)

**Legal Basis:**
Furnishers and bureaus must maintain tangible documentary evidence for all reported information. Upon consumer dispute, you must provide:

**DEMAND FOR BUSINESS RECORDS:**

For each account in dispute:
1. **Original creditor's running account ledger** - complete transaction history
2. **Billing statements** covering entire period account reported
3. **Payment history documentation** with specific payment dates/amounts
4. **Charge-off authorization** (if applicable)
5. **Metro 2 format submission** proof from furnisher
6. **Any written communications** about account status
7. **Verification method documentation** - how you verified this information

**Specific Accounts Requiring Verification:**
[List each disputed account with required documentation]

---

**OUTPUT THIS FULL 80-120 PAGE PACKAGE:**
- TOTAL PAGES: [count and confirm 80+]
- All Parts 0-7 with full forensic detail
- NO templates - ONLY actual Stage 1 account data
- Definitive scores and percentages (not "potential")
- Quantified damages with formulas shown
- RLPP language intensity for Round {dispute_round}
- Professional litigation-ready format
- Scissor markers (✂️) around all letters
- Ready for bureaus or immediate attorney submission

---

**FINAL VALIDATION CHECKLIST:**
- [ ] Total pages: 80+ (aim for 107-120)
- [ ] All 8-12+ violations included
- [ ] Bureau-by-bureau comparisons with specific data
- [ ] Definitive standing score 1-10
- [ ] Willfulness scoring 0-16 points  
- [ ] Damages formulas shown
- [ ] Case law with holdings and applications
- [ ] Client-facing report 40-50 pages
- [ ] All 3 bureau dispute letters (Equifax, Experian, TransUnion)
- [ ] MOV requests
- [ ] RLPP language appropriate for Round {dispute_round}
- [ ] NO placeholders or templates - all actual data
- [ ] Ready for immediate legal action or settlement
"""
        
        return prompt


def get_prompt_loader():
    """Factory function to get PromptLoader instance"""
    return PromptLoader()
