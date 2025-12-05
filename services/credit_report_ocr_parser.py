"""
Credit Report OCR Parser - Uses Claude Vision for Image-Based PDFs
===================================================================
This parser handles three-bureau credit reports that are image-based (scanned/screenshot).
Uses the same Claude Vision approach as your existing ocr_service.py
"""
import os
import json
import base64
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Use same API key setup as ocr_service.py
ANTHROPIC_API_KEY = os.environ.get('FCRA Automation Secure', '')
if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 20:
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

_anthropic_client = None


def get_anthropic_client():
    """Get or create Anthropic client instance."""
    global _anthropic_client
    if _anthropic_client is None:
        if ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) >= 20:
            try:
                from anthropic import Anthropic
                _anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("Credit Report Parser: Anthropic client initialized")
            except Exception as e:
                logger.error(f"Credit Report Parser: Failed to initialize Anthropic client: {e}")
                return None
        else:
            logger.warning("Credit Report Parser: Invalid or missing Anthropic API key")
            return None
    return _anthropic_client


def _convert_pdf_to_images(file_path: str, max_pages: int = 20) -> Optional[List[str]]:
    """Convert PDF pages to base64 encoded images."""
    try:
        from pdf2image import convert_from_path

        # Convert PDF to images (150 DPI is good balance of quality vs size)
        images = convert_from_path(file_path, dpi=150, first_page=1, last_page=max_pages)
        base64_images = []

        for i, img in enumerate(images):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name, 'PNG')
                with open(tmp.name, 'rb') as f:
                    base64_images.append(base64.standard_b64encode(f.read()).decode('utf-8'))
                os.unlink(tmp.name)

        logger.info(f"Converted PDF to {len(base64_images)} images")
        return base64_images if base64_images else None

    except ImportError:
        logger.error("pdf2image not installed. Run: pip install pdf2image")
        logger.error("Also need poppler: apt-get install poppler-utils")
        return None
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return None


