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

---

## FTC REPORT - QUESTION BY QUESTION GUIDE

```
________________________________________________________________________________

                    FTC IDENTITY THEFT REPORT - COPY/PASTE GUIDE

                    Website: https://www.identitytheft.gov

________________________________________________________________________________

STEP 1: Go to https://www.identitytheft.gov
        Click: "Get started"

________________________________________________________________________________

QUESTION 1: "My info was exposed in a data breach"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Equifax                                                           │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 2: "Yes, someone used my info..."

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit card accounts                                              │
        │  (or select "loans or leases" if that applies to your inquiries)   │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 3: "To open a fraudulent account"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  To open a fraudulent account                                      │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 4: "Theft Details Page"
            "What company or bank issued the credit card?"

        TYPE:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Not applicable                                                    │
        └─────────────────────────────────────────────────────────────────────┘

        Everything else on this page: LEAVE BLANK

________________________________________________________________________________

QUESTION 5: "Your Information Page"

        - Input your name
        - Input phone # (you will receive a verification code)

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Myself                                                            │
        └─────────────────────────────────────────────────────────────────────┘

        - Input your Birthday
        - Input your Address

________________________________________________________________________________

QUESTION 6: Series of Yes/No Questions

        SELECT FOR EACH:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No                                                                │
        │  No                                                                │
        │  No, not at this time                                              │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 7: "Yes (review report)"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes (review report)                                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 8: "Yes (fraudulent accounts)"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes (fraudulent accounts)                                         │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 9: Checkboxes

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  None of the checkboxes                                            │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 10: "Company Name"

        Input the inquiry information EXACTLY how it is shown on the report
        + type in date

        EXAMPLE:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  BK OF AMER 07/11/2023                                             │
        └─────────────────────────────────────────────────────────────────────┘

        (Upload up to three - we will attach the rest later)

________________________________________________________________________________

QUESTION 11: "No (requested fraud alert)"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No (requested fraud alert)                                        │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 12: "No (contacted police)"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No (contacted police)                                             │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 13: "Yes (info exposed in breach)"

        Check boxes:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  [X] YES Equifax                                                   │
        │  [X] YES Marriott                                                  │
        │  [X] YES Breach not listed                                         │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 14: "Yes (debt collector contacted you)"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes (debt collector contacted you)                                │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 15: Statement Box

        COPY THIS EXACT TEXT (replace bracketed items with your inquiries):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  These inquiries do not belong to me, please have them removed     │
        │  from my credit report:                                            │
        │                                                                     │
        │  BK OF AMER (04/05/2023), LIGHTSTRM (04/04/2023),                  │
        │  US BANK (04/04/2023), ELAN FINANI (03/07/2023)                    │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

        ** LIST ALL YOUR INQUIRIES WITH DATES - EXACTLY AS SHOWN ON REPORT **

________________________________________________________________________________

QUESTION 16: Input inquiry information

        Input the inquiry information exactly how it is shown on the report

________________________________________________________________________________

FINALIZE:

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Submit without an account                                         │
        └─────────────────────────────────────────────────────────────────────┘

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Text message                                                      │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

*** CRITICAL - DO NOT SKIP ***

        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  DOWNLOAD PDF DOC                                                  │
        │                                                                     │
        │  The PDF report CANNOT be retrieved after you leave this page!     │
        │  Download it NOW and save it to your computer.                     │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

RECORD YOUR FTC INFORMATION

FTC Report Number:  _________________________________

Date Filed:         _________________________________

PDF Downloaded:     [ ] Yes - Saved to computer

________________________________________________________________________________
```

---

# PHASE 2: CFPB COMPLAINT

## Timing
Submit IMMEDIATELY after completing FTC Report.

## Important Requirement
Submit SEPARATE complaints for each credit bureau (TransUnion and Equifax).
You will go through this process TWICE - once for each bureau.

## Portal Information
```
URL:            https://www.consumerfinance.gov/complaint/
Duration:       10-15 minutes per bureau
Response:       15 business days (federal requirement)
```

