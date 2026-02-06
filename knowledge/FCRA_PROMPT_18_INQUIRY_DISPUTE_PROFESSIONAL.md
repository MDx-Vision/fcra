# FCRA PROMPT 18 v1.0 — INQUIRY DISPUTE SYSTEM

## Document Purpose
This prompt generates professional documentation for disputing unauthorized credit inquiries pursuant to FCRA Section 604 (Permissible Purposes) and Section 609 (Disclosure Requirements). All output must adhere to enterprise documentation standards suitable for legal proceedings and regulatory compliance.

## Trigger Conditions
- "inquiry dispute" / "remove inquiries" / "hard inquiry"
- "609 letter" / "unauthorized inquiry"
- "permissible purpose" / "no consent"

---

# INQUIRY DISPUTE PROCESS OVERVIEW

## Legal Foundation
Under FCRA Section 604, a consumer reporting agency may furnish a consumer report only for specific permissible purposes. Inquiries made without proper authorization constitute violations of federal law.

## Process Timeline
Typical removal timeframe: 7-14 business days

## Multi-Phase Approach

```
+--------+     +--------+     +--------+     +--------+     +--------+
| PHASE  |     | PHASE  |     | PHASE  |     | PHASE  |     | PHASE  |
|   1    | --> |   2    | --> |   3    | --> |   4    | --> |   5    |
| FTC    |     | CFPB   |     | 609    |     | Phone  |     | 2nd    |
| Report |     |Complaint|    | Letters|     |Follow-up|    | CFPB   |
+--------+     +--------+     +--------+     +--------+     +--------+
```

---

# PHASE 1: FTC IDENTITY THEFT REPORT

## Applicability
Submit FTC Report ONLY when inquiries are NOT attached to an open account.

## Portal Information
```
URL:            https://www.identitytheft.gov
Duration:       10-15 minutes
Document Type:  Identity Theft Report
```

## Step-by-Step Instructions

```
________________________________________________________________________________

                         FTC REPORT SUBMISSION GUIDE

________________________________________________________________________________

STEP 1:  Navigate to https://www.identitytheft.gov
         Select: "Report Identity Theft"

STEP 2:  When prompted "Which statement best describes your situation?"
         Select: "I want to report identity theft"

STEP 3:  When prompted "What did the identity thief do?"
         Select: "Other"

STEP 4:  When prompted "Tell us how your information was misused"
         Select: "Someone opened an account or made a purchase without
                  my permission"

STEP 5:  Enter the following information for each disputed inquiry:
         - Company Name: [CREDITOR NAME]
         - Date Noticed: [CURRENT MONTH/YEAR]
         - Description: "Unauthorized credit inquiry"

STEP 6:  Complete personal information screens as prompted

STEP 7:  In the narrative section, enter:
         "The following inquiry/inquiries were made without my knowledge,
         authorization, or consent. I did not apply for credit with this
         company and did not authorize any third party to do so. This is
         identity theft."

STEP 8:  Submit and IMMEDIATELY download the PDF report

         CRITICAL: The PDF cannot be retrieved after leaving this page.

________________________________________________________________________________

RECORD YOUR INFORMATION

FTC Report Number:  _________________________________

Date Filed:         _________________________________

PDF Downloaded:     [ ] Confirmed

________________________________________________________________________________
```

---

# PHASE 2: CFPB COMPLAINT

## Timing
Submit IMMEDIATELY after completing FTC Report.

## Important Requirement
Submit SEPARATE complaints for each credit bureau (TransUnion and Equifax).

## Portal Information
```
URL:            https://www.consumerfinance.gov/complaint/
Duration:       10-15 minutes per bureau
Response:       15 business days (federal requirement)
```

## Complaint Template

