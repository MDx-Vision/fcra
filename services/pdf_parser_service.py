"""
PDF Parser Service for extracting structured data from credit report PDFs.
Supports Experian, TransUnion, and Equifax credit report formats.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _extract_text_pypdf2(file_path: str) -> Optional[str]:
    """Extract text using PyPDF2."""
    try:
        import PyPDF2

        text_parts = []
        with open(file_path, "rb") as f:
            try:
                reader = PyPDF2.PdfReader(f)
                if reader.is_encrypted:
                    return None
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            except PyPDF2.errors.FileNotDecryptedError:
                return None
        return "\n\n".join(text_parts) if text_parts else None
    except ImportError:
        logger.warning("PyPDF2 not available")
        return None
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {e}")
        return None


def _extract_text_pdfplumber(file_path: str) -> Optional[str]:
    """Extract text using pdfplumber (better for tabular data)."""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            row_text = " | ".join(
                                [str(cell) if cell else "" for cell in row]
                            )
                            if row_text.strip():
                                text_parts.append(row_text)
        return "\n\n".join(text_parts) if text_parts else None
    except ImportError:
        logger.warning("pdfplumber not available")
        return None
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")
        return None


def _extract_text_pypdf(file_path: str) -> Optional[str]:
    """Extract text using pypdf (fallback)."""
    try:
        from pypdf import PdfReader

        text_parts = []
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            return None
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts) if text_parts else None
    except ImportError:
        logger.warning("pypdf not available")
        return None
    except Exception as e:
        logger.error(f"pypdf extraction failed: {e}")
        return None


def extract_text_from_pdf(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from PDF using multiple methods.
    Returns (text, error_message).
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"

    text = _extract_text_pdfplumber(file_path)
    if text and len(text.strip()) > 100:
        logger.info(f"Extracted {len(text)} chars using pdfplumber")
        return text, None

    text = _extract_text_pypdf2(file_path)
    if text is None:
        return None, "PDF is password-protected. Please provide an unprotected PDF."
    if text and len(text.strip()) > 100:
        logger.info(f"Extracted {len(text)} chars using PyPDF2")
        return text, None

    text = _extract_text_pypdf(file_path)
    if text is None:
        return None, "PDF is password-protected. Please provide an unprotected PDF."
    if text and len(text.strip()) > 100:
        logger.info(f"Extracted {len(text)} chars using pypdf")
        return text, None

    if not text or len(text.strip()) < 100:
        return (
            None,
            "This appears to be an image-based PDF. Please use the OCR scanner instead.",
        )

    return text, None


BUREAU_PATTERNS = {
    "Experian": [
        r"experian",
        r"experian\.com",
        r"experian information solutions",
        r"experian consumer services",
    ],
    "TransUnion": [
        r"transunion",
        r"trans\s*union",
        r"transunion\.com",
        r"transunion llc",
    ],
    "Equifax": [
        r"equifax",
        r"equifax\.com",
        r"equifax information services",
        r"equifax inc",
    ],
}


def detect_bureau(text: str) -> str:
    """Detect which credit bureau the report is from."""
    if not text:
        return "Unknown"

    text_lower = text.lower()

    bureau_scores = {}
    for bureau, patterns in BUREAU_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower))
            score += matches
        bureau_scores[bureau] = score

    if max(bureau_scores.values()) > 0:
        return max(bureau_scores, key=bureau_scores.get)

    return "Unknown"


DATE_PATTERNS = [
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
    r"(\d{1,2})/(\d{1,2})/(\d{2})",
    r"(\d{1,2})-(\d{1,2})-(\d{4})",
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})",
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})",
]


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date to YYYY-MM-DD format."""
    if not date_str:
        return None

    date_str = date_str.strip()

    for pattern in DATE_PATTERNS:
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if pattern == DATE_PATTERNS[3]:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                elif pattern == DATE_PATTERNS[4]:
                    month_name, day, year = groups[0], int(groups[1]), int(groups[2])
                    month = _month_to_num(month_name)
                elif pattern == DATE_PATTERNS[5]:
                    day, month_name, year = int(groups[0]), groups[1], int(groups[2])
                    month = _month_to_num(month_name)
                else:
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    if year < 100:
                        year += 2000 if year < 50 else 1900

                return f"{year:04d}-{month:02d}-{day:02d}"
            except (ValueError, TypeError):
                pass

    return date_str


