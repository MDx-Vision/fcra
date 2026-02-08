# FCRA PROMPT 17 v7.0 — SECTION 605B IDENTITY THEFT BLOCK REQUEST

## Document Purpose
This prompt generates professional documentation for identity theft disputes pursuant to FCRA Section 605B. All output must adhere to enterprise documentation standards suitable for legal proceedings and regulatory compliance.

## Trigger Conditions
- "5DKO" / "5 day knockout" / "knockout"
- "identity theft dispute" / "605B block"
- "unauthorized account" / "fraudulent account"

---

# PHASE 1: PRELIMINARY DOCUMENTATION

## Input Requirements
- Consumer credit report (any bureau format)

## Output Deliverables
- Document 1: Data Agency Security Freeze Instructions
- Document 2: Federal Trade Commission Report Guide
- Document 3: Client Information Summary
- Document 4: FTC Identity Theft Affidavit (Pre-populated)
- Document 5: CFPB Complaint Instructions (file WITH FTC - same day)

---

## PHASE 1 — STEP 1: DATA EXTRACTION

### Consumer Information
```
FULL LEGAL NAME:     [Extract from report header]
DATE OF BIRTH:       [MM/DD/YYYY format]
SSN (Last 4):        [If displayed]
STREET ADDRESS:      [Complete address]
CITY:                [City name]
STATE:               [Two-letter code]
ZIP CODE:            [5 or 9 digit]
```

### Disputed Account Details
For each account under dispute:
```
ACCOUNT REFERENCE:   [Sequential number]
CREDITOR:            [Exact name as reported]
ACCOUNT NUMBER:      [Complete number including masks]
ACCOUNT TYPE:        [Credit Card / Installment Loan / Collection / Authorized User]
DATE OPENED:         [MM/YYYY]
HIGH CREDIT:         [Dollar amount]
CURRENT STATUS:      [Open / Closed / Collection / Charged Off]
DISPUTE BASIS:       [Unauthorized / Fraudulent / Identity Theft]
BUREAU REPORTING:
  - TransUnion:      [Yes / No]
  - Experian:        [Yes / No]
  - Equifax:         [Yes / No]
```

---

## PHASE 1 — DOCUMENT TEMPLATES

### DOCUMENT 1: Data_Agency_Security_Freeze_[CLIENT].md

```markdown
________________________________________________________________________________

                    DATA AGENCY SECURITY FREEZE INSTRUCTIONS

________________________________________________________________________________

Client:         [CLIENT NAME]
Generated:      [DATE]
Classification: Pre-Dispute Preparation

________________________________________________________________________________

EXECUTIVE SUMMARY

Before initiating disputes with consumer reporting agencies, security freezes
must be placed with the following specialty data agencies. Credit bureaus
routinely verify information through these sources. Completing these freezes
prior to dispute submission increases the probability of successful removal.

________________________________________________________________________________

REQUIRED ACTIONS

Complete all three freezes before proceeding to dispute submission.
Estimated time: 20-30 minutes total.

________________________________________________________________________________

1. LEXISNEXIS CONSUMER CENTER

   Telephone:    1-888-497-0011
   Online:       https://consumer.risk.lexisnexis.com/freeze

   Instructions:
   - Request a security freeze on your consumer file
   - Provide identity verification when prompted
   - Record the PIN provided for future reference

   Estimated Duration: 5-10 minutes

________________________________________________________________________________

2. TELETRACK (CORELOGIC)

   Telephone:    1-877-309-5226 (automated system)
   Online:       https://consumers.teletrack.com/freeze

   Instructions:
   - Follow automated prompts for security freeze placement
   - A confirmation PIN will be mailed to your address
   - Retain this PIN for future credit applications

   Estimated Duration: 5 minutes

________________________________________________________________________________

3. INNOVIS

   Telephone:    1-866-712-4546
   Online:       https://www.innovis.com/personal/securityFreeze

   Instructions:
   - Request a security freeze on your consumer file
   - Verify your identity as prompted
   - Record the PIN provided

   Estimated Duration: 5-10 minutes

________________________________________________________________________________

AGENCIES NOT REQUIRED FOR THIS DISPUTE TYPE

The following agencies do not typically affect creditor verifications and
may be deferred:
- Advanced Resolution Services
- Intelius

________________________________________________________________________________

IMPORTANT NOTICE

After credit restoration is complete and before applying for new credit,
you must temporarily lift or remove these freezes. Each agency provides
lift options via telephone or online portal using your assigned PIN.

________________________________________________________________________________
```

---

### DOCUMENT 2: FTC_Police_Report_Instructions_[CLIENT].md

