# FCRA PROMPT 07: SECONDARY BUREAUS â€” FREEZE + FILE (SEPARATE FILES)
## Upload â†’ Analyze â†’ Generate 9 Separate Files

**Version:** 3.0 (Separate File Output)  
**Created:** November 24, 2025  
**Output:** 9 separate files (one per secondary bureau)  

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Upload credit report

**STEP 2:** Paste client info

**STEP 3:** Claude generates 9 freeze + file request letters as separate files

**STEP 4:** Download individual files

---

## ðŸ“ CLIENT INFO:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- SSN (Full): [XXX-XX-XXXX]
- DOB: [MM/DD/YYYY]

PREVIOUS ADDRESSES (Last 5 years):
- [Address 1 or "None"]

CASE INFO:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
SECONDARY BUREAU FREEZE + FILE GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Analyze report to confirm consumer info
2. Generate 9 freeze + file request letters
3. **SAVE EACH AS SEPARATE FILE**

**FILE NAMING:**

```
Freeze_Innovis_[LASTNAME]_[CASENUM].md
Freeze_ChexSystems_[LASTNAME]_[CASENUM].md
Freeze_ClarityServices_[LASTNAME]_[CASENUM].md
Freeze_LexisNexisConsumer_[LASTNAME]_[CASENUM].md
Freeze_CoreLogicTeletrack_[LASTNAME]_[CASENUM].md
Freeze_FactorTrust_[LASTNAME]_[CASENUM].md
Freeze_MicroBilt_[LASTNAME]_[CASENUM].md
Freeze_LexisNexisRisk_[LASTNAME]_[CASENUM].md
Freeze_DataX_[LASTNAME]_[CASENUM].md
```

**Use create_file tool for each.**

===========================================================================
LETTER TEMPLATE (Each Bureau)
===========================================================================

[Consumer Name]
[Address]

[Date]

[BUREAU NAME]
[BUREAU ADDRESS]

**SENT VIA CERTIFIED MAIL**

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**RE: SECURITY FREEZE REQUEST & FULL FILE DISCLOSURE DEMAND**
**FCRA Â§Â§ 1681c-1 and 1681g**
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

**Consumer:** [Name]
**SSN:** [XXX-XX-XXXX]
**DOB:** [MM/DD/YYYY]
**Case Reference:** [Case Number]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Dear Sir or Madam:

Pursuant to FCRA, I submit the following DEMANDS.

---------------------------------------------------------------------------
DEMAND #1: SECURITY FREEZE â€” FCRA Â§ 1681c-1
---------------------------------------------------------------------------

I DEMAND security freeze on my file maintained by [Bureau Name].

**YOUR OBLIGATIONS:**
1. Place freeze within 1-3 business days
2. Send confirmation within 5 business days
3. Provide unique PIN/password
4. NO FEE (prohibited by federal law)

**Failure = statutory damages + punitive + attorney fees.**

---------------------------------------------------------------------------
DEMAND #2: FULL FILE DISCLOSURE â€” FCRA Â§ 1681g
---------------------------------------------------------------------------

I DEMAND complete disclosure of ALL information in my file:

[Bureau-specific disclosure items based on their specialty]

**FREE disclosure per FCRA Â§ 1681j.**

---------------------------------------------------------------------------
CONSUMER IDENTIFICATION
---------------------------------------------------------------------------

**Name:** [Full Legal Name]
**SSN:** [XXX-XX-XXXX]
**DOB:** [MM/DD/YYYY]
**Current Address:** [Address]
**Previous Addresses:** [List]

---------------------------------------------------------------------------

**Non-compliance = CFPB, FTC, State AG complaints + FCRA legal action.**

Sincerely,
[Consumer Name]
Date: [Date]

**ENCLOSURES:** ID, SSN card, proof of address

===========================================================================
AFTER GENERATING ALL 9 FILES
===========================================================================

**FILES CREATED:**

| # | File Name | Bureau | Specialty |
|---|-----------|--------|-----------|
| 1 | Freeze_Innovis_[NAME]_[CASE].md | Innovis | 4th traditional |
| 2 | Freeze_ChexSystems_[NAME]_[CASE].md | ChexSystems | Banking |
| 3 | Freeze_ClarityServices_[NAME]_[CASE].md | Clarity | Payday loans |
| 4 | Freeze_LexisNexisConsumer_[NAME]_[CASE].md | LN Consumer | Employment |
| 5 | Freeze_CoreLogicTeletrack_[NAME]_[CASE].md | Teletrack | Subprime |
| 6 | Freeze_FactorTrust_[NAME]_[CASE].md | Factor Trust | Installment |
| 7 | Freeze_MicroBilt_[NAME]_[CASE].md | MicroBilt | Alternative |
| 8 | Freeze_LexisNexisRisk_[NAME]_[CASE].md | LN Risk | Fraud data |
| 9 | Freeze_DataX_[NAME]_[CASE].md | DataX | Subprime |

**Total Files Generated:** 9

**All saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINKS:**

[Provide computer:// links for all 9]

**NEXT STEPS:**
1. Download all 9 letters
2. Include enclosures with each
3. Mail ALL via certified mail
4. Wait 15-30 days for file disclosures
5. Once received â†’ Use Prompt 08 to dispute errors

===========================================================================
END OF PROMPT
===========================================================================
