import os
import re
import io
import zipfile

# API Configuration
ANTHROPIC_API_KEY = os.environ['FCRA Automation Secure']
from anthropic import Anthropic

client = Anthropic(api_key=ANTHROPIC_API_KEY)
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
from datetime import datetime
from database import init_db, get_db, Client, CreditReport, Analysis, DisputeLetter, Violation, Standing, Damages, CaseScore
from pdf_generator import LetterPDFGenerator, SectionPDFGenerator
from litigation_tools import calculate_damages, calculate_case_score, assess_willfulness
from jwt_utils import require_jwt, create_token
import json

app = Flask(__name__)

# Allow Replit frontend + WordPress frontend + any admin UIs
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Allow large credit report uploads (up to 20MB)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Store received credit reports
credit_reports = []

# Track which analyses have been marked as delivered (in-memory flag)
delivered_cases = set()

# Initialize PDF generators
pdf_gen = LetterPDFGenerator()
section_pdf_gen = SectionPDFGenerator()

# Create required directories
os.makedirs("static/section_pdfs", exist_ok=True)
os.makedirs("static/generated_letters", exist_ok=True)
os.makedirs("static/logs", exist_ok=True)

# Initialize database
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️  Database initialization error: {e}")


@app.route('/')
def home():
    """Home page - shows form or status"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FCRA Analysis - Brightpath Ascend</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #34495e; font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        .required { color: #e74c3c; }
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 14px;
        }
        textarea { min-height: 120px; font-family: monospace; }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        button:disabled { background: #95a5a6; }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 FCRA Analysis System</h1>
        <p class="subtitle">Brightpath Ascend Group</p>

        <form id="form">
            <div class="form-group">
                <label>CLIENT NAME <span class="required">*</span></label>
                <input type="text" id="clientName" required>
            </div>

            <div class="form-group">
                <label>CMM CONTACT ID <span class="required">*</span></label>
                <input type="text" id="cmmContactId" required>
            </div>

            <div class="form-group">
                <label>CREDIT PROVIDER <span class="required">*</span></label>
                <select id="creditProvider" required>
                    <option value="">-- Select Provider --</option>
                    <option value="IdentityIQ.com">IdentityIQ.com</option>
                    <option value="MyScoreIQ.com">MyScoreIQ.com</option>
                    <option value="SmartCredit.com">SmartCredit.com</option>
                    <option value="MyFreeScoreNow.com">MyFreeScoreNow.com</option>
                    <option value="HighScoreNow.com">HighScoreNow.com</option>
                    <option value="IdentityClub.com">IdentityClub.com</option>
                    <option value="PrivacyGuard.com">PrivacyGuard.com</option>
                    <option value="IDClub.com">IDClub.com</option>
                    <option value="MyThreeScores.com">MyThreeScores.com</option>
                    <option value="MyScore750.com">MyScore750.com</option>
                    <option value="CreditHeroScore.com">CreditHeroScore.com</option>
                    <option value="CFILifePlan.com">CFILifePlan.com</option>
                </select>
            </div>

            <div class="form-group">
                <label>DISPUTE ROUND <span class="required">*</span></label>
                <select id="disputeRound" required>
                    <option value="1">Round 1 - Initial Dispute (New Client)</option>
                    <option value="2">Round 2 - MOV Request / Follow-up</option>
                    <option value="3">Round 3 - Pre-Litigation Warning</option>
                    <option value="4">Round 4 - Final Demand / Intent to Sue</option>
                </select>
                <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                    <strong>Round 1:</strong> New client - full analysis + initial strong RLPP letters<br>
                    <strong>Round 2+:</strong> Existing client - escalated letters based on bureau responses
                </small>
            </div>

            <div id="existingClientFields" style="display: none;">
                <div class="form-group">
                    <label>PREVIOUS DISPUTE LETTER(S)</label>
                    <textarea id="previousLetters" placeholder="Paste the dispute letters you previously sent to the bureaus..."></textarea>
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Copy/paste the actual letters you sent in previous rounds
                    </small>
                </div>

                <div class="form-group">
                    <label>BUREAU RESPONSE(S)</label>
                    <textarea id="bureauResponses" placeholder="Paste bureau responses here, or type 'NO RESPONSE' if they ignored you..."></textarea>
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Include all responses from Experian, TransUnion, and Equifax
                    </small>
                </div>

                <div class="form-group">
                    <label>DISPUTE TIMELINE</label>
                    <input type="text" id="disputeTimeline" placeholder="e.g., Sent 10/15/25, Response 11/1/25">
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Dates sent and received for violation tracking
                    </small>
                </div>
            </div>

<div class="form-group">
    <label>ANALYSIS MODE <span class="required">*</span></label>
    <select id="analysisMode" required>
        <option value="manual">Manual Review (Stop at verification checkpoint)</option>
        <option value="auto">Automatic (Generate complete report immediately)</option>
    </select>
    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
        <strong>Manual:</strong> Review violations before client report (recommended for new cases)<br>
        <strong>Automatic:</strong> Generate everything in one pass (faster, for clear cases)
    </small>
</div>
            <div class="form-group">
                <label>CREDIT REPORT HTML <span class="required">*</span></label>
                <textarea id="creditReportHTML" required></textarea>
            </div>

            <button type="submit">🚀 ANALYZE</button>
            <div id="status" class="status"></div>
        </form>
    </div>

    <script>
        // Show/hide existing client fields based on dispute round
        document.getElementById('disputeRound').addEventListener('change', function() {
            const round = parseInt(this.value);
            const existingFields = document.getElementById('existingClientFields');
            
            if (round > 1) {
                existingFields.style.display = 'block';
            } else {
                existingFields.style.display = 'none';
            }
        });

        document.getElementById('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            const status = document.getElementById('status');

            btn.disabled = true;
            btn.textContent = '⏳ Sending...';

            try {
                const disputeRound = parseInt(document.getElementById('disputeRound').value);
                const payload = {
                    clientName: document.getElementById('clientName').value,
                    cmmContactId: document.getElementById('cmmContactId').value,
                    creditProvider: document.getElementById('creditProvider').value,
                    disputeRound: disputeRound,
                    analysisMode: document.getElementById('analysisMode').value,
                    creditReportHTML: document.getElementById('creditReportHTML').value
                };

                // Add existing client data for Round 2+
                if (disputeRound > 1) {
                    payload.previousLetters = document.getElementById('previousLetters').value;
                    payload.bureauResponses = document.getElementById('bureauResponses').value;
                    payload.disputeTimeline = document.getElementById('disputeTimeline').value;
                }

                const response = await fetch('/webhook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (result.success) {
                    status.className = 'status success';
                    status.innerHTML = '✅ Success! Report received for ' + result.client;
                    status.style.display = 'block';
                    document.getElementById('form').reset();
                    document.getElementById('existingClientFields').style.display = 'none';
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                status.className = 'status error';
                status.innerHTML = '❌ Error: ' + error.message;
                status.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 ANALYZE';
            }
        });
    </script>
</body>
</html>'''


def clean_credit_report_html(html):
    """Strip unnecessary HTML to reduce size"""
    from bs4 import BeautifulSoup
    import re

    print(f"📊 Original size: {len(html):,} characters")

    # Remove inline styles
    html = re.sub(r'style="[^"]*"', '', html)
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Remove base64 images
    html = re.sub(r'data:image/[^;]+;base64,[^"\']+', '', html)

    # Extract just the text content
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    print(f"✂️ Cleaned size: {len(text):,} characters")
    print(
        f"💰 Saved: {len(html) - len(text):,} characters ({100 - (len(text)/len(html)*100):.1f}% reduction)"
    )

    return text


# Section markers for splitting credit reports (enhanced patterns)
SECTION_MARKERS = {
    "tradelines": ["ACCOUNTS", "TRADELINES", "REVOLVING ACCOUNTS", "INSTALLMENT ACCOUNTS", "OPEN ACCOUNTS", "CLOSED ACCOUNTS"],
    "collections": ["COLLECTION", "COLLECTIONS"],
    "public_records": ["PUBLIC RECORD", "PUBLIC RECORDS", "BANKRUPTCIES", "JUDGMENTS", "TAX LIENS"],
    "inquiries": ["INQUIRIES", "CREDIT INQUIRIES", "REGULAR INQUIRIES", "HARD INQUIRIES"],
}


def split_report_into_sections(text: str) -> dict:
    """Split cleaned report text into logical sections based on common headings"""
    sections = {k: [] for k in SECTION_MARKERS.keys()}
    current_key = None

    if not text:
        return {}

    lines = text.splitlines()
    for line in lines:
        upper = line.strip().upper()

        # Check if this line looks like a section heading
        new_key = None
        for key, markers in SECTION_MARKERS.items():
            if any(m in upper for m in markers):
                new_key = key
                break

        if new_key:
            current_key = new_key
            sections[current_key].append(line)
        elif current_key:
            sections[current_key].append(line)

    # Join and drop empty sections
    finalized = {}
    for key, lines_list in sections.items():
        joined = "\n".join(lines_list).strip()
        if joined:
            finalized[key] = joined

    print("📚 split_report_into_sections:", {k: len(v) for k, v in finalized.items()})
    return finalized


def merge_standing(standings: list) -> dict:
    """Merge multiple standing blocks (OR booleans, SUM counts, concatenate strings)"""
    if not standings:
        return {"has_concrete_harm": False, "concrete_harm_type": "", "harm_details": "", "has_dissemination": False, "dissemination_details": "", "has_causation": False, "causation_details": "", "denial_letters_count": 0, "adverse_action_notices_count": 0}

    merged = {
        "has_concrete_harm": False,
        "concrete_harm_type": [],
        "harm_details": [],
        "has_dissemination": False,
        "dissemination_details": [],
        "has_causation": False,
        "causation_details": [],
        "denial_letters_count": 0,
        "adverse_action_notices_count": 0,
    }

    for s in standings:
        if not s:
            continue
        merged["has_concrete_harm"] = merged["has_concrete_harm"] or s.get("has_concrete_harm", False)
        merged["has_dissemination"] = merged["has_dissemination"] or s.get("has_dissemination", False)
        merged["has_causation"] = merged["has_causation"] or s.get("has_causation", False)
        if s.get("concrete_harm_type"): merged["concrete_harm_type"].append(str(s.get("concrete_harm_type")))
        if s.get("harm_details"): merged["harm_details"].append(str(s.get("harm_details")))
        if s.get("dissemination_details"): merged["dissemination_details"].append(str(s.get("dissemination_details")))
        if s.get("causation_details"): merged["causation_details"].append(str(s.get("causation_details")))
        merged["denial_letters_count"] += int(s.get("denial_letters_count", 0) or 0)
        merged["adverse_action_notices_count"] += int(s.get("adverse_action_notices_count", 0) or 0)

    return {
        "has_concrete_harm": merged["has_concrete_harm"],
        "concrete_harm_type": " | ".join(merged["concrete_harm_type"]),
        "harm_details": "\n\n".join(merged["harm_details"]),
        "has_dissemination": merged["has_dissemination"],
        "dissemination_details": "\n\n".join(merged["dissemination_details"]),
        "has_causation": merged["has_causation"],
        "causation_details": "\n\n".join(merged["causation_details"]),
        "denial_letters_count": merged["denial_letters_count"],
        "adverse_action_notices_count": merged["adverse_action_notices_count"],
    }


def merge_actual_damages(damages_list: list) -> dict:
    """Merge multiple actual_damages blocks by summing numeric fields"""
    merged = {"credit_denials_amount": 0, "higher_interest_amount": 0, "credit_monitoring_amount": 0, "time_stress_amount": 0, "other_actual_amount": 0, "notes": ""}
    notes = []
    for d in damages_list:
        if not d:
            continue
        merged["credit_denials_amount"] += float(d.get("credit_denials_amount", 0) or 0)
        merged["higher_interest_amount"] += float(d.get("higher_interest_amount", 0) or 0)
        merged["credit_monitoring_amount"] += float(d.get("credit_monitoring_amount", 0) or 0)
        merged["time_stress_amount"] += float(d.get("time_stress_amount", 0) or 0)
        merged["other_actual_amount"] += float(d.get("other_actual_amount", 0) or 0)
        if d.get("notes"): notes.append(str(d["notes"]))
    merged["notes"] = "\n\n".join(notes)
    return merged


def merge_litigation_data(section_results: list) -> dict:
    """Merge litigation_data from multiple sections into one"""
    all_violations = []
    standings = []
    damages_blocks = []
    for r in section_results:
        if not r:
            continue
        all_violations.extend(r.get("violations", []) or [])
        standings.append(r.get("standing", {}) or {})
        damages_blocks.append(r.get("actual_damages", {}) or {})
    merged = {
        "violations": all_violations,
        "standing": merge_standing(standings),
        "actual_damages": merge_actual_damages(damages_blocks),
    }
    print(f"🧩 merge_litigation_data: {len(all_violations)} total violations merged")
    return merged


def run_stage1_for_all_sections(client_name, cmm_id, provider, credit_report_text, analysis_mode="manual", dispute_round=1, previous_letters="", bureau_responses="", dispute_timeline=""):
    """Split report into sections and run Stage 1 analysis per section, merge results"""
    import time
    
    sections = split_report_into_sections(credit_report_text)
    if not sections:
        return {'success': False, 'error': 'Could not detect any recognizable sections in report'}

    all_section_results = []
    combined_analysis_parts = []
    total_tokens = 0
    total_cost = 0.0
    any_cache_read = False

    for section_name, section_text in sections.items():
        print(f"\n🔍 Stage 1 analysis for section: {section_name} ({len(section_text):,} chars)")
        result = analyze_with_claude(
            client_name=client_name,
            cmm_id=cmm_id,
            provider=provider,
            credit_report_html=section_text,
            analysis_mode=analysis_mode,
            dispute_round=dispute_round,
            previous_letters=previous_letters,
            bureau_responses=bureau_responses,
            dispute_timeline=dispute_timeline,
            stage=1
        )

        if not result.get('success'):
            print(f"❌ Section {section_name} failed: {result.get('error')}")
            all_section_results.append({'section_name': section_name, 'analysis': '', 'raw_litigation_data': None, 'error': result.get('error')})
            continue

        analysis_text = result.get('analysis', '') or ''
        litigation_data = extract_litigation_data(analysis_text)
        combined_analysis_parts.append(f"\n\n{'='*80}\nSECTION: {section_name.upper()}\n{'='*80}\n\n{analysis_text}")
        all_section_results.append({'section_name': section_name, 'analysis': analysis_text, 'raw_litigation_data': litigation_data})
        total_tokens += int(result.get('tokens_used', 0) or 0)
        total_cost += float(result.get('cost', 0.0) or 0.0)
        any_cache_read = any_cache_read or bool(result.get('cache_read', False))
        time.sleep(1)  # Rate limit protection

    parsed_litigation_blocks = [r['raw_litigation_data'] for r in all_section_results if r.get('raw_litigation_data')]
    if not parsed_litigation_blocks:
        return {'success': False, 'error': 'No valid litigation_data extracted from any section', 'combined_analysis': "\n\n".join(combined_analysis_parts), 'per_section': all_section_results, 'tokens_used': total_tokens, 'cost': total_cost, 'cache_read': any_cache_read}

    merged_litigation = merge_litigation_data(parsed_litigation_blocks)
    return {'success': True, 'combined_analysis': "\n\n".join(combined_analysis_parts), 'litigation_data': merged_litigation, 'per_section': all_section_results, 'tokens_used': total_tokens, 'cost': total_cost, 'cache_read': any_cache_read}


def truncate_for_token_limit(text, max_tokens_for_report=140_000):
    """
    Hard cap the report size so the full prompt stays under Anthropic's 200k token limit.
    Rough approximation: ~4 characters per token for English text.
    """
    if not text:
        return text

    approx_tokens = len(text) / 4.0
    if approx_tokens <= max_tokens_for_report:
        return text

    ratio = max_tokens_for_report / approx_tokens
    new_len = int(len(text) * ratio)
    truncated = text[:new_len]

    print(
        f"⚠️ truncate_for_token_limit: report truncated for token limit: "
        f"{len(text):,} chars (~{approx_tokens:,.0f} tokens) -> "
        f"{len(truncated):,} chars (~{len(truncated)/4.0:,.0f} tokens)"
    )

    return truncated


def analyze_with_claude(client_name,
                        cmm_id,
                        provider,
                        credit_report_html,
                        analysis_mode='manual',
                        dispute_round=1,
                        previous_letters='',
                        bureau_responses='',
                        dispute_timeline='',
                        stage=1,
                        stage_1_results=''):
    """Send credit report to Claude for FCRA analysis - TWO STAGE WORKFLOW
    
    Stage 1: Violations/Standing/Damages analysis only (small prompt, fits token limit)
    Stage 2: Client documents/letters generation (uses Stage 1 results)
    """
    try:
        # CRITICAL: Clean & truncate HTML for Stage 1 to stay under 200k token limit
        if stage == 1:
            print(f"\n🧹 Cleaning credit report HTML to fit token limits...")
            credit_report_html = clean_credit_report_html(credit_report_html)
            print(f"🔒 Truncating to token limit...")
            credit_report_html = truncate_for_token_limit(credit_report_html, max_tokens_for_report=140_000)
        
        # Define round_names globally for both stages
        round_names = {
            1: "Round 1 - Initial Dispute (RLPP Strong Language)",
            2: "Round 2 - MOV Request / Follow-up",
            3: "Round 3 - Pre-Litigation Warning", 
            4: "Round 4 - Final Demand / Intent to Sue"
        }
        
        if stage == 1:
            # STAGE 1: Small prompt for violations/standing/damages analysis ONLY (~80-100k tokens)
            prompt = """Act as an expert consumer protection attorney. Analyze this credit report for FCRA violations.

