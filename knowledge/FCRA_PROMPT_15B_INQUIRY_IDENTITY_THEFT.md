# FCRA PROMPT 15B: IDENTITY THEFT INQUIRY DISPUTES (§ 605B BLOCK)
## Full Identity Theft Package for Fraudulent Inquiries

**Version:** 1.0
**Created:** January 13, 2026
**Use Case:** REAL identity theft victims with fraudulent hard inquiries
**Output:** Professional DOCX letters with full legal framework
**Requirements:** FTC Report + Police Report + Identity Theft Affidavit

---

## ⚠️ WHEN TO USE THIS PROMPT

**USE 15B (This Prompt) When:**
- Consumer is a VICTIM of identity theft
- Someone STOLE their identity and applied for credit
- Data breach led to fraudulent applications
- Family member/roommate committed identity theft
- Consumer has or will file FTC report and police report

**USE 15A (Permissible Purpose) When:**
- Consumer just didn't authorize the pull (not identity theft)
- Car dealer ran credit without asking
- Company pulled without permission
- No crime occurred - just unauthorized access

---

## 📋 LEGAL FRAMEWORK

### Primary Statute: 15 U.S.C. § 1681c-2 (FCRA § 605B) - Block of Information

**(a) BLOCK.** Except as otherwise provided... a consumer reporting agency shall block the reporting of any information in the file of a consumer that the consumer identifies as information that resulted from an alleged identity theft, not later than **4 BUSINESS DAYS** after the date of receipt...

**REQUIREMENTS FOR BLOCK:**
1. Appropriate proof of identity
2. Copy of identity theft report
3. Identification of the fraudulent information
4. Statement that information does not relate to any transaction by consumer

### Supporting Statutes:
- § 1681b - Permissible purposes (creditor had no permissible purpose for fraud application)
- § 1681n - Willful noncompliance (statutory + punitive damages)
- § 1681o - Negligent noncompliance (actual damages)
- § 1681s-2 - Furnisher duties upon notice of identity theft

### Key Case Law:
- **Sloane v. Equifax Info. Servs., LLC, 510 F.3d 495 (4th Cir. 2007)** - CRA duty to block identity theft information
- **Yang v. Government Employees Ins. Co., 146 F.3d 1320 (11th Cir. 1998)** - Identity theft creates no permissible purpose
- **Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)** - Permissible purpose strictly construed
- **Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)** - Willfulness standard
- **Dennis v. BEH-1, LLC, 520 F.3d 1066 (9th Cir. 2008)** - Notice requirements strictly enforced

---

## 📝 CLIENT INFO TEMPLATE

```
CONSUMER INFORMATION:
- Full Legal Name: [Name]
- Current Address: [Address]
- City, State ZIP: [City, State ZIP]
- SSN Last 4: [XXXX]
- Date of Birth: [MM/DD/YYYY]
- Phone: [Phone]
- Email: [Email]

IDENTITY THEFT DOCUMENTATION:
- FTC Report Number: [Number or "To Be Filed"]
- FTC Report Date: [Date]
- Police Report Number: [Number or "To Be Filed"]
- Police Report Date: [Date]
- Police Department: [Name]

FRAUDULENT INQUIRIES:

Inquiry 1:
- Company Name: [e.g., Capital One]
- Date of Inquiry: [MM/DD/YYYY]
- Bureau(s): [TU / EX / EQ]
- Consumer Statement: "I did NOT apply. This was identity theft."

Inquiry 2:
- Company Name: [e.g., Synchrony Bank]
- Date of Inquiry: [MM/DD/YYYY]
- Bureau(s): [TU / EX / EQ]
- Consumer Statement: "I did NOT apply. This was identity theft."

[Add more as needed]

ADDITIONAL INFORMATION:
- How did identity theft occur? [Data breach / stolen wallet / family member / unknown]
- When did consumer discover the theft? [Date]
- Were any fraudulent ACCOUNTS opened? [Yes - use Prompt 14 / No]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

You are an FCRA litigation specialist. Generate professional DOCX dispute letters for IDENTITY THEFT fraudulent inquiries using 15 U.S.C. § 1681c-2 (§ 605B Block Request).

**TASK:** Generate the following documents as SEPARATE DOCX FILES:

1. **§ 605B Block Request to EACH BUREAU** with fraudulent inquiries
2. **Identity Theft Notice to EACH CREDITOR** that pulled fraudulently
3. **FTC Report Answer Guide** (what to enter on IdentityTheft.gov)
4. **Mailing Checklist** with all enclosures

Use the docx library (Node.js) with professional formatting matching Brightpath Ascend Group standards.

---

## BUREAU LETTER TEMPLATE (§ 605B Identity Theft Block)

```javascript
// STRUCTURE FOR BUREAU LETTERS