---

## CFPB COMPLAINT - QUESTION BY QUESTION GUIDE

```
________________________________________________________________________________

                    CFPB COMPLAINT - COPY/PASTE GUIDE

                    Website: https://www.consumerfinance.gov/complaint/

________________________________________________________________________________

                    *** FILE SEPARATE COMPLAINTS FOR EACH BUREAU ***

                    Complete this form TWICE:
                    [ ] Once for TransUnion
                    [ ] Once for Equifax

________________________________________________________________________________

STEP 1: Go to https://www.consumerfinance.gov/complaint/
        Click: "Submit A Complaint" (top right)

________________________________________________________________________________

STEP 2: Select "Start a new complaint"
        Create an account and verify email address

________________________________________________________________________________

QUESTION 1: "What is this complaint about?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit reporting or other personal consumer reports               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 2: "What type of credit reporting product?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit reporting                                                  │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 3: "What type of problem are you having?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Improper use of your report                                       │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 4: "Which best describes your problem?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit inquiries on your report that you don't recognize          │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 5: "Have you already tried to fix this problem with the company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes                                                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 6: "Did you request information from the company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes                                                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 7: "Did the company provide you this information?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes                                                               │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 8: "What happened?"

        COPY THIS EXACT TEXT (replace items in brackets):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  I just recently looked at my report from [CREDIT BUREAU] on       │
        │  [TODAY DATE], and I saw some hard inquiries that are the result   │
        │  of Identity Theft.                                                │
        │                                                                     │
        │  Please block and/or remove all information resulting from         │
        │  Identity Theft pursuant to FCRA 605B (15 U.S.C. & 1681 c-2)      │
        │  which states that these accounts must be removed within           │
        │  4 Business Days of receipt.                                       │
        │                                                                     │
        │  These accounts are causing me hardship and they are hindering     │
        │  me from obtaining new credit.                                     │
        │                                                                     │
        │  1. [Name of inquiry and Date] Please block and/or remove all      │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        │  2. [Name of inquiry and Date] Please block and/or remove all      │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

        EXAMPLE (filled in):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  I just recently looked at my report from TRANSUNION on            │
        │  January 15, 2026, and I saw some hard inquiries that are the      │
        │  result of Identity Theft.                                         │
        │                                                                     │
        │  Please block and/or remove all information resulting from         │
        │  Identity Theft pursuant to FCRA 605B (15 U.S.C. & 1681 c-2)      │
        │  which states that these accounts must be removed within           │
        │  4 Business Days of receipt.                                       │
        │                                                                     │
        │  These accounts are causing me hardship and they are hindering     │
        │  me from obtaining new credit.                                     │
        │                                                                     │
        │  1. BK OF AMER (04/05/2023) Please block and/or remove all         │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        │  2. LIGHTSTRM (04/04/2023) Please block and/or remove all          │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 9: "What would be a fair resolution to this issue?"

        COPY THIS EXACT TEXT (replace items in brackets):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  Delete these hard inquiries; [Name of inquiry and Date],          │
        │  [Name of inquiry and Date], [Name of inquiry and Date],           │
        │  has violated my rights.                                           │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

        EXAMPLE (filled in):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  Delete these hard inquiries; BK OF AMER (04/05/2023),             │
        │  LIGHTSTRM (04/04/2023), US BANK (04/04/2023),                     │
        │  has violated my rights.                                           │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 10: "Select a file to attach?"

        UPLOAD:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Upload the PDF FTC Report                                         │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 11: "What company is this complaint about?"

        TYPE:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Type the credit bureau name:                                      │
        │                                                                     │
        │  For TransUnion complaint: TRANSUNION                              │
        │  For Equifax complaint:    EQUIFAX                                 │
        │  (For Experian complaint:  EXPERIAN)                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 12: "Your information"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  SSN, Name, and date of birth                                      │
        └─────────────────────────────────────────────────────────────────────┘

        Fill out all the necessary information

________________________________________________________________________________

QUESTION 13: "Do you want to complain about another company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No                                                                │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 14: "Who are you submitting this complaint for?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Myself                                                            │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

STEP 3: Review the complaint

        Double-check all information is correct

________________________________________________________________________________

STEP 4: Submit the complaint

        ┌─────────────────────────────────────────────────────────────────────┐
        │  *** DO NOT REFRESH ***                                            │
        │                                                                     │
        │  It will restart everything. It may take time to process.          │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

NOTE: This process may remove the inquiries by itself within 72 hours.
      If it doesn't, then continue to the next step (609 Letters).

________________________________________________________________________________

RECORD YOUR CFPB INFORMATION

CFPB Complaint # (TransUnion):  _________________________________

CFPB Complaint # (Equifax):     _________________________________

Date Filed (TransUnion):        _________________________________

Date Filed (Equifax):           _________________________________

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
| TransUnion  | TransUnion Consumer Solutions                            |
|             | P.O. Box 2000                                           |
|             | Chester, PA 19016                                       |
+-------------+----------------------------------------------------------+
| Equifax     | Equifax Credit Information Services INC                  |
|             | P.O. BOX 740256                                         |
|             | Atlanta, GA 30374                                       |
+-------------+----------------------------------------------------------+
```

