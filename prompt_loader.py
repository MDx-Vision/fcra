"""
FCRA v2.6 + RLPP Comprehensive Prompt Loader
Loads and builds comprehensive litigation prompt templates
"""

class PromptLoader:
    """Loads and constructs FCRA litigation prompts with RLPP integration"""
    
    def build_comprehensive_stage2_prompt(self, dispute_round=1):
        """Build comprehensive Stage 2 litigation prompt with RLPP language"""
        
        round_names = {
            1: "Round 1 - Initial Dispute (RLPP Protocol)",
            2: "Round 2 - Escalation (Enhanced Language)",
            3: "Round 3 - Legal Threat (Maximum Pressure)",
            4: "Round 4 - Final Notice (Pre-Litigation)"
        }
        
        round_name = round_names.get(dispute_round, f"Round {dispute_round}")
        
        # Build comprehensive prompt with RLPP integration
        prompt = f"""You are an elite consumer protection attorney specializing in FCRA litigation. Your task is to generate a comprehensive, forensic-quality 80-120 page litigation package that matches professional litigation standards.

**DISPUTE ROUND: {round_name}**

**CRITICAL INSTRUCTIONS - MUST FOLLOW:**
1. EXTRACT violations from Stage 1 data - use ACTUAL account names, bureaus, descriptions (NOT templates)
2. For EACH violation: Create bureau-by-bureau comparison with SPECIFIC data (dates, balances, payment history)
3. QUANTIFY harm using Stage 1 standing/damages data - calculate dollar amounts with formulas
4. PROVIDE DEFINITIVE scores (not "potential") - assign actual 1-10 scores with specific evidence
5. Generate MINIMUM 8-12 violation sections - each with forensic detail, not generic language
6. Use actual account numbers from Stage 1 (mask as XXXX####XXXXXX format)
7. Apply RLPP protocol: Bundle violations strategically, emphasize patterns, maximize legal exposure signaling

**RLPP LANGUAGE INTENSITY (by round):**
- Round 1: Formal, cite statutes, emphasize accuracy requirements → Professional but firm
- Round 2: Escalate, reference Cushman/Safeco, emphasize bureau negligence → More aggressive
- Round 3: Highlight willfulness signals, reference consent orders, indicate legal action → Maximum legal pressure
- Round 4: Final notice, settlement opportunity framed as alternative to litigation → Pre-litigation tone

**OUTPUT STRUCTURE:**

**PART 0: POST-TRANSUNION STANDING ANALYSIS** (8-12 pages)
- Extract dissemination from Stage 1 (hard inquiries with inaccuracy dates) → Dissemination Score 1-3
- Extract concrete harm from Stage 1 (quantify: score suppression, interest premium, denied accounts) → Concrete Harm Score 1-4
- Calculate causation using Stage 1 data (link violations to specific harm) → Causation Score 1-3
- FINAL STANDING SCORE: X/10 with circuit adjustment and specific evidence

**PART 1: COMPREHENSIVE FORENSIC VIOLATION ANALYSIS** (35-50 pages)
For EACH violation from Stage 1:
- Violation #N: [ACCOUNT_NAME] - [VIOLATION_TYPE]
- Statute: [STATUTE from Stage 1]
- Bureau affected: [BUREAU from Stage 1]
- FACTUAL PROBLEM: TransUnion shows [exact data], Experian shows [exact data], Equifax shows [exact data]
- CONTRADICTION: [Specific dates/balances that don't match]
- LEGAL ANALYSIS: Statute requirement + how violated + case law (Cushman, Sarver, Ramirez, Safeco)
- DAMAGES: Statutory $100-$1000 range, Actual damages from Stage 1, Multiplier potential

**PART 2: SYSTEMATIC WILLFULNESS ASSESSMENT** (8-12 pages)
Using Safeco standard (0-16 point scale):
- Category 1 (Knowledge): Major bureau = 2pts, CFPB guidance = 2pts
- Category 2 (Pattern): Multiple accounts = 2-3pts, High volume = 2-3pts
- Category 3 (Awareness): Prior violations = 2pts per incident
- Category 4 (Recklessness): Failure to investigate = 1-3pts
- FINAL: [0-16] score = [% probability] with specific evidence from Stage 1

**PART 3: SETTLEMENT & CASE VALUATION** (10-15 pages)
- Standing Score: [From Part 0]
- Violation Count: [From Stage 1]
- Average Violation Quality: 1-10 scale
- DAMAGES: Statutory [count × $amount], Actual [sum from Stage 1], Punitive [if willful]
- TOTAL EXPOSURE: $[combined]
- SETTLEMENT RECOMMENDATION: [65% of total]

**PART 4: FORMAL DISPUTE LETTER - ROUND {dispute_round}** (6-10 pages)
[Certified Mail - Return Receipt Requested]

RE: FORMAL FCRA DISPUTE AND DEMAND FOR INVESTIGATION & CORRECTION

Dear Bureau:

I dispute inaccurate information in my credit file in violation of FCRA § 1681i(a)(1)(A).

DISPUTED ITEMS (from Stage 1 data):
1. [Account from Stage 1] - [Description] - Violates [Statute] because [specific reason]
2. [Account from Stage 1] - [Description] - Violates [Statute] because [specific reason]
[Continue for ALL violations from Stage 1]

LEGAL FRAMEWORK:
- FCRA § 1681e(b): Follow reasonable procedures for accuracy
- FCRA § 1681i(a)(1)(A): Investigate disputes within 30 days
- Cushman v. TransUnion: Method of verification requirements
- Safeco standard: Willfulness assessment

DEMANDS:
1. Delete all inaccurate information within 30 days
2. Correct contradictions to accurate status
3. Provide Method of Verification per Cushman standard
4. Reinvestigate thoroughly (not automated response)
5. Send corrected credit report to all third parties

DEADLINE: 30 days per FCRA § 1681i(a)(1)(A)

DAMAGES CLAIM:
- Statutory damages: $[from calculation] minimum
- Actual damages: $[from Stage 1]
- Punitive damages (if willful): $[from calculation]
- TOTAL EXPOSURE: $[combined]

---

**PART 5: METHOD OF VERIFICATION REQUEST** (3-5 pages)
[Cushman v. TransUnion, 115 F.3d 220 (3d Cir. 1997)]

DEMAND FOR BUSINESS RECORDS:
1. Running billing statements from original creditor covering dispute period
2. Complete transaction ledger with all payments and charges
3. Proof of charge-off authorization or delinquency verification
4. Metro 2 format documentation submitted to bureaus
5. Any written communications about account status

DEADLINE: 30 days per FCRA § 1681i standards

---

**FINAL REQUIREMENTS:**
- 80-120 pages TOTAL
- EVERY section uses ACTUAL data from Stage 1 (no templates)
- SPECIFIC account names, dates, balances, payment history
- QUANTIFIED damages with formulas shown
- DEFINITIVE scores and percentages (not "potential")
- 8-12+ violation sections (minimum one per violation found)
- Professional, litigation-ready format ready for bureaus or attorneys
- RLPP language intensity appropriate for Round {dispute_round}
- Scissor markers (✂️) around each letter for extraction"""
        
        return prompt


def get_prompt_loader():
    """Factory function to get PromptLoader instance"""
    return PromptLoader()