**YOUR TASK - ANALYSIS ONLY (No client documents):**

PART 0: POST-TRANSUNION STANDING (Required first - *TransUnion LLC v. Ramirez*, 141 S. Ct. 2190)
- Verify THREE elements for each negative item:
  1. DISSEMINATION: Who viewed inaccurate information? (Lender, employer, landlord?)
  2. CONCRETE HARM: Actual damage? (Loan denial, higher APR, job rejection, rental denial?)
  3. CAUSATION: Did inaccuracy cause the harm? ("But for" test)
- Assign standing strength: STRONG (9-10/10), MODERATE (6-8/10), WEAK (3-5/10), FATAL (0-2/10)

PART 1: FORENSIC VIOLATION IDENTIFICATION
- Analyze EVERY negative item: charge-offs, collections, late payments, inquiries
- For each violation identify:
  * Account name and bureau
  * Exact FCRA section violated (§605B, §607(b), §611, §623, etc.)
  * Specific inaccuracy/violation
  * Evidence supporting the violation
  * Is it willful? (knowing/reckless disregard + objectively unreasonable)

PART 2: WILLFULNESS ASSESSMENT (Safeco standard)
- Score willfulness 0-25 based on:
  1. Direct knowledge of FCRA requirement (0-4 pts)
  2. Pattern of violations (0-5 pts)
  3. Ignoring complaints (0-6 pts)
  4. Inadequate procedures (0-5 pts)
  5. Post-violation conduct (0-5 pts)
- If score ≥15 AND objectively unreasonable = likely willful
- If score <10 OR arguably reasonable = likely negligent

