# FCRA PROMPT 15A: REGULAR INQUIRY DISPUTES (§ 604 PERMISSIBLE PURPOSE)
## Unauthorized Hard Inquiries - No Identity Theft Required

**Version:** 1.0  
**Created:** January 13, 2026  
**Use Case:** Consumer did NOT authorize the credit pull (but NOT identity theft)  
**Output:** Professional DOCX letters with full legal framework  
**Requirements:** Just the dispute letter - NO FTC/Police report needed

---

## ⚠️ WHEN TO USE THIS PROMPT

**USE 15A (This Prompt) When:**
- Consumer says "I never applied with them"
- Car dealer ran credit without permission
- Company did hard pull instead of soft pull
- Creditor pulled on closed/paid account
- Pre-approval turned into hard inquiry
- Consumer doesn't know who the company is

**USE 15B (Identity Theft) When:**
- Consumer is a VICTIM of identity theft
- Someone STOLE their identity and applied
- Data breach led to fraudulent applications
- Consumer needs FTC report + police report

---

## 📋 LEGAL FRAMEWORK

### Primary Statute: 15 U.S.C. § 1681b - Permissible Purposes

A consumer reporting agency may furnish a consumer report ONLY for:
- (a)(3)(A) Credit transaction initiated by consumer
- (a)(3)(F) Legitimate business need in transaction initiated by consumer

**KEY:** The consumer must INITIATE the transaction. No initiation = No permissible purpose.

### Supporting Statutes:
- § 1681n - Willful noncompliance (statutory + punitive damages)
- § 1681o - Negligent noncompliance (actual damages)
- § 1681i - Reinvestigation duties
- § 1681e(b) - Accuracy requirements

### Key Case Law:
- **Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)** - Permissible purpose requires transaction initiated by consumer
- **Spokeo, Inc. v. Robins, 578 U.S. 330 (2016)** - Concrete harm requirement for standing
- **Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)** - Willfulness standard
- **Pintos v. Pacific Creditors Ass'n, 605 F.3d 665 (9th Cir. 2010)** - Permissible purpose strictly construed

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

UNAUTHORIZED INQUIRIES:

Inquiry 1:
- Company Name: [e.g., XYZ Auto Dealer]
- Date of Inquiry: [MM/DD/YYYY]
- Bureau(s): [TU / EX / EQ]
- Consumer Statement: [e.g., "Went for test drive, never authorized credit check"]

Inquiry 2:
- Company Name: [e.g., Capital One]
- Date of Inquiry: [MM/DD/YYYY]
- Bureau(s): [TU / EX / EQ]
- Consumer Statement: [e.g., "Never applied, don't know this company"]

[Add more as needed]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

You are an FCRA litigation specialist. Generate professional DOCX dispute letters for unauthorized hard inquiries using 15 U.S.C. § 1681b (Permissible Purpose) violations.

**TASK:** Generate the following documents as SEPARATE DOCX FILES:

1. **Inquiry letter to EACH BUREAU** that shows unauthorized inquiries
2. **Demand letter to EACH CREDITOR** that pulled without authorization

Use the docx library (Node.js) with professional formatting matching Brightpath Ascend Group standards:
- Arial font, size 22
- Professional tables with gray headers
- Section separators (═══════)
- Comprehensive legal citations
- Damages exposure tables
- Litigation hold notices

---

## BUREAU LETTER TEMPLATE (§ 604 Permissible Purpose)

