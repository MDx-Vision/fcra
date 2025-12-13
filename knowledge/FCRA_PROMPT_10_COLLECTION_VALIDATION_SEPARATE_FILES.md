# FCRA PROMPT 10: COLLECTION VALIDATION (SEPARATE FILES)
## Upload â†’ Analyze â†’ Generate Separate File Per Collector

**Version:** 2.0 (Separate File Output)  
**Created:** November 24, 2025  
**Output:** One file per debt collector  

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Upload credit report

**STEP 2:** Paste client info

**STEP 3:** Claude analyzes, identifies collectors, generates separate files

**STEP 4:** Download individual files

---

## ðŸ“ CLIENT INFO:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- SSN Last 4: [XXXX]
- DOB: [MM/DD/YYYY]
- State: [State]

CASE INFO:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
COLLECTION VALIDATION GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Analyze report, identify all collection accounts
2. Generate one validation letter per collector
3. **SAVE EACH AS SEPARATE FILE**

**FILE NAMING:**

```
Validation_[COLLECTOR_NAME]_[LASTNAME]_[CASENUM].md
```

Example: `Validation_PortfolioRecovery_SMITH_12345.md`

**Use create_file tool for each letter.**

===========================================================================
LETTER TEMPLATE (Per Collector)
===========================================================================

[Consumer Name]
[Address]

[Date]

[COLLECTOR NAME]
[COLLECTOR ADDRESS]

**SENT VIA CERTIFIED MAIL**

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
**RE: FORMAL DEBT VALIDATION DEMAND â€” FDCPA Â§ 1692g**
**CEASE COLLECTION AND REPORTING UNTIL VALIDATED**
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

**Consumer:** [Name]
**SSN (Last 4):** XXX-XX-[XXXX]
**Case Reference:** [Case Number]

**Account(s) Referenced:**
[List all accounts this collector has]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Dear Sir or Madam:

Pursuant to FDCPA Â§ 1692g, I DEMAND VALIDATION of alleged debt(s).

**This is NOT a refusal to pay. This is a demand for PROOF.**

---------------------------------------------------------------------------
SECTION 1: VALIDATION DEMAND
---------------------------------------------------------------------------

I DEMAND within 30 DAYS:

â˜ Original signed contract bearing MY SIGNATURE
â˜ Complete chain of custody documentation
â˜ Full accounting of all charges
â˜ Complete payment history
â˜ Proof of statute of limitations compliance
â˜ License to collect in [State]
â˜ Original creditor name and address

---------------------------------------------------------------------------
SECTION 2: CEASE REPORTING â€” FCRA Â§ 1681s-2
---------------------------------------------------------------------------

UNTIL YOU PROVIDE VALIDATION:

1. CEASE reporting to credit bureaus
2. REMOVE existing tradelines
3. DO NOT resume reporting unless validated

**Reporting unvalidated debt violates FCRA Â§ 1681s-2(a)(1)(A).**

---------------------------------------------------------------------------
SECTION 3: CEASE CONTACT â€” FDCPA Â§ 1692c
---------------------------------------------------------------------------

CEASE ALL:
- Telephone contact
- Written contact (except validation or legal notice)

**Further contact without validation = harassment under Â§ 1692d.**

---------------------------------------------------------------------------
SECTION 4: CONSEQUENCES
---------------------------------------------------------------------------

Non-compliance results in:

- CFPB complaint
- FTC complaint  
- State AG complaint
- FDCPA/FCRA legal action
- Statutory damages: $1,000 per violation
- Attorney fees: Mandatory

---------------------------------------------------------------------------

Direct correspondence to:

[Firm Name]
[Firm Address]

Case Reference: [Case Number]

Sincerely,

_______________________________________
[Consumer Name]

Date: [Date]

**CC:** Experian, TransUnion, Equifax

===========================================================================
AFTER GENERATING ALL FILES
===========================================================================

**FILES CREATED:**

| # | File Name | Collector | Accounts |
|---|-----------|-----------|----------|
| 1 | Validation_[COLL1]_[NAME]_[CASE].md | [Collector 1] | [X] |
| 2 | Validation_[COLL2]_[NAME]_[CASE].md | [Collector 2] | [X] |

**Total Files:** [X]

**All saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINKS:**

[Provide computer:// links]

**SUMMARY TABLE:**

| # | Collector | Account # | Original Creditor | Balance |
|---|-----------|-----------|-------------------|---------|
| 1 | [Name] | [#] | [OC] | $[X] |
| 2 | [Name] | [#] | [OC] | $[X] |

**Total Collections Disputed:** [X]
**Total Balance Disputed:** $[X,XXX]

**NEXT STEPS:**
1. Download all letters
2. Mail via certified mail
3. CC to all 3 credit bureaus
4. Set 30-day follow-up

===========================================================================
END OF PROMPT
===========================================================================