```markdown
________________________________________________________________________________

               FEDERAL TRADE COMMISSION AND POLICE REPORT GUIDE

________________________________________________________________________________

Client:         [CLIENT NAME]
Location:       [CITY], [STATE]
Generated:      [DATE]

________________________________________________________________________________

OBJECTIVE

Complete the FTC Identity Theft Report and obtain a police case number.
These documents are legally required under FCRA Section 605B to establish
an Identity Theft Report, which mandates a 4-business-day response from
consumer reporting agencies.

Total Estimated Time: 20-25 minutes

________________________________________________________________________________

SECTION A: FTC IDENTITY THEFT REPORT

The FTC report is a prerequisite for police department acceptance of
identity theft complaints.

Portal:         https://www.identitytheft.gov
Duration:       10-15 minutes

________________________________________________________________________________

STEP-BY-STEP INSTRUCTIONS

Navigate to https://www.identitytheft.gov and click "Report identity theft"

--------------------------------------------------------------------------------

STEP 1: THEFT DETAILS

"What did the identity thief use your information for?"
Select the category matching your disputed account:
- Credit card accounts
- Loans or leases (student loans, auto loans, mortgages, etc.)
- Debit, checking, or savings accounts
- Other account types

"Tell us how your information was misused"
Select: to open a fraudulent account

If you selected Credit card accounts, you will see a form:
"Credit Card Opened by the Thief"

+-------------------------------+----------------------------------------+
| Field                         | Value                                  |
+-------------------------------+----------------------------------------+
| Company or bank that issued   | [CREDITOR NAME from credit report]     |
| the credit card               |                                        |
+-------------------------------+----------------------------------------+
| When did you first notice     | Month: [Select]  Year: [Select]        |
| the problem?                  |                                        |
+-------------------------------+----------------------------------------+
| When was the account opened?  | Month: [Select]  Year: [Select]        |
| (if known)                    |                                        |
+-------------------------------+----------------------------------------+
| Estimate total fraudulent     | $[AMOUNT] (leave blank if unknown)     |
| charges (if known)            |                                        |
+-------------------------------+----------------------------------------+
| Account number (if known)     | [ACCOUNT NUMBER]                       |
+-------------------------------+----------------------------------------+

Click "+ Add another fraudulent credit card account" for additional accounts.

--------------------------------------------------------------------------------

STEP 2: YOUR INFORMATION

Enter your personal information:

+-------------------------------+----------------------------------------+
| Field                         | Value                                  |
+-------------------------------+----------------------------------------+
| First name (required)         | [YOUR FIRST NAME]                      |
+-------------------------------+----------------------------------------+
| Middle name                   | [YOUR MIDDLE NAME]                     |
+-------------------------------+----------------------------------------+
| Last name (required)          | [YOUR LAST NAME]                       |
+-------------------------------+----------------------------------------+
| Primary phone number          | [YOUR PHONE - verification code sent]  |
+-------------------------------+----------------------------------------+
| Phone type                    | Mobile / Home / Work                   |
+-------------------------------+----------------------------------------+
| Email address                 | [YOUR EMAIL]                           |
+-------------------------------+----------------------------------------+
| Confirm email address         | [YOUR EMAIL]                           |
+-------------------------------+----------------------------------------+

"Who are you filing this complaint for?"
Select: myself

Date of Birth: Year [Select] Month [Select] Day [Select]

Current Mailing Address:
- Street address
- Apt. Number / PO Box (if applicable)
- City
- State [Select]
- Zip code

"You have lived at this address since:"
Select: Year [Select] Month [Select]

"Has the victim's legal name or address changed since the theft occurred?"
Select: No

"Is the victim a military service member or veteran — or a spouse or
dependent of one?"
Select: No (unless applicable)

--------------------------------------------------------------------------------

STEP 3: SUSPECT INFORMATION

"Do you know anything about the person who stole your identity?"
Select: No, not at this time

--------------------------------------------------------------------------------

STEP 4: ADDITIONAL INFORMATION

CREDIT BUREAUS SECTION:

"Have you reviewed a copy of your credit report?"
Select: Yes

"Were there any fraudulent accounts included in your credit report?"
Select: Yes

"Was any personal information wrong in your credit report?"
Check any that apply or "None of the above"

COMPANY INQUIRIES (for hard inquiries):
If you see inquiries you didn't initiate, enter up to 3:
- Company name: [CREDITOR NAME] [DATE]
- Click "+ Add Company" for additional entries

LAW ENFORCEMENT DETAILS:

"Have you requested a fraud alert from one of the three national bureaus?"
Select: No, not yet

"Have you contacted your local police department?"
Select: No, not yet (will complete after FTC report)

DATA BREACH HISTORY:

"Was your personal information exposed in a data breach?"
Select: Yes
Check all applicable breaches (Equifax, Marriott, etc.)

DEBT COLLECTORS:

"Has a debt collector contacted you about an account that isn't yours?"
Select: No (or Yes if applicable)

--------------------------------------------------------------------------------

STEP 5: PERSONAL STATEMENT

"Tell us what happened in your own words"

This statement will be included in your FTC Identity Theft Report.
Do NOT include account numbers, SSN, or other sensitive data.
1000 character limit.

COPY AND CUSTOMIZE:

The following account(s) were opened fraudulently using my personal
information without my knowledge, authorization, or consent:

[CREDITOR 1] - Account #[XXXX] - Opened [DATE]
[CREDITOR 2] - Account #[XXXX] - Opened [DATE]

This is identity theft. I am filing this report with the Federal Trade
Commission and will file a police report. I request immediate blocking
of all fraudulent information from my credit file pursuant to FCRA
Section 605B.

--------------------------------------------------------------------------------

STEP 6: REVIEW YOUR COMPLAINT

Review all information for accuracy.

Click "Submit" to complete your report.

CRITICAL: Download the PDF report IMMEDIATELY.
The PDF cannot be retrieved after leaving this page.

Save as: FTC_Report_[YOUR_NAME]_[DATE].pdf

________________________________________________________________________________

RECORD YOUR FTC INFORMATION

FTC Report Number:  _________________________________

Date Filed:         _________________________________

PDF Downloaded:     [ ] Confirmed

________________________________________________________________________________

SECTION B: POLICE REPORT

With your FTC Report Number, proceed to file a police report.

________________________________________________________________________________

OPTION 1: ONLINE FILING (Recommended)

Many jurisdictions accept online identity theft reports.

Search Terms:
- "[CITY] [STATE] online police report"
- "[CITY] [STATE] identity theft report"
- "[STATE] state police online report"

STATE-SPECIFIC RESOURCES:

NEW JERSEY
- NJ State Police: https://njsp.njoag.gov/online-services/
- Local departments: Search "[CITY] NJ police online report"

FLORIDA
- Miami-Dade: https://www.miamidade.gov/global/service.page
- Most cities: Search "[CITY] FL COPLOGIC"

CALIFORNIA
- CA DOJ: https://oag.ca.gov/idtheft
- LAPD: https://www.lapdonline.org/report-a-crime/

NEW YORK
- NYPD: https://www.nyc.gov/site/nypd/services/law-enforcement/online-crime-reporting.page

TEXAS
- Houston PD: https://www.houstonpolice.org/report

Online Filing Steps:
1. Locate your jurisdiction's online reporting portal
2. Select "Identity Theft" or "Fraud" category
3. Enter your FTC Report Number when prompted
4. List all fraudulent accounts
5. Screenshot and save the confirmation page
6. Record the case number

________________________________________________________________________________

OPTION 2: IN-PERSON FILING

Police Department:  [CITY] Police Department
Address:            [To be determined by client]
Telephone:          [To be determined by client]

Required Documents:
- Government-issued photo identification
- FTC Identity Theft Report PDF (from Section A)
- Credit report pages with disputed items highlighted

Recommended Statement to Officer:

"I have filed an FTC Identity Theft Report and need to file a police
report for identity theft. Here is my FTC report and the credit report
pages showing the fraudulent accounts. I am requesting a case number
for my records."

________________________________________________________________________________

ACCOUNTS TO REPORT AS FRAUDULENT

+------------------+---------------+-------------+------------------------+
| Creditor         | Account No.   | Date Opened | Classification         |
+------------------+---------------+-------------+------------------------+
| [CREDITOR 1]     | [ACCOUNT #]   | [DATE]      | Fraudulent/Unauthorized|
| [CREDITOR 2]     | [ACCOUNT #]   | [DATE]      | Fraudulent/Unauthorized|
+------------------+---------------+-------------+------------------------+

________________________________________________________________________________

RECORD YOUR POLICE REPORT INFORMATION

Case Number:        _________________________________

Department Name:    _________________________________

Date Filed:         _________________________________

Filing Method:      [ ] Online    [ ] In-Person

Officer Name/Badge: _________________________________ (if applicable)

________________________________________________________________________________

NEXT STEPS

Upon completion of both the FTC report and police report:
1. Complete and notarize the FTC Identity Theft Affidavit
2. Return with:
   - FTC Report Number
   - Police Case Number
   - Notarized Affidavit(s)
3. Phase 2 documents will be generated for bureau submission

________________________________________________________________________________
```

---

### DOCUMENT 3: Client_Summary_[CLIENT].md

