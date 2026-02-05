# FCRA PROMPT 14: IDENTITY THEFT 5-DAY KNOCKOUT (SEPARATE FILES)
## Legitimate § 605B Package with RLPP Integration

**Version:** 1.0 (Separate File Output)
**Created:** January 9, 2026
**Use Case:** Real identity theft victims requiring full § 605B block + § 623 furnisher notice
**Output:** 14 separate files for complete identity theft remediation
**Integrates:** RLPP bundling + Standing documentation + Damages calculation

---

## ⚠️ CRITICAL: LEGITIMACY REQUIREMENT

**This prompt is ONLY for REAL identity theft victims.**

Before proceeding, staff MUST verify:
- Consumer did NOT open, authorize, or benefit from the disputed accounts
- Consumer has a legitimate identity theft claim (not just "I don't want to pay this")
- Consumer is willing to sign affidavit under penalty of perjury

**Filing false identity theft claims is a federal crime.** This prompt generates documents that will be submitted to law enforcement (police), federal agencies (FTC), and courts (notarized affidavit). False statements expose the consumer AND the firm to criminal liability.

---

## 📋 HOW TO USE:

**STEP 1:** Verify legitimacy (use screening checklist output)

**STEP 2:** Start new Claude chat

**STEP 3:** Upload credit report (PDF or PNG — all 3 bureaus)

**STEP 4:** Paste client info block + fraudulent accounts list (below)

**STEP 5:** Copy everything from "PROMPT STARTS HERE" and paste

**STEP 6:** Claude generates all documents as separate files

**STEP 7:** Download individual files from outputs folder

---

## 📝 CLIENT INFO TEMPLATE (Copy & Fill In):

```
CONSUMER INFORMATION:
- Full Name: [Full Legal Name]
- Current Address: [Address]
- City, State ZIP: [City, State ZIP]
- SSN Last 4: [XXXX]
- Date of Birth: [MM/DD/YYYY]
- Phone: [Phone]
- Email: [Email]
- Driver's License #: [License Number]
- DL State: [State]

FIRM INFORMATION:
- Firm Name: Brightpath Ascend Group
- Address: [Your Address]
- Phone: [Your Phone]
- Email: [Your Email]

CASE INFORMATION:
- Case File Number: [Your case number]
- Today's Date: [Date]
- Intake Date: [Date]

FRAUDULENT ACCOUNTS (List ALL - we generate letters for each):

Account 1:
- Creditor Name: [e.g., Capital One]
- Account Number (as shown on report): [XXXXXXXXXXXX1234]
- Account Type: [Credit Card / Auto Loan / Personal Loan / Collection / etc.]
- Date Opened (as shown on report): [MM/DD/YYYY]
- Balance/High Balance: [$X,XXX]
- Appears on which bureaus: [EX / EQ / TU or combination]

Account 2:
- Creditor Name: [e.g., Portfolio Recovery]
- Account Number (as shown on report): [XXXXXXXXXXXX5678]
- Account Type: [Collection]
- Date Opened (as shown on report): [MM/DD/YYYY]
- Balance/High Balance: [$X,XXX]
- Appears on which bureaus: [EX / EQ / TU]

[Add more accounts as needed - copy the format above]

RELATED FRAUDULENT INQUIRIES (if any):
- Inquiry 1: [Creditor Name] - [Date] - [Bureau]
- Inquiry 2: [Creditor Name] - [Date] - [Bureau]

HARM DOCUMENTATION (for standing):
- Has consumer been denied credit? [Yes/No]
- If yes, denial details: [Lender name, date, what they applied for]
- Denial letter available? [Yes/No]
- Other harm: [Increased rates, job denial, emotional distress, etc.]

IDENTITY THEFT DETAILS:
- When did consumer discover the fraud? [Date]
- How did consumer discover it? [Pulled credit report / received bill / collection call / etc.]
- Does consumer know how identity was stolen? [Data breach / lost wallet / family member / unknown]
- Has consumer filed police report yet? [Yes/No - if yes, provide case number]
- Has consumer filed FTC report yet? [Yes/No - if yes, provide report number]
```

---

## =======================================================================
## PROMPT STARTS HERE ⬇️ (COPY EVERYTHING BELOW)
## =======================================================================

===========================================================================
FCRA IDENTITY THEFT 5-DAY KNOCKOUT — SEPARATE FILE OUTPUT
WITH RLPP INTEGRATION, § 623 FURNISHER LETTERS, AND STANDING DOCUMENTATION
===========================================================================

**YOUR TASK:**

Generate a complete identity theft remediation package including:
1. Staff screening checklist (legitimacy verification)
2. Police report script
3. FTC Identity Theft Report answers (copy-paste ready)
4. FTC Affidavit pre-filled fields
5. § 605B letters to all 3 CRAs
6. § 623(a)(6) letters to each furnisher
7. Envelope checklist with enclosures
8. Timeline tracker with deadlines
9. Phone follow-up scripts
10. Standing documentation
11. Damages calculator (if violations occur)
12. Reinsertion dispute letter (if account comes back)