```javascript
// STRUCTURE FOR BUREAU LETTERS

HEADER:
- Consumer name, address, contact info
- Date
- "VIA: CERTIFIED MAIL, RETURN RECEIPT REQUESTED"

TO:
- Bureau name and address

RE LINE:
═══════════════════════════════════════════════════════════════════════════
RE: FORMAL FCRA DISPUTE - UNAUTHORIZED HARD INQUIRIES
15 U.S.C. § 1681b - PERMISSIBLE PURPOSE VIOLATIONS
FIRST DISPUTE - ESTABLISHING NOTICE FOR WILLFULNESS
═══════════════════════════════════════════════════════════════════════════

SECTION 1: NOTICE OF FORMAL DISPUTE
- This constitutes formal dispute under § 1681i
- Disputing unauthorized inquiries that lack permissible purpose
- "This is not a request. This is a LEGAL DEMAND backed by federal law."

SECTION 2: UNAUTHORIZED INQUIRIES TO BE REMOVED

[TABLE FOR EACH INQUIRY]
| Field | Information |
|-------|-------------|
| Company Name | [COMPANY] |
| Date of Inquiry | [DATE] |
| Did I apply for credit? | NO |
| Did I authorize this pull? | NO |
| Permissible Purpose? | NONE |

SECTION 3: LEGAL BASIS - § 1681b PERMISSIBLE PURPOSE

Under 15 U.S.C. § 1681b, a consumer reporting agency may only furnish 
a consumer report for specific permissible purposes:

§ 1681b(a)(3)(A): "To a person which it has reason to believe intends 
to use the information in connection with a credit transaction involving 
the consumer on whom the information is to be furnished and involving 
the extension of credit to, or review of an account of, the consumer."

KEY REQUIREMENT: The transaction must be INITIATED BY THE CONSUMER.

I did NOT initiate any transaction with [COMPANY]. I did NOT apply for 
credit. I did NOT authorize any credit inquiry. Therefore, [COMPANY] 
had NO PERMISSIBLE PURPOSE to access my consumer report.

Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002): "A permissible 
purpose must exist at the time the report is obtained... the consumer 
must be the one who initiates the transaction."

SECTION 4: YOUR DUTIES UNDER FCRA

Upon receipt of this dispute, you are REQUIRED to:

1. Conduct a REASONABLE REINVESTIGATION per § 1681i(a)(1)(A)
2. Contact [COMPANY] and DEMAND proof of permissible purpose
3. If [COMPANY] cannot provide proof of my application or authorization,
   DELETE the inquiry per § 1681i(a)(5)(A)
4. Provide results within 30 days per § 1681i(a)(1)(A)

A generic "verified" response is NOT ACCEPTABLE. Per Cushman v. Trans 
Union Corp., 115 F.3d 220 (3d Cir. 1997), you must conduct a GENUINE 
reinvestigation, not simply parrot what the furnisher claims.

SECTION 5: DEMAND FOR METHOD OF VERIFICATION (§ 1681i(a)(7))

If you "verify" this inquiry, I DEMAND you provide:
- The specific permissible purpose [COMPANY] claims
- Documentation of my alleged application or authorization
- Date and method of my alleged credit application
- Business name, address, phone of verification contact

SECTION 6: PRESERVATION OF RECORDS - LITIGATION HOLD

[BUREAU] is hereby directed to PRESERVE all records:
- All communications with [COMPANY] regarding this inquiry
- All records of permissible purpose verification
- All audit logs showing when/how this inquiry was added
- All reinvestigation records

Failure to preserve = SPOLIATION OF EVIDENCE.

SECTION 7: DAMAGES EXPOSURE

[TABLE]
| Violation | Statutory Basis | Damages Range |
|-----------|-----------------|---------------|
| Unauthorized inquiry reporting | § 1681e(b) | $100-$1,000 |
| Failure to remove after dispute | § 1681i | $100-$1,000 |
| Per inquiry (x [NUMBER]) | § 1681n | $[CALC]-$[CALC] |
| Willful noncompliance | § 1681n | Punitive 2-4x |
| Attorney fees | § 1681n(a)(3) | $15,000+ |
| TOTAL EXPOSURE | | $[RANGE] |

SECTION 8: FORMAL DEMAND

I DEMAND [BUREAU] take the following actions within 30 DAYS:

1. CONTACT [COMPANY] and demand proof of permissible purpose
2. If no proof provided, IMMEDIATELY DELETE the inquiry
3. PROVIDE written reinvestigation results per § 1681i(a)(6)
4. PROVIDE method of verification per § 1681i(a)(7)
5. PROVIDE updated consumer disclosure showing deletion

SECTION 9: CONSEQUENCES OF NON-COMPLIANCE

If you fail to remove these unauthorized inquiries within 30 DAYS:

1. File Regulatory Complaints:
   - Consumer Financial Protection Bureau (CFPB)
   - Federal Trade Commission (FTC)
   - [STATE] Attorney General

2. Initiate Federal Litigation:
   - Statutory damages under § 1681n
   - Actual damages for credit harm
   - Punitive damages (willfulness established by notice)
   - Attorney fees per § 1681n(a)(3)

LEGAL CITATIONS:
- 15 U.S.C. § 1681b - Permissible purposes of consumer reports
- 15 U.S.C. § 1681e(b) - Accuracy of reports
- 15 U.S.C. § 1681i - Procedure in case of disputed accuracy
- 15 U.S.C. § 1681n - Civil liability for willful noncompliance
- Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)
- Pintos v. Pacific Creditors Ass'n, 605 F.3d 665 (9th Cir. 2010)
- Safeco Insurance Co. v. Burr, 551 U.S. 47 (2007)
- Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997)

SIGNATURE BLOCK + ENCLOSURES
```

