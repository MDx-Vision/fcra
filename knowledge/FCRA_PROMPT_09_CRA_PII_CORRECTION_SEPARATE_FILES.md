# FCRA PROMPT 09: BIG 3 CRA â€” PII CORRECTION (SEPARATE FILES)
## Upload â†’ Analyze â†’ Confirm â†’ Generate 3 Separate Files

**Version:** 3.0 (Separate File Output + Two-Step)
**Created:** November 24, 2025
**Output:** 3 separate PII correction letters after user confirmation

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Upload credit report

**STEP 2:** Paste correct PII info

**STEP 3:** Claude shows PII discrepancy table + asks confirmation

**STEP 4:** Confirm what to keep/delete

**STEP 5:** Claude generates 3 letters as separate files

**STEP 6:** Download individual files

---

## ðŸ“ CORRECT PII TEMPLATE:

```
CORRECT INFORMATION (Only what SHOULD appear):

NAME: [Full Legal Name]
ADDRESS: [Current Address]
SSN: [XXX-XX-XXXX]
DOB: [MM/DD/YYYY]
PHONE: [Phone or "REMOVE ALL"]
EMPLOYER: [Employer or "REMOVE ALL"]

CASE INFO:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
FCRA PII CORRECTION GENERATOR (SEPARATE FILES + TWO-STEP)
===========================================================================

**TWO-STEP PROCESS:**

**STEP 1:** Analyze report â†’ Show PII table â†’ Ask confirmation
**STEP 2:** After confirmation â†’ Generate 3 separate files

**FILE NAMING:**

```
PII_Experian_[LASTNAME]_[CASENUM].md
PII_TransUnion_[LASTNAME]_[CASENUM].md
PII_Equifax_[LASTNAME]_[CASENUM].md
```

---

**STEP 1 OUTPUT:**

Generate PII discrepancy table:

| PII Type | TransUnion | Experian | Equifax | CORRECT | Action |
|----------|------------|----------|---------|---------|--------|
| Name | [TU data] | [EX data] | [EQ data] | [User input] | [Actions needed] |
| Address | [TU data] | [EX data] | [EQ data] | [User input] | [Actions needed] |
| DOB | [TU data] | [EX data] | [EQ data] | [User input] | [Actions needed] |

**CRITICAL ISSUES IDENTIFIED:**

1. [Issue 1 description]
2. [Issue 2 description]

**CONFIRMATION NEEDED:**

Previous Addresses:
- [Address 1] â€” KEEP or DELETE?
- [Address 2] â€” KEEP or DELETE?

Employers:
- [Employer 1] â€” KEEP or DELETE?

**QUICK OPTION:** Reply "proceed with full cleanup" to delete all except current

---

**AFTER USER CONFIRMS, PROCEED TO STEP 2:**

Generate 3 separate PII correction letters based on user's instructions.

Use create_file tool for each.

===========================================================================
LETTER TEMPLATE (For Each CRA)
===========================================================================

[Consumer Name]
[Address]

[Date]

[CRA NAME]
[CRA ADDRESS]

**SENT VIA CERTIFIED MAIL**

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**RE: FORMAL DEMAND TO CORRECT PERSONAL IDENTIFYING INFORMATION**
**FCRA Â§Â§ 1681e(b), 1681i â€” INACCURATE PII VIOLATES FEDERAL LAW**
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

**Consumer:** [Name]
**SSN:** [XXX-XX-XXXX]
**Case Reference:** [Case Number]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Dear Sir or Madam:

I have reviewed my credit file from [CRA Name] and discovered **INACCURATE
PERSONAL IDENTIFYING INFORMATION** in violation of FCRA Â§ 1681e(b).

**This is not a request. This is a DEMAND backed by federal law.**

---------------------------------------------------------------------------
SECTION 1: INACCURATE PII IN YOUR FILE â€” DELETE THESE
---------------------------------------------------------------------------

[Based on analysis, list what THIS bureau shows incorrectly:]

**INCORRECT NAMES:**
âœ— [Wrong name 1] â€” DELETE
âœ— [Wrong name 2] â€” DELETE

**INCORRECT ADDRESSES:**
âœ— [Wrong address 1] â€” DELETE
âœ— [Wrong address 2] â€” DELETE

**INCORRECT PHONE NUMBERS:**
âœ— [Wrong phone 1] â€” DELETE

**INCORRECT EMPLOYERS:**
âœ— [Wrong employer 1] â€” DELETE

---------------------------------------------------------------------------
SECTION 2: CORRECT INFORMATION â€” KEEP ONLY THESE
---------------------------------------------------------------------------

**NAME:** âœ“ [Full Legal Name] â€” DELETE ALL OTHERS

**ADDRESS:** âœ“ [Current Address] â€” DELETE ALL OTHERS
[If user approved previous addresses, list them]

**SSN:** âœ“ [XXX-XX-XXXX] â€” DELETE ALL VARIATIONS

**DOB:** âœ“ [MM/DD/YYYY]

**PHONE:** âœ“ [Phone or NONE] â€” DELETE ALL OTHERS

**EMPLOYER:** âœ“ [Employer or NONE] â€” DELETE ALL OTHERS

---------------------------------------------------------------------------
SECTION 3: WHY THIS MATTERS â€” LEGAL VIOLATIONS
---------------------------------------------------------------------------

Inaccurate PII violates FCRA Â§ 1681e(b) and causes direct harm:

1. **Mixed file risk** â€” Incorrect PII can mix my file with another consumer
2. **Identity theft vulnerability**
3. **Inaccurate credit reporting**
4. **Employment and housing impact**

**EVERY DAY you maintain inaccurate PII = continuing Â§ 1681e(b) violation.**

---------------------------------------------------------------------------
SECTION 4: DAMAGES EXPOSURE
---------------------------------------------------------------------------

| Violation | Damages |
|-----------|---------|
| Failure to maintain accuracy | $100-$1,000 per violation |
| Failure to correct after notice | $100-$1,000 per violation |
| Mixed file (if applicable) | $1,000+ |
| Punitive (if willful) | 2-4x statutory |
| Attorney fees | $15,000+ |

**You are on notice. Continued inaccuracy after this letter = willfulness
under Safeco v. Burr.**

---------------------------------------------------------------------------
SECTION 5: DEMAND
---------------------------------------------------------------------------

I DEMAND [CRA Name]:

1. DELETE all incorrect PII listed in Section 1
2. CONFIRM corrections in writing within 30 days
3. PROVIDE updated disclosure showing ONLY correct PII

**Non-compliance = CFPB, FTC, State AG complaints + FCRA litigation.**

---------------------------------------------------------------------------

[Consumer Name]
[Address]

Sincerely,

_______________________________________
[Consumer Name]

Date: [Date]

**ENCLOSURES:** ID, SSN card, proof of address

===========================================================================
AFTER GENERATING STEP 2 FILES
===========================================================================

**FILES CREATED:**

| # | File Name | CRA |
|---|-----------|-----|
| 1 | PII_Experian_[NAME]_[CASE].md | Experian |
| 2 | PII_TransUnion_[NAME]_[CASE].md | TransUnion |
| 3 | PII_Equifax_[NAME]_[CASE].md | Equifax |

**All files saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINKS:**

[Provide computer:// links]

**NEXT STEPS:**
1. Download all 3 letters
2. Print on letterhead
3. Include enclosures
4. Mail via certified mail

===========================================================================
END OF PROMPT
===========================================================================
