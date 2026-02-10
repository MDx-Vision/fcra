"""
Negative Item Extractor Service

Extracts negative/disputable items from parsed credit reports.
These items are then saved to the DisputeItem table for use by
AI Dispute Writer, 5-Day Knockout, Goodwill Letters, etc.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NegativeItemExtractor:
    """Extract negative items from credit reports for dispute generation."""

    # Status keywords indicating negative items
    NEGATIVE_STATUS_KEYWORDS = [
        "late",
        "past due",
        "delinquent",
        "charge off",
        "charged off",
        "chargeoff",
        "collection",
        "repossession",
        "foreclosure",
        "bankruptcy",
        "judgment",
        "lien",
        "settled",
        "written off",
        "profit and loss",
        "bad debt",
        "seriously past due",
        "account charged off",
        "paid charge off",
        "unpaid",
        "in collections",
        "sold to",
        "transferred",
        "closed for cause",
    ]

    # Payment status patterns indicating late payments
    LATE_PAYMENT_PATTERNS = [
        r"30\s*day",
        r"60\s*day",
        r"90\s*day",
        r"120\s*day",
        r"150\s*day",
        r"180\s*day",
        r"\d+\s*days?\s*(?:past\s*due|late)",
    ]

    # Positive status keywords (exclude these)
    POSITIVE_STATUS_KEYWORDS = [
        "pays as agreed",
        "paying as agreed",
        "paid as agreed",
        "current",
        "paid satisfactorily",
        "account in good standing",
        "never late",
        "open/never late",
    ]

    def __init__(self, parsed_report: Dict[str, Any]):
        """
        Initialize with a parsed credit report.

        Args:
            parsed_report: Dict from credit_report_parser containing
                          accounts, inquiries, collections, public_records
        """
        self.report = parsed_report
        self.client_id = parsed_report.get("client_id")
        self.client_name = parsed_report.get("client_name", "Unknown")

    def extract_all_negative_items(self) -> List[Dict]:
        """
        Main entry point - extract all negative items from the credit report.

        Returns:
            List of negative item dicts ready for DisputeItem creation
        """
        items = []

        # Extract from different sections
        items.extend(self._extract_negative_tradelines())
        items.extend(self._extract_inquiries())
        items.extend(self._extract_collections())
        items.extend(self._extract_public_records())

        logger.info(
            f"Extracted {len(items)} negative items for {self.client_name}: "
            f"{self._summarize_items(items)}"
        )

        return items

    def _summarize_items(self, items: List[Dict]) -> str:
        """Create summary string of items by type."""
        counts = {}
        for item in items:
            item_type = item.get("item_type", "unknown")
            counts[item_type] = counts.get(item_type, 0) + 1
        return ", ".join(f"{k}={v}" for k, v in counts.items())

    def _extract_negative_tradelines(self) -> List[Dict]:
        """
        Extract tradeline accounts with negative indicators.

        Looks for:
        - Late payments (30/60/90/120+ days)
        - Charge-offs
        - Settled accounts
        - Closed for cause
        - High utilization (>90%)
        """
        negative_items = []
        accounts = self.report.get("accounts", [])

        for idx, account in enumerate(accounts):
            negative_reasons = self._detect_negative_indicators(account)

            if negative_reasons:
                item_type = self._classify_item_type(account, negative_reasons)
                bureaus = self._get_reporting_bureaus(account)

                item = {
                    "source_index": idx,
                    "creditor_name": account.get("creditor", "Unknown"),
                    "account_id": self._extract_account_number(account),
                    "item_type": item_type,
                    "bureaus": bureaus,
                    "status": account.get("status")
                    or account.get("payment_status", ""),
                    "balance": self._parse_currency(account.get("balance")),
                    "credit_limit": self._parse_currency(account.get("credit_limit")),
                    "high_credit": self._parse_currency(account.get("high_credit")),
                    "date_opened": account.get("date_opened"),
                    "date_closed": account.get("date_closed"),
                    "last_reported": account.get("last_reported"),
                    "last_payment": account.get("last_payment"),
                    "account_type": account.get("account_type"),
                    "negative_reasons": negative_reasons,
                    "comments": account.get("comments", ""),
                    "raw_data": account,
                }
                negative_items.append(item)

        return negative_items

    def _detect_negative_indicators(self, account: Dict) -> List[str]:
        """
        Detect negative indicators in an account.

        Returns list of reasons why this account is negative.
        """
        reasons = []

        # Combine all status fields
        status_text = " ".join(
            [
                str(account.get("status", "")),
                str(account.get("payment_status", "")),
                str(account.get("account_status", "")),
                str(account.get("account_rating", "")),  # Include account_rating
                str(account.get("comments", "")),
                str(account.get("creditor_remarks", "")),  # Include creditor remarks
            ]
        ).lower()

        # Check for negative status keywords FIRST (before positive check)
        for keyword in self.NEGATIVE_STATUS_KEYWORDS:
            if keyword in status_text:
                reasons.append(f"Status indicates: {keyword}")

        # Check for late payment patterns in status text
        for pattern in self.LATE_PAYMENT_PATTERNS:
            if re.search(pattern, status_text, re.IGNORECASE):
                match = re.search(pattern, status_text, re.IGNORECASE)
                reasons.append(f"Late payment: {match.group(0)}")

        # Check payment_history array for late payment codes (30, 60, 90, 120, etc.)
        payment_history = account.get("payment_history", [])
        late_months = []
        for entry in payment_history:
            month = entry.get("month", "")
            for bureau in ["transunion", "experian", "equifax"]:
                val = str(entry.get(bureau, "")).strip()
                # Values like "30", "60", "90", "120", "150", "180" indicate late payments
                # Values like "OK", "U", "-", "" are not late
                if val in ["30", "60", "90", "120", "150", "180", "CO", "FC", "RP"]:
                    late_months.append(f"{month} {bureau}: {val}")

        if late_months:
            # Limit to first 3 for brevity
            reasons.append(f"Payment history shows late: {', '.join(late_months[:3])}")

        # Check late_payments dict (different format)
        late_payments_dict = account.get("late_payments", {})
        for bureau, lates in late_payments_dict.items():
            if lates and isinstance(lates, dict):
                for days, count in lates.items():
                    if count:
                        reasons.append(f"Late payments ({bureau}): {count}x {days}")

        # If explicitly positive AND no reasons found so far, skip
        if not reasons:
            for positive in self.POSITIVE_STATUS_KEYWORDS:
                if positive in status_text:
                    return []

        # Check for high utilization
        balance = self._parse_currency(account.get("balance"))
        limit = self._parse_currency(account.get("credit_limit"))
        if balance and limit and limit > 0:
            utilization = (balance / limit) * 100
            if utilization > 90:
                reasons.append(f"High utilization: {utilization:.0f}%")

        # Check bureau-specific statuses
        bureaus_data = account.get("bureaus", {})
        for bureau_name, bureau_data in bureaus_data.items():
            if isinstance(bureau_data, dict) and bureau_data.get("present"):
                bureau_status = str(bureau_data.get("status", "")).lower()
                bureau_rating = str(bureau_data.get("account_rating", "")).lower()
                bureau_comments = str(bureau_data.get("comments", "")).lower()
                bureau_remarks = str(bureau_data.get("creditor_remarks", "")).lower()
                combined = f"{bureau_status} {bureau_rating} {bureau_comments} {bureau_remarks}"

                for keyword in self.NEGATIVE_STATUS_KEYWORDS:
                    if (
                        keyword in combined
                        and f"Bureau {bureau_name}: {keyword}" not in reasons
                    ):
                        reasons.append(f"Bureau {bureau_name}: {keyword}")

        return reasons

    def _classify_item_type(self, account: Dict, negative_reasons: List[str]) -> str:
        """
        Classify the item type based on account data and negative reasons.

        Returns one of: late_payment, charge_off, collection, repossession,
                       high_utilization, settled, tradeline
        """
        reasons_text = " ".join(negative_reasons).lower()
        status_text = " ".join(
            [
                str(account.get("status", "")),
                str(account.get("payment_status", "")),
                str(account.get("comments", "")),
            ]
        ).lower()

        # Check for charge-off
        if "charge" in reasons_text and "off" in reasons_text:
            return "charge_off"
        if "charge off" in status_text or "chargeoff" in status_text:
            return "charge_off"

        # Check for collection
        if "collection" in reasons_text or "collection" in status_text:
            return "collection"

        # Check for repossession
        if "repossession" in reasons_text or "repossession" in status_text:
            return "repossession"
        if "repo" in status_text and (
            "vehicle" in status_text or "auto" in status_text
        ):
            return "repossession"

        # Check for settled
        if "settled" in reasons_text or "settled" in status_text:
            return "settled"

        # Check for late payment
        for pattern in self.LATE_PAYMENT_PATTERNS:
            if re.search(pattern, reasons_text, re.IGNORECASE):
                return "late_payment"
            if re.search(pattern, status_text, re.IGNORECASE):
                return "late_payment"

        # Check for high utilization
        if "utilization" in reasons_text:
            return "high_utilization"

        # Default to generic tradeline issue
        return "tradeline"

    def _get_reporting_bureaus(self, account: Dict) -> List[str]:
        """
        Determine which bureaus report this account.

        Returns list of bureau names: ["Equifax", "Experian", "TransUnion"]
        """
        bureaus = []
        bureaus_data = account.get("bureaus", {})

        bureau_mapping = {
            "transunion": "TransUnion",
            "experian": "Experian",
            "equifax": "Equifax",
        }

        for key, display_name in bureau_mapping.items():
            bureau_info = bureaus_data.get(key, {})
            if isinstance(bureau_info, dict) and bureau_info.get("present"):
                bureaus.append(display_name)

        # If no bureau info, check for bureau-specific fields
        if not bureaus:
            if account.get("tu_balance") or account.get("transunion_balance"):
                bureaus.append("TransUnion")
            if account.get("ex_balance") or account.get("experian_balance"):
                bureaus.append("Experian")
            if account.get("ef_balance") or account.get("equifax_balance"):
                bureaus.append("Equifax")

        # If still no bureaus, assume all three
        if not bureaus:
            bureaus = ["Equifax", "Experian", "TransUnion"]

        return bureaus

    def _extract_account_number(self, account: Dict) -> str:
        """Extract account number, masked if available."""
        # Try direct account_number field
        acct_num = account.get("account_number")
        if acct_num and acct_num != "null":
            return acct_num

        # Try bureau-specific numbers
        bureaus_data = account.get("bureaus", {})
        for bureau_data in bureaus_data.values():
            if isinstance(bureau_data, dict):
                num = bureau_data.get("number")
                if num and num != "null":
                    return num

        return "N/A"

    def _extract_inquiries(self) -> List[Dict]:
        """
        Extract hard inquiries from the report.

        Hard inquiries can be disputed if:
        - Unauthorized (no permissible purpose)
        - Identity theft
        - Too old (some states have limits)
        """
        negative_items = []
        inquiries = self.report.get("inquiries", [])

        for idx, inquiry in enumerate(inquiries):
            # Skip soft inquiries if identifiable
            inquiry_type = str(inquiry.get("type", "")).lower()
            if "soft" in inquiry_type or "promotional" in inquiry_type:
                continue

            bureaus = self._get_inquiry_bureaus(inquiry)

            item = {
                "source_index": idx,
                "creditor_name": inquiry.get("company")
                or inquiry.get("creditor")
                or inquiry.get("name", "Unknown"),
                "account_id": "INQUIRY",
                "item_type": "inquiry",
                "bureaus": bureaus,
                "status": "Hard Inquiry",
                "balance": None,
                "credit_limit": None,
                "high_credit": None,
                "date_opened": inquiry.get("date") or inquiry.get("inquiry_date"),
                "date_closed": None,
                "last_reported": inquiry.get("date") or inquiry.get("inquiry_date"),
                "last_payment": None,
                "account_type": inquiry.get("type", "Hard Inquiry"),
                "negative_reasons": ["Hard inquiry on credit report"],
                "comments": inquiry.get("reason", ""),
                "raw_data": inquiry,
            }
            negative_items.append(item)

        return negative_items

    def _get_inquiry_bureaus(self, inquiry: Dict) -> List[str]:
        """Determine which bureaus report this inquiry."""
        bureaus = []

        # Check bureau field
        bureau = inquiry.get("bureau", "").lower()
        if "transunion" in bureau or "tu" in bureau:
            bureaus.append("TransUnion")
        if "experian" in bureau or "ex" in bureau:
            bureaus.append("Experian")
        if "equifax" in bureau or "eq" in bureau:
            bureaus.append("Equifax")

        # Check bureaus dict
        bureaus_data = inquiry.get("bureaus", {})
        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")
        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")

        # Check direct bureau boolean flags (common in MyFreeScoreNow format)
        if inquiry.get("transunion") is True:
            bureaus.append("TransUnion")
        if inquiry.get("experian") is True:
            bureaus.append("Experian")
        if inquiry.get("equifax") is True:
            bureaus.append("Equifax")

        # Remove duplicates
        bureaus = list(set(bureaus))

        # Default to all if unknown
        if not bureaus:
            bureaus = ["Equifax", "Experian", "TransUnion"]

        return bureaus

    def _extract_collections(self) -> List[Dict]:
        """
        Extract collection accounts from the report.

        Collections are always negative and disputable.
        """
        negative_items = []
        collections = self.report.get("collections", [])

        for idx, collection in enumerate(collections):
            bureaus = self._get_reporting_bureaus(collection)

            item = {
                "source_index": idx,
                "creditor_name": collection.get("creditor")
                or collection.get("agency", "Unknown"),
                "account_id": self._extract_account_number(collection),
                "item_type": "collection",
                "bureaus": bureaus,
                "status": collection.get("status", "Collection"),
                "balance": self._parse_currency(collection.get("balance")),
                "credit_limit": None,
                "high_credit": self._parse_currency(collection.get("original_amount")),
                "date_opened": collection.get("date_opened")
                or collection.get("date_assigned"),
                "date_closed": None,
                "last_reported": collection.get("last_reported"),
                "last_payment": collection.get("last_payment"),
                "account_type": "Collection",
                "negative_reasons": ["Collection account"],
                "comments": collection.get("comments", ""),
                "original_creditor": collection.get("original_creditor"),
                "raw_data": collection,
            }
            negative_items.append(item)

        return negative_items

    def _extract_public_records(self) -> List[Dict]:
        """
        Extract public records (bankruptcy, judgments, liens) from the report.

        Public records are serious derogatory items.
        """
        negative_items = []
        public_records = self.report.get("public_records", [])

        for idx, record in enumerate(public_records):
            bureaus = self._get_reporting_bureaus(record)
            record_type = self._classify_public_record(record)

            item = {
                "source_index": idx,
                "creditor_name": record.get("court")
                or record.get("source", "Public Record"),
                "account_id": record.get("case_number")
                or record.get("reference", "N/A"),
                "item_type": record_type,
                "bureaus": bureaus,
                "status": record.get("status", record_type),
                "balance": self._parse_currency(record.get("amount")),
                "credit_limit": None,
                "high_credit": None,
                "date_opened": record.get("filed_date") or record.get("date"),
                "date_closed": record.get("satisfied_date")
                or record.get("released_date"),
                "last_reported": record.get("last_reported"),
                "last_payment": None,
                "account_type": record_type,
                "negative_reasons": [f"Public record: {record_type}"],
                "comments": record.get("comments", ""),
                "raw_data": record,
            }
            negative_items.append(item)

        return negative_items

    def _classify_public_record(self, record: Dict) -> str:
        """Classify the type of public record."""
        record_text = " ".join(
            [
                str(record.get("type", "")),
                str(record.get("description", "")),
                str(record.get("status", "")),
            ]
        ).lower()

        if "bankruptcy" in record_text:
            return "bankruptcy"
        if "judgment" in record_text:
            return "judgment"
        if "lien" in record_text:
            return "tax_lien"
        if "foreclosure" in record_text:
            return "foreclosure"

        return "public_record"

    def _parse_currency(self, value: Any) -> Optional[float]:
        """Parse currency string to float."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        try:
            # Remove currency symbols and commas
            clean = re.sub(r"[^\d.\-]", "", str(value))
            if clean:
                return float(clean)
        except (ValueError, TypeError):
            pass

        return None


def extract_negative_items_from_report(parsed_report: Dict) -> List[Dict]:
    """
    Convenience function to extract negative items from a parsed credit report.

    Args:
        parsed_report: Dict from CreditReportParser.parse()

    Returns:
        List of negative item dicts
    """
    extractor = NegativeItemExtractor(parsed_report)
    return extractor.extract_all_negative_items()


def extract_negative_items_from_json_file(json_path: str) -> List[Dict]:
    """
    Extract negative items from a credit report JSON file.

    Args:
        json_path: Path to the JSON file from credit import

    Returns:
        List of negative item dicts
    """
    import json

    with open(json_path, "r") as f:
        parsed_report = json.load(f)

    return extract_negative_items_from_report(parsed_report)
