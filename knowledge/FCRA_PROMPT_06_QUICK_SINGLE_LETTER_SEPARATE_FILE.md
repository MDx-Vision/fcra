# FCRA PROMPT 06: QUICK SINGLE LETTER (SEPARATE FILE)
## Generate One Letter Fast â€” Separate File Output

**Version:** 2.0 (Separate File Output)
**Created:** November 24, 2025
**Output:** One letter saved as separate downloadable file

---

## ðŸ“‹ HOW TO USE:

**STEP 1:** Paste account details (no report upload needed)

**STEP 2:** Claude generates letter as separate file

**STEP 3:** Download file

---

## ðŸ“ INPUT TEMPLATE:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- SSN Last 4: [XXXX]

LETTER TYPE: [Round 1 / MOV / Pre-Arb]

RECIPIENT: [CRA or Furnisher Name]
RECIPIENT ADDRESS: [Address]

ACCOUNT INFO:
- Account Number: [Number]
- Creditor: [Name]

VIOLATION DESCRIPTION (Plain English):
[Describe what's wrong]

LATE PAYMENTS ON THIS ACCOUNT:
[List dates or "None"]

OPTIONAL RLPP BUNDLING:
[List late payments from OTHER accounts or "None"]

CASE INFO:
- Case Number: [Number]
- Today's Date: [Date]
```

---

## =======================================================================
## PROMPT STARTS HERE â¬‡ï¸
## =======================================================================

===========================================================================
QUICK SINGLE LETTER GENERATOR (SEPARATE FILE)
===========================================================================

**YOUR TASK:**

1. Generate ONE letter based on input
2. **SAVE AS SEPARATE FILE**

**FILE NAMING:**

```
Quick_[ROUND]_[RECIPIENT]_[LASTNAME]_[CASENUM].md
```

Examples:
- `Quick_Round1_Experian_SMITH_12345.md`
- `Quick_MOV_CapitalOne_JONES_67890.md`
- `Quick_PreArb_TransUnion_BROWN_11111.md`

**Use create_file tool.**

===========================================================================
LETTER TEMPLATE
===========================================================================

[Generate appropriate letter based on type selected:
- Round 1: Standard RLPP dispute
- MOV: Method of Verification demand
- Pre-Arb: Pre-arbitration demand]

[Use templates from Prompts 02, 03, or 05 as appropriate]

===========================================================================
FILE GENERATED
===========================================================================

**FILE CREATED:**

Quick_[TYPE]_[RECIPIENT]_[NAME]_[CASE].md

**Saved to:** /mnt/user-data/outputs/

**DOWNLOAD LINK:**

[Provide computer:// link]

**NEXT STEPS:**
1. Download letter
2. Print on letterhead
3. Include enclosures
4. Mail via certified mail

===========================================================================
END OF PROMPT
===========================================================================