```markdown
________________________________________________________________________________

                         IDENTITY THEFT DISPUTE SUMMARY

________________________________________________________________________________

CONFIDENTIAL — CLIENT FILE

Client:                 [CLIENT NAME]
Case Initiated:         [DATE]
Document Reference:     5DKO-[CLIENT_ID]-[DATE]

________________________________________________________________________________

SECTION 1: CLIENT INFORMATION

+------------------------+---------------------------------------------+
| Full Legal Name        | [CLIENT NAME]                               |
+------------------------+---------------------------------------------+
| Date of Birth          | [MM/DD/YYYY]                                |
+------------------------+---------------------------------------------+
| Social Security (Last 4)| [XXXX]                                     |
+------------------------+---------------------------------------------+
| Current Address        | [STREET ADDRESS]                            |
|                        | [CITY], [STATE] [ZIP]                       |
+------------------------+---------------------------------------------+
| Telephone              | [PHONE NUMBER]                              |
+------------------------+---------------------------------------------+
| Email                  | [EMAIL ADDRESS]                             |
+------------------------+---------------------------------------------+

________________________________________________________________________________

SECTION 2: DISPUTED ACCOUNTS

ACCOUNT 1
+------------------------+---------------------------------------------+
| Creditor Name          | [CREDITOR NAME]                             |
+------------------------+---------------------------------------------+
| Account Number         | [FULL ACCOUNT NUMBER]                       |
+------------------------+---------------------------------------------+
| Account Type           | [Credit Card / Loan / Collection / AU]      |
+------------------------+---------------------------------------------+
| Date Opened            | [MM/YYYY]                                   |
+------------------------+---------------------------------------------+
| High Credit/Balance    | $[AMOUNT]                                   |
+------------------------+---------------------------------------------+
| Dispute Basis          | [Unauthorized / Fraudulent / Identity Theft]|
+------------------------+---------------------------------------------+
| Bureau Reporting       |                                             |
|   TransUnion           | [Yes / No]                                  |
|   Experian             | [Yes / No]                                  |
|   Equifax              | [Yes / No]                                  |
+------------------------+---------------------------------------------+

[Repeat for additional accounts]

________________________________________________________________________________

SECTION 3: BUREAU ACTION MATRIX

+-------------+------------------+---------------------------+
| Bureau      | Reporting Status | Required Action           |
+-------------+------------------+---------------------------+
| TransUnion  | [Reporting/Not]  | [605B Block Request/None] |
+-------------+------------------+---------------------------+
| Experian    | [Reporting/Not]  | [605B Block Request/None] |
+-------------+------------------+---------------------------+
| Equifax     | [Reporting/Not]  | [605B Block Request/None] |
+-------------+------------------+---------------------------+

________________________________________________________________________________

SECTION 4: PHASE 2 REQUIREMENTS

The following must be obtained before Phase 2 document generation:

[ ] Police Report Case Number:     _________________________________

[ ] Police Department Name:        _________________________________

[ ] Report Filing Date:            _________________________________

[ ] FTC Report Number:             _________________________________

[ ] FTC Report Date:               _________________________________

[ ] Third-Party Freezes Completed: [ ] LexisNexis  [ ] Teletrack  [ ] Innovis

[ ] Affidavit(s) Notarized:        [ ] Yes (Quantity: ___)

________________________________________________________________________________

SECTION 5: NEXT ACTIONS

1. Complete data agency security freezes (Document 1)
2. File FTC Identity Theft Report at identitytheft.gov
3. File police report (online or in-person)
4. Complete and notarize FTC Identity Theft Affidavit(s)
5. Return with required documentation for Phase 2

Upon receipt of required documentation, the following will be generated:
- Bureau dispute letters (3)
- Online submission templates
- Certified mail envelope checklist
- Telephone follow-up scripts
- Compliance tracking worksheet
- Escalation procedures (CFPB, reinsertion, BBB)

________________________________________________________________________________
```

---

### DOCUMENT 4: FTC_Affidavit_[CLIENT].md

```markdown
________________________________________________________________________________

                    FTC IDENTITY THEFT AFFIDAVIT COMPLETION GUIDE

________________________________________________________________________________

Client:         [CLIENT NAME]
Form Location:  https://www.identitytheft.gov (generates affidavit)
                OR https://ftc-identity-theft-affidavit.pdffiller.com/

NOTARIZATION REQUIRED

________________________________________________________________________________

IMPORTANT: SEPARATE AFFIDAVIT REQUIREMENT

Each disputed account requires a separate notarized affidavit for EACH
bureau where the account is reported.

AFFIDAVIT CALCULATION:

+------------------+-------------------+---------------------+
| Account          | Bureaus Reporting | Affidavits Required |
+------------------+-------------------+---------------------+
| [CREDITOR 1]     | [TU/EX/EQ]        | [#]                 |
+------------------+-------------------+---------------------+
| [CREDITOR 2]     | [TU/EX/EQ]        | [#]                 |
+------------------+-------------------+---------------------+
| TOTAL            |                   | [#]                 |
+------------------+-------------------+---------------------+

________________________________________________________________________________

AFFIDAVIT SECTION RESPONSES

SECTIONS 1-7: PERSONAL INFORMATION

+-----+--------------------------------+--------------------------------+
| #   | Field                          | Response                       |
+-----+--------------------------------+--------------------------------+
| 1   | Full Legal Name                | [CLIENT NAME]                  |
+-----+--------------------------------+--------------------------------+
| 2   | Date of Birth                  | [MM/DD/YYYY]                   |
+-----+--------------------------------+--------------------------------+
| 3   | Social Security Number         | [XXX-XX-XXXX]                  |
+-----+--------------------------------+--------------------------------+
| 4   | Current Address                | [ADDRESS, CITY, STATE ZIP]     |
+-----+--------------------------------+--------------------------------+
| 5   | Resided at Address Since       | [MM/YYYY - client to provide]  |
+-----+--------------------------------+--------------------------------+
| 6   | Telephone Number               | [PHONE]                        |
+-----+--------------------------------+--------------------------------+
| 7   | Email Address                  | [EMAIL]                        |
+-----+--------------------------------+--------------------------------+

SECTIONS 8-10: INFORMATION AT TIME OF FRAUD

Select: "Same as above" for all fields (if applicable)

SECTIONS 11-13: DECLARATIONS

+-----+------------------------------------------+-----------------+
| #   | Declaration                              | Select          |
+-----+------------------------------------------+-----------------+
| 11  | Did you authorize the transaction(s)?   | DID NOT         |
+-----+------------------------------------------+-----------------+
| 12  | Did you receive goods, services, or     | DID NOT         |
|     | money as a result?                       |                 |
+-----+------------------------------------------+-----------------+
| 13  | Are you working with anyone who may     | AM NOT          |
|     | have participated?                       |                 |
+-----+------------------------------------------+-----------------+

SECTIONS 14-15: Not applicable — Skip

SECTION 16: DOCUMENTATION PROVIDED

Check all that apply:
[ ] Valid government-issued photo identification
[ ] Proof of residence (utility bill, bank statement)

SECTION 17: Not applicable — Skip

SECTIONS 18-19: FRAUDULENT ACCOUNT INFORMATION

+--------------------------------+------------------------------------+
| Field                          | Response                           |
+--------------------------------+------------------------------------+
| Name of Institution            | [CREDITOR NAME]                    |
+--------------------------------+------------------------------------+
| Account Number                 | [ACCOUNT NUMBER]                   |
+--------------------------------+------------------------------------+
| Type of Account                | [Credit Card / Auto Loan / Other]  |
+--------------------------------+------------------------------------+
| Account Status                 | Opened fraudulently                |
+--------------------------------+------------------------------------+
| Date Account Opened            | [DATE FROM CREDIT REPORT]          |
+--------------------------------+------------------------------------+
| Date Fraud Discovered          | [MONTH YEAR]                       |
+--------------------------------+------------------------------------+

SECTION 20: LAW ENFORCEMENT REPORT

+--------------------------------+------------------------------------+
| Field                          | Response                           |
+--------------------------------+------------------------------------+
| Report Filing Method           | [ ] Online automated report        |
|                                | [ ] In-person filing               |
+--------------------------------+------------------------------------+
| Police Department              | [DEPARTMENT NAME]                  |
+--------------------------------+------------------------------------+
| Report/Case Number             | [CASE NUMBER]                      |
+--------------------------------+------------------------------------+
| Report Date                    | [DATE FILED]                       |
+--------------------------------+------------------------------------+
| Copy of Report Received        | Yes                                |
+--------------------------------+------------------------------------+
| FTC Complaint Number           | [FROM FTC PDF - upper right]       |
+--------------------------------+------------------------------------+

________________________________________________________________________________

NOTARIZATION OPTIONS

+------------------+------------+------------+-----------------------------+
| Provider         | Duration   | Cost       | Notes                       |
+------------------+------------+------------+-----------------------------+
| NotaryLive.com   | 15-30 min  | ~$25       | Online video notarization   |
+------------------+------------+------------+-----------------------------+
| Bank Branch      | Walk-in    | Free       | Call ahead to confirm       |
|                  |            |            | notary availability         |
+------------------+------------+------------+-----------------------------+
| UPS Store        | Walk-in    | $5-15      | No appointment required     |
+------------------+------------+------------+-----------------------------+

ONLINE NOTARIZATION PROCESS (NotaryLive.com):

1. Navigate to notarylive.com
2. Upload completed affidavit PDF
3. Complete identity verification
4. Connect with notary via video call (approximately 15 minutes)
5. Download notarized PDF immediately upon completion

REMINDER: You must complete [#] separate notarized affidavits—one for
each bureau where each account is reported.

________________________________________________________________________________
```

---

## PHASE 1 CLIENT COMMUNICATION