PART 3: STATUTE OF LIMITATIONS VERIFICATION
- For each violation: When did it OCCUR? Within 5-year absolute limit?
- When did client DISCOVER violation? Within 2-year discovery rule?
- All violations included must be timely

PART 4: DAMAGES CALCULATION
- Statutory damages (willful only): $100-$1,000 per violation
- Actual damages: Credit denials, higher interest, credit monitoring, time/stress, emotional distress
- Calculate conservatively, based on documentation

**OUTPUT FORMAT (CRITICAL):**
After completing Parts 0-4, output this JSON at the very end:

<LITIGATION_DATA>
{
  "violations": [
    {
      "account_name": "Account Name",
      "bureau": "Equifax/Experian/TransUnion",
      "fcra_section": "§611(a)(1)(A)",
      "violation_type": "Failed Reasonable Investigation",
      "description": "Specific facts (50 words max)",
      "is_willful": true/false,
      "willfulness_indicators": "Evidence if willful"
    }
  ],
  "standing": {
    "has_concrete_harm": true/false,
    "concrete_harm_type": "Credit Denial / Higher Interest / Other",
    "harm_details": "Specific facts with dates/amounts",
    "has_dissemination": true/false,
    "dissemination_details": "Who saw the inaccuracy",
    "has_causation": true/false,
    "causation_details": "Proof inaccuracy caused harm",
    "denial_letters_count": 0,
    "adverse_action_notices_count": 0
  },
  "actual_damages": {
    "credit_denials_amount": 0,
    "higher_interest_amount": 0,
    "credit_monitoring_amount": 0,
    "time_stress_amount": 0,
    "other_actual_amount": 0,
    "notes": "Calculation details"
  }
}
</LITIGATION_DATA>

**CRITICAL RULES:**
1. Output JSON ONLY at the end - no other text after </LITIGATION_DATA>
2. Base ALL violations on your own analysis - no fabrication
3. Dollar amounts must be numbers (no $ signs, no commas)
4. Include willfulness_indicators ONLY if is_willful = true"""
        else:
            # STAGE 2: Full prompt for client documents generation (uses Stage 1 results)
            prompt = f"""Act as an expert consumer protection attorney. Generate client-facing litigation documents.

**CONTEXT - Use these Stage 1 findings:**
{stage_1_results}

**YOUR TASK - GENERATE CLIENT DOCUMENTS:**

Create a comprehensive litigation package for Round {dispute_round}:

PART 5: EXECUTIVE SUMMARY (2-3 pages)
- Case overview: violations identified, standing strength, settlement probability
- Key findings: Most damaging violations, willfulness indicators
- Recommended strategy and timeline

PART 6: DETAILED VIOLATION ANALYSIS (20-25 pages)
- For each violation: Account history, inaccuracy, evidence, legal analysis
- Standing assessment: Concrete harm, dissemination, causation with proof
- Willfulness analysis: Intent indicators, pattern evidence, comparable cases
- Case law citations: Recent decisions supporting your violations

PART 7: DISPUTE LETTER - Round {dispute_round} (5-7 pages)
- Strong RLPP language: Sophisticated legal tone, case law references
- Cite specific violations with statutory sections (§605B, §611(a)(1)(A), etc.)
- Include evidence from analysis: Dates, account details, contradictions
- Demand: Correction, deletion, or verification with tangible ledgers
- Timeline: 30-day response deadline (per FCRA §611(a)(1)(A))

PART 8: MOV REQUEST (if applicable) (2-3 pages)
- Method of Verification demand (Cushman v. TransUnion requirement)
- Request for tangible business records, running billing statements
- Proof of original furnisher contact
- 30-day deadline enforcement

PART 9: SETTLEMENT/CASE STRATEGY (3-5 pages)
- Standing strength assessment (1-10 scale with justification)
- Willfulness probability (% confidence with evidence)
- Damages range: Conservative to aggressive
- Settlement value: Pre-litigation demand vs trial exposure
- Timeline to resolution
- Bureau-specific strategy (Equifax vs Experian vs TransUnion)

**TONE & STYLE:**
- Professional, authoritative, litigation-ready
- Sophisticated legal language without being pretentious
- RLPP Protocol: Bundle violations to force manual compliance review
- Action-oriented: Clear demands, specific deadlines, consequences

**OUTPUT:**
Generate the complete client package (40-50 pages total). Make it professional, thorough, and ready to send to the credit bureaus or attorneys."""
        
        # Stage 2 needs round_names variable
        if stage != 1:
            round_names = {
                1: "Round 1 - Initial Dispute (RLPP Strong Language)",
                2: "Round 2 - MOV Request / Follow-up",
                3: "Round 3 - Pre-Litigation Warning", 
                4: "Round 4 - Final Demand / Intent to Sue"
            }
        
        super_prompt = prompt
        
        # Stage 2 needs additional context in system prompt
        if stage != 1:
            super_prompt += """

You have Stage 1 analysis results. Now generate the client-facing documents:

PART 5: CLIENT-FACING REPORT (40-50 pages)
- Executive Summary
- Detailed violation analysis
- Standing assessment
- Damages calculation
- Legal strategy & case strength

PART 6: DISPUTE LETTERS
- Round """ + str(dispute_round) + """ letter with RLPP language
- Statutory citations
- Violation documentation
- Proof of willfulness

PART 7: MOV REQUEST (if applicable)
- Method of Verification request
- Bureau-specific requirements
- Deadline enforcement

Output the complete client-facing documents."""
        
        # For Stage 1, build dispute context and user message
        if stage == 1:
            round_names = {
                1: "Round 1 - Initial Dispute (RLPP Strong Language)",
                2: "Round 2 - MOV Request / Follow-up",
                3: "Round 3 - Pre-Litigation Warning", 
                4: "Round 4 - Final Demand / Intent to Sue"
            }
            
            dispute_context = ""
            if dispute_round > 1 and (previous_letters or bureau_responses):
                dispute_context = f"""

PREVIOUS DISPUTE CONTEXT:
Timeline: {dispute_timeline if dispute_timeline else 'Not provided'}
Previous Letters: {previous_letters if previous_letters else 'Not provided'}
Bureau Responses: {bureau_responses if bureau_responses else 'NO RESPONSE - Possible §611(a)(7) violation'}
"""
            
            user_message = f"""
🚨 STAGE 1: VIOLATIONS & DAMAGES ANALYSIS

CLIENT: {client_name} (CMM ID: {cmm_id})
Provider: {provider}
Dispute Round: {round_names.get(dispute_round, 'Round ' + str(dispute_round))}

{dispute_context}

CREDIT REPORT:
{credit_report_html}

TASK: Analyze ONLY for violations, standing, and damages.
Output JSON at end with violations, standing, actual_damages.
NO client reports, NO letters - just the analysis data.
"""
        else:
            # Stage 2: Use previous Stage 1 results
            user_message = f"""
🚨 STAGE 2: CLIENT DOCUMENTS GENERATION

Previous Stage 1 Analysis:
{stage_1_results}

CLIENT: {client_name} (CMM ID: {cmm_id})
Provider: {provider}
Dispute Round: {round_names.get(dispute_round, 'Round ' + str(dispute_round))}

TASK: Generate client-facing documents using Stage 1 results:
- 40-50 page detailed report
- Dispute letters with RLPP language
- MOV requests
- Full litigation analysis