# The magic prompt that tells Claude exactly what to extract
CREDIT_REPORT_EXTRACTION_PROMPT = """You are an expert at analyzing three-bureau credit reports (TransUnion, Experian, Equifax combined).

Analyze this credit report and extract ALL data in the following JSON structure.

IMPORTANT: 
- Return ONLY valid JSON, no additional text
- Extract data for ALL THREE bureaus where available
- Include ALL accounts shown, not just a few
- Be precise with numbers and dates

{
    "reference_number": "report reference number",
    "report_date": "MM/DD/YYYY",

    "personal_info": {
        "transunion": {
            "name": "full name as shown",
            "also_known_as": "AKA names",
            "dob": "year or full date",
            "current_address": "full address",
            "previous_addresses": ["address1", "address2"],
            "employer": "employer name"
        },
        "experian": {
            "name": "full name as shown",
            "also_known_as": "AKA names", 
            "dob": "year or full date",
            "current_address": "full address",
            "previous_addresses": ["address1", "address2"],
            "employer": "employer name or NA"
        },
        "equifax": {
            "name": "full name as shown",
            "also_known_as": "AKA names",
            "dob": "year or full date", 
            "current_address": "full address",
            "previous_addresses": ["address1", "address2"],
            "employer": "employer name or NA"
        }
    },

    "credit_scores": {
        "transunion": {"score": 000, "rank": "Fair/Poor/Good/Excellent"},
        "experian": {"score": 000, "rank": "Fair/Poor/Good/Excellent"},
        "equifax": {"score": 000, "rank": "Fair/Poor/Good/Excellent"}
    },

    "summary_stats": {
        "transunion": {
            "total_accounts": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
            "delinquent": 0,
            "derogatory": 0,
            "collections": 0,
            "balances": 0.00,
            "payments": 0.00,
            "public_records": 0,
            "inquiries": 0
        },
        "experian": {
            "total_accounts": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
            "delinquent": 0,
            "derogatory": 0,
            "collections": 0,
            "balances": 0.00,
            "payments": 0.00,
            "public_records": 0,
            "inquiries": 0
        },
        "equifax": {
            "total_accounts": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
            "delinquent": 0,
            "derogatory": 0,
            "collections": 0,
            "balances": 0.00,
            "payments": 0.00,
            "public_records": 0,
            "inquiries": 0
        }
    },

    "accounts": [
        {
            "creditor_name": "CREDITOR NAME",
            "account_number": "masked account number like XXXXXX1234",
            "account_type": "Revolving/Installment/Open/Mortgage",
            "account_type_detail": "Credit Card/Auto Loan/etc",

            "tu_reported": true,
            "tu_status": "Open/Closed",
            "tu_balance": 0.00,
            "tu_credit_limit": 0.00,
            "tu_high_credit": 0.00,
            "tu_monthly_payment": 0.00,
            "tu_date_opened": "MM/DD/YYYY",
            "tu_payment_status": "exact status text like 'Pays account as agreed' or '30 days past due'",
            "tu_past_due": 0.00,
            "tu_last_reported": "MM/DD/YYYY",
            "tu_bureau_code": "Individual/Joint/Authorized User",

            "ex_reported": true,
            "ex_status": "Open/Closed",
            "ex_balance": 0.00,
            "ex_credit_limit": 0.00,
            "ex_high_credit": 0.00,
            "ex_monthly_payment": 0.00,
            "ex_date_opened": "MM/DD/YYYY",
            "ex_payment_status": "exact status text",
            "ex_past_due": 0.00,
            "ex_last_reported": "MM/DD/YYYY",
            "ex_bureau_code": "Individual/Joint/Authorized User",

            "eq_reported": true,
            "eq_status": "Open/Closed",
            "eq_balance": 0.00,
            "eq_credit_limit": 0.00,
            "eq_high_credit": 0.00,
            "eq_monthly_payment": 0.00,
            "eq_date_opened": "MM/DD/YYYY",
            "eq_payment_status": "exact status text",
            "eq_past_due": 0.00,
            "eq_last_reported": "MM/DD/YYYY",
            "eq_bureau_code": "Individual/Joint/Authorized User",

            "payment_history": [
                {"month": "Oct", "year": "25", "tu": "OK", "ex": "OK", "eq": "OK"},
                {"month": "Sep", "year": "25", "tu": "OK", "ex": "30", "eq": "OK"}
            ]
        }
    ],

    "inquiries": [
        {
            "company": "Company Name",
            "type": "Banks and S&Ls/Finance/etc",
            "date": "MM/DD/YYYY",
            "bureau": "TransUnion/Experian/Equifax"
        }
    ],

    "public_records": [
        {
            "type": "Bankruptcy/Judgment/Tax Lien",
            "filed_date": "MM/DD/YYYY",
            "court": "court name",
            "amount": 0.00,
            "status": "status",
            "bureau": "which bureau reports it"
        }
    ],

    "creditor_contacts": [
        {
            "creditor_name": "CREDITOR NAME",
            "address": "full address",
            "phone": "phone number"
        }
    ]
}

CRITICAL EXTRACTION RULES:

1. ACCOUNTS - Extract EVERY account shown. There should be 10-20+ accounts typically.
   - Look for section headers like "Account History" or "Trade Lines"
   - Each creditor block has data for up to 3 bureaus in columns

2. PAYMENT STATUS - Extract the EXACT text shown:
   - "Pays account as agreed" = Current (good)
   - "Current" = Current (good)  
   - "30 days past due" or "Past due 30 days" = Late (bad)
   - "60 days past due" = Very Late (bad)
   - "Not more than two payments past due" = Late (bad)

3. PAYMENT HISTORY - The grid showing OK/30/60/90 for each month
   - "OK" = paid on time
   - "30" = 30 days late
   - "60" = 60 days late
   - Empty or "-" = no data

4. NAMES - Note if the name is different across bureaus (this is a discrepancy)

5. CREDITOR CONTACTS - Usually at the end, with addresses and phone numbers

Extract ALL the data you can see. Do not skip accounts or sections."""


def parse_credit_report_vision(file_path: str) -> Dict[str, Any]:
    """
    Parse a credit report PDF using Claude Vision.
    Works on image-based PDFs that pdfplumber cannot read.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with parsed credit report data
    """
    result = {
        "success": False,
        "error": None,
        "report_type": "three_bureau",
        "extraction_method": "claude_vision",
        "data": None,
        "tokens_used": 0
    }

    # Check file exists
    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    # Get Claude client
    client = get_anthropic_client()
    if not client:
        result["error"] = "Anthropic API client not available. Check ANTHROPIC_API_KEY."
        return result

    # Convert PDF to images
    logger.info(f"Converting PDF to images: {file_path}")
    pdf_images = _convert_pdf_to_images(file_path, max_pages=20)

    if not pdf_images:
        result["error"] = "Could not convert PDF to images. Install: pip install pdf2image and apt-get install poppler-utils"
        return result

    logger.info(f"Sending {len(pdf_images)} images to Claude Vision for analysis")

    # Build message content with all page images
    messages_content = []

    for i, img_base64 in enumerate(pdf_images):
        messages_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_base64
            }
        })

    # Add the extraction prompt
    messages_content.append({
        "type": "text",
        "text": CREDIT_REPORT_EXTRACTION_PROMPT
    })

    try:
        # Call Claude Vision
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,  # Large output for full report
            temperature=0,
            messages=[{
                "role": "user",
                "content": messages_content
            }]
        )

        response_text = response.content[0].text.strip()
        result["tokens_used"] = response.usage.input_tokens + response.usage.output_tokens

        # Clean up JSON response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON
        try:
            extracted_data = json.loads(response_text)
            result["success"] = True
            result["data"] = extracted_data

            # Add analysis
            result["data"]["discrepancies"] = detect_discrepancies(extracted_data)
            result["data"]["derogatory_accounts"] = detect_derogatory_accounts(extracted_data.get("accounts", []))

            # Log summary
            accounts = extracted_data.get("accounts", [])
            scores = extracted_data.get("credit_scores", {})
            logger.info(f"Extracted: {len(accounts)} accounts, "
                       f"Scores: TU={scores.get('transunion', {}).get('score')}, "
                       f"EX={scores.get('experian', {}).get('score')}, "
                       f"EQ={scores.get('equifax', {}).get('score')}")

        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse Claude response as JSON: {je}")
            result["error"] = f"JSON parse error: {je}"
            result["raw_response"] = response_text[:2000]  # Save for debugging

    except Exception as e:
        logger.error(f"Claude Vision API error: {e}")
        result["error"] = str(e)

    return result