Upon completion of Phase 1 document generation, present the following summary:

```
Phase 1 documentation has been prepared for your identity theft dispute.

DOCUMENTS GENERATED:

1. Data Agency Security Freeze Instructions
   Complete these freezes before submitting bureau disputes.

2. FTC and Police Report Guide
   Step-by-step instructions for required federal filings.

3. Client Information Summary
   Consolidated case information for your records.

4. FTC Identity Theft Affidavit Guide
   Pre-populated responses for affidavit completion.

REQUIRED ACTIONS:

1. Complete third-party agency freezes (estimated: 20-30 minutes)
2. File FTC Identity Theft Report at identitytheft.gov
3. File police report using provided instructions
4. Complete and notarize required affidavit(s)

Upon completion, provide:
- FTC Report Number
- Police Case Number
- Police Department Name
- Filing Date
- Notarized Affidavit(s)

Phase 2 documentation will be generated upon receipt of these items.
```

---

# PHASE 2: DISPUTE SUBMISSION DOCUMENTATION

## Input Requirements
- FTC Report Number
- Police Case Number
- Police Department Name
- Filing Date
- Notarized Affidavit(s)
- Submission Method Preference (Online / Certified Mail)

## Output Deliverables
- Documents 5-7: Bureau Dispute Letters (TransUnion, Experian, Equifax)
- Document 8: Online Submission Guide
- Document 9: Certified Mail Checklist
- Document 10: Telephone Follow-Up Scripts
- Document 11: Compliance Tracking Worksheet
- Document 12: CFPB Escalation Procedure
- Document 13: Reinsertion Dispute Procedure
- Document 14: BBB Dispute Strategy (for collection accounts)

---

## PHASE 2 — DOCUMENT TEMPLATES

### DOCUMENT 5: Bureau_Letter_TransUnion_[CLIENT].md

```markdown
________________________________________________________________________________

                    FCRA SECTION 605B BLOCK REQUEST — TRANSUNION

________________________________________________________________________________

[DATE]

[CLIENT NAME]
[CLIENT ADDRESS]
[CITY], [STATE] [ZIP]

TransUnion
Fraud Victim Assistance Department
P.O. Box 2000
Chester, PA 19016

RE: Identity Theft Block Request
    Account Reference: [ACCOUNT NUMBER]

Dear Sir or Madam:

I am a victim of identity theft. The information referenced below, which
appears on my consumer credit file, does not relate to any transaction that
I authorized. This account is the result of identity theft.

DISPUTED ACCOUNT:
Creditor:        [CREDITOR NAME]
Account Number:  [ACCOUNT NUMBER]

Pursuant to Section 605B of the Fair Credit Reporting Act (15 U.S.C.
Section 1681c-2), I hereby request that you block the reporting of any
information resulting from this identity theft within four (4) business
days of receipt of this request.

ENCLOSED DOCUMENTATION:

1. Copy of consumer credit report with fraudulent item identified
2. FTC Identity Theft Report (Report No. [FTC NUMBER])
3. Police Report (Case No. [CASE NUMBER], [DEPARTMENT], [DATE])
4. Notarized Identity Theft Affidavit
5. Copy of government-issued identification
6. Copy of Social Security card
7. Proof of current residence
8. FCRA Section 605B statutory reference

The Fair Credit Reporting Act requires you to block this fraudulent
information within four (4) business days and to notify all furnishers
of this information of the block.

I appreciate your prompt attention to this matter.

Respectfully,


_________________________________
[CLIENT NAME]

Enclosures: As stated

________________________________________________________________________________
```

---

### DOCUMENT 6: Bureau_Letter_Experian_[CLIENT].md

```markdown
________________________________________________________________________________

                    FCRA SECTION 605B BLOCK REQUEST — EXPERIAN

________________________________________________________________________________

[DATE]

[CLIENT NAME]
[CLIENT ADDRESS]
[CITY], [STATE] [ZIP]

Experian
P.O. Box 9554
Allen, TX 75013

RE: Identity Theft Block Request
    Account Reference: [ACCOUNT NUMBER]

Dear Sir or Madam:

I am a victim of identity theft. The information referenced below, which
appears on my consumer credit file, does not relate to any transaction that
I authorized. This account is the result of identity theft.

DISPUTED ACCOUNT:
Creditor:        [CREDITOR NAME]
Account Number:  [ACCOUNT NUMBER]

Pursuant to Section 605B of the Fair Credit Reporting Act (15 U.S.C.
Section 1681c-2), I hereby request that you block the reporting of any
information resulting from this identity theft within four (4) business
days of receipt of this request.

ENCLOSED DOCUMENTATION:

1. Copy of consumer credit report with fraudulent item identified
2. FTC Identity Theft Report (Report No. [FTC NUMBER])
3. Police Report (Case No. [CASE NUMBER], [DEPARTMENT], [DATE])
4. Notarized Identity Theft Affidavit
5. Copy of government-issued identification
6. Copy of Social Security card
7. Proof of current residence
8. FCRA Section 605B statutory reference

The Fair Credit Reporting Act requires you to block this fraudulent
information within four (4) business days and to notify all furnishers
of this information of the block.

I appreciate your prompt attention to this matter.

Respectfully,


_________________________________
[CLIENT NAME]

Enclosures: As stated

________________________________________________________________________________
```

---

### DOCUMENT 7: Bureau_Letter_Equifax_[CLIENT].md

```markdown
________________________________________________________________________________

                    FCRA SECTION 605B BLOCK REQUEST — EQUIFAX

________________________________________________________________________________

[DATE]

[CLIENT NAME]
[CLIENT ADDRESS]
[CITY], [STATE] [ZIP]

Equifax
P.O. Box 105069
Atlanta, GA 30348-5069

RE: Identity Theft Block Request
    Account Reference: [ACCOUNT NUMBER]

Dear Sir or Madam:

I am a victim of identity theft. The information referenced below, which
appears on my consumer credit file, does not relate to any transaction that
I authorized. This account is the result of identity theft.

DISPUTED ACCOUNT:
Creditor:        [CREDITOR NAME]
Account Number:  [ACCOUNT NUMBER]

Pursuant to Section 605B of the Fair Credit Reporting Act (15 U.S.C.
Section 1681c-2), I hereby request that you block the reporting of any
information resulting from this identity theft within four (4) business
days of receipt of this request.

ENCLOSED DOCUMENTATION:

1. Copy of consumer credit report with fraudulent item identified
2. FTC Identity Theft Report (Report No. [FTC NUMBER])
3. Police Report (Case No. [CASE NUMBER], [DEPARTMENT], [DATE])
4. Notarized Identity Theft Affidavit
5. Copy of government-issued identification
6. Copy of Social Security card
7. Proof of current residence
8. FCRA Section 605B statutory reference

The Fair Credit Reporting Act requires you to block this fraudulent
information within four (4) business days and to notify all furnishers
of this information of the block.

I appreciate your prompt attention to this matter.

Respectfully,


_________________________________
[CLIENT NAME]

Enclosures: As stated

________________________________________________________________________________
```

---

### DOCUMENT 8: Online_Submission_Guide_[CLIENT].md