---

## PREPARING LETTERS FOR CREDIT BUREAUS

```
________________________________________________________________________________

                    STEP 1: GATHER YOUR INFO & DOCS

________________________________________________________________________________

Documents Needed:

[ ] Your Full Name
[ ] Your Address
[ ] Your Birthdate
[ ] Copy of Driver's License
[ ] Copy of Social Security Card
[ ] Proof of Residency (e.g. utility bill, phone bill, or bank statement)

________________________________________________________________________________

                    STEP 2: DOCUMENT PREPARATION

________________________________________________________________________________

1. Use the letter template below

2. Reference your FTC complaint in your letter

3. List all inquiries that you believe are incorrect and should be removed

4. Input the "Bank Name" EXACTLY as shown on report
   Example: FAIRWINDS CREDIT UNI

5. Input the date in the following format: Month Day, Year
   Example: January 17, 2023

6. Repeat the entire process for both bureaus

________________________________________________________________________________

                    STEP 3: VERIFICATION

________________________________________________________________________________

Double-check all the information in your letter:

[ ] Verify today's date
[ ] Verify Name
[ ] Verify Address (look at driver's license)
[ ] Input SSN (look at SSN Card)
[ ] Verify typed name at the bottom as the "signature"

Make sure the details match what's in your FTC report:

[ ] Match the inquiries and the dates
[ ] Make sure none of them are Experian (that is a different process)

[ ] Save and keep a copy of everything

*** VERIFY - VERIFY - VERIFY everything ***

________________________________________________________________________________

                    STEP 4: SEND THE LETTERS

________________________________________________________________________________

MAKE SURE ALL DOCS ARE THERE:

[ ] 609 Letters
[ ] FTC Report
[ ] Copy of Driver's License
[ ] Copy of SSN card
[ ] Proof of Address

Mail the letters to the respective credit bureaus as CERTIFIED MAIL (IMPORTANT).

Make sure to keep a record of your mail and the receipt.

________________________________________________________________________________
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
The documentation will take 5 full business days to process once it arrives.
If you still see the inquiries there after the 8th full business day of
processing, call them and ask politely to have them removed.

## Bureau Contact Information

```
________________________________________________________________________________

                         TELEPHONE FOLLOW-UP GUIDE

________________________________________________________________________________

TRANSUNION
----------
Telephone:      1-800-916-8800
Hold Time:      Approximately 30 minutes

STEPS:
1. Call the number
2. Select the "Dispute" option
3. Do NOT select option #1
4. If prompted for text confirmation, hit # multiple times
5. Once connected to an agent, provide your information
6. Mention: "I recently sent a letter about fraudulent inquiries due to
   identity theft on my credit report. An FTC report was attached.
   I'd like to confirm the inquiries removal."