Make it professional and litigation-ready.
"""
        
        # Call Claude API
        print(f"\n🤖 Sending to Claude API for analysis...")
        print(f"   Stage: {stage}")
        print(f"   Analysis mode: {analysis_mode if stage == 1 else 'auto (Stage 2)'}")
        print(f"   Prompt size: {len(super_prompt):,} characters")
        print(f"   Report size: {len(credit_report_html):,} characters" if stage == 1 else "")
        
        import time
        start_time = time.time()
        
        # Normalize prompts to ensure cache consistency (strip whitespace)
        normalized_super_prompt = super_prompt.strip()
        normalized_user_message = user_message.strip()
        
        # Token logging for visibility
        approx_prompt_tokens = (len(normalized_super_prompt) + len(normalized_user_message)) / 4.0
        print(f"📏 Approx prompt tokens before API call: ~{approx_prompt_tokens:,.0f}")
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50000,
                temperature=0,
                timeout=900.0,
                system=[
                    {
                        "type": "text",
                        "text": normalized_super_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": normalized_user_message
                }]
            )
        except Exception as api_err:
            error_msg = f"Claude API Error: {str(api_err)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API call completed in {elapsed_time:.1f} seconds")

        # Extract token usage and calculate cost savings (guard against errors)
        usage = getattr(message, 'usage', None)
        if usage:
            # Cost per million tokens (Anthropic pricing for Claude Sonnet 4)
            INPUT_COST_PER_MTOK = 3.00  # $3 per million input tokens
            CACHED_INPUT_COST_PER_MTOK = 0.30  # $0.30 per million cached tokens (90% discount)
            OUTPUT_COST_PER_MTOK = 15.00  # $15 per million output tokens
            
            # Calculate costs
            input_tokens = getattr(usage, 'input_tokens', 0)
            cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
            cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            
            # Actual cost calculation
            cache_creation_cost = (cache_creation_tokens / 1_000_000) * INPUT_COST_PER_MTOK
            cache_read_cost = (cache_read_tokens / 1_000_000) * CACHED_INPUT_COST_PER_MTOK
            regular_input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MTOK
            output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MTOK
            
            total_input_tokens = input_tokens + cache_creation_tokens + cache_read_tokens
            total_cost = cache_creation_cost + cache_read_cost + regular_input_cost + output_cost
            cost_without_cache = ((input_tokens + cache_creation_tokens + cache_read_tokens) / 1_000_000) * INPUT_COST_PER_MTOK + output_cost
            
            savings = cost_without_cache - total_cost
            savings_percent = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0
            
            print("\n" + "="*60)
            print("💰 COST ANALYSIS")
            print("="*60)
            print(f"📊 Token Usage:")
            print(f"   Input tokens: {input_tokens:,}")
            if cache_creation_tokens > 0:
                print(f"   Cache creation: {cache_creation_tokens:,} (first request)")
            if cache_read_tokens > 0:
                print(f"   Cache read: {cache_read_tokens:,} (90% cheaper!)")
            print(f"   Output tokens: {output_tokens:,}")
            print(f"   Total: {total_input_tokens + output_tokens:,}")
            
            print(f"\n💵 Cost Breakdown:")
            if cache_creation_cost > 0:
                print(f"   Cache creation: ${cache_creation_cost:.4f}")
            if cache_read_cost > 0:
                print(f"   Cached input: ${cache_read_cost:.4f} ⚡")
            if regular_input_cost > 0:
                print(f"   Regular input: ${regular_input_cost:.4f}")
            print(f"   Output: ${output_cost:.4f}")
            print(f"   TOTAL: ${total_cost:.4f}")
            
            if cache_read_tokens > 0:
                print(f"\n🎉 SAVINGS:")
                print(f"   Without caching: ${cost_without_cache:.4f}")
                print(f"   With caching: ${total_cost:.4f}")
                print(f"   You saved: ${savings:.4f} ({savings_percent:.1f}%)")
            elif cache_creation_tokens > 0:
                print(f"\n📌 Cache Status: Created")
                print(f"   Next requests will save ~${cache_creation_cost * 0.9:.4f} (90% discount)")
            
            print("="*60 + "\n")

        analysis_result = ""
        for block in message.content:
            if block.type == 'text':
                analysis_result += block.text

        print(f"\n✅ Analysis result length: {len(analysis_result):,} characters")

        # Extract litigation data if Stage 1
        if stage == 1:
            extract_litigation_data(analysis_result)
        
        # Calculate totals safely
        total_tokens = 0
        total_cost_final = 0
        if usage:
            total_tokens = total_input_tokens + output_tokens
            total_cost_final = total_cost
        
        return {
            'success': True,
            'analysis': analysis_result,
            'client': client_name,
            'stage': stage,
            'tokens_used': total_tokens,
            'cost': total_cost_final,
            'cache_read': cache_read_tokens > 0 if usage else False
        }

    except Exception as e:
        print(f"❌ Claude API Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def extract_litigation_data(analysis_text):
    """Extract structured litigation data from Claude's analysis"""
    import json
    import re
    
    try:
        # Try to find <LITIGATION_DATA> JSON block
        pattern = r'<LITIGATION_DATA>\s*(\{[\s\S]*?\})\s*</LITIGATION_DATA>'
        match = re.search(pattern, analysis_text)
        
        if match:
            json_str = match.group(1)
            print(f"✅ Found <LITIGATION_DATA> block ({len(json_str)} characters)")
        else:
            # Fallback: look for bare JSON at end
            last_brace = analysis_text.rfind('{')
            if last_brace == -1:
                print("⚠️  No JSON found in analysis")
                return None
            json_str = analysis_text[last_brace:]
            print(f"✅ Found bare JSON at end ({len(json_str)} characters)")
        
        # Parse JSON
        litigation_data = json.loads(json_str)
        
        # Validate structure
        if 'violations' not in litigation_data:
            litigation_data['violations'] = []
        if 'standing' not in litigation_data:
            litigation_data['standing'] = {}
        if 'actual_damages' not in litigation_data:
            litigation_data['actual_damages'] = {}
        
        print(f"   ✅ Extracted {len(litigation_data.get('violations', []))} violations")
        return litigation_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error extracting litigation data: {str(e)}")
        return None