```markdown
________________________________________________________________________________

                    ONLINE DISPUTE SUBMISSION PROCEDURES

________________________________________________________________________________

Client:         [CLIENT NAME]
Generated:      [DATE]
Method:         Electronic Submission

________________________________________________________________________________

SUBMISSION OVERVIEW

Online submission through bureau portals typically results in faster
resolution (24 hours to 30 days). Each account must be disputed separately
with each bureau where it appears.

NOTE: Repeat this process for EACH account and EACH bureau combination.

________________________________________________________________________________

SECTION A: PORTAL REGISTRATION

If you do not have existing accounts with each bureau, create them prior
to dispute submission.

EXPERIAN
Portal:     https://www.experian.com/upload
            OR https://usa.experian.com
Action:     Create account or log in; complete identity verification

EQUIFAX
Portal:     https://www.equifax.com/personal/disputes
            OR https://my.equifax.com
Action:     Create myEquifax account; complete identity verification

TRANSUNION
Portal:     https://www.transunion.com/dispute
            OR https://service.transunion.com
Action:     Create account or log in; complete identity verification

________________________________________________________________________________

SECTION B: REQUIRED DOCUMENT UPLOADS

For each dispute submission, prepare digital copies of:

[ ] FTC Identity Theft Report PDF
[ ] Police Report (or confirmation with case number)
[ ] Notarized Identity Theft Affidavit
[ ] Government-issued photo identification (front and back)
[ ] Social Security card
[ ] Proof of current address (utility bill, bank statement, or phone bill)
[ ] Bureau-specific dispute letter

________________________________________________________________________________

SECTION C: SUBMISSION PROCEDURES

EXPERIAN

1. Log in to your Experian account
2. Navigate to: Help Center > Start New Dispute
3. Locate account: [CREDITOR NAME]
4. Select dispute reason: "Identity theft" or "Fraudulent account"
5. Upload all supporting documentation
6. In the comments section, enter:

   ----------------------------------------------------------------
   I am a victim of identity theft. This account was opened
   fraudulently without my knowledge or consent. Enclosed please
   find my FTC Identity Theft Report, Police Report (Case No.
   [CASE NUMBER]), and Notarized Affidavit. Pursuant to FCRA
   Section 605B, I request this account be blocked within four
   (4) business days.
   ----------------------------------------------------------------

7. Submit and capture confirmation screen
8. Record confirmation number: _____________________

________________________________________________________________________________

EQUIFAX

1. Log in to your Equifax account
2. Navigate to: Credit Report > [Locate Account]
3. Select: "Dispute this account"
4. Select reason: "This is not my account" or "Identity theft/fraud"
5. Upload all supporting documentation
6. In the comments section, enter the same statement as above
7. Submit and capture confirmation screen
8. Record confirmation number: _____________________

________________________________________________________________________________

TRANSUNION

1. Log in to your TransUnion account
2. Select: Start New Dispute
3. Locate account: [CREDITOR NAME]
4. When asked "Disputed in past 120 days?": Select "No"
5. Select reason: "Identity theft / fraudulent account"
6. Select: "Other, provide details"
7. Upload all supporting documentation
8. In the comments section, enter the same statement as above
9. Submit and capture confirmation screen
10. Record confirmation number: _____________________

________________________________________________________________________________

SECTION D: SUBMISSION TRACKING

+-------------+----------------------+------------------+
| Bureau      | Confirmation Number  | Submission Date  |
+-------------+----------------------+------------------+
| Experian    |                      |                  |
+-------------+----------------------+------------------+
| Equifax     |                      |                  |
+-------------+----------------------+------------------+
| TransUnion  |                      |                  |
+-------------+----------------------+------------------+

________________________________________________________________________________

IMPORTANT REMINDERS

1. Submit separate disputes for each account at each bureau where reported
2. Capture screenshots of all confirmation pages
3. Telephone follow-up is recommended 5 business days after submission
   (refer to Document 10: Telephone Follow-Up Scripts)

________________________________________________________________________________
```

---

### DOCUMENT 9: Certified_Mail_Checklist_[CLIENT].md

```markdown
________________________________________________________________________________

                    CERTIFIED MAIL SUBMISSION CHECKLIST

________________________________________________________________________________

Client:         [CLIENT NAME]
Generated:      [DATE]
Method:         USPS Certified Mail with Return Receipt

________________________________________________________________________________

ENVELOPE REQUIREMENTS

Send a SEPARATE envelope to each bureau where the disputed account appears.

REQUIRED ENVELOPES:

+-------------+------------------+------------------+
| Bureau      | Account Reported | Envelope Required|
+-------------+------------------+------------------+
| TransUnion  | [CREDITOR]       | [ ] Yes  [ ] No  |
+-------------+------------------+------------------+
| Experian    | [CREDITOR]       | [ ] Yes  [ ] No  |
+-------------+------------------+------------------+
| Equifax     | [CREDITOR]       | [ ] Yes  [ ] No  |
+-------------+------------------+------------------+

________________________________________________________________________________

CONTENTS PER ENVELOPE

Each envelope must contain the following documents:

DISPUTE DOCUMENTATION
[ ] Bureau-specific dispute letter (Documents 5, 6, or 7)
[ ] FTC Identity Theft Report PDF
[ ] Police Report copy (Case No. [CASE NUMBER])
[ ] Notarized Identity Theft Affidavit (for this bureau)
[ ] FCRA Section 605B statutory text (1 page)

IDENTITY VERIFICATION
[ ] Copy of driver's license (front and back)
[ ] Copy of Social Security card

PROOF OF RESIDENCE (include one)
[ ] Utility bill (showing name and current address)
[ ] Bank statement (showing name and current address)
[ ] Phone bill (showing name and current address)

CREDIT REPORT
[ ] Page(s) showing disputed account(s) with item(s) circled/highlighted

________________________________________________________________________________

MAILING ADDRESSES

TRANSUNION
Fraud Victim Assistance Department
P.O. Box 2000
Chester, PA 19016

EXPERIAN
P.O. Box 9554
Allen, TX 75013

EQUIFAX
P.O. Box 105069
Atlanta, GA 30348-5069

________________________________________________________________________________

MAILING INSTRUCTIONS

1. Use USPS Certified Mail with Return Receipt Requested
2. Retain certified mail receipt with tracking number
3. Retain green return receipt card when returned
4. Record tracking numbers below

________________________________________________________________________________

TRACKING RECORD

+-------------+----------------------+--------------+--------------+
| Bureau      | Tracking Number      | Date Mailed  | Receipt Date |
+-------------+----------------------+--------------+--------------+
| TransUnion  |                      |              |              |
+-------------+----------------------+--------------+--------------+
| Experian    |                      |              |              |
+-------------+----------------------+--------------+--------------+
| Equifax     |                      |              |              |
+-------------+----------------------+--------------+--------------+

________________________________________________________________________________
```

---

### DOCUMENT 10: Telephone_Scripts_[CLIENT].md

