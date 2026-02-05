#!/usr/bin/env python3
"""
Seed Training Content Script
Ingests Credit Repair Course and Metro 2® Course content into the knowledge base,
seeds Metro 2® codes, and creates comprehensive SOPs.
"""

import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, KnowledgeContent, Metro2Code, SOP, ChexSystemsDispute

def get_db():
    return SessionLocal()

CREDIT_REPAIR_SECTIONS = [
    {
        "section_number": 1,
        "section_title": "The Battlefield: Laws, Players, and Rules",
        "content": """Credit repair takes place on a highly regulated field where language, evidence, and timing matter as much as intent. Before we write a single letter or submit a single dispute, we need a precise view of the terrain: who creates and uses credit data, which laws govern their conduct, what rights consumers have, and how decisions are actually made inside credit reporting systems.

**1.1 The Ecosystem: Who Does What—and Why It Matters**

A credit report is not a single database but a stitched view assembled by consumer reporting agencies (CRAs)—primarily Equifax, Experian, and TransUnion for personal credit—based on information furnished by thousands of organizations. Those data furnishers include banks and credit unions, card issuers, auto and mortgage lenders, debt collectors, utilities, telecoms, and fintechs. Each furnisher reports using standardized structures (most commonly the Metro 2® format) and is responsible for accuracy and timely updates.

End users—lenders, insurers, employers (with consent), landlords—rely on CRA data to make decisions, and must follow adverse-action and permissible-purpose rules. Regulators such as the CFPB and FTC set and enforce standards; state attorneys general and banking departments add local oversight. Industry bodies (e.g., CDIA) publish technical guidance that shapes how data must be presented so it can be interpreted consistently across systems.

**1.2 The Governing Law: What Sets the Boundaries**

The Fair Credit Reporting Act (FCRA) is the central statute. For consumers, it guarantees file disclosure, dispute and reinvestigation rights, the ability to place fraud alerts and security freezes, and limits on how long negative information may remain (the "obsolescence" rules). For furnishers, it imposes duties to report with accuracy and integrity, to investigate disputes received from CRAs, and to correct or delete information that cannot be verified.

The FCRA works alongside related laws:
- **FDCPA** (Fair Debt Collection Practices Act) controls the conduct of third-party collectors
- **Regulation F** implements FDCPA communications rules
- **FACTA** added identity-theft protections and Red Flags obligations
- **GLBA** governs privacy and safeguarding of nonpublic personal information
- **ECOA/Reg B** requires fair lending and adverse-action notice content
- **CROA** (Credit Repair Organizations Act) imposes disclosures, contract requirements, and fee timing restrictions

**1.3 Rights and Duties: How Disputes Are Supposed to Work**

Consumers have the right to obtain their reports, to identify inaccuracies, and to submit disputes. When a CRA receives a dispute, it must conduct a reasonable reinvestigation and, in most cases, transmit the dispute to the furnisher through an electronic workflow (commonly e-OSCAR). The furnisher must review its system of record and supporting documentation, compare it to the consumer's claims and attachments, and then verify, correct, or delete the disputed information.

**1.4 The Data Layer: Metro 2®, DOFD, and Why Details Matter**

Most furnishers report in Metro 2®, a field-based standard that encodes account type, status, balances, dates, consumer identifiers, dispute indicators, and remarks. Two concepts matter immediately:

1. **Date of First Delinquency (DOFD)** drives how long many negative items can remain. Changing DOFD improperly (often called "re-aging") is a serious violation; correcting DOFD accurately is an appropriate remedy when records support it.

2. **Dispute indicators and compliance condition codes** are how furnishers communicate an active investigation or special circumstance (e.g., account affected by natural disaster or identity theft).

**1.5 Ethics and Prohibited Tactics**

Effective credit repair is not a loophole hunt. It is the disciplined correction of inaccurate or incomplete data using lawful processes. That means:
- No file segregation schemes
- No "new identity" or CPN scams
- No mass-mailing of knowingly false disputes
- No harassment of furnishers or CRAs
- No misrepresentation to consumers about guaranteed outcomes""",
        "tags": ["FCRA", "FDCPA", "CROA", "Metro 2", "CRA", "furnishers", "disputes", "fundamentals"],
        "statute_references": ["FCRA §611", "FCRA §623", "FDCPA", "CROA", "ECOA", "GLBA", "FACTA"],
        "difficulty_level": "beginner",
        "estimated_read_time": 15
    },
    {
        "section_number": 2,
        "section_title": "FCRA §611 Tactics: Forcing Bureaus to Correct or Delete",
        "content": """FCRA §611 is your primary weapon for forcing credit bureaus to investigate and correct inaccurate information. This section covers the tactical application of §611 reinvestigation rights.

**2.1 The §611 Reinvestigation Right**

Under FCRA §611, when a consumer disputes information directly with a CRA, the bureau must:
1. Conduct a reasonable reinvestigation within 30 days (can extend to 45 days if consumer provides additional information)
2. Forward all relevant information to the furnisher
3. Provide results in writing within 5 business days of completion
4. Delete or modify information that cannot be verified

**2.2 Crafting Effective §611 Disputes**

The quality of your dispute determines the quality of your result. Key principles:

**Be Specific**: Instead of "This account is not mine," state: "The account number ending in 4523 reports a 60-day late payment in March 2023. My bank records confirm on-time payment received March 1, 2023 (see attached confirmation #12345)."

**Provide Evidence**: Attach supporting documentation:
- Payment confirmations
- Bank statements
- Original creditor correspondence
- Court documents (bankruptcies, judgments)

**One Issue Per Dispute**: Don't bundle multiple accounts. Each dispute should address one tradeline with one clear issue.

**2.3 The e-OSCAR System**

When bureaus receive disputes, they typically transmit them to furnishers via e-OSCAR (Online Solution for Complete and Accurate Reporting). Understanding e-OSCAR limitations helps you craft better disputes:

- Character limits on dispute descriptions
- Standardized dispute codes (may oversimplify your claim)
- Document attachment limitations
- Processing time constraints

**2.4 Handling Bureau Responses**

After investigation, bureaus must provide:
- Written notice of results
- Updated credit report if changes made
- Description of reinvestigation procedure
- Notice of right to add consumer statement

If the bureau "verifies" disputed information, you have options:
1. Request Method of Verification (MOV)
2. Escalate to §623 direct furnisher dispute
3. File CFPB complaint
4. Consider §621 regulatory escalation

**2.5 Frivolous Dispute Defense**

Bureaus can reject disputes they deem "frivolous or irrelevant" if:
- You don't provide sufficient identifying information
- The dispute is substantially similar to a previous dispute
- You don't explain the basis for the dispute

Counter this by:
- Always providing new evidence with resubmissions
- Varying dispute language and focus
- Documenting specific inaccuracies each time""",
        "tags": ["FCRA 611", "reinvestigation", "disputes", "e-OSCAR", "bureau tactics", "MOV"],
        "statute_references": ["FCRA §611", "FCRA §611(a)", "FCRA §611(b)"],
        "difficulty_level": "intermediate",
        "estimated_read_time": 12
    },
    {
        "section_number": 3,
        "section_title": "FCRA §623 Tactics: Forcing Furnishers to Investigate and Correct",
        "content": """When bureau disputes don't resolve issues, FCRA §623 gives you direct access to data furnishers. This section covers advanced §623 tactics for forcing furnisher compliance.

**3.1 Understanding §623 Duties**

FCRA §623 imposes two categories of duties on furnishers:

**§623(a) - General Accuracy Duties**:
- Report only accurate information
- Promptly update or correct reported information
- Not report information known to be incomplete or inaccurate
- Provide notice of dispute to CRAs

**§623(b) - Investigation Duties After Notice from CRA**:
- Conduct investigation within 30 days
- Review all relevant information provided
- Report results to CRA
- Modify, delete, or permanently block disputed information if inaccurate

**3.2 The Direct Furnisher Dispute**

After you've disputed with a bureau and received the §611 results, you can dispute directly with the furnisher. Key advantages:
- Bypasses e-OSCAR limitations
- Allows detailed evidence submission
- Creates direct legal obligation on furnisher
- Establishes paper trail for potential litigation

**3.3 Crafting the §623 Letter**

Your direct furnisher dispute should include:
1. **Clear identification** of the consumer and account
2. **Specific dispute** of what is inaccurate
3. **Evidence** supporting your position
4. **Legal citation** to §623(b) duties
5. **Request for investigation** and correction
6. **Demand for written response** within 30 days

**3.4 Escalation Pathway**

If the furnisher fails to respond or verifies inaccurate information:

1. **Send second dispute** with additional evidence
2. **File CFPB complaint** documenting furnisher non-compliance
3. **Consider FCRA §621 regulatory complaint** to prudential regulator
4. **Evaluate FCRA §616/§617 civil liability** for willful or negligent violations

**3.5 Evidence That Moves Furnishers**

Furnishers respond to evidence that creates legal risk:
- Original creditor statements showing different information
- Payment histories contradicting reported data
- Court documents (bankruptcy discharge, judgment satisfaction)
- Identity theft affidavits and police reports
- Method of verification requests showing weak verification""",
        "tags": ["FCRA 623", "furnisher disputes", "direct disputes", "escalation", "investigation duties"],
        "statute_references": ["FCRA §623", "FCRA §623(a)", "FCRA §623(b)", "FCRA §616", "FCRA §617"],
        "difficulty_level": "advanced",
        "estimated_read_time": 14
    },
    {
        "section_number": 4,
        "section_title": "The Mortgage Late-Payment Removal Method",
        "content": """Mortgage late payments are among the most damaging items on a credit report. This section covers specialized tactics for mortgage late payment removal using Regulation Z and RESPA.

**4.1 Why Mortgage Lates Are Different**

Mortgage late payments carry outsized impact because:
- High-value accounts with long history
- Scoring models weight mortgage performance heavily
- Lenders view mortgage lates as serious risk indicator
- Can persist for 7 years from date of delinquency

**4.2 Regulation Z (TILA) Approach**

The Truth in Lending Act (Regulation Z) requires mortgage servicers to:
- Credit payments as of date received (not date processed)
- Apply payments in specific order
- Provide accurate periodic statements
- Handle payment processing within business-day requirements

**Common Reg Z violations creating dispute opportunities**:
- Payment posted to wrong date
- Payment misallocated between principal/interest/escrow
- Periodic statement errors
- Late fee calculation errors

**4.3 RESPA Qualified Written Request (QWR)**

Under RESPA §6, you can send a Qualified Written Request demanding:
- Complete payment history
- Documentation of reported late payments
- Explanation of payment application
- Copies of relevant servicing records

The servicer must acknowledge within 5 business days and respond within 30 days. Failure to comply properly creates additional dispute leverage.

**4.4 Building the Mortgage Late Dispute**

Step 1: **Obtain payment history** via QWR
Step 2: **Compare to credit report** for discrepancies
Step 3: **Document timing issues** (payment date vs. processing date)
Step 4: **Draft dispute letter** citing Reg Z requirements
Step 5: **Escalate if necessary** to CFPB mortgage complaint

**4.5 Forbearance and Modification Issues**

COVID-era forbearances and loan modifications created reporting chaos:
- Forbearance should not be reported as delinquency
- Post-modification status should reflect current terms
- Trial modification periods have specific reporting rules
- CARES Act protections override normal reporting""",
        "tags": ["mortgage", "Reg Z", "RESPA", "QWR", "late payments", "forbearance", "TILA"],
        "statute_references": ["Reg Z", "RESPA §6", "TILA", "CARES Act"],
        "difficulty_level": "advanced",
        "estimated_read_time": 11
    },
    {
        "section_number": 5,
        "section_title": "Collections & The FDCPA: Validations, Limits on Contact, and Deleting Unverifiable Collections",
        "content": """Collection accounts require specialized dispute strategies leveraging the Fair Debt Collection Practices Act (FDCPA). This section covers debt validation, harassment protections, and deletion tactics.

**5.1 FDCPA Fundamentals**

The FDCPA applies to third-party debt collectors (not original creditors) and provides:
- Right to written validation of debt
- Cease communication rights
- Restrictions on contact timing and methods
- Prohibition of harassment and false statements
- Limits on contacting third parties

**5.2 The Debt Validation Letter**

Within 30 days of first contact, you can demand validation:
- Name and address of original creditor
- Amount owed with itemization
- Documentation showing you owe the debt
- Proof of collector's authority to collect

**Key validation requirements**:
- Must be in writing
- Sent within 30 days of initial communication
- Collector must cease collection until validated

**5.3 When Validation Fails**

If collector cannot properly validate:
- They cannot continue collection activity
- They should not report to credit bureaus
- You can dispute any credit reporting as unverified
- FDCPA violations may have occurred

**5.4 The FDCPA/FCRA Connection**

Use FDCPA validation failures to support FCRA disputes:

1. Send debt validation letter to collector
2. If validation inadequate, send §611 dispute to bureaus
3. Cite lack of proper validation as basis for deletion
4. If verified anyway, escalate to §623 direct dispute
5. Consider FDCPA litigation for continued collection

**5.5 Regulation F Updates**

The CFPB's Regulation F (effective Nov 2021) updated FDCPA rules:
- Limited call attempts to 7 per week per debt
- Added email and text communication rules
- Required disclosures about time-barred debt
- Clarified validation requirements

**5.6 Time-Barred Debt Strategy**

For debts past the statute of limitations:
- Collector cannot sue to collect
- Making a payment may restart SOL
- Reporting may still be valid if within 7-year window
- Use SOL expiration as additional dispute leverage""",
        "tags": ["FDCPA", "collections", "debt validation", "Regulation F", "SOL", "harassment"],
        "statute_references": ["FDCPA", "Reg F", "FCRA §611", "FCRA §623"],
        "difficulty_level": "intermediate",
        "estimated_read_time": 13
    },
    {
        "section_number": 6,
        "section_title": "Identity Theft & §605B Blocks: Lawful 'Sweep' Strategy for Fraud Accounts",
        "content": """FCRA §605B provides powerful tools for removing fraudulent accounts resulting from identity theft. This section covers proper use of identity theft blocks.

**5.1 Understanding §605B**

FCRA §605B allows identity theft victims to block reporting of fraudulent information. Key requirements:
- Must be a victim of identity theft
- Must provide appropriate proof of identity
- Must identify specific items resulting from identity theft
- Must provide copy of identity theft report

**5.2 The Identity Theft Report**

An identity theft report must include:
1. **FTC Identity Theft Affidavit** (IdentityTheft.gov)
2. **Police report** or equivalent (can be online filing)
3. **Supporting documentation** of the theft

The report must specifically identify which accounts/items are fraudulent.

**5.3 Proper §605B Request Process**

Step 1: File FTC Identity Theft Report at IdentityTheft.gov
Step 2: File police report (many jurisdictions allow online)
Step 3: Send §605B block request to each CRA with:
   - Identity theft report
   - Proof of identity
   - List of fraudulent items
   - Written statement that items are fraudulent

**5.4 CRA Obligations**

Upon receiving a valid §605B request, CRAs must:
- Block the information within 4 business days
- Notify furnishers of the block
- Not unblock without valid reason

**5.5 The "Sweep" Strategy - Lawful Application**

For genuine identity theft victims with multiple fraudulent accounts:
1. Document all fraudulent accounts comprehensively
2. File complete identity theft report
3. Send single §605B request covering all fraud items
4. Follow up to ensure all blocks implemented

**5.6 WARNING: Misuse Consequences**

§605B abuse is a federal crime. Never:
- File false identity theft reports
- Block legitimate accounts you simply want removed
- Use §605B to avoid paying valid debts
- Create documentation of theft that didn't occur

Violations can result in:
- Criminal prosecution
- Civil liability
- Reversal of all blocks
- Permanent flagging by CRAs""",
        "tags": ["identity theft", "605B", "fraud", "block", "FTC affidavit", "police report"],
        "statute_references": ["FCRA §605B", "FCRA §605A"],
        "difficulty_level": "intermediate",
        "estimated_read_time": 10
    },
    {
        "section_number": 7,
        "section_title": "Advanced FCRA Weapons: Obsolescence, DOFD Mastery, Frivolous-Dispute Defenses, and §621 Escalations",
        "content": """This section covers advanced FCRA tactics including obsolescence rules, DOFD manipulation detection, frivolous dispute responses, and regulatory escalation.

**7.1 Obsolescence Rules (FCRA §605)**

FCRA §605 sets reporting time limits:
- **7 years**: Most negative items (from DOFD)
- **10 years**: Chapter 7/11 bankruptcy (from filing)
- **7 years**: Chapter 13 bankruptcy (from filing, some from discharge)
- **7 years**: Judgments (from entry)
- **7 years**: Tax liens (from payment)
- No limit: Criminal convictions (for employment)

**7.2 Date of First Delinquency (DOFD) Mastery**

DOFD determines when the 7-year clock starts. Critical rules:
- DOFD = date of first delinquency leading to charge-off/collection
- Cannot be reset by subsequent activity
- Must be reported accurately by furnisher
- Sale of debt does not reset DOFD

**Common DOFD violations**:
- Re-aging by debt buyers
- Incorrect DOFD after account transfer
- DOFD missing or inaccurate
- Multiple DOFDs for same delinquency

**7.3 Defeating Frivolous Dispute Claims**

When bureaus claim your dispute is frivolous:

Counter-strategies:
1. **Provide new evidence** with each resubmission
2. **Vary dispute focus** (different aspect of same item)
3. **Document basis clearly** in dispute letter
4. **File CFPB complaint** if legitimate dispute rejected
5. **Request written explanation** of frivolous determination

**7.4 FCRA §621 Regulatory Escalation**

§621 empowers regulatory agencies to enforce FCRA. Escalation targets:

**For CRAs**: CFPB (primary), FTC
**For Banks**: OCC, Federal Reserve, FDIC
**For Credit Unions**: NCUA
**For Non-Bank Furnishers**: CFPB, FTC, State AG

Escalation letter should include:
- Specific FCRA violations alleged
- Timeline of dispute attempts
- Evidence of non-compliance
- Request for regulatory action

**7.5 Building the Escalation Case**

Before regulatory escalation:
1. Exhaust §611 and §623 processes
2. Document every communication
3. Identify specific statute violations
4. Calculate potential damages
5. Consider attorney consultation""",
        "tags": ["obsolescence", "DOFD", "frivolous disputes", "621 escalation", "regulatory", "CFPB"],
        "statute_references": ["FCRA §605", "FCRA §621", "FCRA §611", "FCRA §623"],
        "difficulty_level": "advanced",
        "estimated_read_time": 14
    },
    {
        "section_number": 8,
        "section_title": "What Bureaus Don't Advertise: e-OSCAR Limits, Furnisher Verification Weaknesses, and Lawful Pressure Points",
        "content": """Understanding system limitations and verification weaknesses allows you to craft more effective disputes. This section reveals what bureaus and furnishers don't tell consumers.

**8.1 e-OSCAR Limitations**

The e-OSCAR system has significant constraints:

**Character limits**: Dispute descriptions truncated to ~240 characters
**Code simplification**: Complex disputes reduced to 2-3 digit codes
**Document handling**: Limited attachment capability
**Verification weakness**: "Match" doesn't mean "verified"

**8.2 Furnisher Verification Reality**

What furnishers actually do during "investigation":
- Often just check if name/SSN/account match their database
- May not review attached documentation
- Frequently auto-verify within minutes
- Rely on computer matching, not human review

This creates opportunities for:
- Detailed disputes that can't be reduced to codes
- Evidence that contradicts database entries
- Requests for Method of Verification
- Documentation of inadequate investigation

**8.3 Method of Verification (MOV) Requests**

After bureau verifies, you can request:
- Description of reinvestigation procedure
- Name, address, phone of furnisher contacted
- Method by which furnisher verified information

Use MOV responses to:
- Identify weak verification processes
- Build case for inadequate investigation
- Support regulatory complaints
- Establish willfulness for litigation

**8.4 Lawful Pressure Points**

Leverage points that encourage correction:

1. **Documentation quality**: Detailed evidence creates legal risk
2. **Specific error identification**: Forces actual review
3. **Regulatory threat**: CFPB complaints get attention
4. **Litigation risk**: Attorney letters change dynamics
5. **Pattern documentation**: Multiple similar complaints signal systemic issues

**8.5 Timing Strategies**

Tactical timing considerations:
- End of month: Processing backlogs may mean less scrutiny
- After CFPB complaint: Furnisher may be more responsive
- Before SOL expiration: Creates litigation pressure
- After annual credit check: Fresh eyes on old items""",
        "tags": ["e-OSCAR", "verification", "MOV", "pressure points", "system limits", "tactics"],
        "statute_references": ["FCRA §611(a)(6)", "FCRA §611(a)(7)"],
        "difficulty_level": "advanced",
        "estimated_read_time": 11
    }
]