7. You'll be asked for identity verification
   - If they suggest text/email verification, clarify that you're on
     your business phone and cannot receive texts
   - Request to answer security questions instead
8. They will ask about report specifics. E.g., "Name the lender and
   monthly payment for an auto loan/mortgage/credit card."
   Scan the report and answer accordingly.
9. If needed, be persistent in your request
10. If uncooperative, ask to speak with a supervisor.
    This might need repetition.

________________________________________________________________________________

EQUIFAX
-------
Telephone:      1-800-525-6285
Hold Time:      Approximately 15 minutes

STEPS:
1. Call the number
2. Connect directly with an agent
3. Provide your information
4. Mention: "I recently sent a letter about fraudulent inquiries due to
   identity theft on my credit report. An FTC report was attached.
   I'd like to confirm the inquiries' removal."
5. You'll be asked for identity verification
   - If they suggest text/email verification, clarify that you're on
     your business phone and cannot receive texts
   - Request to answer security questions instead
6. They will ask about report specifics. E.g., "Name the lender and
   monthly payment for an auto loan/mortgage/credit card."
   Scan the report and answer accordingly.
7. If needed, be persistent in your request
8. If uncooperative, ask to speak with a supervisor.
   This might need repetition.

________________________________________________________________________________

IMPORTANT NOTES:

- Be prepared for potential multiple calls
- It might take 3-4 calls for a successful resolution

________________________________________________________________________________

IF THEY WON'T REMOVE OVER THE PHONE:

If you are not able to confirm the removal or they won't let you remove
them over the phone after this strategy (try calling multiple times),
they should be able to tell you WHY.

Make the adjustment and submit everything again.

If still facing issues, proceed to 2nd CFPB Complaint (Phase 5).

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

## 2nd CFPB COMPLAINT - QUESTION BY QUESTION GUIDE

