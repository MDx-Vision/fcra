# FCRA PROMPT 02: ROUND 1 LETTERS ONLY (SEPARATE FILES)
## Upload Report → Generate Individual Letter Files

**Version:** 2.0 (Separate File Output)  
**Created:** November 24, 2025  
**Use Case:** Existing clients who need Round 1 dispute letters only  
**Output:** Each letter saved as a separate downloadable file  
**Does NOT Generate:** Client report, standing analysis, violation summary

---

## 📋 HOW TO USE:

**STEP 1:** Start new Claude chat

**STEP 2:** Upload credit report (PDF or PNG — all 3 bureaus)

**STEP 3:** Paste client info block (below)

**STEP 4:** Copy everything from "PROMPT STARTS HERE" and paste

**STEP 5:** Claude generates letters and saves each as separate file

**STEP 6:** Download individual files from outputs folder

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

FIRM INFORMATION:
- Firm Name: Brightpath Ascend Group
- Address: [Your Address]
- Phone: [Your Phone]
- Email: [Your Email]

CASE INFORMATION:
- Case File Number: [Your case number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

===========================================================================
FCRA ROUND 1 LETTERS GENERATOR — SEPARATE FILE OUTPUT
===========================================================================

**YOUR TASK:**

1. Analyze uploaded credit report
2. Identify all violations for Round 1 RLPP strategy
3. Generate dispute letters (CRAs + Furnishers)
4. **SAVE EACH LETTER AS A SEPARATE FILE** in /mnt/user-data/outputs/

**CRITICAL: Use create_file tool to save each letter separately.**

**FILE NAMING CONVENTION:**

For CRA letters:
- `Round1_Experian_[LASTNAME]_[CASENUM].md`
- `Round1_TransUnion_[LASTNAME]_[CASENUM].md`
- `Round1_Equifax_[LASTNAME]_[CASENUM].md`

For Furnisher letters:
- `Round1_[FURNISHER_NAME]_[LASTNAME]_[CASENUM].md`

Example:
- `Round1_Experian_PERDOMO_12345.md`
- `Round1_CapitalOne_PERDOMO_12345.md`

===========================================================================
GENERATION INSTRUCTIONS
===========================================================================

**STEP 1: ANALYZE REPORT**

Identify violations:
- Impossible contradictions (cross-bureau)
- Metro 2 compliance failures
- Late payments without evidence
- Charge-off balance issues
- Ghost accounts
- Any other FCRA violations

**STEP 2: RLPP BUNDLING**

For EACH letter (CRA or Furnisher):
- Lead with strongest violation for that recipient
- Bundle in ALL late payments from consumer's file
- Use "poison pill" strategy (delete easier than investigate)

**STEP 3: GENERATE LETTERS**

Create one letter per recipient:
- 3 CRA letters (Experian, TransUnion, Equifax)
- 1 letter per furnisher with violations

**STEP 4: SAVE AS SEPARATE FILES**

Use create_file tool for EACH letter with proper naming.

===========================================================================
LETTER TEMPLATE — USE FOR EACH RECIPIENT
===========================================================================

[Consumer Full Name]
[Consumer Address]
[City, State ZIP]

[Today's Date]

[RECIPIENT NAME]
[RECIPIENT ADDRESS]

**SENT VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED**

═══════════════════════════════════════════════════════════════════════
**RE: FORMAL DISPUTE OF INACCURATE INFORMATION**
**FCRA § 1681i — DEMAND FOR REINVESTIGATION**
═══════════════════════════════════════════════════════════════════════

**Consumer:** [Full Legal Name]
**SSN (Last 4):** XXX-XX-[XXXX]
**Date of Birth:** [DOB]
**Case Reference:** [Case Number]

═══════════════════════════════════════════════════════════════════════

Dear Sir or Madam:

Pursuant to the Fair Credit Reporting Act, 15 U.S.C. § 1681i, I am formally 
disputing the following inaccurate information in my credit file.

[IF CRA - INCLUDE THIS SECTION:]
As a consumer reporting agency, you are required under FCRA § 1681e(b) to 
"follow reasonable procedures to assure maximum possible accuracy." The 
violations detailed below demonstrate your failure to meet this standard.

[IF FURNISHER - INCLUDE THIS SECTION:]
As a furnisher of information, you are required under FCRA § 1681s-2(a) to 
ensure accuracy before reporting and to conduct reasonable investigations 
of disputes.

---------------------------------------------------------------------------
SECTION 1: PRIMARY VIOLATION — [VIOLATION TYPE]
---------------------------------------------------------------------------

**Account:** [Account Number]
**Creditor:** [Creditor Name]

**VIOLATION DETAILS:**

[Describe the PRIMARY violation for this recipient - the strongest one]

[For impossible contradictions:]
Your report shows [Account] with [Status/Balance], but:
- [Other Bureau 1] reports: [Different Status/Balance]
- [Other Bureau 2] reports: [Different Status/Balance]

**These reports are mutually exclusive. All three cannot be accurate 
simultaneously.** Under FCRA § 1681e(b), maintaining logically impossible 
data is a clear violation.

[For Metro 2 violations:]
Your report shows [Account] with:
- Payment Status: "[Status]"
- Payment Rating: "[Rating]"

**This combination violates Metro 2® reporting standards.** An account 
cannot be reported as "[Status]" while also showing "[Rating]."

[For late payments:]
Your report shows a [X]-day late payment on [Date] for [Account].

**This late payment lacks supporting evidence:**
- No late fee assessed
- No interest rate increase
- No warning letter documentation
- No change in account status

Under *Cushman v. Trans Union Corp.*, you must provide tangible documentary 
proof. Without such proof, this late payment appears fabricated and must 
be deleted.

[For charge-offs:]
Your report shows [Account] was charged off for $[Amount], yet the balance 
continues to show as $[Current Balance].

**A charged-off account cannot continue accruing charges.** This violates 
FCRA § 1681s-2 and demonstrates either inaccurate reporting or continued 
improper collection activity.

**DEMAND:** [Delete this account / Correct balance to $0 / Update status 
to accurate / etc.]

---------------------------------------------------------------------------
SECTION 2: ADDITIONAL VIOLATIONS — LATE PAYMENT BUNDLING
---------------------------------------------------------------------------

**In addition to the primary violation above, the following late payments 
in my file also lack documentation and must be deleted:**

[LIST ALL LATE PAYMENTS FROM THE CONSUMER'S ENTIRE FILE]

**Account:** [Account 2]
**Creditor:** [Creditor 2]
**Late Payment(s):** [Date(s)]
**Problem:** No documented late fee, no rate increase, no warning letter

**DEMAND:** Delete all disputed late payments

---

**Account:** [Account 3]
**Creditor:** [Creditor 3]
**Late Payment(s):** [Date(s)]
**Problem:** No documented late fee, no rate increase, no warning letter

**DEMAND:** Delete all disputed late payments

---

[Continue for ALL accounts with late payments]

---------------------------------------------------------------------------
SECTION 3: LEGAL REQUIREMENTS
---------------------------------------------------------------------------

Under FCRA § 1681i, you are required to:

1. Conduct a reasonable reinvestigation within **30 DAYS**
2. Review all relevant information provided
3. **DELETE** information that cannot be verified
4. **CORRECT** information that is inaccurate
5. Provide written notice of results within **5 DAYS** of completion

Under *Cushman v. Trans Union Corp.*, verification requires tangible 
documentary proof — not mere confirmation from your database. You must 
obtain and review actual documentation supporting each disputed item.

**For late payments specifically:** You must provide:
- Copy of late fee assessment
- Documentation of interest rate increase
- Copy of warning letter sent to consumer
- Account statements showing late payment processing

**If you cannot provide this documentation, you MUST DELETE the late 
payment under FCRA § 1681i(a)(5)(A).**

---------------------------------------------------------------------------
SECTION 4: CONSEQUENCES OF NON-COMPLIANCE
---------------------------------------------------------------------------

Failure to conduct a reasonable reinvestigation or delete unverifiable 
information will result in:

1. Formal complaint to the **Consumer Financial Protection Bureau (CFPB)** 
   under 12 C.F.R. § 1022.43

2. Formal complaint to the **Federal Trade Commission (FTC)**

3. Formal complaint to **[State] Attorney General**

4. Pursuit of all legal remedies under FCRA including:
   - Statutory damages of $100-$1,000 per willful violation (§ 1681n)
   - Actual damages for negligent violations (§ 1681o)
   - Punitive damages for willful non-compliance
   - Attorney fees and costs

**You are hereby on notice.** Under *Safeco Insurance Co. v. Burr*, 
continued reporting of disputed information without proper verification 
after receiving this letter may constitute willful violation, exposing you 
to enhanced damages.

---------------------------------------------------------------------------
SECTION 5: REPRESENTATION NOTICE
---------------------------------------------------------------------------

Please direct all correspondence regarding this matter to:

[Firm Name]
[Firm Address]
[Firm Phone]
[Firm Email]

**Case Reference:** [Case Number]

Do not contact the consumer directly. All communication must go through 
our office.

---------------------------------------------------------------------------

Sincerely,

_______________________________________
[Consumer Name]

Date: [Today's Date]

═══════════════════════════════════════════════════════════════════════
**ENCLOSURES:**
☐ Copy of credit report (disputed items highlighted)
☐ Copy of government-issued ID
☐ Proof of address
═══════════════════════════════════════════════════════════════════════

===========================================================================
AFTER GENERATING ALL LETTERS
===========================================================================

**PROVIDE SUMMARY TABLE:**

| # | File Name | Recipient | Type | Violations |
|---|-----------|-----------|------|------------|
| 1 | Round1_Experian_[NAME]_[CASE].md | Experian | CRA | [Count] |
| 2 | Round1_TransUnion_[NAME]_[CASE].md | TransUnion | CRA | [Count] |
| 3 | Round1_Equifax_[NAME]_[CASE].md | Equifax | CRA | [Count] |
| 4 | Round1_[FURNISHER1]_[NAME]_[CASE].md | [Furnisher 1] | Furnisher | [Count] |
| 5 | Round1_[FURNISHER2]_[NAME]_[CASE].md | [Furnisher 2] | Furnisher | [Count] |

**Total Letters Generated:** [X]
**Total Files Created:** [X]

**All files saved to:** `/mnt/user-data/outputs/`

**DOWNLOAD LINKS:**

[Provide computer:// link for each file]

**NEXT STEPS:**
1. Download all letters
2. Review for accuracy
3. Print on letterhead
4. Include enclosures
5. Mail via certified mail, return receipt requested
6. Set 30-day follow-up reminder

===========================================================================
END OF PROMPT
===========================================================================