```
________________________________________________________________________________

                         CFPB COMPLAINT SUBMISSION

________________________________________________________________________________

Bureau:         [ ] TransUnion    [ ] Equifax

________________________________________________________________________________

COMPLAINT NARRATIVE (Copy and customize):

--------------------------------------------------------------------------------
I am filing this complaint regarding unauthorized credit inquiries that appear
on my [BUREAU NAME] credit report. These inquiries were made without my
knowledge, authorization, or consent.

DISPUTED INQUIRIES:

Creditor:       [CREDITOR NAME]
Inquiry Date:   [DATE]
Authorization:  NONE PROVIDED

I have filed an FTC Identity Theft Report (Reference: [FTC NUMBER]).

Under FCRA Section 604, consumer reporting agencies may only furnish reports
for permissible purposes. I did not apply for credit with the creditor(s)
listed above and did not authorize any third party to access my credit file.

I request immediate investigation and removal of these unauthorized inquiries.
--------------------------------------------------------------------------------

________________________________________________________________________________

RECORD YOUR INFORMATION

CFPB Complaint (TransUnion): _________________________________

CFPB Complaint (Equifax):    _________________________________

Date Filed:                  _________________________________

________________________________________________________________________________
```

---

# PHASE 3: SECTION 609 DISPUTE LETTERS

## Mailing Method
Certified Mail with Return Receipt Requested

## Bureau Addresses

```
+-------------+----------------------------------------------------------+
| Bureau      | Address                                                  |
+-------------+----------------------------------------------------------+
| TransUnion  | P.O. Box 2000                                           |
|             | Chester, PA 19016                                       |
+-------------+----------------------------------------------------------+
| Equifax     | P.O. BOX 740256                                         |
|             | Atlanta, GA 30374                                       |
+-------------+----------------------------------------------------------+
```

---

## DOCUMENT TEMPLATE: TransUnion_609_Letter_[CLIENT].md

```markdown
________________________________________________________________________________

                    FCRA SECTION 609 INQUIRY DISPUTE

________________________________________________________________________________

[DATE]

[CLIENT NAME]
[CLIENT ADDRESS]
[CITY], [STATE] [ZIP]

TransUnion Consumer Solutions
P.O. Box 2000
Chester, PA 19016

________________________________________________________________________________

RE: Dispute of Unauthorized Credit Inquiries
    Request for Removal Pursuant to FCRA Section 609

________________________________________________________________________________

Dear TransUnion:

This letter is to inform you that I have become a victim of identity theft.
The following credit inquiries appearing on my TransUnion credit report were
made without my knowledge, authorization, or consent.

________________________________________________________________________________

DISPUTED INQUIRIES

+------------------------+---------------------+-----------------------------+
| Creditor Name          | Date of Inquiry     | Authorization Status       |
+------------------------+---------------------+-----------------------------+
| [CREDITOR 1]           | [DATE]              | NO AUTHORIZATION PROVIDED  |
+------------------------+---------------------+-----------------------------+
| [CREDITOR 2]           | [DATE]              | NO AUTHORIZATION PROVIDED  |
+------------------------+---------------------+-----------------------------+

________________________________________________________________________________

LEGAL BASIS FOR REMOVAL

Under FCRA Section 604 (15 U.S.C. Section 1681b), consumer reporting agencies
are prohibited from furnishing consumer reports except for specific permissible
purposes. These include:

1. Written authorization from the consumer
2. Court order
3. Legitimate business transaction initiated by the consumer

I did not provide written authorization. No court order exists. I did not
initiate any business transaction with these creditors.

________________________________________________________________________________

SUPPORTING DOCUMENTATION ENCLOSED

[ ] FTC Identity Theft Report (Reference: [FTC NUMBER])
[ ] CFPB Complaint Confirmation (Reference: [CFPB NUMBER])
[ ] Copy of Government-Issued Photo Identification
[ ] Proof of Current Residence

________________________________________________________________________________

REQUEST FOR ACTION

Pursuant to FCRA Section 605B (15 U.S.C. Section 1681c-2), I demand the
immediate removal of these fraudulent inquiries from my credit file. Please
provide written confirmation of removal within fifteen (15) business days.

________________________________________________________________________________

Respectfully,


_______________________________
[CLIENT NAME]

Date of Birth:    [DOB]
SSN (Last 4):     [LAST 4 SSN]

________________________________________________________________________________

Enclosures: As stated above

Method of Delivery: USPS Certified Mail
Tracking Number:    ____________________________

________________________________________________________________________________
```