```markdown
________________________________________________________________________________

                         TELEPHONE FOLLOW-UP PROCEDURES

________________________________________________________________________________

Client:         [CLIENT NAME]
Timing:         5 business days after dispute submission

________________________________________________________________________________

PREPARATION

Before calling, have the following information readily available:

- Account Name:      [CREDITOR NAME]
- Account Number:    [ACCOUNT NUMBER]
- Police Case No.:   [CASE NUMBER]
- Social Security Number
- Date of Birth
- Current Address
- All dispute documentation

________________________________________________________________________________

EXPERIAN

Telephone:      1-855-414-6048  (alternate: 1-877-870-5640)
Call Timing:    5 business days after submission
Duration:       Approximately 20 minutes

NAVIGATION PROCEDURE:

1. Enter Social Security Number when prompted
2. Enter ZIP Code when prompted
3. Voice prompt: State "Fraud"
4. Voice prompt: State "Start a Dispute"
5. Voice prompt: State "Identity Theft" (or press 3)
6. Confirm you are a victim of identity theft
7. Request transfer to "Fraud Department" (may need to repeat)
8. Correct department identification: "Special Services"
9. DECLINE if offered fraud alert placement

STATEMENT TO REPRESENTATIVE:

"I am calling regarding an identity theft dispute I recently submitted.
I am a victim of identity theft and have a fraudulent account on my
credit report that I need removed. I submitted documentation including
a police report, FTC Identity Theft Report, and notarized affidavit.
The account is [CREDITOR NAME], account number [ACCOUNT NUMBER]. My
police report case number is [CASE NUMBER]. I am requesting this
account be blocked pursuant to FCRA Section 605B."

KEY PHRASES:
- "I do not recognize this account"
- "This account is fraudulent"
- "I have documentation proving identity theft"
- "I am requesting a 605B block"

Request confirmation that the account will be blocked.

________________________________________________________________________________

EQUIFAX

Telephone:      1-800-525-6285
Call Timing:    5 business days after submission
Duration:       Approximately 15 minutes

NAVIGATION PROCEDURE:

1. Follow voice prompts to reach a representative
2. Request the fraud/identity theft department if not automatically routed

STATEMENT TO REPRESENTATIVE:

Use the same statement as provided for Experian above.

Request confirmation that the account will be blocked.

________________________________________________________________________________

TRANSUNION

Telephone:      1-800-916-8800
Call Timing:    6 business days after submission
Duration:       Approximately 30 minutes (longest wait time)

NAVIGATION PROCEDURE:

1. Press 1 for English
2. Voice prompt: State "Dispute"
3. Voice prompt: State "Yes" to confirm
4. Do NOT press 1 to follow up on existing dispute
5. Do NOT press 1 for text message options
6. Wait for live representative (press # if prompted for text)

STATEMENT TO REPRESENTATIVE:

Use the same statement as provided for Experian above.

Request confirmation that the account will be blocked.

________________________________________________________________________________

IF INITIAL CALL IS UNSUCCESSFUL:

1. End the call professionally
2. Call again immediately and speak with a different representative
3. Request a supervisor if the representative is unable to assist
4. Document each call: date, time, representative name, outcome
5. Continue attempts on subsequent business days if necessary

________________________________________________________________________________

CALL LOG

+-------------+----------+--------+------------------+------------------+
| Bureau      | Date     | Time   | Representative   | Outcome          |
+-------------+----------+--------+------------------+------------------+
| Experian    |          |        |                  |                  |
+-------------+----------+--------+------------------+------------------+
| Equifax     |          |        |                  |                  |
+-------------+----------+--------+------------------+------------------+
| TransUnion  |          |        |                  |                  |
+-------------+----------+--------+------------------+------------------+

________________________________________________________________________________
```

---

### DOCUMENT 11: Compliance_Tracking_[CLIENT].md

```markdown
________________________________________________________________________________

                    SECTION 605B COMPLIANCE TRACKING WORKSHEET

________________________________________________________________________________

Client:         [CLIENT NAME]
Case Reference: 5DKO-[CLIENT_ID]-[DATE]

________________________________________________________________________________

SECTION 1: CASE INFORMATION

+------------------------+---------------------------------------------+
| Client Name            | [CLIENT NAME]                               |
+------------------------+---------------------------------------------+
| FTC Report Number      | [FTC NUMBER]                                |
+------------------------+---------------------------------------------+
| Police Case Number     | [CASE NUMBER]                               |
+------------------------+---------------------------------------------+
| Police Department      | [DEPARTMENT NAME]                           |
+------------------------+---------------------------------------------+
| Police Report Date     | [DATE]                                      |
+------------------------+---------------------------------------------+

________________________________________________________________________________

SECTION 2: DISPUTED ACCOUNTS

+------------------+---------------+------------------+
| Creditor         | Account No.   | Bureaus          |
+------------------+---------------+------------------+
| [CREDITOR]       | [ACCOUNT #]   | [TU / EX / EQ]   |
+------------------+---------------+------------------+

________________________________________________________________________________

SECTION 3: PHASE 1 COMPLETION

+--------------------------------------+----------+-------------+
| Action Item                          | Status   | Date        |
+--------------------------------------+----------+-------------+
| LexisNexis freeze placed             | [ ]      |             |
+--------------------------------------+----------+-------------+
| Teletrack freeze placed              | [ ]      |             |
+--------------------------------------+----------+-------------+
| Innovis freeze placed                | [ ]      |             |
+--------------------------------------+----------+-------------+
| FTC Identity Theft Report filed      | [ ]      |             |
+--------------------------------------+----------+-------------+
| CFPB complaints filed (3 bureaus)    | [ ]      |             |
+--------------------------------------+----------+-------------+
| Police report filed                  | [ ]      |             |
+--------------------------------------+----------+-------------+
| Affidavit(s) notarized               | [ ]      |             |
+--------------------------------------+----------+-------------+

________________________________________________________________________________

SECTION 4: PHASE 2 COMPLETION

+--------------------------------------+----------+-------------+
| Action Item                          | Status   | Date        |
+--------------------------------------+----------+-------------+
| Bureau letters prepared              | [ ]      |             |
+--------------------------------------+----------+-------------+
| Disputes submitted to bureaus        | [ ]      |             |
+--------------------------------------+----------+-------------+
| Submission method used               | [ ] Online  [ ] Mail   |
+--------------------------------------+----------+-------------+

________________________________________________________________________________

SECTION 5: BUREAU SUBMISSION TRACKING

+-------------+-----------+---------------+----------+-----------+
| Bureau      | Method    | Reference No. | Sent     | Received  |
+-------------+-----------+---------------+----------+-----------+
| TransUnion  | [ ]Online |               |          |           |
|             | [ ]Mail   |               |          |           |
+-------------+-----------+---------------+----------+-----------+
| Experian    | [ ]Online |               |          |           |
|             | [ ]Mail   |               |          |           |
+-------------+-----------+---------------+----------+-----------+
| Equifax     | [ ]Online |               |          |           |
|             | [ ]Mail   |               |          |           |
+-------------+-----------+---------------+----------+-----------+

________________________________________________________________________________

SECTION 6: COMPLIANCE TIMELINE

+------+----------------------------------------+----------+----------+
| Day  | Action Required                        | Due Date | Complete |
+------+----------------------------------------+----------+----------+
| 0    | File FTC Report at identitytheft.gov   |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 0    | File CFPB complaints (all 3 bureaus)   |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 0-1  | File police report (online or in-person)|         | [ ]      |
+------+----------------------------------------+----------+----------+
| 1-2  | Submit 605B letters to bureaus         |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 4    | 605B statutory deadline (4 bus. days)  |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 5-6  | Phone follow-up with bureaus           |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 7    | Pull credit reports to verify removal  |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 10   | BBB complaint (if collection account)  |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 15   | CFPB response deadline (federal req.)  |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 30   | Confirm removal across all bureaus     |          | [ ]      |
+------+----------------------------------------+----------+----------+
| 45   | Monitor for potential reinsertion      |          | [ ]      |
+------+----------------------------------------+----------+----------+

________________________________________________________________________________

SECTION 7: RESULTS

+-------------+-----------------------+-------------+
| Bureau      | Result                | Date        |
+-------------+-----------------------+-------------+
| TransUnion  | [ ] Blocked           |             |
|             | [ ] Denied            |             |
|             | [ ] Pending           |             |
+-------------+-----------------------+-------------+
| Experian    | [ ] Blocked           |             |
|             | [ ] Denied            |             |
|             | [ ] Pending           |             |
+-------------+-----------------------+-------------+
| Equifax     | [ ] Blocked           |             |
|             | [ ] Denied            |             |
|             | [ ] Pending           |             |
+-------------+-----------------------+-------------+

________________________________________________________________________________

SECTION 8: ESCALATION REFERENCE

If block request denied or item reinserted:
- 2nd CFPB Complaint: Refile citing bureau's failure to comply
- Reinsertion Dispute: Document 13 (FCRA §611 violation)
- BBB Strategy (collections): Document 14
- State Attorney General complaint
- FCRA litigation consultation

________________________________________________________________________________
```

---

### DOCUMENT 12: CFPB_Complaint_[CLIENT].md