---

## CREDITOR LETTER TEMPLATE (§ 1681b Demand)

```javascript
// STRUCTURE FOR CREDITOR LETTERS

HEADER:
- Consumer name, address, contact info
- Date
- "VIA: CERTIFIED MAIL, RETURN RECEIPT REQUESTED"

TO:
- Creditor name and address

RE LINE:
═══════════════════════════════════════════════════════════════════════════
RE: UNAUTHORIZED CREDIT INQUIRY - DEMAND FOR REMOVAL
15 U.S.C. § 1681b - NO PERMISSIBLE PURPOSE
Inquiry Date: [DATE]
═══════════════════════════════════════════════════════════════════════════

SECTION 1: NOTICE OF UNAUTHORIZED INQUIRY

On [DATE], your company accessed my consumer credit report through 
[BUREAU(S)]. This inquiry was NOT AUTHORIZED.

I CERTIFY UNDER PENALTY OF PERJURY:
- I did NOT apply for credit with [COMPANY]
- I did NOT authorize [COMPANY] to access my credit report
- I have NO business relationship with [COMPANY]
- [COMPANY] had NO permissible purpose under § 1681b

SECTION 2: LEGAL BASIS - § 1681b VIOLATION

Under 15 U.S.C. § 1681b, you may ONLY access a consumer report with 
permissible purpose. The primary permissible purposes are:

§ 1681b(a)(3)(A): Credit transaction INITIATED BY THE CONSUMER
§ 1681b(a)(3)(F): Legitimate business need in consumer-initiated transaction

I did NOT initiate ANY transaction with your company. Therefore, you 
had NO permissible purpose to access my credit report.

Accessing a consumer report WITHOUT permissible purpose is a FEDERAL 
VIOLATION carrying significant civil liability.

SECTION 3: YOUR LIABILITY

Under 15 U.S.C. § 1681n (willful) and § 1681o (negligent), you are 
liable for:

| Damages Category | Statutory Basis | Range |
|------------------|-----------------|-------|
| Statutory damages | § 1681n(a)(1)(A) | $100-$1,000 |
| Actual damages | § 1681n(a)(1)(A) | Varies |
| Punitive damages | § 1681n(a)(2) | Unlimited |
| Attorney fees | § 1681n(a)(3) | $15,000+ |

Key Case: Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002) - 
"Obtaining a consumer report under false pretenses or without 
permissible purpose creates liability under § 1681n."

SECTION 4: DEMANDS

I DEMAND that [COMPANY]:

1. IMMEDIATELY notify Experian, Equifax, and TransUnion to DELETE 
   this inquiry from my credit file

2. PROVIDE written confirmation that deletion requests have been sent

3. PROVIDE any documentation you claim shows my authorization 
   (you have none because I never authorized this)

4. IMPLEMENT procedures to prevent future unauthorized pulls

5. PRESERVE all records related to this inquiry for potential litigation

SECTION 5: PRESERVATION OF RECORDS

[COMPANY] is hereby directed to PRESERVE:
- All records of the alleged application or authorization
- All communications with credit bureaus regarding this inquiry
- All internal records showing why this inquiry was made
- Employee records showing who ordered this credit pull

SECTION 6: RESPONSE DEADLINE

You have 15 DAYS from receipt of this letter to:
1. Confirm deletion requests sent to all bureaus
2. Provide any claimed proof of permissible purpose

SECTION 7: CONSEQUENCES OF NON-COMPLIANCE

If you fail to request deletion within 15 DAYS:

1. I will file complaints with:
   - Consumer Financial Protection Bureau (CFPB)
   - Federal Trade Commission (FTC)
   - [STATE] Attorney General

2. I will initiate federal litigation seeking:
   - Statutory damages (minimum $100, up to $1,000)
   - Actual damages
   - Punitive damages
   - Attorney fees and costs

LEGAL CITATIONS:
- 15 U.S.C. § 1681b - Permissible purposes
- 15 U.S.C. § 1681n - Willful noncompliance
- 15 U.S.C. § 1681o - Negligent noncompliance
- Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)
- Pintos v. Pacific Creditors Ass'n, 605 F.3d 665 (9th Cir. 2010)

SIGNATURE BLOCK + ENCLOSURES
```