def detect_discrepancies(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect discrepancies between bureaus."""
    discrepancies = []

    # Check personal info - name variations
    pi = data.get("personal_info", {})
    tu_name = pi.get("transunion", {}).get("name", "")
    ex_name = pi.get("experian", {}).get("name", "")
    eq_name = pi.get("equifax", {}).get("name", "")

    names = [n for n in [tu_name, ex_name, eq_name] if n]
    if len(set(names)) > 1:
        discrepancies.append({
            "type": "personal_info",
            "field": "name",
            "description": f"Name varies: TU='{tu_name}', EX='{ex_name}', EQ='{eq_name}'"
        })

    # Check summary stats - delinquent count
    stats = data.get("summary_stats", {})
    tu_delinq = stats.get("transunion", {}).get("delinquent", 0)
    ex_delinq = stats.get("experian", {}).get("delinquent", 0)
    eq_delinq = stats.get("equifax", {}).get("delinquent", 0)

    if tu_delinq != ex_delinq or ex_delinq != eq_delinq:
        discrepancies.append({
            "type": "summary",
            "field": "delinquent",
            "description": f"Delinquent count varies: TU={tu_delinq}, EX={ex_delinq}, EQ={eq_delinq}"
        })

    # Check account discrepancies
    for account in data.get("accounts", []):
        creditor = account.get("creditor_name", "Unknown")

        # Balance discrepancy
        balances = [
            account.get("tu_balance"),
            account.get("ex_balance"),
            account.get("eq_balance")
        ]
        balances = [b for b in balances if b is not None]
        if len(balances) >= 2 and len(set(balances)) > 1:
            discrepancies.append({
                "type": "account",
                "account": creditor,
                "field": "balance",
                "description": f"Balance varies for {creditor}"
            })

        # Payment status discrepancy
        statuses = [
            account.get("tu_payment_status", ""),
            account.get("ex_payment_status", ""),
            account.get("eq_payment_status", "")
        ]
        statuses = [s for s in statuses if s]
        if len(statuses) >= 2 and len(set(statuses)) > 1:
            discrepancies.append({
                "type": "account",
                "account": creditor,
                "field": "payment_status",
                "description": f"Payment status varies for {creditor}"
            })

    return discrepancies


def detect_derogatory_accounts(accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify accounts with derogatory marks."""
    derogatory = []

    bad_keywords = [
        "past due", "late", "collection", "charge off", "charged off",
        "delinquent", "30 days", "60 days", "90 days", "120 days",
        "not more than"
    ]

    for account in accounts:
        issues = []
        creditor = account.get("creditor_name", "Unknown")

        for bureau, prefix in [("TransUnion", "tu"), ("Experian", "ex"), ("Equifax", "eq")]:
            status = str(account.get(f"{prefix}_payment_status", "")).lower()
            past_due = account.get(f"{prefix}_past_due", 0) or 0

            # Check payment status
            for keyword in bad_keywords:
                if keyword in status:
                    issues.append({
                        "bureau": bureau,
                        "issue": f"Payment status: {account.get(f'{prefix}_payment_status', '')}"
                    })
                    break

            # Check past due amount
            if past_due > 0:
                issues.append({
                    "bureau": bureau,
                    "issue": f"Past due: ${past_due}"
                })

        if issues:
            derogatory.append({
                "creditor_name": creditor,
                "account_number": account.get("account_number"),
                "issues": issues
            })

    return derogatory


def get_worst_payment_status(account: Dict[str, Any]) -> Dict[str, str]:
    """Get the worst payment status across all bureaus for display."""
    statuses = [
        str(account.get("tu_payment_status", "")).lower(),
        str(account.get("ex_payment_status", "")).lower(),
        str(account.get("eq_payment_status", "")).lower()
    ]

    # Check for severe delinquency first
    for status in statuses:
        if "90" in status or "120" in status or "charge" in status:
            return {"text": "90+ Days Late", "class": "badge-danger", "color": "red"}

    for status in statuses:
        if "60" in status:
            return {"text": "60 Days Past Due", "class": "badge-danger", "color": "red"}

    for status in statuses:
        if "30" in status or "not more than" in status:
            return {"text": "30 Days Past Due", "class": "badge-warning", "color": "yellow"}

    # Check for good status
    for status in statuses:
        if "current" in status or "pays" in status or "agreed" in status:
            return {"text": "Current", "class": "badge-success", "color": "green"}

    # Check for closed
    for status in statuses:
        if "closed" in status or "paid" in status:
            return {"text": "Closed", "class": "badge-secondary", "color": "gray"}

    return {"text": "Unknown", "class": "badge-secondary", "color": "gray"}


# =============================================================================
# MAIN ENTRY POINT - Replace parse_credit_report_pdf in pdf_parser_service.py
# =============================================================================

def parse_credit_report_pdf(file_path: str) -> Dict[str, Any]:
    """
    Main entry point for parsing credit report PDFs.

    First tries text extraction (pdfplumber), falls back to Claude Vision for image PDFs.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with parsed credit report data
    """
    # Try text extraction first
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

            # If we got substantial text, use text parser
            if len(text.strip()) > 500:
                logger.info(f"PDF has extractable text ({len(text)} chars), using text parser")
                # Import and use the text-based parser
                from services.pdf_parser_service_text import parse_three_bureau_text
                return parse_three_bureau_text(text)
    except Exception as e:
        logger.warning(f"Text extraction failed: {e}")

    # Fall back to Claude Vision for image-based PDFs
    logger.info("PDF appears to be image-based, using Claude Vision")
    return parse_credit_report_vision(file_path)


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_parser(file_path: str):
    """Test the parser on a credit report PDF."""
    print("=" * 70)
    print("CREDIT REPORT PARSER TEST")
    print(f"File: {file_path}")
    print("=" * 70)

    result = parse_credit_report_vision(file_path)

    if not result["success"]:
        print(f"\n❌ FAILED: {result['error']}")
        return

    data = result["data"]
    print(f"\n✅ SUCCESS - Tokens used: {result['tokens_used']}")

    # Report info
    print(f"\n📋 Report: {data.get('reference_number')} dated {data.get('report_date')}")

    # Scores
    scores = data.get("credit_scores", {})
    print(f"\n📊 CREDIT SCORES:")
    for bureau in ["transunion", "experian", "equifax"]:
        s = scores.get(bureau, {})
        print(f"   {bureau.title()}: {s.get('score')} ({s.get('rank')})")

    # Summary
    stats = data.get("summary_stats", {})
    print(f"\n📈 SUMMARY STATS:")
    print(f"   {'':20} {'TU':>10} {'EX':>10} {'EQ':>10}")
    for stat in ["total_accounts", "open_accounts", "delinquent", "balances"]:
        tu = stats.get("transunion", {}).get(stat, "-")
        ex = stats.get("experian", {}).get(stat, "-")
        eq = stats.get("equifax", {}).get(stat, "-")
        print(f"   {stat:20} {str(tu):>10} {str(ex):>10} {str(eq):>10}")

    # Accounts
    accounts = data.get("accounts", [])
    print(f"\n💳 ACCOUNTS ({len(accounts)} found):")
    for acc in accounts[:10]:  # Show first 10
        status = get_worst_payment_status(acc)
        bal = acc.get("tu_balance") or acc.get("ex_balance") or acc.get("eq_balance") or 0
        print(f"   • {acc.get('creditor_name', 'Unknown'):30} ${bal:>10,.2f}  [{status['text']}]")
    if len(accounts) > 10:
        print(f"   ... and {len(accounts) - 10} more")

    # Discrepancies
    discrepancies = data.get("discrepancies", [])
    if discrepancies:
        print(f"\n⚠️  DISCREPANCIES ({len(discrepancies)}):")
        for d in discrepancies[:5]:
            print(f"   • {d.get('description')}")

    # Derogatory
    derogatory = data.get("derogatory_accounts", [])
    if derogatory:
        print(f"\n🔴 DEROGATORY ACCOUNTS ({len(derogatory)}):")
        for d in derogatory:
            issues = ", ".join([f"{i['bureau']}: {i['issue']}" for i in d.get('issues', [])])
            print(f"   • {d.get('creditor_name')}: {issues}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python credit_report_ocr_parser.py <path_to_pdf>")
    else:
        test_parser(sys.argv[1])