**CRITICAL: Use create_file tool to save EACH document as a separate file in /mnt/user-data/outputs/**

**FILE NAMING CONVENTION:**

```
01_Screening_Checklist_[LASTNAME]_[CASENUM].md
02_Police_Report_Script_[LASTNAME]_[CASENUM].md
03_FTC_Report_Answers_[LASTNAME]_[CASENUM].md
04_FTC_Affidavit_Fields_[LASTNAME]_[CASENUM].md
05_605B_Experian_[LASTNAME]_[CASENUM].md
06_605B_Equifax_[LASTNAME]_[CASENUM].md
07_605B_TransUnion_[LASTNAME]_[CASENUM].md
08_623_Furnisher_[CREDITOR]_[LASTNAME]_[CASENUM].md (one per creditor)
09_Envelope_Checklist_[LASTNAME]_[CASENUM].md
10_Timeline_Tracker_[LASTNAME]_[CASENUM].md
11_Phone_Scripts_[LASTNAME]_[CASENUM].md
12_Standing_Documentation_[LASTNAME]_[CASENUM].md
13_Damages_Calculator_[LASTNAME]_[CASENUM].md
14_Reinsertion_Letter_[LASTNAME]_[CASENUM].md
```

===========================================================================
FILE 1: SCREENING CHECKLIST (Staff Use Only)
===========================================================================

Generate a checklist for staff to verify legitimacy BEFORE proceeding.

```markdown
# IDENTITY THEFT SCREENING CHECKLIST
## Staff Use Only — Complete Before Generating Documents

**Client:** [Full Name]
**Case #:** [Case Number]
**Staff Member:** _______________
**Date Screened:** _______________

---

### SECTION A: LEGITIMACY VERIFICATION

Answer ALL questions. If ANY answer is "No" or "Red Flag," STOP and consult supervisor.

| # | Question | Answer | Notes |
|---|----------|--------|-------|
| 1 | Did consumer state they did NOT open, authorize, or benefit from disputed accounts? | ☐ Yes ☐ No | |
| 2 | Is consumer willing to sign affidavit UNDER PENALTY OF PERJURY? | ☐ Yes ☐ No | |
| 3 | Is consumer willing to file police report? | ☐ Yes ☐ No | |
| 4 | Does consumer's story make sense? (Timeline, discovery method, etc.) | ☐ Yes ☐ No | |
| 5 | Are the accounts consistent with identity theft? (Not just old debts) | ☐ Yes ☐ No | |

---

### SECTION B: RED FLAG CHECK

Check for these warning signs of FALSE identity theft claims:

| Red Flag | Present? | Notes |
|----------|----------|-------|
| Consumer previously acknowledged the debt | ☐ Yes ☐ No | |
| Consumer made payments on the account | ☐ Yes ☐ No | |
| Account address matches consumer's known addresses | ☐ Yes ☐ No | |
| Consumer received and used goods/services from account | ☐ Yes ☐ No | |
| Consumer seems coached or mentions "credit repair program" | ☐ Yes ☐ No | |
| Consumer only disputing accounts in collection/charged-off | ☐ Yes ☐ No | |
| Consumer can't explain how identity was stolen | ☐ Yes ☐ No | |

**If ANY red flags are checked "Yes," DO NOT PROCEED without supervisor approval.**

---

### SECTION C: DOCUMENT CHECKLIST

Consumer must provide:

| Document | Received? | Notes |
|----------|-----------|-------|
| Government-issued photo ID (driver's license or passport) | ☐ Yes ☐ No | |
| Social Security card OR W-2/SSA-1099 | ☐ Yes ☐ No | |
| Proof of current address (utility bill, bank statement) | ☐ Yes ☐ No | |
| Credit report showing fraudulent accounts | ☐ Yes ☐ No | |
| Denial letter(s) if available | ☐ Yes ☐ No | |

---

### SECTION D: APPROVAL

☐ **APPROVED TO PROCEED** — All legitimacy checks passed, documents received

☐ **HOLD** — Need additional verification: ________________________________

☐ **DECLINED** — Does not appear to be legitimate identity theft

**Staff Signature:** _______________  **Date:** _______________

**Supervisor Review (if required):** _______________  **Date:** _______________

---

⚠️ **WARNING:** Filing false identity theft reports is a federal crime. False police reports are crimes in every state. False FTC affidavits violate 18 U.S.C. § 1001. By proceeding, you confirm this case has been properly screened.
```

===========================================================================
FILE 2: POLICE REPORT SCRIPT
===========================================================================

Generate a script for the consumer to use at the police station.

```markdown
# POLICE REPORT SCRIPT
## Identity Theft Report — What to Say & Bring

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## WHAT TO BRING

☐ Driver's license or government-issued photo ID
☐ Credit report with fraudulent accounts circled/highlighted
☐ This script (for reference)
☐ Notepad to write down case number

---

## WHERE TO FILE

**Option 1 — Online (Fastest)**

Search Google for: `"identity theft police report [YOUR CITY]"` or `"online police report [YOUR STATE]"`

Many jurisdictions allow online filing for identity theft. You'll receive a case number via email.

**Option 2 — In Person**

Visit your local police precinct or sheriff's office. Ask for the front desk.

---

## WHAT TO SAY

When you reach the desk officer or online form, say/enter:

> "I'm here to file an identity theft report. I recently discovered fraudulent accounts on my credit report that I did not open. I'm working with the Federal Trade Commission and need a police report case number to complete their identity theft affidavit."

**If asked for details, provide:**

> "I discovered [NUMBER] fraudulent accounts on my credit report:
>
> 1. [CREDITOR 1] — Account #[LAST 4 DIGITS] — Opened [DATE] — Balance $[AMOUNT]
> 2. [CREDITOR 2] — Account #[LAST 4 DIGITS] — Opened [DATE] — Balance $[AMOUNT]
> [List all fraudulent accounts]
>
> I did not open these accounts. I did not authorize anyone to open them. I did not receive any goods, services, or money from them. This is identity theft."

**If asked how it happened:**

> "[Choose the applicable response]
> - I don't know how my identity was stolen
> - I believe it was from the [NAME] data breach
> - I lost my wallet/purse on [DATE]
> - I believe a family member may have used my information without permission
> - My mail was stolen"

**If they ask for more proof:**

> "The FTC instructs victims to obtain a police report case number. I have my credit report showing the fraudulent accounts. Under the voluntary 'Police Report Initiative,' credit bureaus will block accounts reported to law enforcement."

---

## CRITICAL: GET THE CASE NUMBER

Before leaving, make sure you have:

☐ **Police Report Case Number:** _______________
☐ **Date Filed:** _______________
☐ **Officer Name/Badge (if in person):** _______________
☐ **Department Name:** _______________

**You do NOT need a full printed report — just the case number.**

---

## WHAT TO DO AFTER

1. Write down the case number immediately
2. Call or text [FIRM PHONE] to confirm you have it
3. We will use this number for the FTC report and affidavit
4. Keep any receipt or confirmation for your records

---

## IF THEY WON'T TAKE THE REPORT

Some jurisdictions refuse identity theft reports. If this happens:

1. Ask: "Can you provide a case number or incident number for documentation purposes?"
2. Try a neighboring jurisdiction (city police vs. county sheriff)
3. File online through a different portal
4. Contact us — we have alternative documentation methods

---

## TIMELINE

Estimated time: 15-30 minutes in person, 5-10 minutes online

The police just need to log the incident. They won't investigate (identity theft is hard to prosecute). The purpose is to create an official record that triggers § 605B protections.
```

===========================================================================
FILE 3: FTC REPORT ANSWERS
===========================================================================

Generate copy-paste answers for identitytheft.gov.

```markdown
# FTC IDENTITY THEFT REPORT — COPY-PASTE ANSWERS
## For Use at IdentityTheft.gov

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## INSTRUCTIONS

1. Go to: **https://www.identitytheft.gov**
2. Click "Get Started"
3. Follow the prompts and copy-paste the answers below
4. **IMPORTANT:** Complete this process for EACH fraudulent account, for EACH bureau it appears on

---

## STEP-BY-STEP ANSWERS

**Which statement describes your situation?**
> "I want to report identity theft"

**What did the identity thief do?**
> Select: "Credit Card Accounts" (or appropriate category for each account)

**Tell us how your information was used:**
> "To open a fraudulent credit card account" (or appropriate description)

**Click: Continue**

**Credit card opened...**
> Select: "Account (as seen on your report)"

**When did you notice?**
> "[Month] [Year]" — (approximately one month before today)

**When was account opened?**
> "[Date as shown on credit report]"

**Estimate of total fraudulent charges:**
> "$[Balance as shown on report]"

**Account Number:**
> "[Full account number as shown on report including the Xs]"

**CAN ADD ADDITIONAL ACCOUNTS:**
> Select "Yes" and repeat for each fraudulent account
> You can submit up to 5 accounts per report
> If you have more than 5, submit a whole new FTC report

**Click: Continue**

**Your Information:**
> Complete with all your personal information

**Suspect info:**
> "No, not at this time"

**Credit bureaus — Have you reviewed...:**
> "Yes"

**Were there any fraudulent accounts included...:**
> "Yes"

**Was any personal info wrong...:**
> "None of the above"

**Company name (Inquiries):**
> "DO NOT INCLUDE" — (skip the inquiries section)

**Have you requested a fraud alert?**
> "No, not yet"

**Have you contacted your local police department?**
> "Yes" (if already filed) or "No, not yet" (if filing FTC first)

**Police department:**
> "[Your police department name]"

**State:**
> "[Your state]"

**Data breach history:**
> "Yes" — Check all 3 bureaus

**Debt collectors:**
> "No"

**Click: Continue**

**Tell us in your words:**
> "I recently reviewed a copy of my credit report and noticed I had fraudulent accounts on my report. Please remove these accounts from my report. They are hurting my ability to obtain credit."

**Click: Continue**

**What would be a fair resolution?**
> "Please remove all fraudulent accounts. Thank you."

**Attach documents:**
> Upload:
> - FTC Report (if already have one)
> - Picture of DL
> - Picture of SSN Card
> - Proof of address: Utility Bill / Bank Statement / Phone Bill
>   - (Shows your name and address)

**Company Name:**
> "[Credit bureau you are disputing with — Ex: Experian]"

**Information:**
> Select: SSN, Your name, Date of birth

**Fill out all the information**

**Do you want to complain about another company?**
> "No" (unless filing for multiple bureaus at once)

**Review your complaint then submit**

**Download your FTC Report PDF:**
> **Don't skip. You won't be able to go back.**

---

## FTC REPORT NUMBER

After completing, record your FTC Report Number here:

**FTC Report #:** _______________

**Date Filed:** _______________

This number goes on your affidavit and all bureau letters.
```

===========================================================================
FILE 4: FTC AFFIDAVIT FIELDS
===========================================================================

Generate pre-filled fields for the FTC Identity Theft Affidavit.

```markdown
# FTC IDENTITY THEFT AFFIDAVIT — PRE-FILLED FIELDS
## For Notarization

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## INSTRUCTIONS

1. Download the FTC Identity Theft Affidavit from your FTC report
2. Fill in the fields below
3. Take to notary for signature and stamp
4. Make [NUMBER OF BUREAUS + NUMBER OF FURNISHERS] copies

---

## SECTION 1: YOUR PERSONAL INFO

| Field | Value |
|-------|-------|
| Full Legal Name | [FULL NAME] |
| Current Address | [ADDRESS] |
| City, State, ZIP | [CITY, STATE ZIP] |
| Social Security Number | XXX-XX-[LAST 4] |
| Date of Birth | [MM/DD/YYYY] |
| Driver's License # | [LICENSE NUMBER] |
| DL State | [STATE] |
| Phone | [PHONE] |
| Email | [EMAIL] |

**Questions 8-10:** Skip if you did not move recently

---

## SECTION 2: DECLARATIONS

| Question | Answer |
|----------|--------|
| 11 | "Did not" |
| 12 | "Did not" |
| 13 | "Am not" |
| 14 | Skip |
| 15 | Skip |

---

## SECTION 3: DOCUMENTATION

| Question | Answer |
|----------|--------|
| 16 | Check: "A valid government ID" AND "Proof of residence" |
| 17 | Skip (Accounts) |
| 18 | Skip (Inquiries) |

---

## SECTION 4: FRAUD INFORMATION

**Complete for EACH fraudulent account:**

### Account 1:
| Field | Value |
|-------|-------|
| Name of Institution | [CREDITOR 1 NAME] |
| Account Number | [ACCOUNT NUMBER] |
| Account Type | Credit (or appropriate type) |
| Select ONE | "This account was opened fraudulently" |
| Date Opened | [DATE AS SHOWN ON REPORT] |
| Date Discovered | [ONE MONTH PRIOR TO TODAY] |

### Account 2:
| Field | Value |
|-------|-------|
| Name of Institution | [CREDITOR 2 NAME] |
| Account Number | [ACCOUNT NUMBER] |
| Account Type | [TYPE] |
| Select ONE | "This account was opened fraudulently" |
| Date Opened | [DATE AS SHOWN ON REPORT] |
| Date Discovered | [ONE MONTH PRIOR TO TODAY] |

[REPEAT FOR ALL FRAUDULENT ACCOUNTS]

---

## SECTION 5: LAW ENFORCEMENT REPORT

| Question | Answer |
|----------|--------|
| 20 | Select ONE: |
| | ☐ "I filed my report in person with the law enforcement officer and agency listed below" (if in-person) |
| | ☐ "I filed an automated report with the law enforcement agency listed below" (if online) |
| Department | [POLICE DEPARTMENT NAME] |
| Report Number | [POLICE REPORT CASE NUMBER] |
| Report Date | [DATE POLICE REPORT FILED] |
| Did victim receive copy? | "Yes" |
| FTC Complaint Number | [FTC REPORT NUMBER] |

**Leave the rest blank.**

---

## SECTION 6: NOTARIZATION

Take the completed affidavit to a notary. Options:

**Option 1 — Online (Recommended)**
- NotaryLive: https://notarylive.com
- Fast: Done in 30 minutes
- Cost: ~$25 per session

**Option 2 — Your Bank**
- Many banks offer free notary for account holders
- Call ahead to confirm availability

**Option 3 — UPS Store / Notary Service**
- Walk-in notary services available
- Cost: $5-15 per signature

---

## AFTER NOTARIZATION

☐ Make [NUMBER] copies of the notarized affidavit
☐ Keep original in safe place
☐ One copy goes in each envelope (bureaus + furnishers)
```

===========================================================================
FILE 5-7: § 605B LETTERS (ONE PER BUREAU)
===========================================================================

Generate THREE separate letters — one for each CRA.

**TEMPLATE FOR EACH BUREAU LETTER:**

```markdown
# § 605B IDENTITY THEFT BLOCK REQUEST
## [BUREAU NAME]

---

[CONSUMER FULL NAME]
[CONSUMER ADDRESS]
[CITY, STATE ZIP]

[TODAY'S DATE]

[BUREAU NAME]
[BUREAU ADDRESS]
[BUREAU CITY, STATE ZIP]

**SENT VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED**

═══════════════════════════════════════════════════════════════════════════
**RE: FORMAL IDENTITY THEFT BLOCK REQUEST UNDER FCRA § 605B**
**DEMAND FOR 4-BUSINESS-DAY COMPLIANCE**
═══════════════════════════════════════════════════════════════════════════

**Consumer:** [FULL LEGAL NAME]
**SSN (Last 4):** XXX-XX-[XXXX]
**Date of Birth:** [DOB]
**Case Reference:** [CASE NUMBER]

═══════════════════════════════════════════════════════════════════════════

Dear Sir or Madam:

Pursuant to the Fair Credit Reporting Act, **15 U.S.C. § 1681c-2 (FCRA § 605B)**, I am formally requesting that you **BLOCK** the following information from my consumer file, as it resulted from identity theft.

---------------------------------------------------------------------------
SECTION 1: FRAUDULENT ACCOUNTS TO BE BLOCKED
---------------------------------------------------------------------------

I am a victim of identity theft. The following account(s) appear on my credit report maintained by [BUREAU NAME] and were opened fraudulently without my knowledge, authorization, or consent:

**FRAUDULENT ACCOUNT 1:**
| Field | Information |
|-------|-------------|
| Creditor Name | [CREDITOR 1] |
| Account Number | [ACCOUNT NUMBER AS SHOWN] |
| Account Type | [TYPE] |
| Date Opened | [DATE] |
| Balance | $[AMOUNT] |
| I did NOT open this account | ✓ |
| I did NOT authorize this account | ✓ |
| I did NOT benefit from this account | ✓ |

**FRAUDULENT ACCOUNT 2:**
[REPEAT FORMAT FOR EACH ACCOUNT]

**FRAUDULENT INQUIRIES:**
[LIST ANY RELATED INQUIRIES]

---------------------------------------------------------------------------
SECTION 2: § 605B REQUIREMENTS — YOUR LEGAL OBLIGATIONS
---------------------------------------------------------------------------

Under FCRA § 605B (15 U.S.C. § 1681c-2), upon receipt of:

1. ✓ Appropriate proof of my identity — **ENCLOSED**
2. ✓ A copy of an identity theft report — **ENCLOSED**
3. ✓ Identification of the fraudulent information — **PROVIDED ABOVE**
4. ✓ My statement that this information does not relate to any transaction by me — **CONFIRMED**

**You are REQUIRED to BLOCK the reporting of this information NOT LATER THAN 4 BUSINESS DAYS after receipt of this letter.**

---------------------------------------------------------------------------
SECTION 3: NOTIFICATION TO FURNISHER
---------------------------------------------------------------------------

Under FCRA § 605B(b), you are also required to **promptly notify** the furnisher(s) of this information:

1. That this information may be a result of identity theft
2. That an identity theft report has been filed
3. That a block has been requested
4. Of the effective dates of the block

---------------------------------------------------------------------------
SECTION 4: ENCLOSED DOCUMENTATION
---------------------------------------------------------------------------

As required by § 605B(a), I have enclosed:

☐ Copy of FTC Identity Theft Report (Report #[FTC NUMBER])
☐ Copy of Police Report (Case #[POLICE CASE NUMBER])
☐ Copy of Notarized Identity Theft Affidavit
☐ Copy of Government-Issued Photo ID (Driver's License)
☐ Copy of Social Security Card
☐ Copy of Proof of Address (Utility Bill / Bank Statement)
☐ Copy of Credit Report with fraudulent items circled
☐ Copy of FCRA § 605B (statutory text)

---------------------------------------------------------------------------
SECTION 5: CONSEQUENCES OF NON-COMPLIANCE
---------------------------------------------------------------------------

**You are hereby on notice.** Failure to block this information within 4 business days will constitute a violation of FCRA § 605B.

Additionally, any reinsertion of this blocked information without compliance with § 611(a)(5)(B) — including 5-day written notice to me before reinsertion and certification that the information has been verified — will constitute a **separate violation** for which I will pursue all available remedies including:

- Statutory damages of $100-$1,000 per willful violation (§ 1681n)
- Actual damages for negligent violation (§ 1681o)
- Punitive damages for willful non-compliance
- Attorney fees and costs

Under *Safeco Insurance Co. v. Burr*, continued reporting of identity theft information after receiving this formal notice with complete documentation may constitute **willful violation**, exposing you to enhanced damages.

---------------------------------------------------------------------------
SECTION 6: CONFIRMATION REQUESTED
---------------------------------------------------------------------------

Please send written confirmation of the block to:

[FIRM NAME]
[FIRM ADDRESS]
[FIRM PHONE]
[FIRM EMAIL]

**Case Reference:** [CASE NUMBER]

Do not contact the consumer directly. All communication must go through our office.

---------------------------------------------------------------------------

Sincerely,

_______________________________________
[CONSUMER NAME]

Date: [TODAY'S DATE]

═══════════════════════════════════════════════════════════════════════════
**ENCLOSURES:**
☐ FTC Identity Theft Report
☐ Police Report (or case number confirmation)
☐ Notarized Identity Theft Affidavit
☐ Copy of Driver's License
☐ Copy of Social Security Card
☐ Proof of Address
☐ Copy of Credit Report (fraudulent items highlighted)
☐ Copy of FCRA § 605B
═══════════════════════════════════════════════════════════════════════════
```

**BUREAU ADDRESSES:**

**Experian:**
P.O. Box 9554
Allen, TX 75013

**Equifax:**
P.O. Box 740256
Atlanta, GA 30374-0256

**TransUnion:**
Fraud Victim Assistance Department
P.O. Box 2000
Chester, PA 19016

===========================================================================
FILE 8: § 623 FURNISHER LETTERS (ONE PER CREDITOR)
===========================================================================

Generate a SEPARATE letter for EACH furnisher reporting fraudulent accounts.

**TEMPLATE:**

```markdown
# § 623 FURNISHER NOTICE — IDENTITY THEFT
## [CREDITOR NAME]

---

[CONSUMER FULL NAME]
[CONSUMER ADDRESS]
[CITY, STATE ZIP]

[TODAY'S DATE]

[CREDITOR NAME]
[CREDITOR ADDRESS — Look up or use general correspondence address]

**SENT VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED**

═══════════════════════════════════════════════════════════════════════════
**RE: NOTICE OF IDENTITY THEFT — DEMAND TO CEASE REPORTING**
**FCRA § 623(a)(6) — Account #[ACCOUNT NUMBER]**
═══════════════════════════════════════════════════════════════════════════

**Consumer:** [FULL LEGAL NAME]
**SSN (Last 4):** XXX-XX-[XXXX]
**Date of Birth:** [DOB]
**Your Account #:** [ACCOUNT NUMBER]
**Case Reference:** [CASE NUMBER]

═══════════════════════════════════════════════════════════════════════════

Dear Sir or Madam:

I am writing to inform you that the above-referenced account is the result of **identity theft**. I did not open this account, did not authorize anyone to open it on my behalf, and did not receive any goods, services, or money from it.

---------------------------------------------------------------------------
SECTION 1: YOUR LEGAL OBLIGATIONS UNDER FCRA § 623
---------------------------------------------------------------------------

As a furnisher of information to consumer reporting agencies, you are subject to FCRA § 623 (15 U.S.C. § 1681s-2).

**Under § 623(a)(6)(A):** Upon receiving notice that information furnished by you may be the result of identity theft, you must **cease reporting** that information to consumer reporting agencies.

**Under § 623(a)(6)(B):** You must not furnish information relating to this account to any consumer reporting agency.

**This letter constitutes your formal notice.**

---------------------------------------------------------------------------
SECTION 2: IDENTITY THEFT DOCUMENTATION
---------------------------------------------------------------------------

Enclosed please find:

☐ Copy of FTC Identity Theft Report (Report #[FTC NUMBER])
☐ Copy of Police Report (Case #[POLICE CASE NUMBER])
☐ Copy of Notarized Identity Theft Affidavit
☐ Copy of Government-Issued Photo ID

---------------------------------------------------------------------------
SECTION 3: DEMANDS
---------------------------------------------------------------------------

Pursuant to my rights under FCRA § 623, I demand that you:

1. **IMMEDIATELY CEASE** reporting this account to Experian, Equifax, TransUnion, and any other consumer reporting agency

2. **NOTIFY** all consumer reporting agencies to which you have reported this account that it is the result of identity theft and must be deleted

3. **CEASE** all collection activity on this account

4. **Provide written confirmation** that you have complied with these demands

---------------------------------------------------------------------------
SECTION 4: CONSEQUENCES OF NON-COMPLIANCE
---------------------------------------------------------------------------

Continued reporting of this fraudulent account after receipt of this notice, with complete identity theft documentation, will constitute **willful violation** of FCRA § 623(a)(6).

I will pursue all available remedies including:

- Statutory damages of $100-$1,000 per violation (§ 1681n)
- Actual damages (§ 1681o)
- Punitive damages for willful non-compliance
- Attorney fees and costs

Additionally, I have filed identity theft block requests with all three major credit bureaus under FCRA § 605B. You will be receiving notification from them as well.

---------------------------------------------------------------------------
SECTION 5: RESPONSE REQUIRED
---------------------------------------------------------------------------

Please send written confirmation of compliance to:

[FIRM NAME]
[FIRM ADDRESS]
[FIRM PHONE]
[FIRM EMAIL]

**Case Reference:** [CASE NUMBER]

Do not contact the consumer directly. All communication must go through our office.

I expect your compliance within **15 days** of receipt of this letter.

---------------------------------------------------------------------------

Sincerely,

_______________________________________
[CONSUMER NAME]

Date: [TODAY'S DATE]

═══════════════════════════════════════════════════════════════════════════
**ENCLOSURES:**
☐ FTC Identity Theft Report
☐ Police Report
☐ Notarized Identity Theft Affidavit
☐ Copy of Driver's License
═══════════════════════════════════════════════════════════════════════════
```

===========================================================================
FILE 9: ENVELOPE CHECKLIST
===========================================================================

```markdown
# ENVELOPE CHECKLIST
## What Goes in Each Mailing

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## EXPERIAN ENVELOPE

**Mail to:**
Experian
P.O. Box 9554
Allen, TX 75013

**Contents:**
☐ 605B Letter (Experian version)
☐ FTC Identity Theft Report (copy)
☐ Police Report or case number confirmation (copy)
☐ Notarized Affidavit (copy)
☐ Driver's License (copy — front and back)
☐ Social Security Card (copy)
☐ Proof of Address (utility bill/bank statement copy)
☐ Credit Report pages with fraudulent items circled
☐ FCRA § 605B statutory text (copy)

**Mailing Method:** ☐ Certified Mail, Return Receipt Requested
**Tracking #:** _______________
**Date Mailed:** _______________

---

## EQUIFAX ENVELOPE

**Mail to:**
Equifax Information Services, LLC
P.O. Box 740256
Atlanta, GA 30374-0256

**Contents:**
☐ 605B Letter (Equifax version)
☐ FTC Identity Theft Report (copy)
☐ Police Report or case number confirmation (copy)
☐ Notarized Affidavit (copy)
☐ Driver's License (copy — front and back)
☐ Social Security Card (copy)
☐ Proof of Address (utility bill/bank statement copy)
☐ Credit Report pages with fraudulent items circled
☐ FCRA § 605B statutory text (copy)

**Mailing Method:** ☐ Certified Mail, Return Receipt Requested
**Tracking #:** _______________
**Date Mailed:** _______________

---

## TRANSUNION ENVELOPE

**Mail to:**
TransUnion Fraud Victim Assistance Department
P.O. Box 2000
Chester, PA 19016

**Contents:**
☐ 605B Letter (TransUnion version)
☐ FTC Identity Theft Report (copy)
☐ Police Report or case number confirmation (copy)
☐ Notarized Affidavit (copy)
☐ Driver's License (copy — front and back)
☐ Social Security Card (copy)
☐ Proof of Address (utility bill/bank statement copy)
☐ Credit Report pages with fraudulent items circled
☐ FCRA § 605B statutory text (copy)

**Mailing Method:** ☐ Certified Mail, Return Receipt Requested
**Tracking #:** _______________
**Date Mailed:** _______________

---

## FURNISHER ENVELOPES

[REPEAT FOR EACH FURNISHER]

**[CREDITOR 1 NAME] ENVELOPE**

**Mail to:**
[CREDITOR ADDRESS]

**Contents:**
☐ § 623 Furnisher Letter
☐ FTC Identity Theft Report (copy)
☐ Police Report (copy)
☐ Notarized Affidavit (copy)
☐ Driver's License (copy)

**Mailing Method:** ☐ Certified Mail, Return Receipt Requested
**Tracking #:** _______________
**Date Mailed:** _______________

---

## COPY COUNT CALCULATOR

| Document | Copies Needed |
|----------|---------------|
| FTC Report | [3 bureaus + X furnishers] = ___ copies |
| Police Report | [3 bureaus + X furnishers] = ___ copies |
| Notarized Affidavit | [3 bureaus + X furnishers] = ___ copies |
| Driver's License | [3 bureaus + X furnishers] = ___ copies |
| SSN Card | [3 bureaus only] = 3 copies |
| Proof of Address | [3 bureaus only] = 3 copies |
| § 605B Text | [3 bureaus only] = 3 copies |

---

## MAILING TIPS

1. Use **Certified Mail with Return Receipt** for ALL envelopes
2. Keep green receipt cards when they return
3. Take photos of all envelopes before sealing
4. Record all tracking numbers above
5. Keep copies of everything you send
```

===========================================================================
FILE 10: TIMELINE TRACKER
===========================================================================

```markdown
# TIMELINE TRACKER
## Identity Theft Block Deadlines

**Client:** [Full Name]
**Case #:** [Case Number]
**Letters Mailed Date:** [DATE]

---

## KEY DEADLINES

| Bureau | Date Mailed | Est. Delivery | 4-Day Block Deadline | Status |
|--------|-------------|---------------|---------------------|--------|
| Experian | [DATE] | [+3 days] | [Delivery + 4 business days] | ☐ Pending |
| Equifax | [DATE] | [+3 days] | [Delivery + 4 business days] | ☐ Pending |
| TransUnion | [DATE] | [+3 days] | [Delivery + 4 business days] | ☐ Pending |

| Furnisher | Date Mailed | Est. Delivery | Response Deadline | Status |
|-----------|-------------|---------------|-------------------|--------|
| [CREDITOR 1] | [DATE] | [+3 days] | [Delivery + 15 days] | ☐ Pending |
| [CREDITOR 2] | [DATE] | [+3 days] | [Delivery + 15 days] | ☐ Pending |

---

## ACTION CALENDAR

**Day 0 — [MAIL DATE]**
☐ Mail all certified letters
☐ Record tracking numbers
☐ Set calendar reminders

**Day 5-7 — [DATE]**
☐ Check USPS tracking for delivery confirmation
☐ Note actual delivery dates above

**Day 10-12 — [DATE]**
☐ 4-business-day deadline passes for bureaus
☐ Check credit monitoring for blocks
☐ If no block, document violation

**Day 15 — [DATE]**
☐ Follow-up calls to bureaus (see Phone Scripts)
☐ Confirm block status

**Day 20-25 — [DATE]**
☐ Furnisher response deadline passes
☐ Check if accounts still reporting

**Day 30 — [DATE]**
☐ Pull fresh credit reports
☐ Compare to original
☐ Document any ongoing violations

**Day 45 — [DATE]**
☐ Final status check
☐ If violations found, escalate to CFPB/litigation

---

## VIOLATION LOG

Record any compliance failures here:

| Date | Violator | Violation | Evidence |
|------|----------|-----------|----------|
| | | | |
| | | | |

---

## ESCALATION TRIGGERS

Escalate to CFPB complaint if:
☐ Bureau fails to block within 4 business days
☐ Furnisher continues reporting after 15-day notice
☐ Account is reinserted without 5-day written notice
☐ Any party ignores certified mail

Escalate to litigation if:
☐ CFPB complaint produces no result after 30 days
☐ Multiple violations documented
☐ Damages exceed $10,000 exposure
```

===========================================================================
FILE 11: PHONE SCRIPTS
===========================================================================

```markdown
# PHONE FOLLOW-UP SCRIPTS
## Bureau Calls After 5 Business Days

**Client:** [Full Name]
**Case #:** [Case Number]

---

## EXPERIAN CALL

**Phone:** 1-888-397-3742 (or 1-855-414-6048)
**Best Time:** Tuesday-Thursday, 10am-2pm
**Estimated Time:** 15-20 minutes

**Step 1: Navigate Menu**
1. Enter Social Security Number
2. Enter ZIP Code
3. Say "Fraud" when asked
4. Say "Start a Dispute"
5. Confirm calling about "Dispute"
6. Say "Identity Theft" (option #3)
7. Confirm you have been a victim
8. Request to speak to "Fraud Department"

**Step 2: What to Say**

> "I recently sent certified mail documentation for an identity theft block under FCRA 605B. I'm calling to confirm you received my letter and that the fraudulent accounts have been blocked."

**If they ask for details:**

> "I mailed the letter on [DATE] via certified mail. The tracking number is [NUMBER]. I included my FTC Identity Theft Report number [FTC NUMBER], police report case number [POLICE NUMBER], and a notarized affidavit."

**If they say it's not blocked yet:**

> "Under FCRA Section 605B, you're required to block identity theft information within 4 business days of receiving my documentation. I'm documenting this call. When can I expect the block to be implemented?"

**If they try to add a fraud alert instead:**

> "I do NOT want a fraud alert added. I specifically need the identity theft BLOCK under 605B, which requires deletion of the fraudulent accounts — not just an alert."

**Record:**
- Date/Time of call: _______________
- Representative name: _______________
- Confirmation #: _______________
- Block confirmed? ☐ Yes ☐ No
- Notes: _______________

---

## EQUIFAX CALL

**Phone:** 1-800-525-6285
**Estimated Time:** 15 minutes

**Step 1: Navigate**
1. Call and select option to speak to agent
2. Request "Fraud Department"
3. Verify identity (name, address, DOB, SSN)

**Step 2: What to Say**

> "I recently submitted an identity theft block request under FCRA 605B. I sent certified mail on [DATE] with my FTC report, police report, and notarized affidavit. I'm calling to confirm the fraudulent accounts have been blocked."

**If not resolved:**

> "The law requires you to block this information within 4 business days. My documentation was complete. I need to know when this will be resolved or I'll need to file a CFPB complaint."

**Record:**
- Date/Time of call: _______________
- Representative name: _______________
- Confirmation #: _______________
- Block confirmed? ☐ Yes ☐ No
- Notes: _______________

---

## TRANSUNION CALL

**Phone:** 1-800-916-8800
**Estimated Time:** 30 minutes

**Step 1: Navigate**
1. Press 1 for English
2. Say "Dispute" → "Yes" to confirm
3. Do NOT press #1 for follow-up
4. Do NOT press #1 for text
5. Wait for agent (may need to press # multiple times)

**Step 2: What to Say**

> "I submitted an identity theft block request under FCRA 605B via certified mail on [DATE]. I'm calling to confirm the fraudulent accounts have been blocked."

**If they ask what accounts:**

> "The fraudulent account is [CREDITOR NAME], account number ending in [LAST 4]. I sent complete documentation including FTC report number [NUMBER] and police report case number [NUMBER]."

**Important:**

> "Please make sure you do NOT place a security or fraud alert on my report. I specifically need the 605B identity theft BLOCK which removes the fraudulent accounts."

**Record:**
- Date/Time of call: _______________
- Representative name: _______________
- Confirmation #: _______________
- Block confirmed? ☐ Yes ☐ No
- Notes: _______________

---

## IF THEY REFUSE OR DELAY

**Escalation Language:**

> "I understand you may have a process, but federal law is clear. FCRA Section 605B requires a 4-business-day block. I submitted complete documentation via certified mail. Your failure to comply is being documented and will be included in my CFPB complaint. May I speak with a supervisor?"

**If transferred to supervisor:**

> "I'm calling about a 605B identity theft block that hasn't been implemented despite complete documentation. I need this resolved today or I'll be filing a complaint with the Consumer Financial Protection Bureau. What can you do to resolve this right now?"

---

## CALL LOG

| Date | Bureau | Rep Name | Duration | Result | Next Step |
|------|--------|----------|----------|--------|-----------|
| | | | | | |
| | | | | | |
| | | | | | |
```

===========================================================================
FILE 12: STANDING DOCUMENTATION
===========================================================================

```markdown
# STANDING DOCUMENTATION
## Post-TransUnion Requirements for Litigation

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## WHY THIS MATTERS

Under *TransUnion LLC v. Ramirez* (2021), FCRA plaintiffs must prove:
1. **Concrete harm** — Not just a statutory violation
2. **Dissemination** — The inaccurate info was shared with third parties
3. **Causation** — The violation caused the harm

This document records evidence of standing in case litigation becomes necessary.

---

## ELEMENT 1: CONCRETE HARM

**Question:** Has the consumer suffered actual harm from the identity theft?

**Denial of Credit:**
| Date | Creditor | What Applied For | Result | Denial Letter? |
|------|----------|------------------|--------|----------------|
| [DATE] | [LENDER] | [Loan type] | Denied | ☐ Yes ☐ No |
| | | | | |

**Other Concrete Harms:**
☐ Increased interest rate on existing account
☐ Reduced credit limit
☐ Insurance rate increase
☐ Employment denial/issue
☐ Housing/rental denial
☐ Emotional distress (documented)
☐ Time spent resolving fraud
☐ Out-of-pocket expenses

**Description of harm:**
[DESCRIBE THE SPECIFIC HARM THE CONSUMER HAS SUFFERED]

**Harm documentation available:**
☐ Denial letter(s)
☐ Rate increase notice
☐ Employment records
☐ Medical/therapy records (for emotional distress)
☐ Receipts for expenses
☐ Time log

---

## ELEMENT 2: DISSEMINATION

**Question:** Was the fraudulent information provided to third parties?

**Credit Report Inquiries (from report):**
| Date | Company | Purpose | Fraudulent Info Present? |
|------|---------|---------|-------------------------|
| [DATE] | [COMPANY] | [Credit/Employment/etc.] | ☐ Yes ☐ No |
| | | | |

**Evidence of Dissemination:**
☐ Hard inquiries on credit report during fraud period
☐ Denial letter referencing specific fraudulent account
☐ Third party confirms they received report with fraud
☐ Collection calls/letters based on fraudulent account

---

## ELEMENT 3: CAUSATION

**Question:** Did the identity theft/inaccurate reporting CAUSE the harm?

**Causation Analysis:**
[EXPLAIN HOW THE FRAUDULENT ACCOUNTS CAUSED THE SPECIFIC HARM]

Example: "Consumer was denied auto loan by [LENDER] on [DATE]. Denial letter specifically references 'derogatory accounts' which includes the fraudulent [CREDITOR] account. Without this fraudulent account, consumer's credit score would be approximately [XX] points higher, likely qualifying for approval."

---

## STANDING STRENGTH ASSESSMENT

| Element | Strength | Evidence Quality |
|---------|----------|------------------|
| Concrete Harm | ☐ Strong ☐ Moderate ☐ Weak | [Notes] |
| Dissemination | ☐ Strong ☐ Moderate ☐ Weak | [Notes] |
| Causation | ☐ Strong ☐ Moderate ☐ Weak | [Notes] |

**Overall Standing:** ☐ Strong ☐ Moderate ☐ Needs Work

---

## EVIDENCE TO GATHER

If standing is weak, gather:
☐ Apply for credit to create denial letter
☐ Request copy of credit report pulled by denier
☐ Document all time spent on resolution
☐ Keep receipts for any expenses (certified mail, notary, etc.)
☐ Journal emotional impact

---

## FOR LITIGATION FILE

Preserve:
☐ All credit reports showing fraudulent accounts
☐ All denial letters
☐ All certified mail receipts and return cards
☐ All correspondence with bureaus and furnishers
☐ Call logs with dates, times, representative names
☐ Timeline of events
☐ Calculation of damages
```

===========================================================================
FILE 13: DAMAGES CALCULATOR
===========================================================================

```markdown
# DAMAGES CALCULATOR
## If Violations Occur

**Client:** [Full Name]
**Case #:** [Case Number]
**Date Prepared:** [Today's Date]

---

## VIOLATION TRACKING

Record each violation as it occurs:

| # | Date | Violator | Violation Type | FCRA Section |
|---|------|----------|----------------|--------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## VIOLATION TYPES & DAMAGES

### § 605B Violations (Identity Theft Block)

**Failure to block within 4 business days:**
- Statutory damages: $100 - $1,000 per violation
- Per bureau that fails: × ___
- **Subtotal:** $___

**Reinsertion without proper notice:**
- Statutory damages: $100 - $1,000 per reinsertion
- Per account reinserted: × ___
- **Subtotal:** $___

### § 623 Violations (Furnisher Duties)

**Continued reporting after notice:**
- Statutory damages: $100 - $1,000 per violation
- Per furnisher that continues: × ___
- Per month of continued reporting: × ___
- **Subtotal:** $___

### § 611 Violations (Reinvestigation)

**Unreasonable reinvestigation:**
- Statutory damages: $100 - $1,000 per violation
- **Subtotal:** $___

---

## DAMAGES CALCULATION

**STATUTORY DAMAGES:**

| Defendant | Violations | Min ($100 ea) | Max ($1,000 ea) |
|-----------|------------|---------------|-----------------|
| Experian | ___ | $___ | $___ |
| Equifax | ___ | $___ | $___ |
| TransUnion | ___ | $___ | $___ |
| [Furnisher 1] | ___ | $___ | $___ |
| [Furnisher 2] | ___ | $___ | $___ |
| **TOTAL** | ___ | $___ | $___ |

**ACTUAL DAMAGES:**

| Category | Amount | Documentation |
|----------|--------|---------------|
| Lost credit opportunity | $___ | Denial letter |
| Higher interest paid | $___ | Rate comparison |
| Time spent (hours × $XX/hr) | $___ | Time log |
| Out-of-pocket expenses | $___ | Receipts |
| Emotional distress | $___ | Journal/therapy |
| **TOTAL ACTUAL** | $___ | |

**PUNITIVE DAMAGES (if willful):**

Punitive damages can be awarded for willful violations. Courts have awarded 2x-10x statutory damages in egregious cases.

- Conservative estimate (2x statutory): $___
- Moderate estimate (5x statutory): $___
- Aggressive estimate (10x statutory): $___

**ATTORNEY FEES:**

FCRA allows recovery of attorney fees for successful plaintiffs.
- Estimated fees if litigated: $5,000 - $25,000

---

## TOTAL EXPOSURE BY DEFENDANT

| Defendant | Statutory | Actual | Punitive (est.) | Total Range |
|-----------|-----------|--------|-----------------|-------------|
| Experian | $___ | $___ | $___ | $___-$___ |
| Equifax | $___ | $___ | $___ | $___-$___ |
| TransUnion | $___ | $___ | $___ | $___-$___ |
| [Furnisher 1] | $___ | $___ | $___ | $___-$___ |
| [Furnisher 2] | $___ | $___ | $___ | $___-$___ |
| **COMBINED** | $___ | $___ | $___ | **$___-$___** |

---

## SETTLEMENT RANGE

Based on typical FCRA identity theft settlements:

| Scenario | Expected Settlement |
|----------|---------------------|
| Single bureau, single violation | $1,500 - $5,000 |
| Multiple bureaus, single violation each | $5,000 - $15,000 |
| Multiple violations + reinsertion | $15,000 - $35,000 |
| Willful violations with strong evidence | $35,000 - $75,000+ |

**This case estimated range:** $_______ - $_______

---

## WILLFULNESS INDICATORS

Check factors that suggest willful violation (enhances damages):

☐ Violated after receiving certified mail with complete documentation
☐ Violated established written policies
☐ Previous similar violations/lawsuits
☐ Failed to train employees on § 605B
☐ Ignored follow-up communications
☐ Reinserted without investigation
☐ No reasonable basis to decline block

**Willfulness assessment:** ☐ Strong ☐ Moderate ☐ Weak
```

===========================================================================
FILE 14: REINSERTION DISPUTE LETTER
===========================================================================

```markdown
# REINSERTION DISPUTE LETTER
## § 611(a)(5)(B)(ii) Violation

**Use this letter if a blocked account is reinserted without proper 5-day notice.**

---

[CONSUMER FULL NAME]
[CONSUMER ADDRESS]
[CITY, STATE ZIP]

[TODAY'S DATE]

[BUREAU NAME]
[BUREAU ADDRESS]

**SENT VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED**

═══════════════════════════════════════════════════════════════════════════
**RE: UNLAWFUL REINSERTION OF IDENTITY THEFT INFORMATION**
**VIOLATION OF FCRA § 611(a)(5)(B)(ii) AND § 605B**
═══════════════════════════════════════════════════════════════════════════

**Consumer:** [FULL LEGAL NAME]
**SSN (Last 4):** XXX-XX-[XXXX]
**Date of Birth:** [DOB]
**Case Reference:** [CASE NUMBER]

═══════════════════════════════════════════════════════════════════════════

Dear Sir or Madam:

I am writing regarding your **unlawful reinsertion** of previously blocked identity theft information into my consumer file.

---------------------------------------------------------------------------
SECTION 1: TIMELINE OF EVENTS
---------------------------------------------------------------------------

1. **[DATE]** — I submitted complete § 605B identity theft block request with:
   - FTC Identity Theft Report #[NUMBER]
   - Police Report Case #[NUMBER]
   - Notarized Identity Theft Affidavit
   - Proof of identity

2. **[DATE]** — You blocked/deleted the following fraudulent account(s):
   - [CREDITOR NAME] — Account #[NUMBER]

3. **[DATE]** — I discovered the account has been **REINSERTED** into my credit file.

4. **[DATE OF THIS LETTER]** — I am sending this formal notice of violation.

---------------------------------------------------------------------------
SECTION 2: LEGAL VIOLATIONS
---------------------------------------------------------------------------

Your reinsertion of this information violates multiple FCRA provisions:

**VIOLATION 1: § 611(a)(5)(B)(ii) — Failure to Provide Reinsertion Notice**

Under FCRA § 611(a)(5)(B), before reinserting previously deleted information, you MUST:
- Send written notice to the consumer **within 5 business days** of reinsertion
- Provide the name, address, and phone number of the furnisher
- Certify that the information has been verified as accurate

**I received NO such notice before this reinsertion.**

**VIOLATION 2: § 605B(c)(2) — Improper Rescission of Block**

If you rescinded the identity theft block, § 605B(c)(2) requires you to notify me **promptly, in the same manner as reinsertion notices under § 611(a)(5)(B).**

**I received NO such notification.**

**VIOLATION 3: § 607(b) — Failure to Maintain Maximum Accuracy**

By reinserting identity theft information without proper verification or notice, you have failed to maintain maximum possible accuracy as required by FCRA § 607(b).

---------------------------------------------------------------------------
SECTION 3: DEMANDS
---------------------------------------------------------------------------

I demand that you:

1. **IMMEDIATELY DELETE** the reinserted fraudulent account(s) from my credit file

2. **PROVIDE** written explanation of:
   - Why the block was rescinded (if applicable)
   - What "verification" was performed before reinsertion
   - Why I was not notified as required by law

3. **CONFIRM** in writing that the information has been permanently deleted

4. **CERTIFY** that this information will not be reinserted again without proper legal basis and required notice

---------------------------------------------------------------------------
SECTION 4: EVIDENCE OF VIOLATION
---------------------------------------------------------------------------

Enclosed please find:

☐ Copy of original § 605B block request (dated [DATE])
☐ Copy of confirmation of deletion/block (if received)
☐ Copy of current credit report showing reinsertion
☐ Declaration that I received no reinsertion notice

---------------------------------------------------------------------------
SECTION 5: NOTICE OF LEGAL ACTION
---------------------------------------------------------------------------

Your unlawful reinsertion of identity theft information constitutes **willful violation** of the FCRA. You had complete documentation of the identity theft. You blocked the information. You then reinserted it without notice or proper verification.

Under *Safeco Insurance Co. v. Burr*, acting in direct contradiction to established legal requirements constitutes willful violation subjecting you to:

- Statutory damages of $100 - $1,000 per violation (§ 1681n)
- **Punitive damages** for willful non-compliance
- Actual damages
- Attorney fees and costs

If this matter is not resolved within **15 days**, I will:
1. File a complaint with the Consumer Financial Protection Bureau
2. File a complaint with the Federal Trade Commission
3. Pursue all available legal remedies in federal court

---------------------------------------------------------------------------
SECTION 6: RESPONSE REQUIRED
---------------------------------------------------------------------------

Send your response and confirmation of deletion to:

[FIRM NAME]
[FIRM ADDRESS]
[FIRM PHONE]
[FIRM EMAIL]

**Case Reference:** [CASE NUMBER]

Do not contact the consumer directly.

---------------------------------------------------------------------------

Sincerely,

_______________________________________
[CONSUMER NAME]

Date: [TODAY'S DATE]

═══════════════════════════════════════════════════════════════════════════
**ENCLOSURES:**
☐ Original § 605B block request
☐ Original identity theft documentation
☐ Current credit report showing reinsertion
☐ Declaration re: no reinsertion notice received
═══════════════════════════════════════════════════════════════════════════
```

===========================================================================
AFTER GENERATING ALL FILES
===========================================================================

**PROVIDE SUMMARY TABLE:**

| # | File Name | Purpose |
|---|-----------|---------|
| 1 | 01_Screening_Checklist_[NAME]_[CASE].md | Staff verification |
| 2 | 02_Police_Report_Script_[NAME]_[CASE].md | Client instructions |
| 3 | 03_FTC_Report_Answers_[NAME]_[CASE].md | Copy-paste for FTC |
| 4 | 04_FTC_Affidavit_Fields_[NAME]_[CASE].md | Pre-filled affidavit |
| 5 | 05_605B_Experian_[NAME]_[CASE].md | Bureau letter |
| 6 | 06_605B_Equifax_[NAME]_[CASE].md | Bureau letter |
| 7 | 07_605B_TransUnion_[NAME]_[CASE].md | Bureau letter |
| 8+ | 08_623_Furnisher_[CREDITOR]_[NAME]_[CASE].md | Furnisher letters |
| 9 | 09_Envelope_Checklist_[NAME]_[CASE].md | Mailing guide |
| 10 | 10_Timeline_Tracker_[NAME]_[CASE].md | Deadlines |
| 11 | 11_Phone_Scripts_[NAME]_[CASE].md | Follow-up calls |
| 12 | 12_Standing_Documentation_[NAME]_[CASE].md | Litigation prep |
| 13 | 13_Damages_Calculator_[NAME]_[CASE].md | If violations occur |
| 14 | 14_Reinsertion_Letter_[NAME]_[CASE].md | If account returns |

**Total Files Generated:** [X]

**All files saved to:** `/mnt/user-data/outputs/`

**NEXT STEPS FOR STAFF:**

1. ☐ Complete screening checklist (File 1) — verify legitimacy
2. ☐ Give client Police Report Script (File 2) — get case number
3. ☐ Walk client through FTC Report (File 3) — get FTC number
4. ☐ Help client complete Affidavit (File 4) — get notarized
5. ☐ Prepare bureau letters (Files 5-7) — insert FTC/police numbers
6. ☐ Prepare furnisher letters (File 8+) — one per creditor
7. ☐ Assemble envelopes per checklist (File 9)
8. ☐ Mail certified, record tracking numbers
9. ☐ Set timeline reminders (File 10)
10. ☐ Follow up by phone after 5 days (File 11)
11. ☐ Monitor for violations, update damages calculator (File 13)
12. ☐ If account reinserts, send reinsertion letter (File 14)

===========================================================================
END OF PROMPT
===========================================================================
