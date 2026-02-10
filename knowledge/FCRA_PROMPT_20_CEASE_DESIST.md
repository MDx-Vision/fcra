# FCRA PROMPT 20: CEASE & DESIST LETTER (FDCPA §1692c)
## Stop Debt Collector Contact Legally

**Version:** 1.0
**Created:** February 8, 2026
**Output:** One file per collector
**Legal Basis:** Fair Debt Collection Practices Act §1692c(c)

---

## LEGAL AUTHORITY:

**FDCPA §1692c(c)** states:
> "If a consumer notifies a debt collector in writing that the consumer refuses to pay a debt or that the consumer wishes the debt collector to cease further communication with the consumer, the debt collector shall not communicate further with the consumer..."

**Exceptions (collector may still contact for):**
1. Advise consumer collection efforts are being terminated
2. Notify consumer of specific remedies (lawsuit, etc.)
3. Notify consumer they intend to invoke a specific remedy

---

## WHEN TO USE:

**Use Cease & Desist when:**
- Client is being harassed by repeated calls
- Collector is contacting at work after being told not to
- Client wants all contact to stop
- Collector is contacting third parties inappropriately
- Debt is time-barred (past statute of limitations)

**Do NOT use when:**
- Client intends to negotiate or pay
- Debt is recent and collector may sue
- Client needs to dispute the debt (use Validation instead)

**WARNING:** A C&D letter does NOT make the debt go away. Collector may still:
- Report to credit bureaus
- Sell the debt
- File a lawsuit

---

## CLIENT INFO:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- Phone: [Phone]
- SSN Last 4: [XXXX]

COLLECTOR INFO:
- Collector Name: [Name]
- Collector Address: [Address]
- Account Number: [Number]
- Original Creditor: [Name] (if known)
- Alleged Amount: [Amount]

