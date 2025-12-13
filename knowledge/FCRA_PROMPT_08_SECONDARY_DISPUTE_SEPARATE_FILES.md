# FCRA PROMPT 08: SECONDARY BUREAU DISPUTES (SEPARATE FILES)
## Dispute Errors Found in Secondary Bureau Files

**Version:** 2.0 (Separate File Output)  
**Created:** November 24, 2025  
**Output:** One file per secondary bureau disputed  

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Upload or paste info from secondary bureau file disclosure received

**STEP 2:** Paste client info + errors found

**STEP 3:** Claude generates dispute letter as separate file

**STEP 4:** Download file

---

## ðŸ“ CLIENT INFO:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- SSN (Full): [XXX-XX-XXXX]
- DOB: [MM/DD/YYYY]

WHICH BUREAU: [Select one bureau to dispute]

FILE DISCLOSURE INFO:
- Date Received: [Date]
- Date Dated: [Date]

ERRORS FOUND:
[Describe PII errors and/or account errors]

CASE INFO:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
SECONDARY BUREAU DISPUTE GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Generate dispute letter for specified secondary bureau
2. **SAVE AS SEPARATE FILE**

**FILE NAMING:**

```
Dispute_[BUREAU_NAME]_[LASTNAME]_[CASENUM].md
```

Example: `Dispute_ChexSystems_SMITH_12345.md`

**Use create_file tool.**

===========================================================================
LETTER TEMPLATE
===========================================================================

[Consumer Name]
[Address]

[Date]

[BUREAU NAME]
[BUREAU ADDRESS]

**SENT VIA CERTIFIED MAIL**

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**RE: FORMAL DISPUTE OF INACCURATE INFORMATION**
**FCRA Â§ 1681i â€” DEMAND FOR REINVESTIGATION**
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

**Consumer:** [Name]
**SSN:** [XXX-XX-XXXX]
**DOB:** [MM/DD/YYYY]
**File Disclosure Date:** [Date]
**Case Reference:** [Case Number]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Dear Sir or Madam:

On [Date], I received my file disclosure from [Bureau Name]. Upon review, 
I have identified inaccuracies that must be corrected immediately.

Pursuant to FCRA Â§ 1681i, I formally dispute the following.

---------------------------------------------------------------------------
SECTION 1: PERSONAL INFORMATION ERRORS
---------------------------------------------------------------------------

[List PII errors from user input]

**INCORRECT NAME(S):** [List]
**CORRECT:** [Correct name only]

**INCORRECT ADDRESS(ES):** [List]
**CORRECT:** [Correct address only]

[Continue for SSN, DOB, phones, employers]

---------------------------------------------------------------------------
SECTION 2: ACCOUNT ERRORS
---------------------------------------------------------------------------

[List account errors from user input]

**DISPUTED ACCOUNT #1:**
- Company: [Name]
- Account: [Number]
- What Your File Shows: [Description]
- Why Wrong: [Reason]
- DEMAND: [Delete / Correct]

[Continue for all disputed accounts]

---------------------------------------------------------------------------
SECTION 3: UNAUTHORIZED INQUIRIES
---------------------------------------------------------------------------

[If applicable, list unauthorized inquiries]

---------------------------------------------------------------------------
SECTION 4: LEGAL REQUIREMENTS
---------------------------------------------------------------------------

Under FCRA Â§ 1681i, you must:

1. Conduct reasonable reinvestigation within 30 DAYS
2. DELETE information that cannot be verified
3. CORRECT information that is inaccurate
4. Provide written results within 5 DAYS of completion

[Bureau-specific language based on specialty]

---------------------------------------------------------------------------
SECTION 5: CONSEQUENCES
---------------------------------------------------------------------------

Failure to comply results in:

1. CFPB Complaint
2. FTC Complaint
3. State AG Complaint
4. FCRA legal remedies

---------------------------------------------------------------------------

[Consumer Name]
[Address]

Sincerely,

_______________________________________
[Consumer Name]

Date: [Date]

**ENCLOSURES:** Copy of file disclosure, ID, proof of address

===========================================================================
FILE GENERATED
===========================================================================

**FILE CREATED:**

Dispute_[BUREAU]_[NAME]_[CASE].md

**Saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINK:**

[Provide computer:// link]

**NEXT STEPS:**
1. Download letter
2. Include enclosures
3. Mail via certified mail
4. Set 30-day follow-up

===========================================================================
END OF PROMPT
===========================================================================