---

## DOCUMENT TEMPLATE: Equifax_609_Letter_[CLIENT].md

```markdown
________________________________________________________________________________

                    FCRA SECTION 609 INQUIRY DISPUTE

________________________________________________________________________________

[DATE]

[CLIENT NAME]
[CLIENT ADDRESS]
[CITY], [STATE] [ZIP]

Equifax Credit Information Services, Inc.
P.O. BOX 740256
Atlanta, GA 30374

________________________________________________________________________________

RE: Dispute of Unauthorized Credit Inquiries
    Request for Removal Pursuant to FCRA Section 609

________________________________________________________________________________

Dear Equifax:

This letter is to inform you that I have become a victim of identity theft.
The following credit inquiries appearing on my Equifax credit report were
made without my knowledge, authorization, or consent.

________________________________________________________________________________

DISPUTED INQUIRIES

+------------------------+---------------------+-----------------------------+
| Creditor Name          | Date of Inquiry     | Authorization Status       |
+------------------------+---------------------+-----------------------------+
| [CREDITOR 1]           | [DATE]              | NO AUTHORIZATION PROVIDED  |
+------------------------+---------------------+-----------------------------+
| [CREDITOR 2]           | [DATE]              | NO AUTHORIZATION PROVIDED  |
+------------------------+---------------------+-----------------------------+

________________________________________________________________________________

LEGAL BASIS FOR REMOVAL

Under FCRA Section 604 (15 U.S.C. Section 1681b), consumer reporting agencies
are prohibited from furnishing consumer reports except for specific permissible
purposes. These include:

1. Written authorization from the consumer
2. Court order
3. Legitimate business transaction initiated by the consumer

I did not provide written authorization. No court order exists. I did not
initiate any business transaction with these creditors.

________________________________________________________________________________

SUPPORTING DOCUMENTATION ENCLOSED

[ ] FTC Identity Theft Report (Reference: [FTC NUMBER])
[ ] CFPB Complaint Confirmation (Reference: [CFPB NUMBER])
[ ] Copy of Government-Issued Photo Identification
[ ] Proof of Current Residence

________________________________________________________________________________

REQUEST FOR ACTION

Pursuant to FCRA Section 605B (15 U.S.C. Section 1681c-2), I demand the
immediate removal of these fraudulent inquiries from my credit file. Please
provide written confirmation of removal within fifteen (15) business days.

________________________________________________________________________________

Respectfully,


_______________________________
[CLIENT NAME]

Date of Birth:    [DOB]
SSN (Last 4):     [LAST 4 SSN]

________________________________________________________________________________

Enclosures: As stated above

Method of Delivery: USPS Certified Mail
Tracking Number:    ____________________________

________________________________________________________________________________
```

---

# PHASE 4: TELEPHONE FOLLOW-UP

## Timing
5-8 business days after mailing 609 letters

## Bureau Contact Information

```
________________________________________________________________________________

                         TELEPHONE FOLLOW-UP GUIDE

________________________________________________________________________________

TRANSUNION
----------
Telephone:      1-800-916-8800
Hold Time:      Approximately 30 minutes
Best Time:      Tuesday-Thursday, 9:00 AM - 11:00 AM EST

Navigation:
1. Press 2 for English
2. Press 1 for Credit Report
3. Press 2 for Dispute
4. When prompted, say "Representative"
5. Request transfer to Fraud Department if needed

________________________________________________________________________________

EQUIFAX
-------
Telephone:      1-800-525-6285
Hold Time:      Approximately 15-20 minutes
Best Time:      Tuesday-Thursday, 10:00 AM - 12:00 PM EST

Navigation:
1. Press 3 for Credit Report Questions
2. Press 1 for Personal Credit Report
3. Press 0 for Representative
4. Request transfer to Fraud/Dispute Department

________________________________________________________________________________

CALL SCRIPT

"Hello, my name is [CLIENT NAME]. I am calling to follow up on a dispute
letter I mailed regarding unauthorized credit inquiries on my report.

I sent the letter via certified mail on [DATE]. The tracking number is
[TRACKING NUMBER].

I would like to verify that my dispute has been received and processed.
Can you provide me with a status update and expected completion date?"

If resistance is encountered:

"I understand. However, under FCRA Section 611, you are required to
investigate disputes within 30 days. I have also filed complaints with
the FTC and CFPB. My FTC reference number is [FTC NUMBER] and my CFPB
complaint number is [CFPB NUMBER]. Please escalate this matter to your
compliance department."

________________________________________________________________________________

CALL LOG

+-------------+----------+-------------------+----------------+---------------+
| Bureau      | Date     | Representative    | Status         | Notes         |
+-------------+----------+-------------------+----------------+---------------+
| TransUnion  |          |                   |                |               |
+-------------+----------+-------------------+----------------+---------------+
| Equifax     |          |                   |                |               |
+-------------+----------+-------------------+----------------+---------------+

________________________________________________________________________________
```