HEADER:
- Consumer name, address, contact info
- Date
- "VIA: CERTIFIED MAIL, RETURN RECEIPT REQUESTED"

TO:
- Bureau name and address (use Fraud Victim Assistance addresses)

RE LINE:
═══════════════════════════════════════════════════════════════════════════
RE: IDENTITY THEFT - § 605B BLOCK REQUEST
DEMAND TO BLOCK FRAUDULENT INQUIRIES WITHIN 4 BUSINESS DAYS
15 U.S.C. § 1681c-2
═══════════════════════════════════════════════════════════════════════════

SECTION 1: NOTICE OF IDENTITY THEFT

I am a VICTIM OF IDENTITY THEFT. Pursuant to the Fair Credit Reporting
Act, 15 U.S.C. § 1681c-2 (FCRA § 605B), I am formally requesting that
you BLOCK the following fraudulent inquiries from my consumer file.

These inquiries are the result of criminal identity theft. I did NOT
apply for credit with these companies. Someone fraudulently used my
personal information to submit credit applications.

I CERTIFY UNDER PENALTY OF PERJURY:
- I am a victim of identity theft
- These inquiries resulted from fraudulent applications
- I did NOT authorize these credit pulls
- The information does not relate to any transaction by me

SECTION 2: § 605B REQUIREMENTS - ALL SATISFIED

Under 15 U.S.C. § 1681c-2(a), you must block information upon receipt of:

| Requirement | Status |
|-------------|--------|
| (1) Appropriate proof of identity | ✓ ENCLOSED |
| (2) Copy of identity theft report | ✓ ENCLOSED (FTC Report #[NUMBER]) |
| (3) Identification of fraudulent information | ✓ PROVIDED BELOW |
| (4) Statement that info does not relate to my transaction | ✓ CONFIRMED |

ALL REQUIREMENTS ARE SATISFIED. YOU MUST BLOCK WITHIN 4 BUSINESS DAYS.

SECTION 3: FRAUDULENT INQUIRIES TO BE BLOCKED

[TABLE FOR EACH INQUIRY]
| Field | Information |
|-------|-------------|
| Company Name | [COMPANY] |
| Date of Inquiry | [DATE] |
| This was identity theft | ✓ CONFIRMED |
| I did NOT apply | ✓ CONFIRMED |
| I did NOT authorize this pull | ✓ CONFIRMED |

SECTION 4: YOUR LEGAL OBLIGATIONS

Under 15 U.S.C. § 1681c-2(a):

"...a consumer reporting agency shall block the reporting of any
information in the file of a consumer that the consumer identifies
as information that resulted from an alleged identity theft, NOT
LATER THAN 4 BUSINESS DAYS after the date of receipt of—"

This letter satisfies ALL statutory requirements. You have 4 BUSINESS
DAYS from receipt to block these fraudulent inquiries.

SECTION 5: PROHIBITION ON RESALE AND REINSERTION

Under § 1681c-2(b): You are PROHIBITED from reselling blocked information.

Under § 1681c-2(c): You may NOT decline to block or rescind a block
UNLESS you reasonably determine that:
- The information was blocked in error
- The identity theft report was filed fraudulently

You have NO BASIS to decline this block request. I am a legitimate
identity theft victim with proper documentation.

SECTION 6: NOTIFICATION TO FURNISHER

Under § 1681c-2(d), you are REQUIRED to notify [COMPANY] that:
- You have blocked this information
- The information may be the result of identity theft
- This information may not be furnished again

SECTION 7: PRESERVATION OF RECORDS - LITIGATION HOLD

[BUREAU] is hereby directed to PRESERVE all records:
- All communications with [COMPANY] regarding this inquiry
- All records of this block request and your response
- All audit logs showing when inquiry was added and blocked
- All records of notification to furnisher per § 1681c-2(d)
- All records of any attempt to resell or reinstate blocked information

Failure to preserve = SPOLIATION OF EVIDENCE.

SECTION 8: DAMAGES EXPOSURE

Failure to block within 4 business days = FCRA violation:

| Violation | Statutory Basis | Damages Range |
|-----------|-----------------|---------------|
| Failure to block (per inquiry) | § 1681c-2 + § 1681n | $100-$1,000 |
| Multiple inquiries (x[NUMBER]) | § 1681n | $[CALC]-$[CALC] |
| Continued reporting of ID theft | § 1681n | $1,000-$5,000 |
| Willful noncompliance | § 1681n(a)(2) | Punitive 2-4x |
| Attorney fees | § 1681n(a)(3) | $15,000+ |
| Emotional distress (ID theft) | Actual damages | $5,000-$25,000 |
| TOTAL EXPOSURE | | $[RANGE] |

SECTION 9: FORMAL DEMAND

I DEMAND [BUREAU] take the following actions within 4 BUSINESS DAYS:

1. BLOCK all fraudulent inquiries listed above
2. NOTIFY the creditors per § 1681c-2(d)
3. ENSURE blocked information is not resold per § 1681c-2(b)
4. PROVIDE written confirmation of the block
5. PROVIDE updated consumer disclosure showing block

SECTION 10: CONSEQUENCES OF NON-COMPLIANCE

If you fail to block within 4 BUSINESS DAYS:

1. Regulatory Complaints:
   - Consumer Financial Protection Bureau (CFPB)
   - Federal Trade Commission (FTC)
   - [STATE] Attorney General
   - Identity theft creates heightened regulatory scrutiny

2. Federal Litigation:
   - Statutory damages under § 1681n
   - Actual damages for continued identity theft harm
   - Punitive damages (failure to block ID theft is egregious)
   - Attorney fees per § 1681n(a)(3)
   - Emotional distress damages

Identity theft victims receive ENHANCED PROTECTION under FCRA.
Courts view failure to block identity theft information harshly.

LEGAL CITATIONS:
- 15 U.S.C. § 1681c-2 - Block of information resulting from identity theft
- 15 U.S.C. § 1681c-2(a) - Block requirements and 4-day deadline
- 15 U.S.C. § 1681c-2(b) - Prohibition on resale
- 15 U.S.C. § 1681c-2(d) - Notification to furnisher
- 15 U.S.C. § 1681n - Civil liability for willful noncompliance
- 15 U.S.C. § 1681o - Civil liability for negligent noncompliance
- Sloane v. Equifax Info. Servs., LLC, 510 F.3d 495 (4th Cir. 2007)
- Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)