```
________________________________________________________________________________

                    2nd CFPB COMPLAINT - ESCALATION

                    Website: https://www.consumerfinance.gov/complaint/

________________________________________________________________________________

                    *** FILE SEPARATE COMPLAINTS FOR EACH BUREAU ***

________________________________________________________________________________

STEP 1: Go to https://www.consumerfinance.gov/complaint/
        Click: "Submit A Complaint" (top right)

________________________________________________________________________________

STEP 2: Select "Start a new complaint"
        Create an account and verify email address (or log in)

________________________________________________________________________________

QUESTION 1: "What is this complaint about?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit reporting or other personal consumer reports               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 2: "What type of credit reporting product?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Credit reporting                                                  │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 3: "What type of problem are you having?"

        *** DIFFERENT FROM FIRST COMPLAINT ***

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Problem with a company's investigation into an existing problem   │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 4: "Which best describes your problem?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Their investigation did not fix an error on your report           │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 5: "Have you already tried to fix this problem with the company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Yes                                                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 6: "Did you request information from the company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No                                                                │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 7: "What happened?"

        COPY THIS EXACT TEXT (replace items in brackets):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  I am writing to follow up on a previous complaint I submitted     │
        │  concerning inaccuracies in my credit report, specifically         │
        │  related to unauthorized inquiries that are a result of identity   │
        │  theft. Despite my diligent efforts to resolve this issue          │
        │  through various means, the credit bureau has failed to rectify    │
        │  the inaccuracies in compliance with the Fair Credit Reporting     │
        │  Act (FCRA).                                                       │
        │                                                                     │
        │  On reviewing my credit report after filing an FTC report for      │
        │  identity theft, I identified unauthorized inquiries that should   │
        │  not be present. Pursuant to FCRA Section 609B and under the       │
        │  guidelines of Identity Theft pursuant to FCRA 605B (15 U.S.C.     │
        │  & 1681c-2), I demanded the immediate removal of these inquiries   │
        │  within four business days. Despite this, the credit bureau has    │
        │  not taken the required action.                                    │
        │                                                                     │
        │  Furthermore, I have contacted the credit bureau directly to       │
        │  request the removal of these inquiries, but my requests were      │
        │  not honored, demonstrating a lack of adherence to 15 U.S.C.       │
        │  1681s-2, which mandates that no inaccurate information should     │
        │  be furnished by any entity if it knows or has reason to believe   │
        │  the information is inaccurate.                                    │
        │                                                                     │
        │  I provided a detailed dispute letter (Letter 609B) and followed   │
        │  up with a phone call. Despite these efforts, the bureau's         │
        │  investigation concluded without rectifying the inaccuracies,      │
        │  contradicting 15 USC 1681i 5, which requires the agency to        │
        │  delete or modify unverified or inaccurate information promptly.   │
        │                                                                     │
        │  Moreover, the bureau has failed to provide a comprehensive        │
        │  description of the reinvestigation process as stipulated under    │
        │  15 USC 1681i(7), leaving me without the necessary transparency    │
        │  and clarity on the actions taken (or not taken) regarding my      │
        │  dispute.                                                          │
        │                                                                     │
        │  The continued presence of these inaccuracies on my credit         │
        │  report not only violates the FCRA but also has a detrimental      │
        │  impact on my financial wellbeing. I seek the Bureau's             │
        │  intervention to ensure that the credit reporting agency adheres   │
        │  to the stipulated laws and rectifies the errors on my credit      │
        │  report without further delay.                                     │
        │                                                                     │
        │  Enclosed, please find all relevant documentation, including       │
        │  copies of my previous correspondences, the FTC identity theft     │
        │  report, and evidence supporting the unauthorized nature of the    │
        │  inquiries in question.                                            │
        │                                                                     │
        │  I appreciate your attention to this urgent matter and look        │
        │  forward to your swift action to enforce compliance with the       │
        │  FCRA and safeguard my consumer rights.                            │
        │                                                                     │
        │  These accounts are causing me hardship and they are hindering     │
        │  me from obtaining new credit.                                     │
        │                                                                     │
        │  1. [Name of inquiry and Date] Please block and/or remove all      │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        │  2. [Name of inquiry and Date] Please block and/or remove all      │
        │     information resulting from Identity Theft pursuant to          │
        │     FCRA 605B (15 U.S.C. & 1681 c-2).                             │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 8: "What would be a fair resolution to this issue?"

        COPY THIS EXACT TEXT (replace items in brackets):
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        │  Delete these hard inquiries; [Name of inquiry and Date],          │
        │  [Name of inquiry and Date], [Name of inquiry and Date],           │
        │  has violated my rights.                                           │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 9: "Select a file to attach?"

        UPLOAD:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Upload the PDF FTC Report AND the 609B Letter                     │
        └─────────────────────────────────────────────────────────────────────┘

        Click: Next

________________________________________________________________________________

QUESTION 10: "What company is this complaint about?"

        TYPE:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Type the credit bureau name:                                      │
        │                                                                     │
        │  For TransUnion complaint: TRANSUNION                              │
        │  For Equifax complaint:    EQUIFAX                                 │
        │  (For Experian complaint:  EXPERIAN)                               │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 11: "Your information"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  SSN, Name, and date of birth                                      │
        └─────────────────────────────────────────────────────────────────────┘

        Fill out all the necessary information

________________________________________________________________________________

QUESTION 12: "Do you want to complain about another company?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  No                                                                │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

QUESTION 13: "Who are you submitting this complaint for?"

        SELECT:
        ┌─────────────────────────────────────────────────────────────────────┐
        │  Myself                                                            │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

STEP 3: Review the complaint

        Double-check all information is correct

________________________________________________________________________________

STEP 4: Submit the complaint

        ┌─────────────────────────────────────────────────────────────────────┐
        │  *** DO NOT REFRESH ***                                            │
        │                                                                     │
        │  It will restart everything. It may take time to process.          │
        └─────────────────────────────────────────────────────────────────────┘

________________________________________________________________________________

Within a week you should see the inquiries removed.

Remember to always keep records of every interaction and document you send
or receive. It'll be crucial in the event of any discrepancies or further
disputes.

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