---

## ENCLOSURES FOR § 604 DISPUTES (SIMPLER THAN § 605B)

**Bureau Letters:**
- [ ] Copy of government-issued photo ID
- [ ] Copy of Social Security card
- [ ] Proof of current address
- [ ] Copy of credit report with unauthorized inquiries circled

**Creditor Letters:**
- [ ] Copy of government-issued photo ID
- [ ] Copy of credit report showing the inquiry

**NOTE:** NO FTC Report or Police Report required for § 604 disputes!

---

## BUREAU ADDRESSES

**TransUnion:**
P.O. Box 2000
Chester, PA 19016

**Experian:**
P.O. Box 4500
Allen, TX 75013

**Equifax:**
P.O. Box 740256
Atlanta, GA 30374-0256

---

## GENERATE THE LETTERS

Using the client information provided:

1. Create DOCX letter for each bureau with unauthorized inquiries
2. Create DOCX letter for each creditor that pulled
3. Use professional formatting (Arial, tables, separators)
4. Include all legal citations and case law
5. Calculate damages exposure for each letter
6. Save each as separate file to /mnt/user-data/outputs/

**FILE NAMING:**
```
Inquiry604_[BUREAU]_[LASTNAME]_[DATE].docx
Inquiry604_Creditor_[COMPANY]_[LASTNAME]_[DATE].docx
```

---

## WORKFLOW CHECKLIST

**Before Sending:**
- [ ] Verify consumer did NOT apply with these companies
- [ ] Confirm these are HARD inquiries (not soft/promotional)
- [ ] Check if any inquiry led to opened account (use Prompt 14 instead)

**After Generating:**
- [ ] Print letters
- [ ] Gather enclosures (ID, SSN card, proof of address, report copy)
- [ ] Send via certified mail, return receipt requested
- [ ] Record tracking numbers
- [ ] Calendar 30-day follow-up for bureaus
- [ ] Calendar 15-day follow-up for creditors

**Timeline:**
- Day 0: Mail letters
- Day 3-5: Confirm delivery via USPS tracking
- Day 15: Creditor response deadline
- Day 30: Bureau response deadline
- Day 35: If not resolved, escalate to CFPB/FTC

---

## END OF PROMPT 15A
