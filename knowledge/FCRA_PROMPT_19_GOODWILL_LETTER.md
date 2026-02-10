# FCRA PROMPT 19: GOODWILL LETTER (SEPARATE FILES)
## Request Removal of Accurate Negative Items as Courtesy

**Version:** 1.0
**Created:** February 8, 2026
**Output:** One file per creditor
**Strategy:** Request removal based on customer loyalty, not accuracy dispute

---

## HOW TO USE:

**STEP 1:** Upload credit report

**STEP 2:** Paste client info including hardship details (if any)

**STEP 3:** Claude generates personalized goodwill letters per creditor

**STEP 4:** Client sends via mail or online message

---

## IMPORTANT DISTINCTION:

**Goodwill Letter ≠ Dispute Letter**

| Dispute Letter | Goodwill Letter |
|----------------|-----------------|
| Challenges accuracy | Acknowledges accuracy |
| Cites FCRA violations | Requests courtesy removal |
| Legal language | Personal, polite tone |
| Sent to bureaus | Sent directly to creditor |
| 30-day response required | No legal obligation to respond |

**Use goodwill letters for:**
- First-time late payments
- Long-standing customers with otherwise perfect history
- Hardship circumstances (job loss, medical emergency)
- Old negative marks from years ago
- Accounts now paid in full

---

## CLIENT INFO:

```
CONSUMER INFO:
- Full Name: [Name]
- Address: [Address]
- Account Number: [XXXX] (last 4 digits)

ACCOUNT INFO:
- Creditor Name: [Name]
- Account Type: [Credit Card / Loan / etc.]
- Date Opened: [Date]
- Years as Customer: [X years]
- Late Payment Date(s): [Date(s)]
- Current Status: [Paid / Current / Closed]

HARDSHIP INFO (if applicable):
- Circumstance: [Job loss / Medical / Divorce / etc.]
- Date of Hardship: [Date]
- Resolution: [How situation was resolved]

POSITIVE HISTORY:
- Years of on-time payments: [X years]
- Other accounts with creditor: [List]
- Current relationship status: [Active customer / Loyal since XXXX]
```

---

## =======================================================================
## PROMPT STARTS HERE
## =======================================================================

===========================================================================
GOODWILL LETTER GENERATOR (SEPARATE FILES)
===========================================================================

**YOUR TASK:**

1. Review the client's account history and circumstances
2. Generate a personalized goodwill letter for each creditor
3. **SAVE EACH AS SEPARATE FILE**

**FILE NAMING:**

```
Goodwill_[CREDITOR_NAME]_[LASTNAME]_[DATE].md
```

Example: `Goodwill_CapitalOne_SMITH_20260208.md`

**Use create_file tool for each letter.**

===========================================================================
LETTER GUIDELINES
===========================================================================

**TONE:** Personal, sincere, appreciative - NOT legal or demanding

**LENGTH:** 1 page maximum (300-400 words ideal)

**KEY ELEMENTS:**
1. Express appreciation for long-standing relationship
2. Acknowledge the late payment was your fault
3. Explain circumstances without making excuses
4. Highlight your otherwise positive history
5. Request removal as a one-time courtesy
6. Explain how removal would help (mortgage, employment, etc.)
7. Thank them for consideration

**DO NOT:**
- Cite laws or regulations
- Make demands or threats
- Challenge the accuracy
- Use legal jargon
- Be overly lengthy or dramatic

===========================================================================
LETTER TEMPLATE
===========================================================================

[Consumer Name]
[Address]
[City, State ZIP]
[Phone]
[Email]

[Date]

[CREDITOR NAME]
[Goodwill Adjustment Department / Customer Relations]
[Address]

**RE: Goodwill Adjustment Request**
**Account Number ending in: [XXXX]**

Dear [Creditor] Customer Service Team,

**[OPENING - Express gratitude and establish relationship]**

I have been a loyal [Creditor] customer since [Year] and have genuinely valued our [X-year] relationship. I am writing to respectfully request a goodwill adjustment to remove a [late payment / negative mark] from [Date] on my credit report.

**[ACKNOWLEDGMENT - Take responsibility]**

I want to be clear: this is not a dispute of accuracy. The [late payment] did occur, and I take full responsibility. [If hardship: During that time, I was dealing with [circumstance], which temporarily affected my ability to manage payments as I normally would.]

**[POSITIVE HISTORY - Highlight the relationship]**

Looking at my overall history with [Creditor]:
- I have been a customer for [X] years
- I have made [X] on-time payments before and since this incident
- I currently maintain [other accounts / good standing]
- My account is now [current / paid in full]

**[THE ASK - Make the request politely]**

I am hoping [Creditor] might consider removing this one [late payment] from my credit report as a goodwill gesture. I understand there is no obligation to do so, but I would be incredibly grateful.

**[WHY IT MATTERS - Explain the impact]**

This adjustment would greatly help me [qualify for a mortgage / secure employment / achieve a financial goal]. As someone who has learned from this experience and maintained excellent standing since, I respectfully ask for your consideration.

**[CLOSING - Express gratitude]**

Thank you for taking the time to review my request. I have always appreciated [Creditor]'s customer service and hope to remain a loyal customer for many years to come.

Sincerely,

[Signature]

[Consumer Name]
[Phone]
[Email]

---

**ENCLOSURES (Optional but helpful):**
- Recent payment history showing on-time payments
- Proof of hardship resolution (if applicable)
- Letter of recommendation from employer (if applicable)

===========================================================================
CUSTOMIZATION NOTES
===========================================================================

**For Different Scenarios:**

**First-Time Late Payment:**
- Emphasize perfect history before and after
- "One isolated incident in X years of flawless payments"

**Hardship (Medical/Job Loss/Divorce):**
- Brief explanation without over-sharing
- Focus on recovery and current stability
- "I have since regained employment and..."

**Old Negative Mark (3+ years ago):**
- Emphasize time passed and lessons learned
- Current financial responsibility
- "Since then, I have maintained perfect payment history"

**Multiple Late Payments to Same Creditor:**
- Acknowledge the pattern
- Explain the specific time period of difficulty
- Show concrete steps taken to prevent recurrence

**Paid Collection:**
- Thank them for working with you
- Request removal now that debt is satisfied
- "As a gesture of goodwill for settling the account"

===========================================================================
CREDITOR-SPECIFIC TIPS
===========================================================================

**Capital One:** Known to grant goodwill adjustments
**Chase:** Rarely grants but worth trying with strong history
**American Express:** Values customer loyalty highly
**Discover:** Generally customer-friendly
**Wells Fargo:** Submit through secure message center
**Bank of America:** Call first, then follow up in writing
**Credit Unions:** Often more flexible than big banks

**Best Practices:**
1. Call customer service first to gauge receptiveness
2. Get name of representative to address letter to
3. Send via certified mail for paper trail
4. Follow up after 30 days if no response
5. If denied, try again in 6 months

===========================================================================
OUTPUT FORMAT
===========================================================================

Generate the letter in clean, formatted text suitable for:
1. Printing and mailing
2. Copying into creditor's online message center
3. Emailing to customer service

Include the file name at the top:
```
FILE: Goodwill_[CREDITOR]_[LASTNAME]_[DATE].md
```

===========================================================================
END OF PROMPT
===========================================================================