SIGNATURE BLOCK

ENCLOSURES:
☐ FTC Identity Theft Report (Report #[NUMBER])
☐ Police Report (Case #[NUMBER])
☐ Government-Issued Photo ID (copy)
☐ Social Security Card (copy)
☐ Proof of Current Address (copy)
☐ Credit Report with fraudulent inquiries circled
```

---

## CREDITOR LETTER TEMPLATE (Identity Theft Notice)

```javascript
// STRUCTURE FOR CREDITOR LETTERS

HEADER:
- Consumer name, address, contact info
- Date
- "VIA: CERTIFIED MAIL, RETURN RECEIPT REQUESTED"

TO:
- Creditor name and address (fraud department if known)

RE LINE:
═══════════════════════════════════════════════════════════════════════════
RE: IDENTITY THEFT NOTICE - FRAUDULENT CREDIT APPLICATION
DEMAND TO WITHDRAW INQUIRY AND PRESERVE FRAUD RECORDS
Inquiry Date: [DATE]
═══════════════════════════════════════════════════════════════════════════

SECTION 1: NOTICE OF IDENTITY THEFT

I am a VICTIM OF IDENTITY THEFT. This letter serves as formal notice
that the credit application submitted to your company on or about
[DATE] was FRAUDULENT. I did NOT submit this application.

A criminal fraudulently used my personal information to apply for
credit with your company. The resulting inquiry on my credit report
is the product of this criminal activity.

I CERTIFY UNDER PENALTY OF PERJURY:
- I am a victim of identity theft
- I did NOT apply for credit with [COMPANY]
- I did NOT authorize [COMPANY] to access my credit
- The application that caused this inquiry was fraudulent

SECTION 2: DOCUMENTATION ENCLOSED

| Document | Status |
|----------|--------|
| FTC Identity Theft Report | ✓ ENCLOSED (Report #[NUMBER]) |
| Police Report | ✓ ENCLOSED (Case #[NUMBER]) |
| Government-Issued ID | ✓ ENCLOSED |

SECTION 3: YOUR DUTIES UNDER FCRA

Under 15 U.S.C. § 1681s-2(a)(6), when you receive notice that
information may be fraudulent due to identity theft, you have
specific duties including:

- Cease reporting information you know is fraudulent
- Cooperate with consumer in resolving identity theft
- Maintain records related to fraudulent application

Under 15 U.S.C. § 1681b, you had NO PERMISSIBLE PURPOSE to access
my credit report. The application was fraudulent - there was no
legitimate transaction initiated by me.

SECTION 4: DEMANDS

I DEMAND that [COMPANY]:

1. IMMEDIATELY notify Experian, Equifax, and TransUnion to DELETE
   this inquiry from my credit file

2. CONFIRM in writing that you have requested deletion from all bureaus

3. FLAG my personal information to prevent future fraudulent applications

4. PRESERVE all records related to the fraudulent application:
   - The application itself
   - IP address / device information (if online)
   - Any documents submitted
   - All communications

   These records may be needed for law enforcement investigation.

5. PROVIDE me with copies of any application or documents submitted
   in my name (I am entitled to this under FCRA § 609(e))

SECTION 5: FCRA § 609(e) - IDENTITY THEFT VICTIM RIGHTS

Under 15 U.S.C. § 1681g(e), as an identity theft victim with a valid
police report, I am entitled to receive:

"...a copy of all transaction records related to the alleged identity
theft, including any application and business transaction records in
the control of the business entity..."

You have 30 DAYS to provide these records.

SECTION 6: PRESERVATION OF EVIDENCE

[COMPANY] is hereby directed to PRESERVE all records:
- The fraudulent application
- All supporting documents
- IP address, device ID, browser information
- Any biometric or identity verification records
- All communications related to this application
- Records showing who processed this application

These records are essential for potential criminal prosecution
and civil litigation.

SECTION 7: DAMAGES EXPOSURE

| Violation | Statutory Basis | Damages Range |
|-----------|-----------------|---------------|
| No permissible purpose | § 1681b + § 1681n | $100-$1,000 |
| Continued reporting of fraud | § 1681s-2 | $1,000-$5,000 |
| Failure to provide records | § 1681g(e) | $1,000+ |
| Willful noncompliance | § 1681n(a)(2) | Punitive |
| Attorney fees | § 1681n(a)(3) | $15,000+ |

SECTION 8: RESPONSE DEADLINE

You have 15 DAYS to:
1. Confirm deletion requests sent to all bureaus
2. Confirm fraud flag placed on my information

You have 30 DAYS to:
3. Provide copies of fraudulent application per § 609(e)

SECTION 9: CONSEQUENCES OF NON-COMPLIANCE

Failure to cooperate will result in:
- Complaints to CFPB, FTC, and [STATE] Attorney General
- Federal litigation for FCRA violations
- Referral to law enforcement for their failure to assist victim

LEGAL CITATIONS:
- 15 U.S.C. § 1681b - Permissible purposes (none existed)
- 15 U.S.C. § 1681g(e) - Identity theft victim document rights
- 15 U.S.C. § 1681s-2(a)(6) - Furnisher duties for ID theft
- 15 U.S.C. § 1681n - Willful noncompliance
- Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)

SIGNATURE BLOCK

ENCLOSURES:
☐ FTC Identity Theft Report
☐ Police Report
☐ Government-Issued Photo ID
```

---

## FTC REPORT ANSWER GUIDE

```markdown
# FTC IDENTITY THEFT REPORT - ANSWER GUIDE
## IdentityTheft.gov Step-by-Step

**Website:** https://www.identitytheft.gov

---

## QUESTIONS AND ANSWERS

**"Which statement describes your situation?"**
> Select: "I want to report identity theft"

**"What did the identity thief do?"**
> Select: "Opened new accounts or attempted to open new accounts"
> (Even if no account opened, the APPLICATION created an inquiry)

**"What type of accounts?"**
> Select all that apply based on creditor types:
> - Credit card
> - Bank account
> - Loan
> - Other

**"List the companies involved:"**
> [COMPANY 1] - inquiry date [DATE]
> [COMPANY 2] - inquiry date [DATE]
> [COMPANY 3] - inquiry date [DATE]

**"When did you notice the identity theft?"**
> "[Month] [Year]" - when consumer first saw inquiries

**"Describe what happened (in your own words):"**
> "Someone used my personal information without my permission to
> apply for credit with multiple companies. This resulted in
> unauthorized hard inquiries appearing on my credit report. I did
> not apply for credit with these companies. I did not authorize
> anyone to apply on my behalf. These applications were fraudulent."

**"What would be a fair resolution?"**
> "Remove all fraudulent inquiries from my credit report and flag
> my information to prevent future fraudulent applications."

**"Your Information"**
> Complete with consumer's accurate personal information

**"Have you contacted your local police department?"**
> "Yes" if already filed, "No, not yet" if not

---

## RECORD YOUR FTC REPORT NUMBER

**FTC Report #:** _______________________

**Date Filed:** _______________________

**IMPORTANT:** Print the FTC report - you need copies for ALL letters!
```

---

## MAILING CHECKLIST

```markdown
# MAILING CHECKLIST - IDENTITY THEFT INQUIRY DISPUTES

**Client:** [Name]
**Date:** [Date]

---

## BUREAU ENVELOPES

### TRANSUNION
**Mail to:**
TransUnion Fraud Victim Assistance
P.O. Box 2000
Chester, PA 19016

**Contents:**
☐ § 605B Block Request Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Driver's License (copy)
☐ Social Security Card (copy)
☐ Proof of Address (copy)
☐ Credit Report page with inquiries circled

**Tracking #:** _______________
**Date Mailed:** _______________

---

### EXPERIAN
**Mail to:**
Experian
P.O. Box 9554
Allen, TX 75013

**Contents:**
☐ § 605B Block Request Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Driver's License (copy)
☐ Social Security Card (copy)
☐ Proof of Address (copy)
☐ Credit Report page with inquiries circled

**Tracking #:** _______________
**Date Mailed:** _______________

---

### EQUIFAX
**Mail to:**
Equifax Information Services, LLC
P.O. Box 740256
Atlanta, GA 30374-0256

**Contents:**
☐ § 605B Block Request Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Driver's License (copy)
☐ Social Security Card (copy)
☐ Proof of Address (copy)
☐ Credit Report page with inquiries circled

**Tracking #:** _______________
**Date Mailed:** _______________

---

## CREDITOR ENVELOPES

### [CREDITOR 1]
**Mail to:** [Address]

**Contents:**
☐ Identity Theft Notice Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Driver's License (copy)

**Tracking #:** _______________
**Date Mailed:** _______________

### [CREDITOR 2]
**Mail to:** [Address]

**Contents:**
☐ Identity Theft Notice Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Driver's License (copy)

**Tracking #:** _______________
**Date Mailed:** _______________

[Repeat for each creditor]

---

## TIMELINE

| Milestone | Date | Status |
|-----------|------|--------|
| Letters mailed | [DATE] | ☐ |
| Delivery confirmed | [+3-5 days] | ☐ |
| Bureau 4-day deadline | [+7 days] | ☐ |
| Creditor 15-day deadline | [+18 days] | ☐ |
| § 609(e) 30-day deadline | [+33 days] | ☐ |
| Pull fresh reports | [+35 days] | ☐ |

---

## IF NOT RESOLVED

Escalate to:
1. CFPB complaint (consumerfinance.gov/complaint)
2. FTC complaint update
3. State Attorney General
4. Consider litigation - identity theft cases get sympathy from juries
```

---

## GENERATE THE LETTERS

Using the client information provided:

1. Create DOCX § 605B letter for each bureau with fraudulent inquiries
2. Create DOCX Identity Theft Notice for each creditor
3. Create FTC Answer Guide (markdown)
4. Create Mailing Checklist (markdown)
5. Use professional formatting (Arial, tables, separators)
6. Include all legal citations and case law
7. Calculate damages exposure
8. Save each as separate file to /mnt/user-data/outputs/

**FILE NAMING:**
```
Inquiry605B_[BUREAU]_[LASTNAME]_[DATE].docx
Inquiry605B_Creditor_[COMPANY]_[LASTNAME]_[DATE].docx
Inquiry605B_FTC_Guide_[LASTNAME]_[DATE].md
Inquiry605B_Mailing_Checklist_[LASTNAME]_[DATE].md
```

---

## KEY DIFFERENCES FROM PROMPT 15A

| Feature | 15A (Permissible Purpose) | 15B (Identity Theft) |
|---------|---------------------------|----------------------|
| Legal Basis | § 1681b | § 1681c-2 (605B) |
| Deadline for Bureau | 30 days | **4 BUSINESS DAYS** |
| FTC Report Required | NO | **YES** |
| Police Report Required | NO | **YES** |
| Furnisher Notification | Optional | **MANDATORY** (§ 1681c-2(d)) |
| § 609(e) Document Request | No | **YES** |
| Emotional Distress Damages | Unlikely | **LIKELY** |
| Jury Sympathy | Moderate | **HIGH** |

---

## END OF PROMPT 15B