METRO2_COURSE_SECTIONS = [
    {
        "section_number": 1,
        "section_title": "Introduction to Metro 2® and 2025 CRRG® Updates",
        "content": """Metro 2® represents the cornerstone of standardized credit reporting in the United States, enabling data furnishers to communicate consumer credit information accurately and consistently to credit reporting agencies.

**1.1 What is Metro 2®?**

Metro 2® is an electronic data interchange (EDI) format specifically designed for the transmission of consumer credit information from data furnishers to CRAs. Introduced in the 1990s as an evolution from the earlier Metro format, it has become the industry standard, handling billions of tradeline updates annually.

**Core Components**:
- **Header Record**: Identifies the furnisher and file details
- **Base Segments**: Core account information (consumer identifiers, account number, status)
- **Enhanced Segments**: Optional segments (J1/J2 for joint accounts, K for deceased indicators)
- **Trailer Record**: Summarizes totals for validation

**Key Fields for Primary Tradelines**:
- Date Opened
- Credit Limit
- Current Balance
- Account Status (e.g., 11 for current, 97 for charge-off)
- Payment History Profile (24-month string of codes)
- Date of First Delinquency (DOFD) for negatives

**1.2 The Role of the CRRG®**

The Credit Reporting Resource Guide® (CRRG®) is the official companion to Metro 2®, published annually by CDIA. It serves as a comprehensive manual with field specifications, coding guidelines, and FAQs.

**1.3 Key 2025 Updates**

The 2025 CRRG® introduces several revisions:
- **FDCPA Dispute Reporting Guidance**: Updated emphasis on time-barred debt disclosures
- **Government Shutdown Reporting**: New FAQ on payment postponements
- **Enhanced Bankruptcy Rules**: Refinements to DOFD hierarchy and lifecycle reporting
- **Alternative Data and AI Scrutiny**: Expanded sections on utilities/rent reporting
- **New FAQs**: FAQ 71 on construction loans, updates to FAQs 46-48 for transferred accounts""",
        "tags": ["Metro 2", "CRRG", "2025 updates", "data furnisher", "reporting format"],
        "statute_references": ["FCRA §623"],
        "metro2_codes": ["Header", "Base Segment", "J1", "J2", "K Segment"],
        "difficulty_level": "beginner",
        "estimated_read_time": 12
    },
    {
        "section_number": 2,
        "section_title": "Common Metro 2® Reporting Challenges Across Industries",
        "content": """Different industries face unique Metro 2® reporting challenges. Understanding these helps identify common error patterns.

**2.1 Auto Lending Challenges**

- Lease vs. loan distinction in Account Type
- Balloon payment handling
- Voluntary surrender vs. repossession coding
- Trade-in value vs. loan balance discrepancies

**2.2 Mortgage Reporting Complexities**

- Escrow account integration
- Modification and forbearance status
- Construction loan phases
- HELOC vs. fixed mortgage differences

**2.3 Revolving Credit Issues**

- Credit limit changes during billing cycle
- Promotional rate period handling
- Authorized user disputes
- Balance transfer timing

**2.4 Debt Buyer Challenges**

- Chain of title documentation
- DOFD inheritance from original creditor
- Account identification when account numbers change
- Validation documentation requirements

**2.5 Common Error Patterns**

Across all industries, watch for:
- Status code mismatches with payment history
- Balance reporting on closed accounts
- DOFD manipulation or errors
- Missing or incorrect consumer information
- Duplicate reporting by seller and buyer""",
        "tags": ["Metro 2", "auto lending", "mortgage", "revolving", "debt buyers", "error patterns"],
        "statute_references": ["FCRA §623(a)(1)"],
        "difficulty_level": "intermediate",
        "estimated_read_time": 10
    },
    {
        "section_number": 8,
        "section_title": "Decoding Special Comment & Compliance Condition Codes",
        "content": """Metro 2® uses Special Comment Codes (SCC) and Compliance Condition Codes (CCC) to provide context beyond standard fields.

**8.1 Special Comment Codes (Field 29)**

Common SCCs and their meanings:

**Account Status Clarification**:
- **AU**: Authorized user account
- **AW**: Affected by natural/declared disaster
- **B**: Account payments managed by credit counseling
- **CP**: Account closed by consumer
- **CL**: Account closed by credit grantor

**Payment Status**:
- **M**: Account participant deceased
- **Q**: Account assigned to internal/external collections
- **V**: Voluntarily surrendered
- **AC**: Account paid, zero balance

**8.2 Compliance Condition Codes (Field 30)**

CCCs indicate special circumstances:
- **XA**: Account in dispute under FCRA
- **XB**: Account in dispute under FCRA - investigation complete
- **XC**: Completed investigation - consumer disagrees
- **XF**: Account being reported per §605B identity theft block
- **XH**: Account in dispute under FCRA and meets FCRA requirements
- **XR**: Meets requirements for removal

**8.3 Code Violations to Watch**

Common Metro 2® code errors that support disputes:
- Missing XA code during active dispute
- Incorrect status code for account condition
- SCC/CCC conflicts with base segment data
- Missing AU code for authorized user
- Disaster codes not applied when applicable""",
        "tags": ["Metro 2", "SCC", "CCC", "special comment", "compliance condition", "dispute indicators"],
        "statute_references": ["FCRA §611", "FCRA §623"],
        "metro2_codes": ["AU", "AW", "B", "CP", "CL", "M", "Q", "V", "AC", "XA", "XB", "XC", "XF", "XH", "XR"],
        "difficulty_level": "advanced",
        "estimated_read_time": 11
    },
    {
        "section_number": 9,
        "section_title": "Reporting Practices: Monthly vs. Cyclical, Account Status, Payment History Profile, and DOFD Hierarchy",
        "content": """Understanding Metro 2® reporting practices is essential for identifying violations and crafting effective disputes.

**9.1 Account Status Codes**

Two-digit codes indicating current account condition:

**Current/Paid**:
- **11**: Current account (0 days past due)
- **13**: Paid or closed account, zero balance

**Delinquent**:
- **71**: 30 days past due
- **78**: 60 days past due
- **80**: 90 days past due
- **82**: 120 days past due
- **83**: 150 days past due
- **84**: 180+ days past due

**Derogatory**:
- **93**: Account assigned to collections
- **94**: Foreclosure
- **95**: Voluntary surrender
- **96**: Repossession
- **97**: Charge-off

**9.2 Payment History Profile**

The 24-month payment history (Field 25) uses single-digit codes:
- **0**: Current
- **1**: 30-59 days past due
- **2**: 60-89 days past due
- **3**: 90-119 days past due
- **4**: 120-149 days past due
- **5**: 150-179 days past due
- **6**: 180+ days past due
- **B**: No payment history available this month
- **D**: No payment history required
- **E**: Zero balance and current

**9.3 DOFD Hierarchy**

Date of First Delinquency rules:
1. DOFD starts with first delinquency leading to current derogatory status
2. DOFD cannot be reset by sale, transfer, or subsequent payment
3. DOFD must be inherited by debt buyers
4. Incorrect DOFD extends reporting period (re-aging violation)

**9.4 Status/Payment History Conflicts**

Common violations:
- Status code 11 (current) with late payment history
- Status code 97 (charge-off) with zero-filled payment history
- DOFD missing on derogatory account
- Payment history showing improvement but status unchanged""",
        "tags": ["Metro 2", "account status", "payment history", "DOFD", "status codes", "violations"],
        "statute_references": ["FCRA §605", "FCRA §623"],
        "metro2_codes": ["11", "13", "71", "78", "80", "82", "83", "84", "93", "94", "95", "96", "97"],
        "difficulty_level": "intermediate",
        "estimated_read_time": 13
    }
]