def auto_populate_litigation_database(analysis_id, client_id, litigation_data, db):
    """
    Automatically populate Violations, Standing, and Damages tables from extracted data
    """
    from litigation_tools import calculate_damages, calculate_case_score
    
    try:
        print(f"\n🤖 AUTO-POPULATING LITIGATION DATABASE...")
        
        # 1. POPULATE VIOLATIONS
        violations_added = 0
        if litigation_data.get('violations'):
            for v_data in litigation_data['violations']:
                violation = Violation(
                    analysis_id=analysis_id,
                    client_id=client_id,
                    account_name=v_data.get('account_name', 'Unknown'),
                    bureau=v_data.get('bureau', 'Unknown'),
                    fcra_section=v_data.get('fcra_section', ''),
                    violation_type=v_data.get('violation_type', ''),
                    description=v_data.get('description', ''),
                    is_willful=v_data.get('is_willful', False),
                    willfulness_notes=v_data.get('willfulness_indicators', ''),
                    statutory_damages_min=100,
                    statutory_damages_max=1000
                )
                db.add(violation)
                violations_added += 1
            
            print(f"   ✅ Added {violations_added} violations")
        
        # 2. POPULATE STANDING
        if litigation_data.get('standing'):
            s_data = litigation_data['standing']
            standing = Standing(
                analysis_id=analysis_id,
                client_id=client_id,
                has_concrete_harm=s_data.get('has_concrete_harm', False),
                concrete_harm_type=s_data.get('concrete_harm_type', ''),
                concrete_harm_details=s_data.get('harm_details', ''),
                has_dissemination=s_data.get('has_dissemination', False),
                dissemination_details=s_data.get('dissemination_details', ''),
                has_causation=s_data.get('has_causation', False),
                causation_details=s_data.get('causation_details', ''),
                denial_letters_count=s_data.get('denial_letters_count', 0),
                adverse_action_notices_count=s_data.get('adverse_action_notices_count', 0),
                standing_verified=True
            )
            db.add(standing)
            print(f"   ✅ Added standing data (concrete harm: {s_data.get('has_concrete_harm', False)})")
        
        # Commit violations and standing before calculating damages
        db.commit()
        
        # 3. CALCULATE AND POPULATE DAMAGES
        violations_for_calc = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        violations_data = [{
            'fcra_section': v.fcra_section,
            'is_willful': v.is_willful,
            'violation_type': v.violation_type
        } for v in violations_for_calc]
        
        actual_damages_input = litigation_data.get('actual_damages', {})
        damages_calc = calculate_damages(violations_data, actual_damages_input)
        
        damages = Damages(
            analysis_id=analysis_id,
            client_id=client_id,
            credit_denials_amount=damages_calc['actual']['credit_denials'],
            higher_interest_amount=damages_calc['actual']['higher_interest'],
            credit_monitoring_amount=damages_calc['actual']['credit_monitoring'],
            time_stress_amount=damages_calc['actual']['time_stress'],
            other_actual_amount=damages_calc['actual']['other'],
            actual_damages_total=damages_calc['actual']['total'],
            section_605b_count=damages_calc['statutory']['605b']['count'],
            section_605b_amount=damages_calc['statutory']['605b']['amount'],
            section_607b_count=damages_calc['statutory']['607b']['count'],
            section_607b_amount=damages_calc['statutory']['607b']['amount'],
            section_611_count=damages_calc['statutory']['611']['count'],
            section_611_amount=damages_calc['statutory']['611']['amount'],
            section_623_count=damages_calc['statutory']['623']['count'],
            section_623_amount=damages_calc['statutory']['623']['amount'],
            statutory_damages_total=damages_calc['statutory']['total'],
            willfulness_multiplier=damages_calc['punitive']['multiplier'],
            punitive_damages_amount=damages_calc['punitive']['amount'],
            estimated_hours=damages_calc['attorney_fees']['estimated_hours'],
            hourly_rate=damages_calc['attorney_fees']['hourly_rate'],
            attorney_fees_projection=damages_calc['attorney_fees']['total'],
            total_exposure=damages_calc['settlement']['total_exposure'],
            settlement_target=damages_calc['settlement']['target'],
            minimum_acceptable=damages_calc['settlement']['minimum'],
            notes=actual_damages_input.get('notes', '')
        )
        db.add(damages)
        print(f"   ✅ Calculated damages (total exposure: ${damages_calc['settlement']['total_exposure']:,.2f})")
        
        # Commit damages before calculating score
        db.commit()
        
        # 4. CALCULATE AND POPULATE CASE SCORE
        standing_obj = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        standing_data = {
            'has_concrete_harm': standing_obj.has_concrete_harm if standing_obj else False,
            'has_dissemination': standing_obj.has_dissemination if standing_obj else False,
            'has_causation': standing_obj.has_causation if standing_obj else False,
            'denial_letters_count': standing_obj.denial_letters_count if standing_obj else 0
        }
        
        documentation_complete = len(violations_data) > 0 and standing_obj is not None
        
        score_data = calculate_case_score(
            standing_data,
            violations_data,
            damages_calc,
            documentation_complete
        )
        
        case_score = CaseScore(
            analysis_id=analysis_id,
            client_id=client_id,
            total_score=score_data['total'],
            standing_score=score_data['standing'],
            violation_quality_score=score_data['violation_quality'],
            willfulness_score=score_data['willfulness'],
            documentation_score=score_data['documentation'],
            settlement_probability=score_data['settlement_probability'],
            case_strength=score_data['case_strength'],
            recommendation=score_data['recommendation'],
            recommendation_notes='\n'.join(score_data['notes'])
        )
        db.add(case_score)
        print(f"   ✅ Calculated case score ({score_data['total']}/10 - {score_data['case_strength']})")
        
        # Final commit
        db.commit()
        
        print(f"✅ AUTO-POPULATION COMPLETE!")
        print(f"   Violations: {violations_added}")
        print(f"   Standing: Added")
        print(f"   Damages: ${damages_calc['settlement']['total_exposure']:,.2f}")
        print(f"   Case Score: {score_data['total']}/10")
        
        return True
        
    except Exception as e:
        print(f"❌ Error auto-populating database: {str(e)}")
        db.rollback()
        return False


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receives credit report data from HTML form"""
    try:
        # Get data from request
        data = request.get_json() or request.form.to_dict()

        # Extract the specific fields we need
        client_name = data.get('clientName', 'Unknown Client')
        cmm_contact_id = data.get('cmmContactId', 'Unknown')
        credit_provider = data.get('creditProvider', 'Unknown Provider')
        credit_report_html = data.get('creditReportHTML', '')
        analysis_mode = data.get('analysisMode', 'manual')
        dispute_round = int(data.get('disputeRound', 1))
        previous_letters = data.get('previousLetters', '')
        bureau_responses = data.get('bureauResponses', '')
        dispute_timeline = data.get('disputeTimeline', '')
        credit_report_html = clean_credit_report_html(credit_report_html)
        # Validate we got the essential data
        if not credit_report_html:
            return jsonify({
                'success': False,
                'error': 'No credit report HTML provided'
            }), 400

        # Create report record
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'client_name': client_name,
            'cmm_contact_id': cmm_contact_id,
            'credit_provider': credit_provider,
            'report_length': len(credit_report_html),
            'credit_report_html': credit_report_html,
            'status': 'received',
            'processed': False
        }
        # Analyze with Claude API (section-based Stage 1)
        analysis = run_stage1_for_all_sections(
            client_name=client_name,
            cmm_id=cmm_contact_id,
            provider=credit_provider,
            credit_report_text=credit_report_html,
            analysis_mode=analysis_mode,
            dispute_round=dispute_round,
            previous_letters=previous_letters,
            bureau_responses=bureau_responses,
            dispute_timeline=dispute_timeline
        )

        if analysis.get('success'):
            report['analysis'] = analysis.get('combined_analysis', '')
            report['processed'] = True
            report['tokens_used'] = analysis.get('tokens_used', 0)
            report['cost'] = analysis.get('cost', 0)
            print(f"✅ FCRA Section-based Analysis completed for {client_name}")
        else:
            report['analysis_error'] = analysis.get('error', 'Unknown error')
            print(f"⚠️ Section-based analysis failed: {analysis.get('error')}")
        # Store it
        credit_reports.append(report)

        # Log to console
        print("\n" + "=" * 60)
        print("✅ CREDIT REPORT RECEIVED")
        print("=" * 60)
        print(f"Client: {client_name}")
        print(f"CMM ID: {cmm_contact_id}")
        print(f"Provider: {credit_provider}")
        print(f"Report Size: {len(credit_report_html):,} characters")
        print(f"Time: {report['timestamp']}")
        print("=" * 60 + "\n")

        # Return success
        return jsonify({
            'success': True,
            'message': 'Credit report received successfully! ✅',
            'client': client_name,
            'cmm_id': cmm_contact_id,
            'timestamp': report['timestamp'],
            'report_size': len(credit_report_html),
            'total_reports': len(credit_reports)
        }), 200

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/webhook/batch', methods=['POST'])
def webhook_batch():
    """Process multiple credit reports in batch - maximizes cache efficiency
    
    Features:
    - Input validation for each client entry
    - Error isolation (one failure doesn't abort the batch)
    - Complete results including analyses for automation
    - Shared prompt cache across all clients (90% savings after first)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON or no data provided'
            }), 400
        
        clients = data.get('clients', [])
        
        if not clients:
            return jsonify({
                'success': False,
                'error': 'No clients provided in batch request. Expected "clients" array.'
            }), 400
        
        if not isinstance(clients, list):
            return jsonify({
                'success': False,
                'error': '"clients" must be an array'
            }), 400
        
        print("\n" + "=" * 60)
        print(f"📦 BATCH PROCESSING: {len(clients)} clients")
        print("=" * 60)
        
        results = []
        
        for idx, client_data in enumerate(clients, 1):
            # Validate client_data is a dictionary
            if not isinstance(client_data, dict):
                results.append({
                    'client_index': idx,
                    'client_name': f'Client {idx}',
                    'success': False,
                    'error': f'Client entry {idx} is not a valid object',
                    'analysis': None
                })
                print(f"⚠️ Skipping invalid client {idx} (not a valid object)")
                continue
            
            # Extract and validate fields
            client_name = client_data.get('clientName', f'Client {idx}')
            cmm_contact_id = client_data.get('cmmContactId', 'Unknown')
            credit_provider = client_data.get('creditProvider', 'Unknown Provider')
            credit_report_html = client_data.get('creditReportHTML', '')
            analysis_mode = client_data.get('analysisMode', 'manual')
            dispute_round = client_data.get('disputeRound', 1)
            previous_letters = client_data.get('previousLetters', '')
            bureau_responses = client_data.get('bureauResponses', '')
            dispute_timeline = client_data.get('disputeTimeline', '')
            
            print(f"\n🔄 Processing {idx}/{len(clients)}: {client_name}")
            
            # Validate required fields
            if not credit_report_html or not credit_report_html.strip():
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'success': False,
                    'error': 'No credit report HTML provided',
                    'analysis': None
                })
                print(f"⚠️ Skipping {client_name}: No credit report HTML")
                continue
            
            # Validate dispute_round is valid integer
            try:
                dispute_round = int(dispute_round)
                if dispute_round < 1 or dispute_round > 4:
                    raise ValueError("Dispute round must be 1-4")
            except (ValueError, TypeError) as e:
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'success': False,
                    'error': f'Invalid dispute_round: {str(e)}',
                    'analysis': None
                })
                print(f"⚠️ Skipping {client_name}: Invalid dispute round")
                continue
            
            # Process this client (isolated error handling)
            try:
                # Clean the report
                cleaned_html = clean_credit_report_html(credit_report_html)
                
                # Analyze with Claude API (benefits from cached prompt!)
                analysis_result = analyze_with_claude(
                    client_name=client_name,
                    cmm_id=cmm_contact_id,
                    provider=credit_provider,
                    credit_report_html=cleaned_html,
                    analysis_mode=analysis_mode,
                    dispute_round=dispute_round,
                    previous_letters=previous_letters,
                    bureau_responses=bureau_responses,
                    dispute_timeline=dispute_timeline
                )
                
                # Store report
                report = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'client_name': client_name,
                    'cmm_contact_id': cmm_contact_id,
                    'credit_provider': credit_provider,
                    'report_length': len(cleaned_html),
                    'credit_report_html': cleaned_html,
                    'status': 'processed' if analysis_result['success'] else 'failed',
                    'processed': analysis_result['success']
                }
                
                if analysis_result['success']:
                    report['analysis'] = analysis_result['analysis']
                    results.append({
                        'client_index': idx,
                        'client_name': client_name,
                        'cmm_contact_id': cmm_contact_id,
                        'success': True,
                        'message': 'Analysis completed successfully',
                        'analysis': analysis_result['analysis']  # Include full analysis for automation
                    })
                    print(f"✅ Completed: {client_name}")
                else:
                    report['analysis_error'] = analysis_result.get('error', 'Unknown error')
                    results.append({
                        'client_index': idx,
                        'client_name': client_name,
                        'cmm_contact_id': cmm_contact_id,
                        'success': False,
                        'error': analysis_result.get('error', 'Unknown error'),
                        'analysis': None
                    })
                    print(f"❌ Failed: {client_name} - {analysis_result.get('error', 'Unknown error')}")
                
                credit_reports.append(report)
                
            except Exception as client_error:
                # Isolate error - don't let one client crash the entire batch
                error_msg = f"Processing error: {str(client_error)}"
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'cmm_contact_id': cmm_contact_id,
                    'success': False,
                    'error': error_msg,
                    'analysis': None
                })
                print(f"❌ Error processing {client_name}: {error_msg}")
                continue
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print("\n" + "=" * 60)
        print("🎉 BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"❌ Failed: {failed}/{len(results)}")
        if successful > 1:
            print(f"💰 Prompt caching saved ~70-90% on costs (after first request)!")
        print("=" * 60 + "\n")
        
        return jsonify({
            'success': True,  # Batch endpoint succeeded even if some clients failed
            'total_clients': len(results),
            'successful': successful,
            'failed': failed,
            'results': results,  # Includes full analyses for automation
            'message': f'Batch processing complete: {successful}/{len(results)} successful'
        }), 200
        
    except Exception as e:
        print(f"\n❌ BATCH ENDPOINT ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Batch endpoint error: {str(e)}'
        }), 500


@app.route('/history')
def history():
    """View all received reports in JSON format"""
    # Don't include full HTML to keep response manageable
    summary = []
    for report in credit_reports:
        summary.append({
            'timestamp': report['timestamp'],
            'client_name': report['client_name'],
            'cmm_contact_id': report['cmm_contact_id'],
            'credit_provider': report['credit_provider'],
            'report_length': report['report_length'],
            'status': report['status'],
            'processed': report['processed']
        })

    return jsonify({
        'total_reports': len(credit_reports),
        'reports': summary
    }), 200


@app.route('/test')
def test():
    """Test endpoint to verify server is working"""
    return jsonify({
        'status': 'Server is running! ✅',
        'reports_received': len(credit_reports),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ready_for': 'Phase 2 - Claude API Integration'
    }), 200