---

# PHASE 5: SECOND CFPB COMPLAINT (IF NEEDED)

## Trigger Conditions
Submit second CFPB complaint if:
- Inquiries not removed within 15 business days of initial complaint
- Bureau fails to respond to 609 letter within 30 days
- Inquiries reinstated after removal

## Escalation Language

```
________________________________________________________________________________

                    ESCALATED CFPB COMPLAINT NARRATIVE

________________________________________________________________________________

I am filing this escalated complaint regarding the continued presence of
unauthorized credit inquiries on my [BUREAU NAME] credit report.

PREVIOUS COMPLAINT HISTORY:

Initial CFPB Complaint:     [PREVIOUS CFPB NUMBER]
Date Filed:                 [DATE]
FTC Reference Number:       [FTC NUMBER]
609 Letter Sent:            [DATE]
Certified Mail Tracking:    [TRACKING NUMBER]

BUREAU RESPONSE:

The bureau has [failed to respond / provided inadequate response / reinstated
disputed inquiries] despite receiving proper documentation of identity theft.

CONTINUED VIOLATIONS:

The following inquiries remain on my credit report in violation of FCRA
Section 604 and Section 605B:

+------------------------+---------------------+
| Creditor Name          | Date of Inquiry     |
+------------------------+---------------------+
| [CREDITOR 1]           | [DATE]              |
+------------------------+---------------------+

REQUEST FOR ENFORCEMENT ACTION:

I request that the CFPB:
1. Compel immediate removal of these unauthorized inquiries
2. Document this violation in the bureau's regulatory record
3. Consider enforcement action for continued non-compliance

________________________________________________________________________________
```

---

# OUTPUT DOCUMENT GENERATION

## Phase 1 Documents (Pre-Dispute)
Generate when client has disputed inquiries but no FTC/CFPB numbers yet:

1. **FTC_Report_Instructions_[CLIENT].md** - Step-by-step FTC filing guide
2. **CFPB_Complaint_Instructions_[CLIENT].md** - CFPB submission templates
3. **Inquiry_Dispute_Summary_[CLIENT].md** - Client overview document

## Phase 2 Documents (Full Dispute)
Generate when client has FTC number and CFPB complaint numbers:

1. **TransUnion_609_Letter_[CLIENT].md** - Bureau-ready dispute letter
2. **Equifax_609_Letter_[CLIENT].md** - Bureau-ready dispute letter
3. **Phone_Follow_Up_Guide_[CLIENT].md** - Call scripts and tracking
4. **Mailing_Checklist_[CLIENT].md** - Document assembly instructions

---

# DATA EXTRACTION REQUIREMENTS

## Consumer Information
```
FULL LEGAL NAME:     [Extract from credit report or client profile]
DATE OF BIRTH:       [MM/DD/YYYY format]
SSN (Last 4):        [If available]
STREET ADDRESS:      [Complete current address]
CITY:                [City name]
STATE:               [Two-letter code]
ZIP CODE:            [5 or 9 digit]
```