HARASSMENT DETAILS (if applicable):
- Calls per day/week: [Number]
- Calling at work: [Yes/No]
- Calling family/friends: [Yes/No]
- Threats made: [Describe]
- Dates of contact: [List recent dates]
```

---

## =======================================================================
## PROMPT STARTS HERE
## =======================================================================

===========================================================================
CEASE & DESIST LETTER GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Review collector info and harassment details
2. Generate a legally-compliant cease & desist letter
3. **SAVE EACH AS SEPARATE FILE**

**FILE NAMING:**

```
CeaseDesist_[COLLECTOR_NAME]_[LASTNAME]_[DATE].md
```

Example: `CeaseDesist_PortfolioRecovery_SMITH_20260208.md`

**Use create_file tool for each letter.**

===========================================================================
LETTER TEMPLATE
===========================================================================

[Consumer Name]
[Address]
[City, State ZIP]

[Date]

**SENT VIA CERTIFIED MAIL - RETURN RECEIPT REQUESTED**

[COLLECTOR NAME]
[Collector Address]
[City, State ZIP]

═══════════════════════════════════════════════════════════════════════════
**RE: CEASE AND DESIST DEMAND — FDCPA §1692c(c)**
**Account Reference: [Account Number]**
**Original Creditor: [Original Creditor]**
**Alleged Amount: [Amount]**
═══════════════════════════════════════════════════════════════════════════

Dear Sir or Madam:

**THIS IS A FORMAL DEMAND TO CEASE ALL COMMUNICATION PURSUANT TO THE FAIR DEBT COLLECTION PRACTICES ACT, 15 U.S.C. § 1692c(c).**

---------------------------------------------------------------------------
SECTION 1: CEASE AND DESIST DEMAND
---------------------------------------------------------------------------

I am invoking my rights under the Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. § 1692c(c), which states:

> "If a consumer notifies a debt collector in writing that the consumer refuses to pay a debt or that the consumer wishes the debt collector to cease further communication with the consumer, the debt collector shall not communicate further with the consumer with respect to such debt..."

**EFFECTIVE IMMEDIATELY, YOU MUST:**

1. **CEASE all telephone calls** to my home, cell phone, and place of employment
2. **CEASE all written correspondence** except as permitted by law
3. **CEASE all contact with third parties** including family, friends, neighbors, and coworkers
4. **CEASE all electronic communications** including emails, text messages, and voicemails

---------------------------------------------------------------------------
SECTION 2: PERMITTED COMMUNICATIONS
---------------------------------------------------------------------------

I acknowledge you may contact me ONLY to:

1. Advise that your collection efforts are being terminated
2. Notify me that you may invoke a specific remedy (such as filing a lawsuit)
3. Notify me that you are invoking a specific remedy

**Any communication beyond these three exceptions is a violation of federal law.**

---------------------------------------------------------------------------
SECTION 3: VIOLATIONS TO DATE (If applicable)
---------------------------------------------------------------------------

[IF HARASSMENT OCCURRED, INCLUDE THIS SECTION:]

Your collection practices have already violated the FDCPA:

- **§1692c(a)(1):** Calling at unusual/inconvenient times
- **§1692c(a)(3):** Calling my place of employment after being told not to
- **§1692c(b):** Contacting third parties about this debt
- **§1692d:** Harassment through repeated phone calls ([X] calls per [day/week])
- **§1692e:** False or misleading representations
- **§1692f:** Unfair practices

**I am documenting all violations and reserve my right to pursue statutory damages of up to $1,000 per violation, plus actual damages and attorney's fees under §1692k.**

[IF NO HARASSMENT, REMOVE THIS SECTION]

---------------------------------------------------------------------------
SECTION 4: CREDIT REPORTING NOTICE
---------------------------------------------------------------------------

If you report this account to any credit reporting agency, you must report it as **DISPUTED**.

Failure to report the disputed status is a violation of:
- FDCPA §1692e(8) - False credit reporting
- FCRA §623(a)(3) - Furnisher duties regarding disputed information

---------------------------------------------------------------------------
SECTION 5: LEGAL NOTICE
---------------------------------------------------------------------------

**IMPORTANT:** This cease and desist letter does not constitute:
- An acknowledgment of the validity of this debt
- A promise to pay this debt
- A waiver of any statute of limitations defense

I reserve all legal rights and defenses.

---------------------------------------------------------------------------

**GOVERN YOURSELF ACCORDINGLY.**

This letter is being sent via certified mail to create a legal record. Any further communication in violation of this demand will be used as evidence of willful non-compliance.

Sincerely,

______________________________
[Consumer Name]

**Certified Mail Tracking #:** ______________________

═══════════════════════════════════════════════════════════════════════════
**KEEP COPY OF THIS LETTER AND CERTIFIED MAIL RECEIPT FOR YOUR RECORDS**
═══════════════════════════════════════════════════════════════════════════

---

===========================================================================
CUSTOMIZATION NOTES
===========================================================================

**For Time-Barred Debt (Past SOL):**
Add this paragraph:

> "Furthermore, the statute of limitations on this alleged debt has expired under [State] law. Any attempt to collect this time-barred debt through threats of legal action would constitute a violation of FDCPA §1692e(2)(A) - false representation of the legal status of a debt."

**State Statute of Limitations (common):**
| State | Written | Oral |
|-------|---------|------|
| California | 4 years | 2 years |
| Florida | 5 years | 4 years |
| New York | 6 years | 6 years |
| Texas | 4 years | 4 years |
| New Jersey | 6 years | 6 years |

**For Workplace Harassment:**
Add this paragraph:

> "I have informed you on [Date(s)] that I cannot receive calls at my place of employment. Your continued calls to [Employer Name] at [Phone] constitute a violation of FDCPA §1692c(a)(3). Each subsequent call is a separate violation."

**For Third-Party Contact:**
Add this paragraph:

> "You have contacted [Name/Relationship] regarding this debt on [Date(s)]. FDCPA §1692c(b) prohibits debt collectors from communicating with third parties except in limited circumstances. You have violated this provision."

===========================================================================
TRACKING REQUIREMENTS
===========================================================================

**Client should track:**
1. Date letter sent (from certified mail receipt)
2. Certified mail tracking number
3. Date of delivery confirmation
4. Any contact after C&D (document EVERY instance)

**If collector violates C&D:**
- Document date, time, nature of contact
- Save voicemails, letters, texts
- Each violation = potential $1,000 statutory damages
- Consider attorney referral for FDCPA lawsuit

===========================================================================
OUTPUT FORMAT
===========================================================================

Generate the letter in clean, formatted text suitable for:
1. Printing and mailing via certified mail
2. Clear sections for easy reading

Include the file name at the top:
```
FILE: CeaseDesist_[COLLECTOR]_[LASTNAME]_[DATE].md
```

===========================================================================
END OF PROMPT
===========================================================================