```markdown
________________________________________________________________________________

                    CFPB COMPLAINT INSTRUCTIONS

________________________________________________________________________________

Client:         [CLIENT NAME]
Timing:         File IMMEDIATELY after FTC Report (same day recommended)

Portal:         https://www.consumerfinance.gov/complaint

IMPORTANT: File SEPARATE complaints for each bureau where accounts appear.
Complete this process for TransUnion, Experian, AND Equifax.

________________________________________________________________________________

STEP-BY-STEP INSTRUCTIONS

Navigate to https://www.consumerfinance.gov/complaint
Click "Submit a complaint"

________________________________________________________________________________

STEP 1 OF 5: PRODUCT SELECTION

"What is this complaint about?"
Select: Credit reporting or other personal consumer reports

"What type of credit reporting product?"
Select: Credit reporting

Click Next

________________________________________________________________________________

STEP 2 OF 5: PROBLEM TYPE

"What type of problem are you having?"
Select: Incorrect information on your report
        (account or personal information incorrect, information not mine)

"Which best describes your problem?"
Select: Account information incorrect
        OR: Information belongs to someone else

"Have you already tried to fix this problem with the company?"
Select: Yes

Click Next

________________________________________________________________________________

STEP 3 OF 5: WHAT HAPPENED

"Describe what happened"

Include dates, amounts, and actions. Do NOT include SSN, account numbers,
or addresses in the narrative.

COPY AND CUSTOMIZE:

I am a victim of identity theft. The following account(s) were opened
fraudulently using my personal information without my knowledge,
authorization, or consent:

[CREDITOR NAME 1] - Account opened [DATE]
[CREDITOR NAME 2] - Account opened [DATE]

I have filed an FTC Identity Theft Report (Report #[FTC NUMBER]) and a
police report (Case #[CASE NUMBER], [POLICE DEPARTMENT]) documenting
this fraud.

Pursuant to FCRA Section 605B (15 U.S.C. § 1681c-2), I demand that
[BUREAU NAME] block all information resulting from this identity theft
within four (4) business days of receipt of my Identity Theft Report.

This fraudulent account is negatively impacting my credit score and
ability to obtain credit.

--------------------------------------------------------------------------------

"What would be a fair resolution to this issue?"

COPY AND CUSTOMIZE:

Immediately block and permanently delete the following fraudulent
account(s) from my credit report: [CREDITOR NAME] - Account #[LAST 4].
Provide written confirmation of deletion within 15 days.

--------------------------------------------------------------------------------

"Attach documents" (optional but recommended)

Upload your FTC Identity Theft Report PDF

Click Next

________________________________________________________________________________

STEP 4 OF 5: COMPANY INFORMATION

"What company is this complaint about?"

Type the bureau name:
- For TransUnion: TransUnion
- For Experian: Experian
- For Equifax: Equifax

"We need this information to help the company find you in their system"

Check these boxes:
[X] Social Security number (last 4 digits)
[X] Date of birth
[X] Name as it appears on credit report

Enter:
- SSN (last 4): [XXXX]
- Date of birth: [MM] / [DD] / [YYYY]
- Name on credit report: [YOUR FULL NAME]

"Do you want to complain about another company?"
Select: No

Click Next

________________________________________________________________________________

STEP 5 OF 5: YOUR INFORMATION

"Who are you submitting this complaint for?"
Select: Myself

Verify your contact information:
- Name
- Phone number
- Email address
- Country: United States
- Address
- City, State, ZIP

"Preferred Language" (optional): English

Skip demographic information or complete if desired.

Click Review

________________________________________________________________________________

REVIEW AND SUBMIT

Review Steps 1-5 for accuracy.

Check the required boxes:
[X] "I authorize and direct (1) the consumer reporting agency identified
     in my complaint to share determinations of and actions taken..."
[X] "The information given is true to the best of my knowledge..."

Click "Submit your complaint"

________________________________________________________________________________

AFTER SUBMISSION

- Save your CFPB complaint confirmation number immediately
- The bureau MUST respond within 15 days
- Log in to consumerfinance.gov to track complaint status
- You will receive email updates

REPEAT THIS ENTIRE PROCESS for each additional bureau.

________________________________________________________________________________

COMPLAINT TRACKING

+-------------+--------------------+------------------+
| Bureau      | CFPB Case Number   | Submission Date  |
+-------------+--------------------+------------------+
| TransUnion  |                    |                  |
+-------------+--------------------+------------------+
| Experian    |                    |                  |
+-------------+--------------------+------------------+
| Equifax     |                    |                  |
+-------------+--------------------+------------------+

________________________________________________________________________________
```

---

### DOCUMENT 13: Reinsertion_Dispute_[CLIENT].md

```markdown
________________________________________________________________________________

                    REINSERTION VIOLATION DISPUTE PROCEDURE

________________________________________________________________________________

Client:         [CLIENT NAME]
Applicable Law: 15 U.S.C. Section 1681i(a)(5)(B)(ii)

Use this procedure if a previously deleted item reappears on your
credit report.

________________________________________________________________________________

LEGAL BASIS

Under FCRA Section 611(a)(5)(B)(ii), when a consumer reporting agency
deletes an item from a consumer's file, the agency may not reinsert
that information unless:

1. The furnisher certifies that the information is complete and accurate
2. The agency provides written notice to the consumer within five (5)
   business days of the reinsertion

If notification was not received, the reinsertion constitutes a
statutory violation requiring immediate deletion.

________________________________________________________________________________

SECTION 1: CASE INFORMATION

+--------------------------------+------------------------------------+
| Consumer Name                  | [CLIENT NAME]                      |
+--------------------------------+------------------------------------+
| Current Address                | [ADDRESS]                          |
+--------------------------------+------------------------------------+
| Social Security Number         | [SSN]                              |
+--------------------------------+------------------------------------+
| Date of Birth                  | [DOB]                              |
+--------------------------------+------------------------------------+

ACCOUNT INFORMATION:

+--------------------------------+------------------------------------+
| Creditor Name                  | [CREDITOR]                         |
+--------------------------------+------------------------------------+
| Account Number                 | [ACCOUNT NUMBER]                   |
+--------------------------------+------------------------------------+
| Approximate Deletion Date      | [DATE]                             |
+--------------------------------+------------------------------------+
| Reinsertion Date               | [DATE DISCOVERED]                  |
+--------------------------------+------------------------------------+

________________________________________________________________________________

SECTION 2: REINSERTION DISPUTE LETTER

--------------------------------------------------------------------------------

[DATE]

[YOUR NAME]
[YOUR ADDRESS]
[CITY, STATE ZIP]

[CREDIT BUREAU NAME]
[BUREAU ADDRESS]

RE: Reinsertion Violation — 15 U.S.C. Section 1681i(a)(5)(B)(ii)

Dear Sir or Madam:

I am writing to report a violation of the Fair Credit Reporting Act.

The following account was previously deleted from my consumer credit file:

ACCOUNT:         [CREDITOR NAME]
ACCOUNT NUMBER:  [ACCOUNT NUMBER]

I have discovered that this account has been reinserted onto my credit
report WITHOUT the required written notice within five (5) business days
as mandated by 15 U.S.C. Section 1681i(a)(5)(B)(ii).

Under FCRA Section 611(a)(5)(B)(ii), a consumer reporting agency that has
deleted an item of information from a consumer's file must provide written
notice to the consumer within five (5) business days of any reinsertion of
that information.

I did not receive this required notice.

DEMAND FOR RELIEF:

1. Immediately DELETE this improperly reinserted account from my file
2. Provide written confirmation of deletion within fifteen (15) days
3. Send required notifications to all furnishers of this information

Failure to comply may result in:
- Complaint to the Consumer Financial Protection Bureau
- Complaint to the State Attorney General
- Private legal action for willful FCRA violations

Enclosed: Copy of government-issued identification, Social Security card,
and proof of current residence.

Respectfully,


_________________________________
[YOUR NAME]

Enclosures: As stated

--------------------------------------------------------------------------------

________________________________________________________________________________

SECTION 3: SUBMISSION OPTIONS

ONLINE SUBMISSION (Fastest):
- Experian: https://www.experian.com/upload
- Equifax:  https://www.equifax.com/personal/disputes
- TransUnion: https://www.transunion.com/dispute

CERTIFIED MAIL (Recommended for documentation):
- Experian: P.O. Box 4500, Allen, TX 75013
- Equifax: P.O. Box 740256, Atlanta, GA 30374
- TransUnion: P.O. Box 2000, Chester, PA 19016

________________________________________________________________________________

SECTION 4: FOLLOW-UP

72 hours after submission, call to confirm receipt:
- Experian: 1-888-397-3742
- Equifax: 1-800-685-1111
- TransUnion: 1-800-916-8800

If not resolved within 30-45 days:
1. File CFPB complaint at consumerfinance.gov/complaint
2. Contact State Attorney General consumer protection division
3. Consult with FCRA attorney regarding potential litigation

________________________________________________________________________________
```

