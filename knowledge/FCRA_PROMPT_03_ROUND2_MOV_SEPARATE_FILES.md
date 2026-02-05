# FCRA PROMPT 03: ROUND 2 â€” METHOD OF VERIFICATION (SEPARATE FILES)
## Escalated MOV Demands After "Verified" Responses

**Version:** 2.0 (Separate File Output)
**Created:** November 24, 2025
**Use Case:** Round 2 escalation after CRAs/Furnishers claim "verified"
**Output:** Each MOV letter saved as separate downloadable file
**Deadline:** 15 days (shorter than Round 1's 30 days)

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Start new Claude chat

**STEP 2:** Upload credit report + Round 1 letters sent + Bureau responses received

**STEP 3:** Paste client info block

**STEP 4:** Copy prompt and paste

**STEP 5:** Claude generates MOV letters and saves each as separate file

**STEP 6:** Download individual files from outputs folder

---

## ðŸ“ CLIENT INFO TEMPLATE:

```
CONSUMER INFORMATION:
- Full Name: [Name]
- Address: [Address]
- City, State ZIP: [City, State ZIP]
- SSN Last 4: [XXXX]
- DOB: [MM/DD/YYYY]

ROUND 1 INFORMATION:
- Date Round 1 Letters Mailed: [Date]
- Which bureaus/furnishers responded: [List]
- What they claimed: [Verified / Deleted / etc.]

FIRM INFORMATION:
- Firm Name: Brightpath Ascend Group
- Address: [Your Address]

CASE INFORMATION:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
FCRA ROUND 2 â€” METHOD OF VERIFICATION GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Analyze uploaded materials (report + Round 1 letters + responses)
2. Identify which accounts still inaccurate after "verification"
3. Generate aggressive MOV demand letters
4. **SAVE EACH LETTER AS SEPARATE FILE** in /mnt/user-data/outputs/

**FILE NAMING:**

```
Round2_MOV_Experian_[LASTNAME]_[CASENUM].md
Round2_MOV_TransUnion_[LASTNAME]_[CASENUM].md
Round2_MOV_Equifax_[LASTNAME]_[CASENUM].md
Round2_MOV_[FURNISHER]_[LASTNAME]_[CASENUM].md
```

**Use create_file tool for each letter.**

===========================================================================
LETTER TEMPLATE â€” METHOD OF VERIFICATION DEMAND
===========================================================================

[Consumer Full Name]
[Consumer Address]
[City, State ZIP]

[Today's Date]

[RECIPIENT NAME]
[RECIPIENT ADDRESS]

**SENT VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED**

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**RE: METHOD OF VERIFICATION DEMAND â€” FCRA Â§ 1681i(a)(7)**
**CUSHMAN v. TRANS UNION CORP. â€” TANGIBLE PROOF REQUIRED**
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

**Consumer:** [Full Legal Name]
**SSN (Last 4):** XXX-XX-[XXXX]
**Case Reference:** [Case Number]
**Round 1 Dispute Date:** [Date sent]
**Your Response Date:** [Date received]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Dear Sir or Madam:

On [Date], I submitted a formal dispute pursuant to FCRA Â§ 1681i. On [Date],
you responded claiming the disputed information was "verified."

**Pursuant to FCRA Â§ 1681i(a)(7), I DEMAND that you provide the METHOD OF
VERIFICATION you used.**

Under *Cushman v. Trans Union Corp.*, 115 F.3d 220 (3d Cir. 1997),
"verification" requires tangible documentary proof â€” not mere confirmation
from a database or furnisher's assertion.

---------------------------------------------------------------------------
SECTION 1: DISPUTED ITEMS STILL INACCURATE
---------------------------------------------------------------------------

Despite your claim of "verification," the following remain inaccurate:

**Account:** [Account Number]
**Creditor:** [Creditor Name]
**What You Verified:** [What their response claimed]
**Why Still Wrong:** [Explain contradiction/impossibility]

[List each disputed item still showing incorrectly]

---------------------------------------------------------------------------
SECTION 2: METHOD OF VERIFICATION DEMAND
---------------------------------------------------------------------------

Under FCRA Â§ 1681i(a)(7), you must provide:

1. **Complete description** of the reinvestigation procedure used
2. **Name and business address** of the furnisher who provided verification
3. **Actual documentary evidence** you reviewed (not database entries)

**Specifically, provide:**

â˜ Copy of original signed contract/application
â˜ Complete payment history from original creditor
â˜ Documentation of the specific data points verified
â˜ Chain of custody documentation for sold/assigned accounts
â˜ Accounting showing how balance was calculated
â˜ For late payments: Late fee assessment, rate increase, warning letter
â˜ Name and contact info of person who conducted verification

**A computer printout or database entry is NOT verification under Cushman.**

---------------------------------------------------------------------------
SECTION 3: CUSHMAN STANDARD
---------------------------------------------------------------------------

*Cushman v. Trans Union Corp.* established that:

"Verification requires the CRA to obtain additional information from the
furnisher beyond a mere confirmation of the disputed entry. The CRA must
obtain tangible evidence that the item is accurate."

**Your response claiming "verified" without providing tangible documentary
proof violates Cushman.**

**If you cannot provide actual documentation, you must DELETE the disputed
information under FCRA Â§ 1681i(a)(5)(A).**

---------------------------------------------------------------------------
SECTION 4: 15-DAY DEADLINE
---------------------------------------------------------------------------

You have **15 DAYS** from receipt of this letter to:

1. **PROVIDE** the method of verification with documentary evidence, OR
2. **DELETE** the disputed information

Failure to comply within 15 days will result in escalation to regulatory
complaints and legal action.

---------------------------------------------------------------------------
SECTION 5: CONSEQUENCES
---------------------------------------------------------------------------

Non-compliance will result in:

1. **CFPB Complaint** under 12 C.F.R. Â§ 1022.43
2. **FTC Complaint**
3. **State AG Complaint**
4. **Legal action** under FCRA Â§Â§ 1681n and 1681o

**You are on notice.** Continued reporting without proper verification
after this demand constitutes willfulness under *Safeco v. Burr*.

---------------------------------------------------------------------------

Direct all correspondence to:

[Firm Name]
[Firm Address]

Case Reference: [Case Number]

Sincerely,

_______________________________________
[Consumer Name]

Date: [Today's Date]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**ENCLOSURES:**
â˜ Copy of Round 1 dispute letter
â˜ Copy of your "verified" response
â˜ Highlighted inaccuracies still present
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

===========================================================================
AFTER GENERATING ALL LETTERS
===========================================================================

**FILES CREATED:**

| # | File Name | Recipient | Status |
|---|-----------|-----------|--------|
| 1 | Round2_MOV_Experian_[NAME]_[CASE].md | Experian | Generated |
| 2 | Round2_MOV_TransUnion_[NAME]_[CASE].md | TransUnion | Generated |
| 3 | Round2_MOV_Equifax_[NAME]_[CASE].md | Equifax | Generated |
| 4 | Round2_MOV_[FURN1]_[NAME]_[CASE].md | [Furnisher 1] | Generated |

**Total Files Generated:** [X]

**All files saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINKS:**

[Provide computer:// links for each file]

**NEXT STEPS:**
1. Download all MOV letters
2. Print on letterhead
3. Include enclosures (Round 1 letter + their response)
4. Mail via certified mail
5. Set 15-day follow-up reminder

===========================================================================
END OF PROMPT
===========================================================================