@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear all stored reports (for testing)"""
    credit_reports.clear()
    return jsonify({'success': True, 'message': 'All reports cleared'}), 200


@app.route('/view/<int:report_id>')
def view_analysis(report_id):
    """View the Claude analysis for a specific report"""
    if report_id < len(credit_reports):
        report = credit_reports[report_id]
        return f"""
        <html>
        <head><title>FCRA Analysis - {report['client_name']}</title></head>
        <body style="font-family: Arial; max-width: 900px; margin: 40px auto; padding: 20px;">
            <h1>FCRA Analysis: {report['client_name']}</h1>
            <p><strong>CMM ID:</strong> {report['cmm_contact_id']}</p>
            <p><strong>Provider:</strong> {report['credit_provider']}</p>
            <p><strong>Date:</strong> {report['timestamp']}</p>
            <hr>
            <h2>Analysis:</h2>
            <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 20px; border-radius: 8px;">{report.get('analysis', 'No analysis available')}</pre>
            <p><a href="/">← Back to Form</a></p>
        </body>
        </html>
        """
    return "Report not found", 404


@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for generating analyses and letters"""
    return render_template('admin.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_and_generate_letters():
    """Process credit report, run AI analysis, generate PDF letters"""
    db = get_db()
    try:
        data = request.get_json()
        
        client_name = data.get('clientName')
        client_email = data.get('clientEmail', '')
        credit_provider = data.get('creditProvider', 'Unknown')
        credit_report_html = data.get('creditReportHTML', '')
        dispute_round = data.get('disputeRound', 1)
        analysis_mode = data.get('analysisMode', 'auto')
        
        if not client_name or not credit_report_html:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # 🧹 Clean and analyze with section-based Stage 1
        print(f"🧹 Cleaning credit report in /api/analyze endpoint...")
        credit_report_text = clean_credit_report_html(credit_report_html)
        
        # 🚀 Run Stage 1 on each section, merge results
        section_analysis = run_stage1_for_all_sections(
            client_name=client_name,
            cmm_id=data.get('cmmContactId', ''),
            provider=credit_provider,
            credit_report_text=credit_report_text,
            analysis_mode='manual',
            dispute_round=dispute_round,
            previous_letters='',
            bureau_responses='',
            dispute_timeline=''
        )
        
        if not section_analysis.get('success'):
            return jsonify({'success': False, 'error': section_analysis.get('error', 'Analysis failed')}), 500
        
        merged_litigation_data = section_analysis.get('litigation_data', {})
        
        # Create or get client
        client = db.query(Client).filter_by(name=client_name).first()
        if not client:
            client = Client(name=client_name, email=client_email)
            db.add(client)
            db.commit()
            db.refresh(client)
        
        # Save credit report
        credit_report_record = CreditReport(
            client_id=client.id,
            client_name=client_name,
            credit_provider=credit_provider,
            report_html=credit_report_html,
            report_date=datetime.now()
        )
        db.add(credit_report_record)
        db.commit()
        db.refresh(credit_report_record)
        
        # Save analysis with merged Stage 1 results from all sections
        analysis_record = Analysis(
            credit_report_id=credit_report_record.id,
            client_id=client.id,
            client_name=client_name,
            dispute_round=dispute_round,
            analysis_mode='manual',
            stage=1,  # This is Stage 1 analysis
            stage_1_analysis=str(merged_litigation_data),  # Store merged Stage 1 results
            cost=merged_litigation_data.get('total_cost', 0),
            tokens_used=merged_litigation_data.get('total_tokens', 0),
            cache_read=False
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        
        # 🤖 AUTO-POPULATE LITIGATION DATABASE from merged section data
        if merged_litigation_data and merged_litigation_data.get('violations'):
            print(f"\n🎯 Merged litigation data found! Auto-populating database...")
            auto_populate_litigation_database(
                analysis_id=analysis_record.id,
                client_id=client.id,
                litigation_data=merged_litigation_data,
                db=db
            )
        else:
            print(f"\n⚠️  No violations found in merged analysis")
        
        # Extract and generate PDF letters
        letters_generated = []
        
        # Parse individual letters using START/END markers
        import re
        
        # Get combined analysis from section results
        combined_analysis_text = section_analysis.get('combined_analysis', '')
        
        # Find all individual letters
        letter_pattern = r"==.*?START OF DISPUTE LETTER: ([A-Za-z]+) - (.+?)==(.*?)==.*?END OF DISPUTE LETTER:"
        all_letters = re.findall(letter_pattern, combined_analysis_text, re.DOTALL | re.IGNORECASE)
        
        # Group letters by bureau
        bureau_letters = {'Equifax': [], 'Experian': [], 'TransUnion': []}
        for match in all_letters:
            bureau_name = match[0].strip().title()
            account_name = match[1].strip()
            letter_content = match[2].strip()
            
            if bureau_name in bureau_letters:
                bureau_letters[bureau_name].append({
                    'account': account_name,
                    'content': letter_content
                })
        
        # Generate one PDF per bureau combining all letters for that bureau
        for bureau, letters in bureau_letters.items():
            if not letters:
                continue
            
            # Combine all letters for this bureau
            combined_content = f"\n\n{'='*80}\n\n".join([
                f"ACCOUNT: {letter['account']}\n\n{letter['content']}" 
                for letter in letters
            ])
            
            # Generate PDF
            filename = f"{client_name.replace(' ', '_')}_{bureau}_Round{dispute_round}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join('static', 'generated_letters', filename)
            
            try:
                pdf_gen.generate_dispute_letter_pdf(
                    letter_content=combined_content,
                    client_name=client_name,
                    bureau=bureau,
                    round_number=dispute_round,
                    output_path=output_path
                )
                
                # Save letter record
                letter_record = DisputeLetter(
                    analysis_id=analysis_record.id,
                    client_id=client.id,
                    client_name=client_name,
                    bureau=bureau,
                    round_number=dispute_round,
                    letter_content=combined_content,
                    file_path=output_path
                )
                db.add(letter_record)
                db.commit()
                db.refresh(letter_record)
                
                letters_generated.append({
                    'letter_id': letter_record.id,
                    'bureau': bureau,
                    'round': dispute_round,
                    'filepath': output_path,
                    'letter_count': len(letters)
                })
                
                print(f"✅ Generated PDF for {bureau} with {len(letters)} letter(s)")
            except Exception as e:
                print(f"❌ Error generating PDF for {bureau}: {e}")
        
        return jsonify({
            'success': True,
            'client_name': client_name,
            'round': dispute_round,
            'cost': section_analysis.get('cost', 0),
            'tokens_used': section_analysis.get('tokens_used', 0),
            'analysis_id': analysis_record.id,
            'letters': letters_generated
        }), 200
        
    except Exception as e:
        print(f"Error in analyze_and_generate_letters: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/download/<int:letter_id>')
def download_letter(letter_id):
    """Download a generated PDF letter"""
    db = get_db()
    try:
        letter = db.query(DisputeLetter).filter_by(id=letter_id).first()
        
        if not letter:
            return jsonify({'error': 'Letter not found'}), 404
        
        file_path_str = str(letter.file_path)
        if not os.path.exists(file_path_str):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            file_path_str,
            as_attachment=True,
            download_name=f"{letter.client_name}_{letter.bureau}_Round{letter.round_number}.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/download/analysis/<int:analysis_id>/full_report')
def download_full_report(analysis_id):
    """Download full litigation report PDF"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Get first letter from this analysis as template (all have same info)
        letter = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).first()
        if not letter:
            return jsonify({'error': 'No letters generated yet. Click Accept Case first.'}), 404
        
        # Create comprehensive report combining violations, standing, damages
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        report_content = f"""
FCRA LITIGATION ANALYSIS REPORT
Client: {analysis.client_name}
Analysis ID: {analysis.id}
Date: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}

CASE STRENGTH SCORE: {case_score.total_score if case_score else 'N/A'}/10

VIOLATIONS IDENTIFIED: {len(violations)}
"""
        for v in violations:
            report_content += f"\n• {v.fcra_section} - {v.violation_type} ({v.bureau})"
            report_content += f"\n  {v.description}"
            report_content += f"\n  Willful: {'Yes' if v.is_willful else 'No'}"
            report_content += f"\n  Statutory Damages: ${v.statutory_damages_min}-${v.statutory_damages_max}\n"
        
        report_content += f"\nSTANDING ANALYSIS:\n"
        if standing:
            report_content += f"• Concrete Harm: {'Yes' if standing.has_concrete_harm else 'No'}\n"
            report_content += f"• Dissemination: {'Yes' if standing.has_dissemination else 'No'}\n"
            report_content += f"• Causation: {'Yes' if standing.has_causation else 'No'}\n"
        
        report_content += f"\nDAMAGES CALCULATION:\n"
        if damages:
            report_content += f"• Actual Damages: ${damages.actual_damages_total}\n"
            report_content += f"• Statutory Damages: ${damages.statutory_damages_total}\n"
            report_content += f"• Punitive Damages: ${damages.punitive_damages_amount}\n"
            report_content += f"• Total Exposure: ${damages.total_exposure}\n"
            report_content += f"• Settlement Target (65%): ${damages.settlement_target}\n"
        
        # Generate PDF
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 5, report_content)
        
        filename = f"{analysis.client_name.replace(' ', '_')}_Full_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join('static', 'generated_letters', filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf.output(output_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/download/analysis/<int:analysis_id>/round_<int:round_num>')
def download_round_letter(analysis_id, round_num):
    """Download dispute letter for specific round"""
    db = get_db()
    try:
        # Get first letter from this analysis/round
        letter = db.query(DisputeLetter).filter_by(
            analysis_id=analysis_id,
            round_number=round_num
        ).first()
        
        if not letter:
            return jsonify({'error': f'No letter found for Round {round_num}. Click Accept Case first.'}), 404
        
        file_path_str = str(letter.file_path)
        if not os.path.exists(file_path_str):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            file_path_str,
            as_attachment=True,
            download_name=f"{letter.client_name}_Round{round_num}_Dispute_Letter.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/approve/<int:analysis_id>', methods=['POST'])
def approve_analysis_stage_1(analysis_id):
    """
    Approve Stage 1 analysis and trigger Stage 2 (client documents generation).

    Behavior:
    - stage is NULL/0  → treat as Stage 1 (backwards compatible)
    - stage == 1      → run Stage 2, generate docs
    - stage == 2      → already approved, return existing letters (idempotent)
    - anything else   → return error
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404

        # Backwards compatibility: if stage is None or 0, treat it as Stage 1
        if analysis.stage is None or analysis.stage == 0:
            analysis.stage = 1
            db.commit()

        # If Stage 2 already completed, return existing letters instead of error
        if analysis.stage == 2:
            letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
            letters_payload = [{
                'letter_id': l.id,
                'bureau': l.bureau,
                'round': l.round_number,
                'filepath': str(l.file_path)
            } for l in letters]

            return jsonify({
                'success': True,
                'analysis_id': analysis_id,
                'stage': 2,
                'message': 'Client documents already generated',
                'cost': analysis.cost or 0,
                'tokens': analysis.tokens_used or 0,
                'letters': letters_payload
            }), 200

        # Any other unexpected stage value
        if analysis.stage != 1:
            return jsonify({
                'success': False,
                'error': f'Analysis is not in Stage 1 (current stage: {analysis.stage})'
            }), 400

        print(f"\n🚀 STAGE 2: Generating client documents for analysis {analysis_id}...")

        # Get credit report for context
        credit_report = db.query(CreditReport).filter_by(id=analysis.credit_report_id).first()
        if not credit_report:
            return jsonify({'success': False, 'error': 'Credit report not found'}), 404

        # Run Stage 2 with Stage 1 results
        result = analyze_with_claude(
            client_name=analysis.client_name,
            cmm_id='',
            provider=credit_report.credit_provider,
            credit_report_html=credit_report.report_html,
            analysis_mode='auto',
            dispute_round=analysis.dispute_round,
            stage=2,  # STAGE 2: Generate client documents
            stage_1_results=analysis.stage_1_analysis  # Pass Stage 1 results
        )

        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Stage 2 generation failed')
            }), 500

        # Update analysis record with Stage 2 results
        analysis.stage = 2
        analysis.full_analysis = result.get('analysis', '')
        analysis.approved_at = datetime.now()
        analysis.cost = (analysis.cost or 0) + result.get('cost', 0)
        analysis.tokens_used = (analysis.tokens_used or 0) + result.get('tokens_used', 0)
        db.commit()

        # Generate and save dispute letters from Stage 2 output
        print(f"📝 Generating dispute letters from Stage 2 output...")

        stage_2_text = result.get('analysis', '')
        bureau_letters = {}

        # Extract letters from response (format: [Bureau: Account]\nLetter content...)
        letter_pattern = r'\[([^:]+):\s*([^\]]+)\]\s*\n(.*?)(?=\[|$)'
        matches = re.findall(letter_pattern, stage_2_text, re.DOTALL)

        for bureau_name, account_name, letter_content in matches:
            bureau_name = bureau_name.strip().title()
            account_name = account_name.strip()
            letter_content = letter_content.strip()

            if not bureau_name:
                continue

            bureau_letters.setdefault(bureau_name, []).append({
                'account': account_name,
                'content': letter_content
            })

        letters_generated = []

        for bureau, letters in bureau_letters.items():
            if not letters:
                continue

            combined_content = f"\n\n{'='*80}\n\n".join(
                [f"ACCOUNT: {l['account']}\n\n{l['content']}" for l in letters]
            )

            filename = f"{analysis.client_name.replace(' ', '_')}_{bureau}_Round{analysis.dispute_round}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join('static', 'generated_letters', filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            try:
                pdf_gen.generate_dispute_letter_pdf(
                    letter_content=combined_content,
                    client_name=analysis.client_name,
                    bureau=bureau,
                    round_number=analysis.dispute_round,
                    output_path=output_path
                )

                letter_record = DisputeLetter(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id,
                    client_name=analysis.client_name,
                    bureau=bureau,
                    round_number=analysis.dispute_round,
                    letter_content=combined_content,
                    file_path=output_path
                )
                db.add(letter_record)
                db.commit()
                db.refresh(letter_record)

                letters_generated.append({
                    'letter_id': letter_record.id,
                    'bureau': bureau,
                    'round': analysis.dispute_round,
                    'filepath': output_path,
                    'letter_count': len(letters)
                })

                print(f"✅ Generated PDF for {bureau} with {len(letters)} letter(s)")
            except Exception as e:
                print(f"❌ Error generating PDF for {bureau}: {e}")

        print(f"✅ Stage 2 complete! Analysis {analysis_id} ready for delivery")

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'stage': 2,
            'message': 'Client documents generated successfully',
            'cost': result.get('cost', 0),
            'tokens': result.get('tokens_used', 0),
            'letters': letters_generated
        }), 200

    except Exception as e:
        print(f"❌ Error in approve_analysis_stage_1: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/delivered', methods=['GET', 'POST'])
def delivered_status(analysis_id):
    """
    GET  -> return whether case is marked as delivered
    POST -> set/unset delivered flag (front-end toggle)
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404

        global delivered_cases

        if request.method == 'GET':
            return jsonify({
                'success': True,
                'delivered': analysis_id in delivered_cases
            }), 200

        # POST
        data = request.get_json() or {}
        delivered = bool(data.get('delivered', False))

        if delivered:
            delivered_cases.add(analysis_id)
        else:
            delivered_cases.discard(analysis_id)

        return jsonify({
            'success': True,
            'delivered': analysis_id in delivered_cases
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/download_all')
def download_all_letters(analysis_id):
    """Create a ZIP with all generated PDFs for this analysis"""
    db = get_db()
    try:
        letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
        if not letters:
            return jsonify({'success': False, 'error': 'No letters found for this analysis'}), 404

        import io
        import zipfile

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for l in letters:
                path = str(l.file_path)
                if not os.path.exists(path):
                    continue
                # Put each PDF into the zip with a clean filename
                arcname = f"{l.client_name}_{l.bureau}_Round{l.round_number}_{l.id}.pdf"
                zf.write(path, arcname=arcname)

        zip_buffer.seek(0)
        filename = f"FCRA_Letters_Analysis_{analysis_id}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/analysis/<int:analysis_id>/review')
def review_litigation_analysis(analysis_id):
    """Litigation analysis review page"""
    return render_template('litigation_review.html', analysis_id=analysis_id)


@app.route('/api/analysis/<int:analysis_id>/data', methods=['GET'])
def get_analysis_data(analysis_id):
    """Get full analysis data for review page"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        return jsonify({
            'success': True,
            'analysis': {
                'id': analysis.id,
                'client_name': analysis.client_name,
                'dispute_round': analysis.dispute_round,
                'stage': analysis.stage,
                'cost': analysis.cost,
                'tokens_used': analysis.tokens_used,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            'violations': [{
                'id': v.id,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'is_willful': v.is_willful,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max,
                'willfulness_notes': v.willfulness_notes
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else '',
                'concrete_harm_details': standing.concrete_harm_details if standing else '',
                'has_dissemination': standing.has_dissemination if standing else False,
                'dissemination_details': standing.dissemination_details if standing else '',
                'has_causation': standing.has_causation if standing else False,
                'causation_details': standing.causation_details if standing else '',
                'denial_letters_count': standing.denial_letters_count if standing else 0,
                'adverse_action_notices_count': standing.adverse_action_notices_count if standing else 0
            } if standing else None,
            'damages': {
                'credit_denials_amount': damages.credit_denials_amount if damages else 0,
                'higher_interest_amount': damages.higher_interest_amount if damages else 0,
                'credit_monitoring_amount': damages.credit_monitoring_amount if damages else 0,
                'time_stress_amount': damages.time_stress_amount if damages else 0,
                'other_actual_amount': damages.other_actual_amount if damages else 0,
                'actual_damages_total': damages.actual_damages_total if damages else 0,
                'section_605b_count': damages.section_605b_count if damages else 0,
                'section_605b_amount': damages.section_605b_amount if damages else 0,
                'section_607b_count': damages.section_607b_count if damages else 0,
                'section_607b_amount': damages.section_607b_amount if damages else 0,
                'section_611_count': damages.section_611_count if damages else 0,
                'section_611_amount': damages.section_611_amount if damages else 0,
                'section_623_count': damages.section_623_count if damages else 0,
                'section_623_amount': damages.section_623_amount if damages else 0,
                'statutory_damages_total': damages.statutory_damages_total if damages else 0,
                'punitive_damages_amount': damages.punitive_damages_amount if damages else 0,
                'willfulness_multiplier': damages.willfulness_multiplier if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'case_strength': case_score.case_strength if case_score else '',
                'recommendation': case_score.recommendation if case_score else ''
            } if case_score else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/admin/clients')
def view_all_clients():
    """View all clients and their analyses"""
    db = get_db()
    try:
        clients = db.query(Client).order_by(Client.created_at.desc()).all()
        
        clients_data = []
        for client in clients:
            analyses = db.query(Analysis).filter_by(client_id=client.id).order_by(Analysis.created_at.desc()).all()
            letters = db.query(DisputeLetter).filter_by(client_id=client.id).all()
            
            clients_data.append({
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'created_at': client.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_analyses': len(analyses),
                'total_letters': len(letters),
                'latest_round': analyses[0].dispute_round if analyses else 0
            })
        
        return jsonify({
            'success': True,
            'clients': clients_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/violations', methods=['GET', 'POST'])
def manage_violations(analysis_id):
    """Get or add violations for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            violations_data = data.get('violations', [])
            
            for v_data in violations_data:
                willfulness_assessment = assess_willfulness(
                    v_data.get('description', ''),
                    v_data.get('violation_type', '')
                )
                
                violation = Violation(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id,
                    bureau=v_data.get('bureau'),
                    account_name=v_data.get('account_name'),
                    fcra_section=v_data.get('fcra_section'),
                    violation_type=v_data.get('violation_type'),
                    description=v_data.get('description'),
                    statutory_damages_min=v_data.get('statutory_damages_min', 100),
                    statutory_damages_max=v_data.get('statutory_damages_max', 1000),
                    is_willful=willfulness_assessment['is_willful'],
                    willfulness_notes=', '.join(willfulness_assessment['indicators'])
                )
                db.add(violation)
            
            db.commit()
            return jsonify({'success': True, 'message': f'Added {len(violations_data)} violations'}), 200
        
        else:
            violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
            return jsonify({
                'success': True,
                'violations': [{
                    'id': v.id,
                    'bureau': v.bureau,
                    'account_name': v.account_name,
                    'fcra_section': v.fcra_section,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'statutory_damages_min': v.statutory_damages_min,
                    'statutory_damages_max': v.statutory_damages_max,
                    'is_willful': v.is_willful,
                    'willfulness_notes': v.willfulness_notes
                } for v in violations]
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/standing', methods=['GET', 'POST'])
def manage_standing(analysis_id):
    """Get or update standing verification for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            
            standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
            if not standing:
                standing = Standing(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id
                )
                db.add(standing)
            
            standing.has_concrete_harm = data.get('has_concrete_harm', False)
            standing.concrete_harm_type = data.get('concrete_harm_type')
            standing.concrete_harm_details = data.get('concrete_harm_details')
            standing.has_dissemination = data.get('has_dissemination', False)
            standing.dissemination_details = data.get('dissemination_details')
            standing.has_causation = data.get('has_causation', False)
            standing.causation_details = data.get('causation_details')
            standing.denial_letters_count = data.get('denial_letters_count', 0)
            standing.adverse_action_notices_count = data.get('adverse_action_notices_count', 0)
            standing.standing_verified = data.get('standing_verified', False)
            standing.notes = data.get('notes')
            
            db.commit()
            return jsonify({'success': True, 'message': 'Standing updated'}), 200
        
        else:
            standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
            if not standing:
                return jsonify({'success': True, 'standing': None}), 200
            
            return jsonify({
                'success': True,
                'standing': {
                    'has_concrete_harm': standing.has_concrete_harm,
                    'concrete_harm_type': standing.concrete_harm_type,
                    'concrete_harm_details': standing.concrete_harm_details,
                    'has_dissemination': standing.has_dissemination,
                    'dissemination_details': standing.dissemination_details,
                    'has_causation': standing.has_causation,
                    'causation_details': standing.causation_details,
                    'denial_letters_count': standing.denial_letters_count,
                    'adverse_action_notices_count': standing.adverse_action_notices_count,
                    'standing_verified': standing.standing_verified,
                    'notes': standing.notes
                }
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/damages', methods=['GET', 'POST'])
def manage_damages(analysis_id):
    """Calculate and store damages for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            
            violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
            violations_data = [{
                'fcra_section': v.fcra_section,
                'is_willful': v.is_willful,
                'violation_type': v.violation_type
            } for v in violations]
            
            actual_damages_input = {
                'credit_denials': data.get('credit_denials_amount', 0),
                'higher_interest': data.get('higher_interest_amount', 0),
                'credit_monitoring': data.get('credit_monitoring_amount', 0),
                'time_stress': data.get('time_stress_amount', 0),
                'other': data.get('other_actual_amount', 0)
            }
            
            damages_calc = calculate_damages(violations_data, actual_damages_input)
            
            damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
            if not damages:
                damages = Damages(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id
                )
                db.add(damages)
            
            damages.credit_denials_amount = damages_calc['actual']['credit_denials']
            damages.higher_interest_amount = damages_calc['actual']['higher_interest']
            damages.credit_monitoring_amount = damages_calc['actual']['credit_monitoring']
            damages.time_stress_amount = damages_calc['actual']['time_stress']
            damages.other_actual_amount = damages_calc['actual']['other']
            damages.actual_damages_total = damages_calc['actual']['total']
            
            damages.section_605b_count = damages_calc['statutory']['605b']['count']
            damages.section_605b_amount = damages_calc['statutory']['605b']['amount']
            damages.section_607b_count = damages_calc['statutory']['607b']['count']
            damages.section_607b_amount = damages_calc['statutory']['607b']['amount']
            damages.section_611_count = damages_calc['statutory']['611']['count']
            damages.section_611_amount = damages_calc['statutory']['611']['amount']
            damages.section_623_count = damages_calc['statutory']['623']['count']
            damages.section_623_amount = damages_calc['statutory']['623']['amount']
            damages.statutory_damages_total = damages_calc['statutory']['total']
            
            damages.willfulness_multiplier = damages_calc['punitive']['multiplier']
            damages.punitive_damages_amount = damages_calc['punitive']['amount']
            
            damages.estimated_hours = damages_calc['attorney_fees']['estimated_hours']
            damages.hourly_rate = damages_calc['attorney_fees']['hourly_rate']
            damages.attorney_fees_projection = damages_calc['attorney_fees']['total']
            
            damages.total_exposure = damages_calc['settlement']['total_exposure']
            damages.settlement_target = damages_calc['settlement']['target']
            damages.minimum_acceptable = damages_calc['settlement']['minimum']
            
            damages.notes = data.get('notes')
            
            db.commit()
            
            return jsonify({
                'success': True,
                'damages': damages_calc
            }), 200
        
        else:
            damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
            if not damages:
                return jsonify({'success': True, 'damages': None}), 200
            
            return jsonify({
                'success': True,
                'damages': {
                    'actual': {
                        'credit_denials': damages.credit_denials_amount,
                        'higher_interest': damages.higher_interest_amount,
                        'credit_monitoring': damages.credit_monitoring_amount,
                        'time_stress': damages.time_stress_amount,
                        'other': damages.other_actual_amount,
                        'total': damages.actual_damages_total
                    },
                    'statutory': {
                        '605b': {'count': damages.section_605b_count, 'amount': damages.section_605b_amount},
                        '607b': {'count': damages.section_607b_count, 'amount': damages.section_607b_amount},
                        '611': {'count': damages.section_611_count, 'amount': damages.section_611_amount},
                        '623': {'count': damages.section_623_count, 'amount': damages.section_623_amount},
                        'total': damages.statutory_damages_total
                    },
                    'punitive': {
                        'multiplier': damages.willfulness_multiplier,
                        'amount': damages.punitive_damages_amount
                    },
                    'attorney_fees': {
                        'estimated_hours': damages.estimated_hours,
                        'hourly_rate': damages.hourly_rate,
                        'total': damages.attorney_fees_projection
                    },
                    'settlement': {
                        'total_exposure': damages.total_exposure,
                        'target': damages.settlement_target,
                        'minimum': damages.minimum_acceptable
                    }
                }
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/score', methods=['GET', 'POST'])
def get_case_score(analysis_id):
    """Calculate and retrieve case strength score"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        
        standing_data = {
            'has_concrete_harm': standing.has_concrete_harm if standing else False,
            'has_dissemination': standing.has_dissemination if standing else False,
            'has_causation': standing.has_causation if standing else False
        }
        
        violations_data = [{
            'violation_type': v.violation_type,
            'is_willful': v.is_willful
        } for v in violations]
        
        damages_data = {}
        if damages:
            damages_data = {
                'total_exposure': damages.total_exposure,
                'statutory_total': damages.statutory_damages_total
            }
        
        documentation_complete = (standing.denial_letters_count > 0 if standing else False)
        
        score_result = calculate_case_score(
            standing_data,
            violations_data,
            damages_data,
            documentation_complete
        )
        
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        if not case_score:
            case_score = CaseScore(
                analysis_id=analysis_id,
                client_id=analysis.client_id
            )
            db.add(case_score)
        
        case_score.standing_score = score_result['standing']
        case_score.violation_quality_score = score_result['violation_quality']
        case_score.willfulness_score = score_result['willfulness']
        case_score.documentation_score = score_result['documentation']
        case_score.total_score = score_result['total']
        case_score.settlement_probability = score_result['settlement_probability']
        case_score.case_strength = score_result['case_strength']
        case_score.recommendation = score_result['recommendation']
        case_score.recommendation_notes = '\n'.join(score_result['notes'])
        
        db.commit()
        
        return jsonify({
            'success': True,
            'score': score_result
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/complete')
def get_complete_analysis(analysis_id):
    """Get complete litigation analysis including violations, damages, standing, and score"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
        
        return jsonify({
            'success': True,
            'analysis': {
                'id': analysis.id,
                'client_name': analysis.client_name,
                'dispute_round': analysis.dispute_round,
                'analysis_mode': analysis.analysis_mode,
                'cost': analysis.cost,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M')
            },
            'violations': [{
                'id': v.id,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'is_willful': v.is_willful,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else None,
                'has_dissemination': standing.has_dissemination if standing else False,
                'has_causation': standing.has_causation if standing else False,
                'denial_letters_count': standing.denial_letters_count if standing else 0,
                'standing_verified': standing.standing_verified if standing else False
            } if standing else None,
            'damages': {
                'actual_total': damages.actual_damages_total if damages else 0,
                'statutory_total': damages.statutory_damages_total if damages else 0,
                'punitive_total': damages.punitive_damages_amount if damages else 0,
                'attorney_fees': damages.attorney_fees_projection if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'minimum_acceptable': damages.minimum_acceptable if damages else 0
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'case_strength': case_score.case_strength if case_score else 'Unknown',
                'recommendation': case_score.recommendation if case_score else 'Not scored'
            } if case_score else None,
            'letters': [{
                'id': l.id,
                'bureau': l.bureau,
                'round': l.round_number,
                'file_path': l.file_path
            } for l in letters]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "🚀" * 30)
    print("FCRA AUTOMATION SERVER STARTING")
    print("🚀" * 30)
    print(f"\n📡 Listening on port {port}")
    print("✅ Ready to receive credit reports!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