## Inquiry Details
For each disputed inquiry:
```
CREDITOR NAME:       [Exact name as shown on report]
INQUIRY DATE:        [MM/DD/YYYY or MM/YYYY]
BUREAU(S):           [TransUnion / Equifax / Both]
```

## Case Reference Numbers
```
FTC REPORT NUMBER:   [From identitytheft.gov PDF]
CFPB COMPLAINT (TU): [TransUnion complaint number]
CFPB COMPLAINT (EQ): [Equifax complaint number]
```

---

# DOCUMENT FORMATTING STANDARDS

## Typography
- Use monospace-compatible formatting
- ASCII box characters for tables: + - |
- Horizontal rules: ________________ (80 underscores)
- No emojis or decorative characters

## Document Structure
- Clear section headers in CAPS
- Consistent spacing and alignment
- Professional legal document appearance
- Enterprise-grade presentation

## File Naming Convention
```
[DocumentType]_[ClientName]_[Date].md

Examples:
TransUnion_609_Letter_John_Smith_02062026.md
FTC_Report_Instructions_Jane_Doe_02062026.md
Inquiry_Dispute_Summary_Carlos_Garcia_02062026.md
```

---

# MAILING CHECKLIST

```
________________________________________________________________________________

                         CERTIFIED MAIL PACKAGE CONTENTS

________________________________________________________________________________

For each bureau (TransUnion and Equifax), assemble the following:

+---+------------------------------------------+----------+
| # | Document                                 | Included |
+---+------------------------------------------+----------+
| 1 | 609 Dispute Letter (signed and dated)   | [ ]      |
+---+------------------------------------------+----------+
| 2 | FTC Identity Theft Report (full PDF)    | [ ]      |
+---+------------------------------------------+----------+
| 3 | CFPB Complaint Confirmation             | [ ]      |
+---+------------------------------------------+----------+
| 4 | Government-Issued Photo ID (copy)       | [ ]      |
+---+------------------------------------------+----------+
| 5 | Proof of Address (utility bill/bank)    | [ ]      |
+---+------------------------------------------+----------+

________________________________________________________________________________

MAILING INSTRUCTIONS

1. Make copies of ALL documents before mailing
2. Send via USPS Certified Mail with Return Receipt Requested
3. Record tracking numbers immediately
4. Retain green return receipt cards when received

________________________________________________________________________________

TRACKING INFORMATION

TransUnion Letter:
  Date Mailed:      _________________________________
  Tracking Number:  _________________________________
  Delivery Date:    _________________________________

Equifax Letter:
  Date Mailed:      _________________________________
  Tracking Number:  _________________________________
  Delivery Date:    _________________________________

________________________________________________________________________________
```

---

# COMPLIANCE TIMELINE

```
________________________________________________________________________________

                         EXPECTED RESPONSE TIMELINE

________________________________________________________________________________

+---------------------------+------------------+------------------------------+
| Action                    | Deadline         | Authority                   |
+---------------------------+------------------+------------------------------+
| Bureau acknowledgment     | 5 business days  | Industry standard           |
+---------------------------+------------------+------------------------------+
| CFPB response required    | 15 days          | 12 CFR 1002                 |
+---------------------------+------------------+------------------------------+
| Investigation completion  | 30 days          | FCRA Section 611(a)(1)      |
+---------------------------+------------------+------------------------------+
| Written results notice    | 5 days after     | FCRA Section 611(a)(6)      |
+---------------------------+------------------+------------------------------+

________________________________________________________________________________

NOTE: Failure to meet these deadlines constitutes a violation of federal law
and may be documented for potential litigation purposes.

________________________________________________________________________________
```

---

# ESCALATION PROCEDURES

If inquiries are not removed after completing all phases:

1. **State Attorney General Complaint**
   - File complaint with state AG consumer protection division
   - Reference all previous attempts and documentation

2. **FCRA Litigation Consideration**
   - Document all violations and response failures
   - Consult with FCRA attorney for potential lawsuit
   - Statutory damages: $100-$1,000 per violation
   - Willful violations: punitive damages available

3. **Better Business Bureau Complaint**
   - File complaint against non-responsive bureau
   - Request mediation

---

## END OF PROMPT 18