def _month_to_num(month_name: str) -> int:
    """Convert month name to number."""
    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    return months.get(month_name.lower()[:3], 1)


def extract_personal_info(text: str) -> Dict[str, Any]:
    """Extract personal information from credit report text."""
    info = {
        "name": None,
        "address": None,
        "ssn_last_4": None,
        "date_of_birth": None,
        "phone": None,
    }

    if not text:
        return info

    ssn_patterns = [
        r"SSN[:\s]+XXX-XX-(\d{4})",
        r"Social Security[:\s]+\*{5,7}(\d{4})",
        r"SSN[:\s]+\*{5,9}(\d{4})",
        r"XXX-XX-(\d{4})",
        r"\*\*\*-\*\*-(\d{4})",
    ]
    for pattern in ssn_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["ssn_last_4"] = match.group(1)
            break

    name_patterns = [
        r"(?:Consumer|Name|Report\s+For)[:\s]+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})",
        r"^([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3})$",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            if len(name) > 3 and len(name) < 60:
                info["name"] = name.title() if name.isupper() else name
                break

    address_patterns = [
        r"(?:Address|Current Address|Mailing Address)[:\s]+(.{10,100}?)(?:\n|$)",
        r"(\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:ST|AVE|BLVD|DR|RD|LN|CT|WAY|PL|CIR)[.,]?\s+[A-Za-z]+(?:\s+[A-Za-z]+)*[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)",
    ]
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            addr = match.group(1).strip()
            if len(addr) > 10:
                info["address"] = addr
                break

    dob_patterns = [
        r"(?:Date of Birth|DOB|Birth Date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:Date of Birth|DOB|Birth Date)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["date_of_birth"] = normalize_date(match.group(1))
            break

    phone_patterns = [
        r"(?:Phone|Telephone|Tel)[:\s]+\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})",
        r"\((\d{3})\)\s*(\d{3})[\s.-]?(\d{4})",
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["phone"] = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            break

    return info


ACCOUNT_STATUS_MAP = {
    "open": ["open", "active", "current"],
    "closed": ["closed", "paid", "satisfied"],
    "delinquent": ["delinquent", "past due", "late", "derogatory"],
    "collection": ["collection", "charged off", "charge off", "chargeoff"],
    "disputed": ["disputed", "in dispute", "dispute"],
    "paid": ["paid in full", "paid as agreed", "never late"],
}


def classify_account_status(text: str) -> str:
    """Classify account status from text."""
    if not text:
        return "Unknown"

    text_lower = text.lower()

    for status, keywords in ACCOUNT_STATUS_MAP.items():
        for keyword in keywords:
            if keyword in text_lower:
                return status.title()

    return "Unknown"


def extract_currency(text: str) -> Optional[float]:
    """Extract currency amount from text."""
    if not text:
        return None

    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)",
        r"([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass

    match = re.search(r"[\d,]+(?:\.\d{2})?", text)
    if match:
        try:
            val = float(match.group(0).replace(",", ""))
            if val > 0:
                return val
        except ValueError:
            pass

    return None


def extract_accounts(text: str) -> List[Dict[str, Any]]:
    """Extract account information from credit report text."""
    accounts = []

    if not text:
        return accounts

    account_markers = [
        r"(?:REVOLVING ACCOUNTS?|INSTALLMENT ACCOUNTS?|MORTGAGE ACCOUNTS?|OPEN ACCOUNTS?|CLOSED ACCOUNTS?|OTHER ACCOUNTS?)",
        r"(?:Account Name|Creditor Name|Lender)[:\s]",
        r"(?:BANK|CREDIT UNION|FINANCIAL|CAPITAL ONE|CHASE|DISCOVER|WELLS FARGO|CITI|AMEX|AMERICAN EXPRESS|SYNCHRONY|BARCLAYS)",
    ]

    account_pattern = re.compile(
        r"(?P<creditor>[A-Z][A-Za-z0-9\s&.,'-]{2,50}?)[\s\n]+"
        r"(?:Account\s*(?:Number|#)?[:\s]*)?(?P<account_num>[X\d*-]{4,20})?"
        r".*?"
        r"(?:(?:Balance|Current Balance|High Balance)[:\s]*\$?\s*(?P<balance>[\d,]+(?:\.\d{2})?))?"
        r".*?"
        r"(?:(?:Status|Account Status|Condition)[:\s]*(?P<status>[A-Za-z\s]+?))?"
        r".*?"
        r"(?:(?:Date Opened|Opened|Open Date)[:\s]*(?P<opened>[\d/\-]+))?"
        r".*?"
        r"(?:(?:Credit Limit|Limit)[:\s]*\$?\s*(?P<limit>[\d,]+(?:\.\d{2})?))?",
        re.IGNORECASE | re.DOTALL,
    )

    sections = re.split(
        r"(?:REVOLVING|INSTALLMENT|MORTGAGE|ACCOUNTS?|TRADELINE)",
        text,
        flags=re.IGNORECASE,
    )

    for section in sections:
        creditor_pattern = re.compile(
            r"([A-Z][A-Z0-9\s&.,'-]{2,40}(?:BANK|CREDIT|FINANCE|CAPITAL|CARD|AUTO|LOAN|MORTGAGE)?[A-Z0-9]*)"
            r"[\s\n]+.*?"
            r"(?:Account\s*(?:Number|#)?[:\s]*([X\d*-]{4,20}))?",
            re.IGNORECASE | re.DOTALL,
        )

        for match in creditor_pattern.finditer(section):
            creditor = match.group(1).strip() if match.group(1) else None
            account_num = match.group(2).strip() if match.group(2) else None

            if creditor and len(creditor) >= 3:
                context_start = max(0, match.start() - 50)
                context_end = min(len(section), match.end() + 500)
                context = section[context_start:context_end]

                balance_match = re.search(
                    r"(?:Balance|Current Balance|High Balance)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)",
                    context,
                    re.IGNORECASE,
                )
                balance = (
                    extract_currency(balance_match.group(1)) if balance_match else None
                )

                status_match = re.search(
                    r"(?:Status|Account Status|Condition)[:\s]*([A-Za-z\s]+?)(?:\n|$|,)",
                    context,
                    re.IGNORECASE,
                )
                status = (
                    classify_account_status(status_match.group(1))
                    if status_match
                    else classify_account_status(context)
                )

                opened_match = re.search(
                    r"(?:Date Opened|Opened|Open Date)[:\s]*([\d/\-]+)",
                    context,
                    re.IGNORECASE,
                )
                opened = normalize_date(opened_match.group(1)) if opened_match else None

                limit_match = re.search(
                    r"(?:Credit Limit|Limit)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)",
                    context,
                    re.IGNORECASE,
                )
                limit = extract_currency(limit_match.group(1)) if limit_match else None

                payment_history = []
                history_match = re.search(
                    r"(?:Payment History|Pay Status)[:\s]*([OCXR123456789]{1,24})",
                    context,
                    re.IGNORECASE,
                )
                if history_match:
                    payment_history = list(history_match.group(1))

                account_data = {
                    "name": creditor,
                    "number": account_num,
                    "balance": balance,
                    "status": status,
                    "date_opened": opened,
                    "credit_limit": limit,
                    "payment_history": payment_history,
                    "account_type": _detect_account_type(creditor, context),
                }

                if not any(
                    a.get("name", "").upper() == creditor.upper()
                    and a.get("number") == account_num
                    for a in accounts
                ):
                    accounts.append(account_data)

    if len(accounts) < 3:
        generic_pattern = re.compile(
            r"([A-Z][A-Z0-9/\s&.,'-]{3,45})\s+"
            r"(?:Account|Acct)?[#:\s]*([\dXx*-]{4,20})\s+"
            r".*?"
            r"(?:\$\s*)?([\d,]+(?:\.\d{2})?)",
            re.MULTILINE,
        )

        for match in generic_pattern.finditer(text):
            creditor = match.group(1).strip()
            account_num = match.group(2).strip()
            balance = extract_currency(match.group(3))

            if creditor and len(creditor) >= 3:
                if not any(
                    a.get("name", "").upper() == creditor.upper() for a in accounts
                ):
                    accounts.append(
                        {
                            "name": creditor,
                            "number": account_num,
                            "balance": balance,
                            "status": "Unknown",
                            "date_opened": None,
                            "credit_limit": None,
                            "payment_history": [],
                            "account_type": "Unknown",
                        }
                    )

    return accounts[:50]


def _detect_account_type(creditor: str, context: str) -> str:
    """Detect account type from creditor name and context."""
    text = (creditor + " " + context).lower()

    if any(kw in text for kw in ["mortgage", "home loan", "real estate"]):
        return "Mortgage"
    elif any(kw in text for kw in ["auto", "car", "vehicle", "motor"]):
        return "Auto Loan"
    elif any(kw in text for kw in ["student", "education", "school"]):
        return "Student Loan"
    elif any(
        kw in text
        for kw in ["credit card", "card", "visa", "mastercard", "amex", "discover"]
    ):
        return "Credit Card"
    elif any(kw in text for kw in ["installment", "loan"]):
        return "Installment Loan"
    elif any(kw in text for kw in ["revolving", "line of credit", "heloc"]):
        return "Revolving"
    elif any(kw in text for kw in ["medical", "hospital", "doctor", "health"]):
        return "Medical"
    elif any(kw in text for kw in ["utility", "electric", "gas", "water", "phone"]):
        return "Utility"

    return "Unknown"


def extract_inquiries(text: str) -> List[Dict[str, Any]]:
    """Extract inquiry information from credit report text."""
    inquiries = []

    if not text:
        return inquiries

    inquiry_section = None
    inquiry_markers = [
        "INQUIRIES",
        "CREDIT INQUIRIES",
        "REGULAR INQUIRIES",
        "HARD INQUIRIES",
        "REQUESTS FOR YOUR CREDIT",
    ]

    for marker in inquiry_markers:
        idx = text.upper().find(marker)
        if idx != -1:
            end_markers = [
                "PUBLIC RECORD",
                "COLLECTION",
                "ACCOUNT SUMMARY",
                "SCORE",
                "END OF REPORT",
            ]
            end_idx = len(text)
            for end_marker in end_markers:
                temp_idx = text.upper().find(end_marker, idx + len(marker))
                if temp_idx != -1 and temp_idx < end_idx:
                    end_idx = temp_idx
            inquiry_section = text[idx:end_idx]
            break

    if not inquiry_section:
        inquiry_section = text

    inquiry_pattern = re.compile(
        r"([A-Z][A-Za-z0-9\s&.,'-]{2,50})\s+" r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        re.MULTILINE,
    )

    for match in inquiry_pattern.finditer(inquiry_section):
        company = match.group(1).strip()
        date = normalize_date(match.group(2))

        if company and len(company) >= 3:
            skip_words = ["SECTION", "PAGE", "REPORT", "CONSUMER", "YOUR", "THE"]
            if not any(word in company.upper() for word in skip_words):
                inquiry_data = {
                    "company": company,
                    "date": date,
                    "type": "Hard Inquiry",
                }

                if not any(
                    i.get("company", "").upper() == company.upper()
                    and i.get("date") == date
                    for i in inquiries
                ):
                    inquiries.append(inquiry_data)

    return inquiries[:30]


def extract_collections(text: str) -> List[Dict[str, Any]]:
    """Extract collection account information from credit report text."""
    collections = []

    if not text:
        return collections

    collection_section = None
    collection_markers = [
        "COLLECTION",
        "COLLECTIONS",
        "COLLECTION ACCOUNTS",
        "ACCOUNTS IN COLLECTION",
    ]

    for marker in collection_markers:
        idx = text.upper().find(marker)
        if idx != -1:
            end_markers = ["PUBLIC RECORD", "INQUIRIES", "ACCOUNT SUMMARY", "SCORE"]
            end_idx = len(text)
            for end_marker in end_markers:
                temp_idx = text.upper().find(end_marker, idx + len(marker))
                if temp_idx != -1 and temp_idx < end_idx:
                    end_idx = temp_idx
            collection_section = text[idx:end_idx]
            break

    if not collection_section:
        collection_section = text

    collection_pattern = re.compile(
        r"([A-Z][A-Za-z0-9\s&.,'-]{2,50}(?:COLLECTION|AGENCY|RECOVERY|ASSOCIATES|SERVICES)?)"
        r"[\s\n]+"
        r"(?:.*?Original\s*Creditor[:\s]*([A-Za-z0-9\s&.,'-]+?))?"
        r".*?"
        r"(?:\$\s*)?([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE | re.DOTALL,
    )

    for match in collection_pattern.finditer(collection_section):
        agency = match.group(1).strip() if match.group(1) else None
        original_creditor = match.group(2).strip() if match.group(2) else None
        amount = extract_currency(match.group(3)) if match.group(3) else None

        if agency and len(agency) >= 3:
            collection_keywords = [
                "collection",
                "agency",
                "recovery",
                "associates",
                "services",
                "portfolio",
                "midland",
                "lvnv",
                "cavalry",
                "encore",
            ]
            is_collection = any(kw in agency.lower() for kw in collection_keywords)

            if is_collection or (amount and amount > 0):
                collection_data = {
                    "agency": agency,
                    "creditor": original_creditor,
                    "amount": amount,
                    "status": "Open",
                }

                if not any(
                    c.get("agency", "").upper() == agency.upper() for c in collections
                ):
                    collections.append(collection_data)

    return collections[:20]


def extract_public_records(text: str) -> List[Dict[str, Any]]:
    """Extract public record information from credit report text."""
    records = []

    if not text:
        return records

    public_section = None
    public_markers = [
        "PUBLIC RECORD",
        "PUBLIC RECORDS",
        "BANKRUPTCIES",
        "JUDGMENTS",
        "TAX LIENS",
    ]

    for marker in public_markers:
        idx = text.upper().find(marker)
        if idx != -1:
            end_markers = [
                "COLLECTION",
                "INQUIRIES",
                "ACCOUNT SUMMARY",
                "TRADELINE",
                "ACCOUNTS",
            ]
            end_idx = min(len(text), idx + 3000)
            for end_marker in end_markers:
                temp_idx = text.upper().find(end_marker, idx + len(marker))
                if temp_idx != -1 and temp_idx < end_idx:
                    end_idx = temp_idx
            public_section = text[idx:end_idx]
            break

    if not public_section:
        return records

    record_types = {
        "Bankruptcy": ["bankruptcy", "chapter 7", "chapter 13", "chapter 11", "bk"],
        "Judgment": ["judgment", "civil judgment"],
        "Tax Lien": ["tax lien", "federal tax", "state tax"],
        "Foreclosure": ["foreclosure"],
        "Garnishment": ["garnishment", "wage garnishment"],
    }

    for record_type, keywords in record_types.items():
        for keyword in keywords:
            pattern = re.compile(
                rf"({keyword})\s*"
                rf"(?:.*?(?:filed|date)[:\s]*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}))?.*?"
                rf"(?:(?:amount|balance)[:\s]*\$?\s*([\d,]+(?:\.\d{{2}})?))?"
                rf"(?:.*?(?:court|county|status)[:\s]*([A-Za-z\s]+))?",
                re.IGNORECASE | re.DOTALL,
            )

            for match in pattern.finditer(public_section):
                date = normalize_date(match.group(2)) if match.group(2) else None
                amount = extract_currency(match.group(3)) if match.group(3) else None
                court = match.group(4).strip() if match.group(4) else None

                record_data = {
                    "type": record_type,
                    "date_filed": date,
                    "amount": amount,
                    "court": court,
                    "status": "Filed",
                }

                if not any(
                    r.get("type") == record_type and r.get("date_filed") == date
                    for r in records
                ):
                    records.append(record_data)

    return records[:10]


def parse_credit_report_pdf(file_path: str) -> Dict[str, Any]:
    """
    Parse a credit report PDF and extract structured data.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with parsed credit report data
    """
    result = {
        "success": False,
        "error": None,
        "bureau": "Unknown",
        "personal_info": {},
        "accounts": [],
        "inquiries": [],
        "collections": [],
        "public_records": [],
        "raw_text": None,
        "text_length": 0,
        "parsing_confidence": 0.0,
    }

    text, error = extract_text_from_pdf(file_path)

    if error:
        result["error"] = error
        return result

    if not text or len(text.strip()) < 100:
        result["error"] = (
            "Could not extract sufficient text from PDF. This may be an image-based PDF - please use the OCR scanner instead."
        )
        return result

    result["raw_text"] = text
    result["text_length"] = len(text)

    result["bureau"] = detect_bureau(text)
    result["personal_info"] = extract_personal_info(text)
    result["accounts"] = extract_accounts(text)
    result["inquiries"] = extract_inquiries(text)
    result["collections"] = extract_collections(text)
    result["public_records"] = extract_public_records(text)

    confidence = 0.0
    if result["bureau"] != "Unknown":
        confidence += 0.2
    if result["personal_info"].get("name"):
        confidence += 0.2
    if result["personal_info"].get("ssn_last_4"):
        confidence += 0.1
    if len(result["accounts"]) > 0:
        confidence += 0.3
    if len(result["inquiries"]) > 0:
        confidence += 0.1
    if len(result["collections"]) > 0 or len(result["public_records"]) > 0:
        confidence += 0.1

    result["parsing_confidence"] = min(confidence, 1.0)
    result["success"] = True

    logger.info(
        f"Parsed credit report: bureau={result['bureau']}, accounts={len(result['accounts'])}, confidence={result['parsing_confidence']:.2f}"
    )

    return result


def get_parsed_text_for_analysis(parsed_result: Dict[str, Any]) -> str:
    """
    Convert parsed result to text format suitable for Claude analysis.

    Args:
        parsed_result: Result from parse_credit_report_pdf

    Returns:
        Formatted text for analysis
    """
    lines = []

    lines.append(f"=== CREDIT REPORT PARSED DATA ===")
    lines.append(f"Bureau: {parsed_result.get('bureau', 'Unknown')}")
    lines.append("")

    personal = parsed_result.get("personal_info", {})
    lines.append("=== PERSONAL INFORMATION ===")
    if personal.get("name"):
        lines.append(f"Name: {personal['name']}")
    if personal.get("address"):
        lines.append(f"Address: {personal['address']}")
    if personal.get("ssn_last_4"):
        lines.append(f"SSN Last 4: ***-**-{personal['ssn_last_4']}")
    if personal.get("date_of_birth"):
        lines.append(f"Date of Birth: {personal['date_of_birth']}")
    lines.append("")

    accounts = parsed_result.get("accounts", [])
    lines.append(f"=== ACCOUNTS ({len(accounts)}) ===")
    for i, acc in enumerate(accounts, 1):
        lines.append(f"\n--- Account {i} ---")
        lines.append(f"Creditor: {acc.get('name', 'Unknown')}")
        if acc.get("number"):
            lines.append(f"Account Number: {acc['number']}")
        if acc.get("balance") is not None:
            lines.append(f"Balance: ${acc['balance']:,.2f}")
        if acc.get("credit_limit") is not None:
            lines.append(f"Credit Limit: ${acc['credit_limit']:,.2f}")
        lines.append(f"Status: {acc.get('status', 'Unknown')}")
        if acc.get("date_opened"):
            lines.append(f"Date Opened: {acc['date_opened']}")
        if acc.get("account_type"):
            lines.append(f"Account Type: {acc['account_type']}")
        if acc.get("payment_history"):
            lines.append(f"Payment History: {''.join(acc['payment_history'])}")
    lines.append("")

    collections = parsed_result.get("collections", [])
    if collections:
        lines.append(f"=== COLLECTIONS ({len(collections)}) ===")
        for i, col in enumerate(collections, 1):
            lines.append(f"\n--- Collection {i} ---")
            lines.append(f"Collection Agency: {col.get('agency', 'Unknown')}")
            if col.get("creditor"):
                lines.append(f"Original Creditor: {col['creditor']}")
            if col.get("amount") is not None:
                lines.append(f"Amount: ${col['amount']:,.2f}")
            lines.append(f"Status: {col.get('status', 'Unknown')}")
        lines.append("")

    inquiries = parsed_result.get("inquiries", [])
    if inquiries:
        lines.append(f"=== INQUIRIES ({len(inquiries)}) ===")
        for inq in inquiries:
            lines.append(
                f"  {inq.get('date', 'Unknown date')} - {inq.get('company', 'Unknown')}"
            )
        lines.append("")

    public_records = parsed_result.get("public_records", [])
    if public_records:
        lines.append(f"=== PUBLIC RECORDS ({len(public_records)}) ===")
        for rec in public_records:
            amount_str = f" - ${rec['amount']:,.2f}" if rec.get("amount") else ""
            lines.append(
                f"  {rec.get('type', 'Unknown')} ({rec.get('date_filed', 'Unknown date')}){amount_str}"
            )
        lines.append("")

    if parsed_result.get("raw_text"):
        lines.append("=== RAW TEXT EXCERPT (First 5000 chars) ===")
        lines.append(parsed_result["raw_text"][:5000])

    return "\n".join(lines)
