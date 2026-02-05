"""
Credit Report Parser Service
Parses HTML from credit monitoring services into structured three-bureau format.
Specifically optimized for MyScoreIQ Angular-rendered reports.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Track repeated parse failures for admin alerting
_failure_counts: Dict[str, List[datetime]] = defaultdict(list)
_FAILURE_ALERT_THRESHOLD = 5  # Alert after 5 failures
_FAILURE_WINDOW_MINUTES = 60  # Within this time window


def _record_parse_failure(service_name: str, errors: List[Dict]):
    """Record a parse failure and trigger admin alert if threshold exceeded."""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=_FAILURE_WINDOW_MINUTES)

    # Prune old entries
    _failure_counts[service_name] = [
        t for t in _failure_counts[service_name] if t > cutoff
    ]
    _failure_counts[service_name].append(now)

    count = len(_failure_counts[service_name])
    if count >= _FAILURE_ALERT_THRESHOLD:
        logger.critical(
            "ADMIN ALERT: Credit report parser has failed %d times in %d minutes "
            "for service '%s'. Latest errors: %s",
            count,
            _FAILURE_WINDOW_MINUTES,
            service_name,
            ", ".join(e["section"] + ": " + e["error"] for e in errors[:3]),
        )
        # Reset counter after alert
        _failure_counts[service_name] = []

        # Try to send admin notification
        try:
            from services.email_service import send_email

            send_email(
                to_email="admin@brightpathcredit.com",
                subject=f"[ALERT] Credit Report Parser Failures - {service_name}",
                html_content=(
                    f"<h3>Repeated Parse Failures Detected</h3>"
                    f"<p>The credit report parser for <strong>{service_name}</strong> "
                    f"has failed {count} times in the last {_FAILURE_WINDOW_MINUTES} minutes.</p>"
                    f"<p>Recent errors:</p><ul>"
                    + "".join(
                        f"<li>{e['section']}: {e['error']}</li>" for e in errors[:5]
                    )
                    + "</ul>"
                ),
            )
        except Exception:
            pass  # Don't fail if alert email fails


def get_parse_failure_stats() -> Dict:
    """Get current parse failure statistics for monitoring."""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=_FAILURE_WINDOW_MINUTES)
    stats = {}
    for service, timestamps in _failure_counts.items():
        recent = [t for t in timestamps if t > cutoff]
        if recent:
            stats[service] = {
                "count": len(recent),
                "oldest": recent[0].isoformat(),
                "newest": recent[-1].isoformat(),
            }
    return stats


class CreditReportParser:
    """Parse credit report HTML into structured data."""

    SKIP_HEADERS = {
        "THE",
        "AND",
        "FOR",
        "CREDIT REPORT",
        "WATCH",
        "KNOW",
        "FICO",
        "PLAN",
        "YOUR",
        "SCORE",
        "REPORT",
        "SUMMARY",
        "SCORE FACTORS",
        "FACTORS",
        "INQUIRIES",
        "COLLECTIONS",
        "PUBLIC RECORDS",
        "PERSONAL INFORMATION",
        "SUBSCRIBER",
        "ACCOUNT HISTORY",
        "CREDITOR CONTACTS",
        "EXTENDED PAYMENT HISTORY",
        "QUICK LINKS",
        "BACK TO TOP",
        "CREDIT SCORE",
        "MONTH",
        "YEAR",
        "TRANSUNION",
        "EXPERIAN",
        "EQUIFAX",
    }

    def __init__(self, html_content: str, service_name: str = "unknown"):
        self.html = html_content
        self.service = service_name
        self.soup = BeautifulSoup(html_content, "html.parser")
        self._summary_counts: Optional[Dict[str, Any]] = None

    def parse(self) -> Dict:
        """Parse the credit report and return structured data.

        Each section is parsed independently with error recovery.
        If a section fails, it returns empty/default data and parsing continues.
        """
        self._parse_errors: List[Dict[str, str]] = []

        self._summary_counts = self._safe_extract("_extract_summary_counts", default={})

        result = {
            "scores": self._safe_extract("_extract_scores", default={}),
            "personal_info": self._safe_extract("_extract_personal_info", default={}),
            "accounts": self._safe_extract("_extract_accounts", default=[]),
            "inquiries": self._safe_extract("_extract_inquiries", default=[]),
            "public_records": self._safe_extract("_extract_public_records", default=[]),
            "collections": self._safe_extract("_extract_collections", default=[]),
            "creditor_contacts": self._safe_extract(
                "_extract_creditor_contacts", default=[]
            ),
            "summary": {},
            "parse_errors": self._parse_errors,
        }

        result["summary"] = {
            "total_accounts": len(result["accounts"]),
            "total_inquiries": len(result["inquiries"]),
            "total_collections": len(result["collections"]),
            "total_public_records": len(result["public_records"]),
            "had_errors": len(self._parse_errors) > 0,
            "error_count": len(self._parse_errors),
        }

        if self._parse_errors:
            logger.warning(
                "Credit report parsed with %d error(s) [service=%s]: %s",
                len(self._parse_errors),
                self.service,
                ", ".join(e["section"] for e in self._parse_errors),
            )
            _record_parse_failure(self.service, self._parse_errors)

        return result

    def _safe_extract(self, method_name: str, default=None):
        """Safely call an extraction method, returning default on failure."""
        try:
            return getattr(self, method_name)()
        except Exception as e:
            error_info = {
                "section": method_name.replace("_extract_", ""),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self._parse_errors.append(error_info)
            logger.error(
                "Error parsing section '%s' [service=%s]: %s: %s",
                method_name,
                self.service,
                type(e).__name__,
                e,
                exc_info=True,
            )
            return default if default is not None else {}

    def _extract_summary_counts(self) -> Dict:
        """Extract summary counts from the report to determine if collections/public records exist."""
        counts = {
            "collections": 0,
            "public_records": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
        }

        summary_section = self.soup.find("div", id="Summary")
        if not summary_section:
            summary_section = self.soup

        rows = summary_section.find_all("tr") if summary_section else []
        for row in rows:
            label_cell = row.find("td", class_="label")
            if not label_cell:
                continue
            label = label_cell.get_text(strip=True).lower()

            info_cells = row.find_all("td", class_=re.compile(r"info"))
            values = [cell.get_text(strip=True) for cell in info_cells]

            if "collection" in label and "chargeoff" not in label:
                for v in values:
                    if v and v != "-":
                        digits = re.sub(r"\D", "", v)
                        if digits:
                            counts["collections"] = max(
                                counts["collections"], int(digits)
                            )
                            break

            elif "public record" in label:
                for v in values:
                    if v and v != "-":
                        digits = re.sub(r"\D", "", v)
                        if digits:
                            counts["public_records"] = max(
                                counts["public_records"], int(digits)
                            )
                            break

        logger.info(f"Summary counts extracted: {counts}")
        return counts

    def _extract_scores(self) -> Dict[str, Optional[int]]:
        """Extract credit scores for all three bureaus."""
        scores: Dict[str, Optional[int]] = {
            "transunion": None,
            "experian": None,
            "equifax": None,
        }

        # Method 1: Look for CreditScore section with FICO Score 8 table row
        score_section = self.soup.find("div", id="CreditScore")
        if score_section:
            tables = score_section.find_all(
                "table", class_=re.compile(r"rpt_content_table")
            )
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    label_cell = row.find("td", class_="label")
                    if label_cell:
                        label_text = label_cell.get_text(strip=True).lower()
                        # Look for "FICO Score 8:" row
                        if (
                            "fico" in label_text
                            and "score" in label_text
                            and "8" in label_text
                        ):
                            info_cells = row.find_all("td", class_=re.compile(r"info"))
                            if len(info_cells) >= 3:
                                # Order: TransUnion, Experian, Equifax
                                for i, bureau in enumerate(
                                    ["transunion", "experian", "equifax"]
                                ):
                                    if i < len(info_cells):
                                        score_text = info_cells[i].get_text(strip=True)
                                        if score_text and score_text != "-":
                                            try:
                                                score = int(score_text)
                                                if 300 <= score <= 850:
                                                    scores[bureau] = score
                                            except ValueError:
                                                pass
                            break

        # Method 2: Fallback - search by bureau name in tables
        if not any(scores.values()) and score_section:
            tables = score_section.find_all("table")
            for table in tables:
                text = table.get_text()

                if "transunion" in text.lower() and not scores["transunion"]:
                    match = re.search(r"(\d{3})", text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores["transunion"] = score

                elif "experian" in text.lower() and not scores["experian"]:
                    match = re.search(r"(\d{3})", text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores["experian"] = score

                elif "equifax" in text.lower() and not scores["equifax"]:
                    match = re.search(r"(\d{3})", text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores["equifax"] = score

        # Method 3: Fallback - regex on full text
        if not any(scores.values()):
            text = self.soup.get_text()

            tu_match = re.search(r"transunion[:\s]*(\d{3})", text, re.I)
            if tu_match:
                score = int(tu_match.group(1))
                if 300 <= score <= 850:
                    scores["transunion"] = score

            exp_match = re.search(r"experian[:\s]*(\d{3})", text, re.I)
            if exp_match:
                score = int(exp_match.group(1))
                if 300 <= score <= 850:
                    scores["experian"] = score

            eq_match = re.search(r"equifax[:\s]*(\d{3})", text, re.I)
            if eq_match:
                score = int(eq_match.group(1))
                if 300 <= score <= 850:
                    scores["equifax"] = score

        # Method 4: MyFreeScoreNow 3B Report format - bureau-score divs with h1 scores
        if not any(scores.values()):
            bureau_divs = self.soup.find_all("div", class_=re.compile(r"bureau-score"))
            for div in bureau_divs:
                # Check which bureau this is based on class or text
                div_class = " ".join(div.get("class", []))
                h6_tag = div.find("h6")
                h1_tag = div.find("h1")

                if h1_tag:
                    try:
                        score = int(re.sub(r"\D", "", h1_tag.get_text(strip=True)))
                        if 300 <= score <= 850:
                            bureau_text = (
                                h6_tag.get_text(strip=True).lower()
                                if h6_tag
                                else div_class.lower()
                            )
                            if (
                                "transunion" in bureau_text
                                or "border-transunion" in div_class
                            ):
                                scores["transunion"] = score
                            elif (
                                "experian" in bureau_text
                                or "border-experian" in div_class
                            ):
                                scores["experian"] = score
                            elif (
                                "equifax" in bureau_text
                                or "border-equifax" in div_class
                            ):
                                scores["equifax"] = score
                    except (ValueError, AttributeError):
                        pass

        # Method 5: MyFreeScoreNow report-header scores div
        if not any(scores.values()):
            report_header = self.soup.find("div", class_="report-header")
            if report_header:
                score_divs = report_header.find_all("div", class_="flex-basis")
                for div in score_divs:
                    h6_tag = div.find("h6")
                    h1_tag = div.find("h1")
                    if h6_tag and h1_tag:
                        bureau_text = h6_tag.get_text(strip=True).lower()
                        try:
                            score = int(re.sub(r"\D", "", h1_tag.get_text(strip=True)))
                            if 300 <= score <= 850:
                                if "transunion" in bureau_text:
                                    scores["transunion"] = score
                                elif "experian" in bureau_text:
                                    scores["experian"] = score
                                elif "equifax" in bureau_text:
                                    scores["equifax"] = score
                        except (ValueError, AttributeError):
                            pass

        return scores

    def _extract_personal_info(self) -> Dict:
        """Extract personal information from report."""
        info = {
            "name": None,
            "address": None,
            "ssn_last4": None,
            "dob": None,
        }

        # Try MyFreeScoreNow format first (attribute-row based)
        # Must iterate through all h2.headline elements to find Personal Information
        personal_headline = None
        for h2 in self.soup.find_all("h2", class_="headline"):
            if "Personal Information" in h2.get_text():
                personal_headline = h2
                break

        if personal_headline:
            # Find the attribute-collection that follows
            attr_collection = personal_headline.find_next(
                "div", class_="attribute-collection"
            )
            if attr_collection:
                for attr_row in attr_collection.find_all("div", class_="attribute-row"):
                    label_p = attr_row.find("p", class_="text-gray-900")
                    if not label_p:
                        label_p = attr_row.find("p", class_="mb-1")
                    if not label_p:
                        continue

                    label = label_p.get_text(strip=True).lower()
                    value_div = attr_row.find("div", class_="display-attribute")
                    if not value_div:
                        continue

                    value_p = value_div.find("p", class_="fw-semi")
                    if not value_p:
                        value_p = value_div.find("p")
                    if not value_p:
                        continue

                    value = value_p.get_text(strip=True)

                    if "name" in label and not info["name"]:
                        info["name"] = value.title() if value else None
                    elif "birth" in label or "dob" in label:
                        info["dob"] = value
                    elif "address" in label:
                        # Address may contain <br> tags
                        info["address"] = (
                            value_p.get_text(separator=", ", strip=True).title()
                            if value_p
                            else None
                        )

        # Fallback to legacy format (div id="PersonalInformation")
        if not info["name"]:
            personal_section = self.soup.find("div", id="PersonalInformation")
            if personal_section:
                name_row = personal_section.find("td", string=re.compile(r"name", re.I))
                if name_row:
                    parent_row = name_row.find_parent("tr")
                    if parent_row:
                        cells = parent_row.find_all("td", class_=re.compile(r"info"))
                        for cell in cells:
                            name_text = cell.get_text(strip=True)
                            if name_text and name_text != "-":
                                info["name"] = name_text
                                break

        return info

    def _is_valid_creditor_name(self, name: str) -> bool:
        """Check if a name is a valid creditor (not a section header or label)."""
        if not name or len(name) < 3:
            return False

        clean_name = name.upper().strip()

        if clean_name in self.SKIP_HEADERS:
            return False

        for skip in self.SKIP_HEADERS:
            if clean_name == skip or clean_name.startswith(skip + " "):
                return False

        if "{{" in name or "}}" in name:
            return False

        if re.match(r"^[A-Z]{1,3}$", clean_name):
            return False

        return True

    def _extract_accounts(self) -> List[Dict]:
        """Extract all tradeline accounts from Angular-rendered HTML."""
        accounts = []
        seen_creditors = set()

        account_section = self.soup.find("div", id="AccountHistory")
        search_area = self.soup

        if account_section:
            parent_wrapper = account_section.find_parent(
                "div", class_=re.compile(r"rpt_content_wrapper")
            )
            if parent_wrapper:
                search_area = parent_wrapper

        sub_headers = search_area.find_all(
            "div", class_=re.compile(r"sub_header.*ng-binding|sub_header")
        )

        for header in sub_headers:
            text = header.get_text(strip=True)
            text = re.sub(r"\s+", " ", text)

            original_creditor = None
            orig_match = re.search(r"\(Original Creditor:\s*([^)]+)\)", text)
            if orig_match:
                original_creditor = orig_match.group(1).strip()

            text = re.sub(r"\(Original Creditor:.*\)", "", text).strip()

            if not self._is_valid_creditor_name(text):
                continue

            account_key = text

            parent_for_key = header.find_parent("table", class_="crPrint")
            if parent_for_key:
                table_for_key = parent_for_key.find(
                    "table", class_=re.compile(r"rpt_content_table")
                )
                if table_for_key:
                    for row in table_for_key.find_all("tr")[:5]:
                        label_cell = row.find("td", class_="label")
                        if (
                            label_cell
                            and "account" in label_cell.get_text(strip=True).lower()
                            and "#" in label_cell.get_text(strip=True)
                        ):
                            info_cells = row.find_all("td", class_=re.compile(r"info"))
                            for cell in info_cells:
                                acct_num = cell.get_text(strip=True)
                                if acct_num and acct_num != "-":
                                    account_key = f"{text}_{acct_num}"
                                    break
                            break

            if account_key in seen_creditors:
                continue
            seen_creditors.add(account_key)

            account: Dict[str, Any] = {
                "creditor": text,
                "original_creditor": original_creditor,
                "account_number": None,
                "account_type": None,
                "account_type_detail": None,
                "status": None,
                "balance": None,
                "credit_limit": None,
                "high_balance": None,
                "monthly_payment": None,
                "payment_status": None,
                "date_opened": None,
                "date_reported": None,
                "past_due_amount": None,
                "times_30_late": None,
                "times_60_late": None,
                "times_90_late": None,
                "is_authorized_user": False,
                "responsibility": None,
                "payment_history": [],
                "discrepancies": [],
                "has_discrepancy": False,
                "bureaus": {
                    "transunion": {
                        "present": False,
                        "balance": None,
                        "credit_limit": None,
                        "date_opened": None,
                        "status": None,
                    },
                    "experian": {
                        "present": False,
                        "balance": None,
                        "credit_limit": None,
                        "date_opened": None,
                        "status": None,
                    },
                    "equifax": {
                        "present": False,
                        "balance": None,
                        "credit_limit": None,
                        "date_opened": None,
                        "status": None,
                    },
                },
            }

            parent = header.find_parent("table", class_="crPrint")
            if not parent:
                parent = header.find_parent("ng-include")
            if not parent:
                parent = header.parent

            table = None
            if parent:
                table = parent.find("table", class_=re.compile(r"rpt_content_table"))
            if not table:
                table = header.find_next("table", class_=re.compile(r"rpt_content"))

            if table:
                rows = table.find_all("tr")
                for row in rows:
                    label_cell = row.find("td", class_="label")
                    info_cells = row.find_all("td", class_=re.compile(r"info"))

                    if label_cell and info_cells:
                        label = label_cell.get_text(strip=True).lower()
                        values = [cell.get_text(strip=True) for cell in info_cells]

                        first_value = next((v for v in values if v and v != "-"), None)

                        if len(values) >= 3:
                            if values[0] and values[0] != "-":
                                account["bureaus"]["transunion"]["present"] = True
                            if values[1] and values[1] != "-":
                                account["bureaus"]["experian"]["present"] = True
                            if values[2] and values[2] != "-":
                                account["bureaus"]["equifax"]["present"] = True

                        if "account" in label and "#" in label or label == "account #:":
                            account["account_number"] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != "-":
                                    account["bureaus"]["transunion"]["number"] = values[
                                        0
                                    ]
                                if values[1] and values[1] != "-":
                                    account["bureaus"]["experian"]["number"] = values[1]
                                if values[2] and values[2] != "-":
                                    account["bureaus"]["equifax"]["number"] = values[2]

                        elif "account type - detail" in label:
                            account["account_type_detail"] = first_value

                        elif "account type" in label or "classification" in label:
                            account["account_type"] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != "-":
                                    account["bureaus"]["transunion"]["type"] = values[0]
                                if values[1] and values[1] != "-":
                                    account["bureaus"]["experian"]["type"] = values[1]
                                if values[2] and values[2] != "-":
                                    account["bureaus"]["equifax"]["type"] = values[2]

                        elif (
                            "status" in label
                            or "condition" in label
                            or "pay status" in label
                        ):
                            account["status"] = first_value

                        elif label == "balance:" or label == "balances:":
                            account["balance"] = first_value
                            # Store bureau-specific balances
                            if len(values) >= 1 and values[0] and values[0] != "-":
                                account["bureaus"]["transunion"]["balance"] = values[0]
                            if len(values) >= 2 and values[1] and values[1] != "-":
                                account["bureaus"]["experian"]["balance"] = values[1]
                            if len(values) >= 3 and values[2] and values[2] != "-":
                                account["bureaus"]["equifax"]["balance"] = values[2]

                        elif "credit limit" in label:
                            account["credit_limit"] = first_value
                            # Store bureau-specific limits
                            if len(values) >= 1 and values[0] and values[0] != "-":
                                account["bureaus"]["transunion"]["credit_limit"] = (
                                    values[0]
                                )
                            if len(values) >= 2 and values[1] and values[1] != "-":
                                account["bureaus"]["experian"]["credit_limit"] = values[
                                    1
                                ]
                            if len(values) >= 3 and values[2] and values[2] != "-":
                                account["bureaus"]["equifax"]["credit_limit"] = values[
                                    2
                                ]

                        elif "high balance" in label or "high credit" in label:
                            account["high_balance"] = first_value

                        elif "monthly payment" in label:
                            account["monthly_payment"] = first_value

                        elif "date opened" in label:
                            account["date_opened"] = first_value
                            # Store bureau-specific dates
                            if len(values) >= 1 and values[0] and values[0] != "-":
                                account["bureaus"]["transunion"]["date_opened"] = (
                                    values[0]
                                )
                            if len(values) >= 2 and values[1] and values[1] != "-":
                                account["bureaus"]["experian"]["date_opened"] = values[
                                    1
                                ]
                            if len(values) >= 3 and values[2] and values[2] != "-":
                                account["bureaus"]["equifax"]["date_opened"] = values[2]

                        elif "date reported" in label:
                            account["date_reported"] = first_value

                        elif "past due" in label:
                            account["past_due_amount"] = first_value

                        elif "30" in label and "late" in label:
                            account["times_30_late"] = first_value

                        elif "60" in label and "late" in label:
                            account["times_60_late"] = first_value

                        elif "90" in label and "late" in label:
                            account["times_90_late"] = first_value

                        elif "bureau code" in label or "responsibility" in label:
                            account["responsibility"] = first_value
                            # Check if any value indicates authorized user
                            for v in values:
                                if v and (
                                    "authorized" in v.lower()
                                    or "auth user" in v.lower()
                                ):
                                    account["is_authorized_user"] = True
                                    break

            # Extract payment history directly from crPrint table
            crprint_table = header.find_parent("table", class_="crPrint")
            if crprint_table:
                history_table = crprint_table.find(
                    "table", class_=re.compile(r"addr_hsrty")
                )
                if history_table:
                    rows = history_table.find_all("tr")
                    months, years, tu, exp, eqf = [], [], [], [], []
                    for row in rows:
                        cells = row.find_all("td")
                        if len(cells) < 2:
                            continue
                        label = cells[0].get_text(strip=True).lower()
                        values = [c.get_text(strip=True) for c in cells[1:]]
                        if "month" in label:
                            months = values
                        elif "year" in label:
                            years = values
                        elif "transunion" in label:
                            tu = values
                        elif "experian" in label:
                            exp = values
                        elif "equifax" in label:
                            eqf = values
                    for i in range(min(len(months), len(years))):
                        account["payment_history"].append(
                            {
                                "month": months[i],
                                "year": years[i],
                                "transunion": (
                                    tu[i].strip()
                                    if i < len(tu) and tu[i].strip()
                                    else None
                                ),
                                "experian": (
                                    exp[i].strip()
                                    if i < len(exp) and exp[i].strip()
                                    else None
                                ),
                                "equifax": (
                                    eqf[i].strip()
                                    if i < len(eqf) and eqf[i].strip()
                                    else None
                                ),
                            }
                        )

            accounts.append(account)

        # If no accounts found with MyScoreIQ method, try MyFreeScoreNow 3B Report format
        if not accounts:
            accounts = self._extract_accounts_myfreescorenow()

        return accounts

    def _extract_accounts_myfreescorenow(self) -> List[Dict]:
        """Extract accounts from MyFreeScoreNow 3B Report HTML structure."""
        accounts = []

        # MyFreeScoreNow 3B Report uses .account-container divs
        containers = self.soup.find_all("div", class_=re.compile(r"account-container"))

        if not containers:
            logger.debug("No MyFreeScoreNow account containers found")
            return accounts

        logger.info(f"Found {len(containers)} MyFreeScoreNow account containers")

        # Track current account type from section headers
        current_account_type = None

        for container in containers:
            # Check for account type section header before this container
            prev_sibling = container.find_previous_sibling(
                "div", class_="accounttype-heading"
            )
            if prev_sibling:
                h3 = prev_sibling.find("h3")
                if h3:
                    current_account_type = h3.get_text(strip=True).replace(
                        " Accounts", ""
                    )

            account: Dict[str, Any] = {
                "creditor": None,
                "original_creditor": None,
                "account_number": None,
                "account_type": current_account_type,
                "account_type_detail": None,
                "status": None,
                "account_status": None,
                "payment_status": None,
                "account_rating": None,
                "account_description": None,
                "dispute_status": None,
                "creditor_type": None,
                "creditor_remarks": None,
                "balance": None,
                "balance_owed": None,
                "credit_limit": None,
                "high_balance": None,
                "monthly_payment": None,
                "last_payment": None,
                "last_payment_date": None,
                "past_due_amount": None,
                "date_opened": None,
                "date_reported": None,
                "date_last_activity": None,
                "last_verified": None,
                "closed_date": None,
                "times_30_late": None,
                "times_60_late": None,
                "times_90_late": None,
                "utilization": None,
                "is_negative": "negative-account" in container.get("class", []),
                "payment_history": [],
                "bureaus": {
                    "transunion": {"present": True},
                    "experian": {"present": True},
                    "equifax": {"present": True},
                },
            }

            # Get creditor name from data-test-account-name or strong tag
            name_el = container.find(attrs={"data-test-account-name": True})
            if not name_el:
                name_el = container.find("strong", class_="fs-16")
            if name_el:
                account["creditor"] = name_el.get_text(strip=True)

            # Get account number from the heading paragraph (after the strong creditor name tag)
            heading_p = container.find("p", attrs={"data-uw-ignore-translate": True})
            if heading_p:
                # The account number is the text AFTER the strong tag (creditor name)
                strong_tag = heading_p.find("strong")
                if strong_tag:
                    # Get all text after the strong tag
                    remaining_text = ""
                    for sibling in strong_tag.next_siblings:
                        if hasattr(sibling, "get_text"):
                            remaining_text += sibling.get_text(strip=True)
                        else:
                            remaining_text += str(sibling).strip()
                    remaining_text = remaining_text.strip()
                    if remaining_text and (
                        re.search(r"\d", remaining_text) or "*" in remaining_text
                    ):
                        account["account_number"] = remaining_text

            # Get status from data-test-account-status
            status_el = container.find(attrs={"data-test-account-status": True})
            if status_el:
                status_text = status_el.get_text(strip=True)
                account["status"] = status_text
                account["account_status"] = status_text

            # Get closed date or last payment date from heading
            heading_div = container.find("div", class_="account-heading")
            if heading_div:
                text_end = heading_div.find("div", class_="text-end")
                if text_end:
                    label_p = text_end.find("p", class_="mb-0")
                    value_p = text_end.find("p", class_="fw-bold")
                    if label_p and value_p:
                        label = label_p.get_text(strip=True).lower()
                        value = value_p.get_text(strip=True)
                        if "closed" in label:
                            account["closed_date"] = value
                        elif "last payment" in label:
                            account["last_payment_date"] = value

            # Get credit utilization from SVG chart
            util_el = container.find("text", class_="circle-chart__percent")
            if util_el:
                util_text = util_el.get_text(strip=True)
                account["utilization"] = util_text

            # Get balance from .balance row
            balance_row = container.find(
                "div", class_=re.compile(r"attribute-row.*balance")
            )
            if balance_row:
                display_attr = balance_row.find("div", class_="display-attribute")
                if display_attr:
                    p_tag = display_attr.find("p")
                    if p_tag:
                        bal_text = p_tag.get_text(strip=True)
                        # Extract first dollar amount as balance
                        bal_match = re.search(r"\$[\d,]+", bal_text)
                        if bal_match:
                            account["balance"] = bal_match.group(0)
                            account["balance_owed"] = bal_match.group(0)
                        # Check for credit limit
                        limit_match = re.search(r"\$([\d,]+)\s+Limit", bal_text)
                        if limit_match:
                            account["credit_limit"] = f"${limit_match.group(1)}"
                        # Check for original amount (high balance for mortgages)
                        orig_match = re.search(r"Orig\.?\s*\$([\d,]+)", bal_text)
                        if orig_match:
                            account["high_balance"] = f"${orig_match.group(1)}"

            # Get payment amount and date from .payment row
            payment_row = container.find(
                "div", class_=re.compile(r"attribute-row.*payment")
            )
            if payment_row:
                display_attr = payment_row.find("div", class_="display-attribute")
                if display_attr:
                    p_tag = display_attr.find("p")
                    if p_tag:
                        pay_text = p_tag.get_text(strip=True)
                        pay_match = re.search(r"\$[\d,]+", pay_text)
                        if pay_match:
                            account["monthly_payment"] = pay_match.group(0)
                            account["last_payment"] = pay_match.group(0)
                        # Get date last posted
                        date_match = re.search(
                            r"Date Last Posted\s*(\d{1,2}/\d{1,2}/\d{4})", pay_text
                        )
                        if date_match:
                            account["date_reported"] = date_match.group(1)

            # Get late payment info
            late_30 = container.find(attrs={"data-test-30-late": True})
            late_60 = container.find(attrs={"data-test-60-late": True})
            late_90 = container.find(attrs={"data-test-90-late": True})

            if late_30:
                try:
                    account["times_30_late"] = int(late_30.get_text(strip=True))
                except ValueError:
                    pass
            if late_60:
                try:
                    account["times_60_late"] = int(late_60.get_text(strip=True))
                except ValueError:
                    pass
            if late_90:
                try:
                    account["times_90_late"] = int(late_90.get_text(strip=True))
                except ValueError:
                    pass

            # Extract expanded details if available (from "View all details" modal)
            # MyFreeScoreNow uses .account-modal-body for the expanded details
            modal = container.find("div", class_="account-modal")
            if modal:
                modal_body = modal.find("div", class_="account-modal-body")
                if modal_body:
                    # Parse the attributes table (grid layout with bureau columns)
                    self._parse_myfreescorenow_modal_details(modal_body, account)

                    # Extract 2-year payment history from the modal
                    history_section = modal_body.find("div", class_="payment-history")
                    if history_section:
                        account["payment_history"] = (
                            self._extract_myfreescorenow_payment_history(
                                history_section
                            )
                        )
                    else:
                        # Try parent modal
                        history_section = modal.find("div", class_="payment-history")
                        if history_section:
                            account["payment_history"] = (
                                self._extract_myfreescorenow_payment_history(
                                    history_section
                                )
                            )

            # Also try to find payment history directly in container if not found in modal
            if not account.get("payment_history"):
                history_section = container.find(
                    "div", class_=re.compile(r"payment-history")
                )
                if history_section:
                    account["payment_history"] = (
                        self._extract_myfreescorenow_payment_history(history_section)
                    )

            # Only add if we got a creditor name
            if account["creditor"]:
                accounts.append(account)

        logger.info(f"Extracted {len(accounts)} accounts from MyFreeScoreNow format")
        return accounts

    def _parse_myfreescorenow_modal_details(self, modal_body, account: Dict) -> None:
        """Parse expanded account details from MyFreeScoreNow modal 'View all details' section.

        The HTML structure uses a grid with bureau columns:
        <div class="attributes-table">
          <div class="d-grid grid-cols-4">
            <div class="attribute-label"></div>
            <div class="bg-transunion">TransUnion</div>
            <div class="bg-experian">Experian</div>
            <div class="bg-equifax">Equifax</div>
            <div class="attribute-label">Account #</div>
            <div>867348*******</div>
            <div>867348*******</div>
            <div>867348*******</div>
            ...
          </div>
        </div>
        """
        # Find the attributes table grid
        grid = modal_body.find("div", class_="d-grid")
        if not grid:
            return

        # Get all direct children divs
        cells = grid.find_all("div", recursive=False)
        if len(cells) < 4:
            return

        # Process in groups of 4 (label, TU value, EX value, EQ value)
        current_row = 0
        for i in range(0, len(cells) - 3, 4):
            label_div = cells[i]
            tu_div = cells[i + 1]
            ex_div = cells[i + 2]
            eq_div = cells[i + 3]

            # Skip header row
            label_class = label_div.get("class", [])
            if "bg-transunion" in " ".join(label_class) or not label_div.get_text(
                strip=True
            ):
                continue

            label = label_div.get_text(strip=True).lower()
            tu_val = tu_div.get_text(strip=True)
            ex_val = ex_div.get_text(strip=True)
            eq_val = eq_div.get_text(strip=True)

            # Get first non-empty, non-dash value
            value = (
                tu_val
                if tu_val and tu_val != "--"
                else (
                    ex_val
                    if ex_val and ex_val != "--"
                    else (eq_val if eq_val and eq_val != "--" else None)
                )
            )

            if not value:
                continue

            # Map labels to account fields
            if "account #" in label or "account number" in label:
                if not account.get("account_number"):
                    account["account_number"] = value
                # Store per-bureau values
                account["bureaus"]["transunion"]["account_number"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["account_number"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["account_number"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "high balance" in label or "high credit" in label:
                account["high_balance"] = value
                account["bureaus"]["transunion"]["high_balance"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["high_balance"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["high_balance"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "last verified" in label:
                account["last_verified"] = value
                account["bureaus"]["transunion"]["last_verified"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["last_verified"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["last_verified"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "date of last activity" in label or "last activity" in label:
                account["date_last_activity"] = value
                account["bureaus"]["transunion"]["date_last_activity"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["date_last_activity"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["date_last_activity"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "date reported" in label:
                account["date_reported"] = value
                account["bureaus"]["transunion"]["date_reported"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["date_reported"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["date_reported"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "date opened" in label:
                account["date_opened"] = value
                account["bureaus"]["transunion"]["date_opened"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["date_opened"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["date_opened"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "balance owed" in label:
                account["balance_owed"] = value
                account["bureaus"]["transunion"]["balance_owed"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["balance_owed"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["balance_owed"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "closed date" in label:
                account["closed_date"] = value
            elif "account rating" in label:
                account["account_rating"] = value
            elif "account description" in label:
                account["account_description"] = value
            elif "dispute status" in label:
                account["dispute_status"] = value
                account["bureaus"]["transunion"]["dispute_status"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["dispute_status"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["dispute_status"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "creditor type" in label:
                account["creditor_type"] = value
            elif "account status" in label:
                account["account_status"] = value
                account["bureaus"]["transunion"]["account_status"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["account_status"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["account_status"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "payment status" in label:
                account["payment_status"] = value
                account["bureaus"]["transunion"]["payment_status"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["payment_status"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["payment_status"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "creditor remarks" in label:
                account["creditor_remarks"] = value
            elif "original creditor" in label:
                account["original_creditor"] = value
            elif "payment amount" in label or "last payment" in label:
                if "amount" in label:
                    account["monthly_payment"] = value
                else:
                    account["last_payment_date"] = value
            elif "term length" in label:
                account["term_length"] = value
            elif "past due" in label:
                account["past_due_amount"] = value
            elif "account type" in label:
                account["account_type_detail"] = value
                account["bureaus"]["transunion"]["account_type"] = (
                    tu_val if tu_val != "--" else None
                )
                account["bureaus"]["experian"]["account_type"] = (
                    ex_val if ex_val != "--" else None
                )
                account["bureaus"]["equifax"]["account_type"] = (
                    eq_val if eq_val != "--" else None
                )
            elif "payment frequency" in label:
                account["payment_frequency"] = value
            elif "credit limit" in label:
                account["credit_limit"] = value

    def _parse_myfreescorenow_account_details(
        self, details_section, account: Dict
    ) -> None:
        """Parse expanded account details from MyFreeScoreNow 'View all details' section."""
        # Look for attribute rows with labels and values
        rows = details_section.find_all("div", class_="attribute-row")
        for row in rows:
            label_el = row.find("p", class_="text-gray-900")
            if not label_el:
                continue
            label = label_el.get_text(strip=True).lower()

            display_attr = row.find("div", class_="display-attribute")
            if not display_attr:
                continue
            value_el = display_attr.find("p")
            if not value_el:
                continue
            value = value_el.get_text(strip=True)

            # Map labels to account fields
            if "account" in label and "#" in label:
                account["account_number"] = value
            elif "high balance" in label or "high credit" in label:
                account["high_balance"] = value
            elif "last verified" in label:
                account["last_verified"] = value
            elif "last activity" in label or "date of last activity" in label:
                account["date_last_activity"] = value
            elif "date reported" in label:
                account["date_reported"] = value
            elif "date opened" in label or "opened" in label:
                account["date_opened"] = value
            elif "balance owed" in label or "balance" in label:
                if not account["balance"]:
                    account["balance_owed"] = value
            elif "closed date" in label:
                account["closed_date"] = value
            elif "account rating" in label or "rating" in label:
                account["account_rating"] = value
            elif "account description" in label or "description" in label:
                account["account_description"] = value
            elif "dispute status" in label:
                account["dispute_status"] = value
            elif "creditor type" in label:
                account["creditor_type"] = value
            elif "account status" in label:
                account["account_status"] = value
            elif "payment status" in label:
                account["payment_status"] = value
            elif "creditor remarks" in label or "remarks" in label:
                account["creditor_remarks"] = value
            elif "original creditor" in label:
                account["original_creditor"] = value
            elif "last payment" in label:
                account["last_payment"] = value
            elif "past due" in label:
                account["past_due_amount"] = value
            elif "account type" in label or "type" in label:
                account["account_type_detail"] = value

    def _extract_myfreescorenow_payment_history(self, history_section) -> List[Dict]:
        """Extract 2-year payment history from MyFreeScoreNow format.

        The HTML structure is:
        <div class="payment-history">
          <p class="text-transunion"> TransUnion </p>
          <div class="d-flex ...">
            <div class="status-C"><p class="month-badge">OK</p><p class="month-label">Dec</p></div>
            <div class="status-4"><p class="month-badge">120</p><p class="month-label">'24</p></div>
            ...
          </div>
        </div>

        Output format (expected by template):
        [
            {"month": "Dec", "year": "24", "transunion": "OK", "experian": "OK", "equifax": "30"},
            ...
        ]
        """
        # Map status codes to display text
        status_display_map = {
            "C": "OK",
            "1": "30",
            "2": "60",
            "3": "90",
            "4": "120",
            "5": "150",
            "6": "-",
            "7": "DF",  # Deferred
            "8": "RP",  # Repossession
            "9": "CO",  # Charge-off
            "U": "-",
            "X": "-",
        }

        # Find the parent container that holds all bureau payment histories
        parent_container = history_section
        parent = history_section.find_parent("div", class_="payment-history")
        if parent and parent.parent:
            parent_container = parent.parent

        # Find all payment history divs (one per bureau)
        all_history_divs = parent_container.find_all(
            "div", class_="d-flex", recursive=True
        )

        # Collect data per bureau
        bureau_data = {"transunion": [], "experian": [], "equifax": []}

        # Process each bureau's section
        for hist_div in parent_container.find_all(
            "div", class_="payment-history", recursive=False
        ):
            # Determine bureau from heading
            bureau_heading = hist_div.find(
                "p",
                class_=re.compile(
                    r"text-transunion|text-experian|text-equifax|payment-history-heading"
                ),
            )
            bureau_name = None
            if bureau_heading:
                heading_text = bureau_heading.get_text(strip=True).lower()
                if "transunion" in heading_text:
                    bureau_name = "transunion"
                elif "experian" in heading_text:
                    bureau_name = "experian"
                elif "equifax" in heading_text:
                    bureau_name = "equifax"

            if not bureau_name:
                continue

            # Find status divs within this bureau section
            flex_container = hist_div.find(
                "div", class_=re.compile(r"d-flex.*gap|d-flex.*flex-wrap")
            )
            if not flex_container:
                flex_container = hist_div

            status_divs = flex_container.find_all(
                "div", class_=re.compile(r"status-[A-Z0-9]")
            )

            for status_div in status_divs:
                # Extract status code from class name
                classes = status_div.get("class", [])
                status_code = None
                for cls in classes:
                    if cls.startswith("status-"):
                        status_code = cls.replace("status-", "")
                        break

                # Get month badge text (OK, 120, etc.)
                badge = status_div.find("p", class_="month-badge")
                badge_text = badge.get_text(strip=True) if badge else ""

                # Get month label (Dec, '24, etc.)
                label = status_div.find("p", class_="month-label")
                month_text = label.get_text(strip=True) if label else ""

                # Determine if this is a year marker or month
                is_year = month_text.startswith("'")
                year = None
                month = month_text
                if is_year:
                    year = month_text.replace("'", "")  # Just "24", "25"
                    month = "Jan"  # Year markers are typically January

                # Map status to display value
                display_status = (
                    badge_text
                    if badge_text in ["OK", "30", "60", "90", "120", "CO"]
                    else status_display_map.get(status_code, "-")
                )

                bureau_data[bureau_name].append(
                    {"month": month, "year": year, "status": display_status}
                )

        # Combine into unified format (one entry per month with all bureaus)
        # Use the longest bureau list as the base
        max_len = max(
            len(bureau_data["transunion"]),
            len(bureau_data["experian"]),
            len(bureau_data["equifax"]),
        )

        history = []
        current_year = None

        for i in range(max_len):
            tu_entry = (
                bureau_data["transunion"][i]
                if i < len(bureau_data["transunion"])
                else {}
            )
            ex_entry = (
                bureau_data["experian"][i] if i < len(bureau_data["experian"]) else {}
            )
            eq_entry = (
                bureau_data["equifax"][i] if i < len(bureau_data["equifax"]) else {}
            )

            # Get month and year from any available entry
            month = (
                tu_entry.get("month")
                or ex_entry.get("month")
                or eq_entry.get("month")
                or ""
            )
            year = tu_entry.get("year") or ex_entry.get("year") or eq_entry.get("year")

            if year:
                current_year = year

            history.append(
                {
                    "month": month[:3] if month else "",  # Truncate to 3 chars
                    "year": current_year or "",
                    "transunion": tu_entry.get("status", "-"),
                    "experian": ex_entry.get("status", "-"),
                    "equifax": eq_entry.get("status", "-"),
                }
            )

        return history

    def _extract_payment_history_for_account(self, parent_element) -> List[Dict]:
        """Extract 2-year payment history grid for an account."""
        history = []

        # Try to find payment history tables within the parent element
        history_tables = parent_element.find_all(
            "table", class_=re.compile(r"addr_hsrty")
        )

        # If not found in parent, try to find in the next sibling crPrint table
        if not history_tables:
            # Look for Extended Payment History section
            ext_history = parent_element.find_all(
                string=re.compile(r"Extended Payment History")
            )
            for eh in ext_history:
                parent_td = eh.find_parent("td")
                if parent_td:
                    history_tables = parent_td.find_all(
                        "table", class_=re.compile(r"addr_hsrty")
                    )
                    if history_tables:
                        break

        for table in history_tables:
            rows = table.find_all("tr")
            if len(rows) < 3:
                continue

            months = []
            years = []
            tu_status = []
            exp_status = []
            eqf_status = []

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                # First cell contains the label (Month, Year, TransUnion, etc.)
                first_cell_text = cells[0].get_text(strip=True).lower()
                # Remaining cells contain the values
                values = [cell.get_text(strip=True) for cell in cells[1:]]

                if "month" in first_cell_text:
                    months = values
                elif "year" in first_cell_text:
                    years = values
                elif "transunion" in first_cell_text:
                    tu_status = values
                elif "experian" in first_cell_text:
                    exp_status = values
                elif "equifax" in first_cell_text:
                    eqf_status = values

            # Build history entries
            for i in range(min(len(months), len(years))):
                # Get status, converting empty strings to None
                tu_val = (
                    tu_status[i].strip()
                    if i < len(tu_status) and tu_status[i].strip()
                    else None
                )
                exp_val = (
                    exp_status[i].strip()
                    if i < len(exp_status) and exp_status[i].strip()
                    else None
                )
                eqf_val = (
                    eqf_status[i].strip()
                    if i < len(eqf_status) and eqf_status[i].strip()
                    else None
                )

                entry = {
                    "month": months[i] if i < len(months) else None,
                    "year": years[i] if i < len(years) else None,
                    "transunion": tu_val,
                    "experian": exp_val,
                    "equifax": eqf_val,
                }
                if entry["month"] and entry["year"]:
                    history.append(entry)

        return history

    def _extract_inquiries(self) -> List[Dict]:
        """Extract credit inquiries from Angular-rendered HTML."""
        inquiries = []
        seen = set()

        inquiry_section = self.soup.find("div", id="Inquiries")
        if inquiry_section:
            rows = inquiry_section.find_all("tr", class_=re.compile(r"ng-scope"))
            for row in rows:
                cells = row.find_all("td", class_=re.compile(r"info"))
                if len(cells) >= 3:
                    creditor = cells[0].get_text(strip=True)
                    inquiry_type = (
                        cells[1].get_text(strip=True)
                        if len(cells) > 1
                        else "Hard Inquiry"
                    )
                    date = cells[2].get_text(strip=True) if len(cells) > 2 else None
                    bureau = cells[3].get_text(strip=True) if len(cells) > 3 else None

                    if creditor and not self._is_valid_creditor_name(creditor):
                        continue

                    key = f"{creditor}_{date}"
                    if key not in seen and creditor:
                        seen.add(key)
                        inquiries.append(
                            {
                                "creditor": creditor,
                                "type": inquiry_type,
                                "date": date,
                                "bureau": bureau,
                            }
                        )

        return inquiries

    def _extract_public_records(self) -> List[Dict[str, Any]]:
        """Extract public records ONLY if they actually exist in the report."""
        records: List[Dict[str, Any]] = []

        if self._summary_counts and self._summary_counts.get("public_records", 0) == 0:
            logger.info("No public records found in summary - skipping extraction")
            return records

        public_section = self.soup.find("div", id="PublicRecords")
        if not public_section:
            return records

        record_headers = public_section.find_all(
            "div", class_=re.compile(r"sub_header")
        )
        for header in record_headers:
            text = header.get_text(strip=True)
            if text and "{{" not in text:
                record_type = "Public Record"
                if "bankruptcy" in text.lower():
                    record_type = "Bankruptcy"
                elif "judgment" in text.lower():
                    record_type = "Civil Judgment"
                elif "lien" in text.lower():
                    record_type = "Tax Lien"

                table = header.find_next("table", class_=re.compile(r"rpt_content"))
                filed_date = None
                if table:
                    rows = table.find_all("tr")
                    for row in rows:
                        label_cell = row.find("td", class_="label")
                        if (
                            label_cell
                            and "filed" in label_cell.get_text(strip=True).lower()
                        ):
                            info_cells = row.find_all("td", class_=re.compile(r"info"))
                            for cell in info_cells:
                                date_text = cell.get_text(strip=True)
                                if date_text and date_text != "-":
                                    filed_date = date_text
                                    break

                records.append(
                    {
                        "type": record_type,
                        "description": text,
                        "date": filed_date,
                        "status": "On Record",
                    }
                )

        return records

    def _extract_collections(self) -> List[Dict[str, Any]]:
        """Extract collection accounts ONLY if they actually exist in the report."""
        collections: List[Dict[str, Any]] = []

        if self._summary_counts and self._summary_counts.get("collections", 0) == 0:
            logger.info("No collections found in summary - skipping extraction")
            return collections

        accounts = self._extract_accounts()
        for account in accounts:
            status = (account.get("status") or "").lower()
            account_type = (account.get("account_type") or "").lower()

            if "collection" in status or "collection" in account_type:
                collections.append(
                    {
                        "agency": account.get("creditor", "Collection Agency"),
                        "original_creditor": account.get(
                            "original_creditor", "Unknown"
                        ),
                        "amount": account.get("balance", "Unknown"),
                        "status": account.get("status", "Open"),
                        "date_opened": account.get("date_opened"),
                    }
                )

        return collections

    def _extract_creditor_contacts(self) -> List[Dict[str, Any]]:
        """Extract creditor contact information including addresses and phone numbers."""
        contacts: List[Dict[str, Any]] = []

        contact_section = self.soup.find("div", id="CreditorContacts")
        if not contact_section:
            contact_section = self.soup.find(
                "div", class_=re.compile(r"rpt_content_contacts")
            )

        if not contact_section:
            return contacts

        table = contact_section.find("table", class_=re.compile(r"rpt_content"))
        if not table:
            return contacts

        rows = table.find_all("tr", class_=re.compile(r"ng-scope"))
        for row in rows:
            cells = row.find_all("td", class_=re.compile(r"info"))
            if len(cells) >= 3:
                creditor_name = cells[0].get_text(strip=True)

                address_cell = cells[1]
                address_parts = []
                for content in address_cell.stripped_strings:
                    if content:
                        address_parts.append(content)
                full_address = " ".join(address_parts)
                full_address = re.sub(r"\s*,\s*", ", ", full_address)
                full_address = re.sub(r"\s+", " ", full_address).strip()

                phone = cells[2].get_text(strip=True) if len(cells) > 2 else None

                if creditor_name and creditor_name != "-":
                    contacts.append(
                        {
                            "creditor": creditor_name,
                            "address": full_address if full_address else None,
                            "phone": phone if phone and phone != "-" else None,
                        }
                    )

        return contacts


def parse_credit_report(html_path: str, service_name: str = "unknown") -> Dict:
    """Parse a credit report file and return structured data."""
    import json
    import os

    try:
        json_path = html_path.replace(".html", ".json")
        extracted_data = None

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    extracted_data = json.load(f)
                logger.info(f"Loaded extracted data from {json_path}")
            except Exception as e:
                logger.warning(f"Failed to load JSON data: {e}")

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        parser = CreditReportParser(html_content, service_name)
        parsed = parser.parse()

        if extracted_data:
            if extracted_data.get("scores"):
                for bureau, score in extracted_data["scores"].items():
                    if score:
                        parsed["scores"][bureau] = score

            # Use JSON accounts if available (JSON extraction is more reliable than HTML parsing)
            # If JSON accounts are empty but HTML parsed some, keep the HTML-parsed ones
            if extracted_data.get("accounts") and len(extracted_data["accounts"]) > 0:
                parsed["accounts"] = []
                for acct in extracted_data["accounts"]:
                    parsed["accounts"].append(
                        {
                            "creditor": acct.get("creditor", "Unknown"),
                            "original_creditor": acct.get("original_creditor"),
                            "account_number": acct.get("account_number", "N/A"),
                            "account_type": acct.get("account_type", "Unknown"),
                            "account_type_detail": acct.get("account_type_detail"),
                            "status": acct.get("status", "Unknown"),
                            "balance": acct.get("balance"),
                            "credit_limit": acct.get("credit_limit"),
                            "high_balance": acct.get("high_balance"),
                            "monthly_payment": acct.get("monthly_payment"),
                            "payment_status": acct.get("payment_status"),
                            "date_opened": acct.get("date_opened"),
                            "date_reported": acct.get("date_reported"),
                            "past_due_amount": acct.get("past_due_amount"),
                            "times_30_late": acct.get("times_30_late"),
                            "times_60_late": acct.get("times_60_late"),
                            "times_90_late": acct.get("times_90_late"),
                            "payment_history": acct.get("payment_history", []),
                            "bureaus": acct.get(
                                "bureaus",
                                {
                                    "transunion": {"present": True},
                                    "experian": {"present": True},
                                    "equifax": {"present": True},
                                },
                            ),
                        }
                    )

            if extracted_data.get("inquiries") and len(extracted_data["inquiries"]) > 0:
                parsed["inquiries"] = extracted_data["inquiries"]

            if "collections" in extracted_data:
                parsed["collections"] = extracted_data.get("collections", [])

            if "public_records" in extracted_data:
                parsed["public_records"] = extracted_data.get("public_records", [])

            if extracted_data.get("creditor_contacts"):
                parsed["creditor_contacts"] = extracted_data["creditor_contacts"]

        # Detect discrepancies between bureaus
        def normalize_value(val):
            if not val or val == "-":
                return None
            # Remove $ and commas for comparison
            return val.replace("$", "").replace(",", "").strip()

        for acct in parsed.get("accounts", []):
            discrepancies = []
            bureaus = acct.get("bureaus", {})

            # Check balance discrepancy
            balances = {}
            for bureau in ["transunion", "experian", "equifax"]:
                bal = normalize_value(bureaus.get(bureau, {}).get("balance"))
                if bal:
                    balances[bureau] = bal
            if len(set(balances.values())) > 1 and len(balances) > 1:
                discrepancies.append({"field": "Balance", "bureau_values": balances})

            # Check credit limit discrepancy
            limits = {}
            for bureau in ["transunion", "experian", "equifax"]:
                lim = normalize_value(bureaus.get(bureau, {}).get("credit_limit"))
                if lim:
                    limits[bureau] = lim
            if len(set(limits.values())) > 1 and len(limits) > 1:
                discrepancies.append({"field": "Credit Limit", "bureau_values": limits})

            # Check date opened discrepancy
            dates = {}
            for bureau in ["transunion", "experian", "equifax"]:
                dt = bureaus.get(bureau, {}).get("date_opened")
                if dt and dt != "-":
                    dates[bureau] = dt
            if len(set(dates.values())) > 1 and len(dates) > 1:
                discrepancies.append({"field": "Date Opened", "bureau_values": dates})

            acct["discrepancies"] = discrepancies
            acct["has_discrepancy"] = len(discrepancies) > 0

        # Count late payments from payment history
        late_count = 0
        on_time_count = 0
        total_payments = 0
        for acct in parsed.get("accounts", []):
            for entry in acct.get("payment_history", []):
                has_data = False
                is_late = False
                is_ok = False
                for bureau in ["transunion", "experian", "equifax"]:
                    val = entry.get(bureau, "")
                    if val:
                        has_data = True
                        if val in ["30", "60", "90", "120", "150", "180"]:
                            is_late = True
                        elif val == "OK":
                            is_ok = True
                if has_data:
                    total_payments += 1
                    if is_late:
                        late_count += 1
                    elif is_ok:
                        on_time_count += 1

        # Calculate credit utilization
        total_balance: float = 0.0
        total_limit: float = 0.0
        for acct in parsed.get("accounts", []):
            balance_str = acct.get("balance", "") or ""
            limit_str = acct.get("credit_limit", "") or ""
            # Parse dollar amounts
            balance_clean = "".join(c for c in balance_str if c.isdigit() or c == ".")
            limit_clean = "".join(c for c in limit_str if c.isdigit() or c == ".")
            try:
                if balance_clean:
                    total_balance += float(balance_clean)
                if limit_clean:
                    total_limit += float(limit_clean)
            except:
                pass

        utilization = 0
        if total_limit > 0:
            utilization = round((total_balance / total_limit) * 100)

        # Payment score
        payment_score = 100
        if total_payments > 0:
            payment_score = round((on_time_count / total_payments) * 100)

        # Account age (simplified - would need date parsing for accurate)
        parsed["analytics"] = {
            "utilization": utilization,
            "total_balance": f"${total_balance:,.0f}",
            "total_limit": f"${total_limit:,.0f}" if total_limit > 0 else "N/A",
            "payment_score": payment_score,
            "on_time_count": on_time_count,
            "total_payments": total_payments,
            "avg_account_age": "N/A",  # Would need date parsing
            "oldest_account": "N/A",  # Would need date parsing
        }

        parsed["summary"] = {
            "total_accounts": len(parsed.get("accounts", [])),
            "total_inquiries": len(parsed.get("inquiries", [])),
            "total_collections": len(parsed.get("collections", [])),
            "total_public_records": len(parsed.get("public_records", [])),
            "total_late_payments": late_count,
        }

        return parsed

    except Exception as e:
        logger.error(f"Failed to parse credit report: {e}")
        return {
            "error": str(e),
            "scores": {"transunion": None, "experian": None, "equifax": None},
            "accounts": [],
            "inquiries": [],
            "public_records": [],
            "collections": [],
            "creditor_contacts": [],
            "summary": {},
        }