METRO2_CODES_DATA = [
    {"code_type": "account_status", "code": "11", "name": "Current Account", "description": "Account is current with 0 days past due. All payments received on time.", "category": "Current", "is_derogatory": False, "severity_score": 0},
    {"code_type": "account_status", "code": "13", "name": "Paid/Closed Zero Balance", "description": "Account paid in full with zero balance. Account is closed.", "category": "Closed", "is_derogatory": False, "severity_score": 0},
    {"code_type": "account_status", "code": "71", "name": "30 Days Past Due", "description": "Account is 30 days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 30},
    {"code_type": "account_status", "code": "78", "name": "60 Days Past Due", "description": "Account is 60 days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 40},
    {"code_type": "account_status", "code": "80", "name": "90 Days Past Due", "description": "Account is 90 days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 50},
    {"code_type": "account_status", "code": "82", "name": "120 Days Past Due", "description": "Account is 120 days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 60},
    {"code_type": "account_status", "code": "83", "name": "150 Days Past Due", "description": "Account is 150 days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 70},
    {"code_type": "account_status", "code": "84", "name": "180+ Days Past Due", "description": "Account is 180 or more days past due as of the Date of Account Information.", "category": "Delinquent", "is_derogatory": True, "severity_score": 80},
    {"code_type": "account_status", "code": "93", "name": "Account Assigned to Collections", "description": "Account has been assigned to internal or external collection department/agency.", "category": "Derogatory", "is_derogatory": True, "severity_score": 85},
    {"code_type": "account_status", "code": "94", "name": "Foreclosure", "description": "Foreclosure proceedings have been initiated on the account.", "category": "Derogatory", "is_derogatory": True, "severity_score": 95},
    {"code_type": "account_status", "code": "95", "name": "Voluntary Surrender", "description": "Consumer voluntarily surrendered the collateral securing the account.", "category": "Derogatory", "is_derogatory": True, "severity_score": 90},
    {"code_type": "account_status", "code": "96", "name": "Repossession", "description": "Collateral was repossessed by the creditor.", "category": "Derogatory", "is_derogatory": True, "severity_score": 90},
    {"code_type": "account_status", "code": "97", "name": "Charge-off", "description": "Account has been charged off by the creditor. Debt is considered uncollectible.", "category": "Derogatory", "is_derogatory": True, "severity_score": 100},
    {"code_type": "special_comment", "code": "AU", "name": "Authorized User", "description": "Account holder is an authorized user, not the primary account holder.", "category": "Account Type", "is_derogatory": False, "severity_score": 0, "dispute_language": "This account is reported as an authorized user account. I did not authorize my addition to this account and request removal under FCRA."},
    {"code_type": "special_comment", "code": "AW", "name": "Natural Disaster", "description": "Account affected by natural or declared disaster. Special accommodation in place.", "category": "Accommodation", "is_derogatory": False, "severity_score": 0},
    {"code_type": "special_comment", "code": "B", "name": "Credit Counseling", "description": "Account payments being managed through credit counseling program.", "category": "Payment Plan", "is_derogatory": False, "severity_score": 0},
    {"code_type": "special_comment", "code": "CP", "name": "Closed by Consumer", "description": "Account was closed at consumer request.", "category": "Closure", "is_derogatory": False, "severity_score": 0},
    {"code_type": "special_comment", "code": "CL", "name": "Closed by Creditor", "description": "Account was closed by credit grantor.", "category": "Closure", "is_derogatory": False, "severity_score": 5},
    {"code_type": "special_comment", "code": "M", "name": "Participant Deceased", "description": "Account participant (primary or secondary) is deceased.", "category": "Special Status", "is_derogatory": False, "severity_score": 0},
    {"code_type": "special_comment", "code": "Q", "name": "Assigned to Collections", "description": "Account has been assigned to internal or external collections.", "category": "Collections", "is_derogatory": True, "severity_score": 80},
    {"code_type": "special_comment", "code": "V", "name": "Voluntarily Surrendered", "description": "Collateral was voluntarily surrendered by consumer.", "category": "Derogatory", "is_derogatory": True, "severity_score": 85},
    {"code_type": "special_comment", "code": "AC", "name": "Account Paid, Zero Balance", "description": "Account has been paid and now has zero balance.", "category": "Paid", "is_derogatory": False, "severity_score": 0},
    {"code_type": "compliance_condition", "code": "XA", "name": "Account in Dispute", "description": "Account is currently in dispute under FCRA. Consumer has filed dispute with CRA.", "category": "Dispute", "is_derogatory": False, "severity_score": 0, "fcra_reference": "FCRA §611"},
    {"code_type": "compliance_condition", "code": "XB", "name": "Dispute Investigation Complete", "description": "Account was in dispute, investigation is now complete.", "category": "Dispute", "is_derogatory": False, "severity_score": 0, "fcra_reference": "FCRA §611"},
    {"code_type": "compliance_condition", "code": "XC", "name": "Consumer Disagrees After Investigation", "description": "Investigation complete but consumer disagrees with outcome.", "category": "Dispute", "is_derogatory": False, "severity_score": 0, "fcra_reference": "FCRA §611"},
    {"code_type": "compliance_condition", "code": "XF", "name": "Identity Theft Block", "description": "Account blocked per FCRA §605B identity theft provisions.", "category": "Identity Theft", "is_derogatory": False, "severity_score": 0, "fcra_reference": "FCRA §605B"},
    {"code_type": "compliance_condition", "code": "XH", "name": "Dispute Meets FCRA Requirements", "description": "Dispute meets FCRA requirements for inclusion.", "category": "Dispute", "is_derogatory": False, "severity_score": 0, "fcra_reference": "FCRA §611"},
    {"code_type": "compliance_condition", "code": "XR", "name": "Meets Removal Requirements", "description": "Account meets requirements for removal from credit file.", "category": "Removal", "is_derogatory": False, "severity_score": 0},
    {"code_type": "payment_history", "code": "0", "name": "Current", "description": "Payment was current for this month. No delinquency.", "category": "Current", "is_derogatory": False, "severity_score": 0},
    {"code_type": "payment_history", "code": "1", "name": "30-59 Days Late", "description": "Payment was 30-59 days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 30},
    {"code_type": "payment_history", "code": "2", "name": "60-89 Days Late", "description": "Payment was 60-89 days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 45},
    {"code_type": "payment_history", "code": "3", "name": "90-119 Days Late", "description": "Payment was 90-119 days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 60},
    {"code_type": "payment_history", "code": "4", "name": "120-149 Days Late", "description": "Payment was 120-149 days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 75},
    {"code_type": "payment_history", "code": "5", "name": "150-179 Days Late", "description": "Payment was 150-179 days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 85},
    {"code_type": "payment_history", "code": "6", "name": "180+ Days Late", "description": "Payment was 180 or more days past due for this month.", "category": "Late", "is_derogatory": True, "severity_score": 95},
    {"code_type": "payment_history", "code": "B", "name": "No Payment History", "description": "No payment history available for this month.", "category": "No Data", "is_derogatory": False, "severity_score": 0},
    {"code_type": "payment_history", "code": "D", "name": "No Payment Required", "description": "No payment required this month (deferment, forbearance, etc.).", "category": "Accommodation", "is_derogatory": False, "severity_score": 0},
    {"code_type": "payment_history", "code": "E", "name": "Zero Balance Current", "description": "Zero balance and current for this month.", "category": "Current", "is_derogatory": False, "severity_score": 0},
]

SOPS_DATA = [
    {
        "title": "New Client Onboarding - 30-Day Kickoff",
        "category": "Client Management",
        "subcategory": "Onboarding",
        "description": "Standard operating procedure for onboarding new credit repair clients within the first 30 days.",
        "content": """This SOP covers the complete client onboarding process from signup to first dispute submission.""",
        "steps": [
            {"order": 1, "title": "Collect Client Information", "description": "Gather all required personal information, identification, and credit monitoring credentials.", "duration_minutes": 30},
            {"order": 2, "title": "Pull Credit Reports", "description": "Access credit reports from all three bureaus via client's credit monitoring service.", "duration_minutes": 15},
            {"order": 3, "title": "Run AI Analysis", "description": "Upload credit reports to platform for automated FCRA violation detection.", "duration_minutes": 5},
            {"order": 4, "title": "Review AI Results", "description": "Review detected violations, verify accuracy, and identify priority items.", "duration_minutes": 45},
            {"order": 5, "title": "Create Dispute Strategy", "description": "Develop dispute strategy prioritizing high-impact items and quick wins.", "duration_minutes": 30},
            {"order": 6, "title": "Generate Round 1 Letters", "description": "Generate §611 dispute letters for first round of disputes.", "duration_minutes": 20},
            {"order": 7, "title": "Client Review Call", "description": "Schedule call to review findings and get client approval on strategy.", "duration_minutes": 30},
            {"order": 8, "title": "Send Disputes", "description": "Mail certified letters to all three bureaus.", "duration_minutes": 15}
        ],
        "checklist_items": [
            {"item": "Client signed engagement agreement", "required": True},
            {"item": "Collected valid ID (2 forms)", "required": True},
            {"item": "Credit monitoring access confirmed", "required": True},
            {"item": "Credit reports obtained from all 3 bureaus", "required": True},
            {"item": "AI analysis completed", "required": True},
            {"item": "Violations reviewed and prioritized", "required": True},
            {"item": "Dispute strategy documented", "required": True},
            {"item": "Round 1 letters generated", "required": True},
            {"item": "Client approved dispute items", "required": True},
            {"item": "Letters sent via certified mail", "required": True}
        ],
        "timeline_days": 30,
        "difficulty": "standard",
        "required_role": "paralegal",
        "related_statutes": ["FCRA §611", "CROA"],
        "tips": [
            "Always verify credit monitoring credentials before client leaves initial consultation",
            "Prioritize items that will have the biggest score impact first",
            "Document all client communications in the case notes"
        ],
        "warnings": [
            "Never guarantee specific outcomes or timelines to clients",
            "Ensure CROA disclosures are provided before collecting payment",
            "Do not dispute accurate information - focus on inaccuracies only"
        ]
    },
    {
        "title": "Round 2 Dispute Processing - 60-Day Escalation",
        "category": "Dispute Management",
        "subcategory": "Round 2",
        "description": "SOP for processing Round 2 disputes after receiving bureau responses to initial disputes.",
        "content": """This SOP covers the escalation process for items verified in Round 1, including Method of Verification requests and §623 direct furnisher disputes.""",
        "steps": [
            {"order": 1, "title": "Review Bureau Responses", "description": "Analyze responses from Round 1 disputes. Categorize as deleted, updated, or verified.", "duration_minutes": 30},
            {"order": 2, "title": "Update Case Status", "description": "Update platform with dispute outcomes. Mark deletions as wins.", "duration_minutes": 15},
            {"order": 3, "title": "Request MOV for Verified Items", "description": "Send Method of Verification requests for items verified without adequate explanation.", "duration_minutes": 20},
            {"order": 4, "title": "Prepare §623 Direct Disputes", "description": "Draft direct furnisher dispute letters for stubborn items.", "duration_minutes": 45},
            {"order": 5, "title": "Gather Additional Evidence", "description": "Request any additional documentation from client that supports disputes.", "duration_minutes": 30},
            {"order": 6, "title": "Generate Round 2 Letters", "description": "Create dispute letters with new evidence and different dispute angles.", "duration_minutes": 25},
            {"order": 7, "title": "Client Progress Update", "description": "Send client update on Round 1 results and Round 2 strategy.", "duration_minutes": 15},
            {"order": 8, "title": "Mail Round 2 Disputes", "description": "Send all Round 2 letters via certified mail.", "duration_minutes": 15}
        ],
        "checklist_items": [
            {"item": "All Round 1 responses received and logged", "required": True},
            {"item": "Deletions/updates recorded in system", "required": True},
            {"item": "MOV requests prepared for verified items", "required": True},
            {"item": "§623 letters drafted for direct furnisher disputes", "required": True},
            {"item": "New evidence gathered and attached", "required": True},
            {"item": "Round 2 letters vary from Round 1 approach", "required": True},
            {"item": "Client notified of progress", "required": True},
            {"item": "Letters sent via certified mail", "required": True}
        ],
        "timeline_days": 60,
        "difficulty": "intermediate",
        "required_role": "paralegal",
        "related_statutes": ["FCRA §611", "FCRA §623", "FCRA §611(a)(6)"],
        "tips": [
            "Always vary your dispute angle - don't send identical disputes",
            "MOV requests often reveal weak verification procedures",
            "Direct furnisher disputes bypass e-OSCAR limitations"
        ],
        "warnings": [
            "Do not submit substantially similar disputes without new evidence",
            "Keep copies of all certified mail receipts",
            "Track 30-day response deadlines carefully"
        ]
    },
    {
        "title": "ChexSystems/EWS Dispute Process",
        "category": "Specialty Bureaus",
        "subcategory": "ChexSystems",
        "description": "SOP for disputing items on ChexSystems and Early Warning Services reports.",
        "content": """ChexSystems and EWS require specialized dispute processes. This SOP covers the complete workflow for removing inaccurate banking history items.""",
        "steps": [
            {"order": 1, "title": "Obtain ChexSystems Report", "description": "Request consumer disclosure from ChexSystems and/or EWS.", "duration_minutes": 15},
            {"order": 2, "title": "Analyze Report Items", "description": "Review reported items for accuracy, completeness, and obsolescence.", "duration_minutes": 30},
            {"order": 3, "title": "Identify Dispute Grounds", "description": "Document specific inaccuracies or violations for each item.", "duration_minutes": 20},
            {"order": 4, "title": "Gather Supporting Documents", "description": "Collect bank statements, account closure letters, or other evidence.", "duration_minutes": 30},
            {"order": 5, "title": "Draft ChexSystems Dispute", "description": "Prepare dispute letter specific to ChexSystems format requirements.", "duration_minutes": 25},
            {"order": 6, "title": "Draft EWS Dispute", "description": "Prepare separate dispute for Early Warning Services if applicable.", "duration_minutes": 25},
            {"order": 7, "title": "Submit Disputes", "description": "Send disputes via certified mail to appropriate addresses.", "duration_minutes": 15},
            {"order": 8, "title": "Track Response Deadlines", "description": "Monitor 30-day response windows and follow up as needed.", "duration_minutes": 10}
        ],
        "checklist_items": [
            {"item": "ChexSystems consumer disclosure obtained", "required": True},
            {"item": "EWS consumer disclosure obtained (if applicable)", "required": False},
            {"item": "All reported items reviewed for accuracy", "required": True},
            {"item": "Dispute grounds documented for each item", "required": True},
            {"item": "Supporting documentation gathered", "required": True},
            {"item": "Dispute letters customized for specialty bureaus", "required": True},
            {"item": "Disputes sent via certified mail", "required": True},
            {"item": "Response deadlines tracked in system", "required": True}
        ],
        "timeline_days": 45,
        "difficulty": "intermediate",
        "required_role": "paralegal",
        "related_statutes": ["FCRA §611", "FCRA §605"],
        "tips": [
            "ChexSystems and EWS have their own dispute addresses - don't use CRA addresses",
            "NSF fees and closed-for-cause accounts are commonly disputed items",
            "Many items on ChexSystems are reported inaccurately or are obsolete"
        ],
        "warnings": [
            "ChexSystems items can prevent opening new bank accounts",
            "EWS and ChexSystems are separate bureaus - dispute with both if items appear on both",
            "5-year reporting period applies to most ChexSystems items"
        ]
    },
    {
        "title": "FCRA §605B Identity Theft Block Request",
        "category": "Identity Theft",
        "subcategory": "605B Block",
        "description": "SOP for properly requesting identity theft blocks under FCRA §605B.",
        "content": """This SOP covers the complete process for legitimate §605B identity theft block requests, including documentation requirements and submission procedures.""",
        "steps": [
            {"order": 1, "title": "Verify Identity Theft", "description": "Confirm with client that accounts are result of actual identity theft.", "duration_minutes": 20},
            {"order": 2, "title": "File FTC Identity Theft Report", "description": "Complete FTC affidavit at IdentityTheft.gov with client.", "duration_minutes": 30},
            {"order": 3, "title": "File Police Report", "description": "Assist client in filing police report (online or in-person).", "duration_minutes": 45},
            {"order": 4, "title": "Identify Fraudulent Accounts", "description": "List all accounts resulting from identity theft on credit reports.", "duration_minutes": 20},
            {"order": 5, "title": "Gather Identity Documents", "description": "Collect proof of identity (driver's license, SSN card, utility bills).", "duration_minutes": 15},
            {"order": 6, "title": "Draft §605B Request Letter", "description": "Prepare block request letter citing §605B requirements.", "duration_minutes": 25},
            {"order": 7, "title": "Compile Documentation Package", "description": "Assemble FTC affidavit, police report, ID copies, and account list.", "duration_minutes": 20},
            {"order": 8, "title": "Submit to All CRAs", "description": "Send §605B requests to Equifax, Experian, and TransUnion.", "duration_minutes": 15}
        ],
        "checklist_items": [
            {"item": "Client confirmed accounts are fraudulent", "required": True},
            {"item": "FTC Identity Theft Report completed", "required": True},
            {"item": "Police report filed and copy obtained", "required": True},
            {"item": "All fraudulent accounts identified and listed", "required": True},
            {"item": "Two forms of ID collected", "required": True},
            {"item": "§605B request letter drafted", "required": True},
            {"item": "Complete documentation package assembled", "required": True},
            {"item": "Requests sent to all three bureaus", "required": True}
        ],
        "timeline_days": 14,
        "difficulty": "intermediate",
        "required_role": "paralegal",
        "related_statutes": ["FCRA §605B", "FCRA §605A"],
        "tips": [
            "Many police departments now allow online identity theft reporting",
            "The FTC Identity Theft Report can be completed entirely online",
            "CRAs must block within 4 business days of receiving valid request"
        ],
        "warnings": [
            "CRITICAL: §605B is ONLY for genuine identity theft - misuse is a federal crime",
            "Never file false identity theft reports",
            "Do not use §605B to remove legitimate accounts the client simply wants deleted",
            "False claims can result in criminal prosecution and civil liability"
        ]
    },
    {
        "title": "90-Day Case Review and Strategy Adjustment",
        "category": "Case Management",
        "subcategory": "Reviews",
        "description": "SOP for conducting comprehensive 90-day case reviews and adjusting dispute strategies.",
        "content": """This SOP covers the process for reviewing case progress at the 90-day mark and making strategic adjustments based on results.""",
        "steps": [
            {"order": 1, "title": "Compile Case Metrics", "description": "Calculate total items disputed, deleted, and remaining.", "duration_minutes": 20},
            {"order": 2, "title": "Review Score Progress", "description": "Compare current credit scores to baseline scores.", "duration_minutes": 15},
            {"order": 3, "title": "Analyze Stubborn Items", "description": "Identify items that have survived multiple dispute rounds.", "duration_minutes": 30},
            {"order": 4, "title": "Evaluate Escalation Options", "description": "Consider CFPB complaints, §621 escalations, or attorney referral for stubborn items.", "duration_minutes": 25},
            {"order": 5, "title": "Prepare Client Report", "description": "Create comprehensive progress report for client.", "duration_minutes": 30},
            {"order": 6, "title": "Strategy Meeting", "description": "Conduct strategy call with client to review progress and next steps.", "duration_minutes": 45},
            {"order": 7, "title": "Update Case Plan", "description": "Document revised strategy in case file.", "duration_minutes": 20},
            {"order": 8, "title": "Set Next Milestones", "description": "Establish goals and timeline for next 30-day period.", "duration_minutes": 15}
        ],
        "checklist_items": [
            {"item": "All dispute outcomes logged and categorized", "required": True},
            {"item": "Score improvements calculated", "required": True},
            {"item": "Stubborn items identified for escalation review", "required": True},
            {"item": "Escalation options evaluated", "required": True},
            {"item": "Progress report prepared", "required": True},
            {"item": "Client strategy call completed", "required": True},
            {"item": "Case plan updated with new strategy", "required": True},
            {"item": "Next milestones documented", "required": True}
        ],
        "timeline_days": 90,
        "difficulty": "standard",
        "required_role": "paralegal",
        "related_statutes": ["FCRA §611", "FCRA §621"],
        "tips": [
            "Track deletion rates by item type to identify what's working",
            "Consider different dispute approaches for stubborn items",
            "CFPB complaints often get results when standard disputes fail"
        ],
        "warnings": [
            "Don't continue disputing items that are clearly accurate",
            "Document client expectations and manage them realistically",
            "Keep records of all strategy discussions"
        ]
    }
]

def seed_knowledge_content(db):
    """Seed the knowledge_content table with course sections."""
    print("Seeding Credit Repair Course sections...")

    for section in CREDIT_REPAIR_SECTIONS:
        existing = db.query(KnowledgeContent).filter_by(
            course="credit_repair",
            section_number=section["section_number"]
        ).first()

        if existing:
            print(f"  Updating Section {section['section_number']}: {section['section_title'][:50]}...")
            existing.section_title = section["section_title"]
            existing.content = section["content"]
            existing.tags = section.get("tags", [])
            existing.statute_references = section.get("statute_references", [])
            existing.difficulty_level = section.get("difficulty_level", "intermediate")
            existing.estimated_read_time = section.get("estimated_read_time", 10)
        else:
            print(f"  Adding Section {section['section_number']}: {section['section_title'][:50]}...")
            content = KnowledgeContent(
                course="credit_repair",
                section_number=section["section_number"],
                section_title=section["section_title"],
                content=section["content"],
                content_type="article",
                tags=section.get("tags", []),
                statute_references=section.get("statute_references", []),
                difficulty_level=section.get("difficulty_level", "intermediate"),
                estimated_read_time=section.get("estimated_read_time", 10),
                display_order=section["section_number"]
            )
            db.add(content)

    print("Seeding Metro 2® Course sections...")

    for section in METRO2_COURSE_SECTIONS:
        existing = db.query(KnowledgeContent).filter_by(
            course="metro2",
            section_number=section["section_number"]
        ).first()

        if existing:
            print(f"  Updating Section {section['section_number']}: {section['section_title'][:50]}...")
            existing.section_title = section["section_title"]
            existing.content = section["content"]
            existing.tags = section.get("tags", [])
            existing.statute_references = section.get("statute_references", [])
            existing.metro2_codes = section.get("metro2_codes", [])
            existing.difficulty_level = section.get("difficulty_level", "intermediate")
            existing.estimated_read_time = section.get("estimated_read_time", 10)
        else:
            print(f"  Adding Section {section['section_number']}: {section['section_title'][:50]}...")
            content = KnowledgeContent(
                course="metro2",
                section_number=section["section_number"],
                section_title=section["section_title"],
                content=section["content"],
                content_type="article",
                tags=section.get("tags", []),
                statute_references=section.get("statute_references", []),
                metro2_codes=section.get("metro2_codes", []),
                difficulty_level=section.get("difficulty_level", "intermediate"),
                estimated_read_time=section.get("estimated_read_time", 10),
                display_order=section["section_number"]
            )
            db.add(content)

    db.commit()
    print(f"✅ Knowledge content seeded successfully!")

def seed_metro2_codes(db):
    """Seed the Metro 2® code lookup tables."""
    print("Seeding Metro 2® codes...")

    for code_data in METRO2_CODES_DATA:
        existing = db.query(Metro2Code).filter_by(
            code_type=code_data["code_type"],
            code=code_data["code"]
        ).first()

        if existing:
            print(f"  Updating {code_data['code_type']} code {code_data['code']}...")
            for key, value in code_data.items():
                setattr(existing, key, value)
        else:
            print(f"  Adding {code_data['code_type']} code {code_data['code']}: {code_data['name']}")
            code = Metro2Code(**code_data)
            db.add(code)

    db.commit()
    print(f"✅ Metro 2® codes seeded successfully! ({len(METRO2_CODES_DATA)} codes)")

def seed_sops(db):
    """Seed the SOP table with standard operating procedures."""
    print("Seeding Standard Operating Procedures...")

    for sop_data in SOPS_DATA:
        existing = db.query(SOP).filter_by(title=sop_data["title"]).first()

        if existing:
            print(f"  Updating SOP: {sop_data['title'][:50]}...")
            for key, value in sop_data.items():
                setattr(existing, key, value)
        else:
            print(f"  Adding SOP: {sop_data['title'][:50]}...")
            sop = SOP(**sop_data)
            db.add(sop)

    db.commit()
    print(f"✅ SOPs seeded successfully! ({len(SOPS_DATA)} procedures)")

def main():
    print("=" * 60)
    print("TRAINING CONTENT SEEDING SCRIPT")
    print("=" * 60)
    print()

    db = get_db()

    try:
        seed_knowledge_content(db)
        print()
        seed_metro2_codes(db)
        print()
        seed_sops(db)
        print()
        print("=" * 60)
        print("ALL TRAINING CONTENT SEEDED SUCCESSFULLY!")
        print("=" * 60)
    except Exception as e:
        print(f"Error seeding content: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