---

### DOCUMENT 14: BBB_Dispute_Strategy_[CLIENT].md

```markdown
________________________________________________________________________________

                    BETTER BUSINESS BUREAU DISPUTE STRATEGY

________________________________________________________________________________

Client:         [CLIENT NAME]
Applicable To:  Collection accounts, debt buyers, third-party accounts

This strategy leverages BBB complaint processes to expedite removal of
collection accounts. Resolution may occur within 24-72 hours.

________________________________________________________________________________

SECTION 1: ACCOUNT INFORMATION

+--------------------------------+------------------------------------+
| Collection Agency Name         | [COLLECTION AGENCY]                |
|   (as shown on credit report)  |                                    |
+--------------------------------+------------------------------------+
| Original Creditor              | [ORIGINAL CREDITOR]                |
+--------------------------------+------------------------------------+
| Account Number                 | [ACCOUNT NUMBER]                   |
+--------------------------------+------------------------------------+
| Balance                        | $[AMOUNT]                          |
+--------------------------------+------------------------------------+
| Date Opened                    | [DATE]                             |
+--------------------------------+------------------------------------+

________________________________________________________________________________

SECTION 2: BBB COMPLAINT PROCEDURE

Navigate to: https://www.bbb.org

1. Select: "File a Complaint" (top navigation)

2. Select: "I'd like to file a complaint against a business, and have
           BBB help me get a resolution"

3. Select: "File a Complaint"

4. Search for business: [COLLECTION AGENCY NAME]
   (Use exact name as shown on credit report)

   NOTE: If the agency is not registered with BBB, proceed directly to
   Section 3 (bureau disputes) as letter disputes may be more effective.

5. Answer preliminary questions:

   +----------------------------------------+--------------------+
   | Question                               | Response           |
   +----------------------------------------+--------------------+
   | Buyer's remorse?                       | No                 |
   +----------------------------------------+--------------------+
   | Employee/employer complaint?           | No                 |
   +----------------------------------------+--------------------+
   | Discrimination/civil rights?           | No                 |
   +----------------------------------------+--------------------+
   | Seeking criminal penalty?              | No                 |
   +----------------------------------------+--------------------+
   | Filed in court?                        | No                 |
   +----------------------------------------+--------------------+
   | Business collecting from business?     | No                 |
   +----------------------------------------+--------------------+
   | Within last 12 months?                 | Yes                |
   +----------------------------------------+--------------------+
   | Health-related issue?                  | No                 |
   +----------------------------------------+--------------------+

6. In "Tell Us About Your Problem" section, enter:

   --------------------------------------------------------------------
   I am not liable for this debt with [ORIGINAL CREDITOR NAME]. I do
   not have a contractual relationship with [COLLECTION AGENCY NAME].
   Upon request, they have failed to provide me with the original
   signed contract as required for debt validation.
   --------------------------------------------------------------------

7. For "Desired Resolution":
   - Select: "Other (requires explanation)"
   - Enter: "Correction to my credit report. I demand this account be
            removed from my credit report."

8. Complete remaining fields and submit

________________________________________________________________________________

SECTION 3: BUREAU DISPUTE FOLLOWING BBB COMPLAINT

After BBB complaint submission, file disputes with each bureau where
the collection account appears.

EXPERIAN — https://usa.experian.com

1. Log in and navigate to credit report
2. Locate collection account
3. Select: "Dispute this account"
4. Select reason: "Not mine" or "No knowledge of account"
5. In comments section, enter:

   --------------------------------------------------------------------
   I am not liable for this debt with [ORIGINAL CREDITOR NAME]. I do
   not have a contractual relationship with [COLLECTION AGENCY NAME].
   They have failed to provide the original signed contract as
   requested for debt validation.
   --------------------------------------------------------------------

6. Submit and record confirmation number

IMPORTANT: Wait for Experian result before proceeding to other bureaus.

________________________________________________________________________________

TRANSUNION — https://service.transunion.com

1. Log in and select: "Start new dispute"
2. Locate collection account
3. "Disputed in past 120 days?": Select "No"
4. Select reason: "It is inaccurate"
5. Select: "Other, provide details"
6. Enter same statement as above
7. Submit and record confirmation number

________________________________________________________________________________

EQUIFAX — https://my.equifax.com

1. Log in and navigate to credit report
2. Locate collection account
3. Select: "Dispute this account"
4. Enter same statement as above
5. Submit and record confirmation number

________________________________________________________________________________

SECTION 4: EXPECTED TIMELINE

+------+------------------------------------------------+
| Day  | Expected Action                                |
+------+------------------------------------------------+
| 0    | Submit BBB complaint                           |
+------+------------------------------------------------+
| 1-3  | Collection agency responds to BBB              |
+------+------------------------------------------------+
| 1-7  | Submit credit bureau disputes                  |
+------+------------------------------------------------+
| 7-30 | Account removal (often faster)                 |
+------+------------------------------------------------+

________________________________________________________________________________

STRATEGIC RATIONALE

1. BBB complaints are publicly visible, creating reputational pressure
2. The process establishes documented debt validation requests
3. Collection agencies frequently delete rather than engage in
   prolonged BBB dispute processes
4. Coordinated bureau disputes reinforce the validation challenge

________________________________________________________________________________
```

---

## PHASE 2 CLIENT COMMUNICATION

Upon completion of Phase 2 document generation, present the following summary:

```
Phase 2 documentation is complete.

DOCUMENTS GENERATED:

5-7.  Bureau Dispute Letters (TransUnion, Experian, Equifax)
8.    Online Submission Guide
9.    Certified Mail Checklist
10.   Telephone Follow-Up Scripts
11.   Compliance Tracking Worksheet
12.   CFPB Escalation Procedure
13.   Reinsertion Dispute Procedure
14.   BBB Dispute Strategy (for collection accounts)

RECOMMENDED EXECUTION SEQUENCE:

1. Select submission method:
   - Online submission: Faster resolution (Document 8)
   - Certified mail: Stronger documentation (Document 9)

2. Submit disputes to all applicable bureaus

3. After 5 business days: Conduct telephone follow-up (Document 10)

4. If not resolved by Day 7: File CFPB complaint (Document 12)

FOR COLLECTION ACCOUNTS:

Consider concurrent BBB complaint (Document 14). This strategy frequently
results in deletion within 24-72 hours.

IF ITEM REAPPEARS AFTER DELETION:

Use reinsertion dispute procedure (Document 13). Improper reinsertion
without notification constitutes a statutory violation requiring
automatic deletion.

COMPLIANCE DEADLINE:

FCRA Section 605B requires bureaus to block identity theft information
within four (4) business days of receiving a complete Identity Theft Report.
```

---

# DOCUMENT VERSION CONTROL

| Version | Date       | Description                                    |
|---------|------------|------------------------------------------------|
| 7.0     | 2026-02-05 | Professional enterprise formatting             |
|         |            | Removed all informal elements                  |
|         |            | Legal document structure implemented           |
|         |            | ASCII table formatting for compatibility       |

# END OF DOCUMENT
