"""
FTC Identity Theft Affidavit PDF Filler Service

Fills the FTC Identity Theft Victim's Complaint and Affidavit form
with client data and selected accounts from the 5-Day Knockout process.

Field mapping determined by analyzing the PDF form structure.
Uses pdfrw for reliable AcroForm field filling.
"""

import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from pdfrw import PdfDict, PdfName, PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# Path to the blank FTC affidavit template
TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "static",
    "pdf_templates",
    "ftc_identity_theft_affidavit.pdf",
)


# Field mapping based on PDF analysis
# Page 1 - About You (Now)
FIELD_MAP_PAGE1 = {
    # (1) Full legal name - First, Middle, Last, Suffix
    "victim_first_name": "Text_1",
    "victim_middle_name": "Text_90",
    "victim_last_name": "Text_91",
    "victim_suffix": "Text_92",
    # (2) Date of birth
    "victim_dob": "Text_2",
    # (3) SSN - split into 3 parts
    "victim_ssn_1": "Text_3",
    "victim_ssn_2": "Text_4",
    "victim_ssn_3": "Text_5",
    # (4) Driver's license
    "victim_dl_state": "Text_6",  # Dropdown
    "victim_dl_number": "Text_7",
    # (5) Current street address
    "victim_street": "Text_93",
    "victim_apt": "Text_8",
    "victim_city": "Text_9",
    "victim_state": "Text_94",  # Dropdown
    "victim_zip": "Text_95",
    "victim_country": "Text_96",
    # (6) Lived at address since
    "victim_address_since": "Text_10",
    # (7) Contact info
    "victim_day_phone_area": "Text_11",
    "victim_day_phone": "Text_12",
    "victim_eve_phone_area": "Text_13",
    "victim_eve_phone": "Text_14",
    "victim_email": "Text_15",
    # (8-10) At time of fraud - same name/address fields
    "fraud_first_name": "Text_16",
    "fraud_middle_name": "Text_97",
    "fraud_last_name": "Text_98",
    "fraud_suffix": "Text_99",
    "fraud_street": "Text_100",
    "fraud_apt": "Text_101",
    "fraud_city": "Text_102",
    "fraud_state": "US_States_Collection_1",
    "fraud_zip": "Text_103",
    "fraud_country": "Text_104",
    "fraud_day_phone_area": "Text_105",
    "fraud_day_phone": "Text_106",
    "fraud_eve_phone_area": "Text_107",
    "fraud_eve_phone": "Text_108",
    "fraud_email": "Text_109",
}

# Page 2 - Declarations & About the Fraud
FIELD_MAP_PAGE2 = {
    # Header repeats victim name/phone
    "p2_victim_name": "Text_24",
    "p2_victim_phone_area": "Text_25",
    "p2_victim_phone": "Text_26",
    # (11) Authorization - did/did not
    "auth_did": "Checkbox_1",
    "auth_did_not": "Checkbox_2",
    # (12) Benefit received - did/did not
    "benefit_did": "Checkbox_3",
    "benefit_did_not": "Checkbox_4",
    # (13) Willing to work with law enforcement - am/am not
    "willing_am": "Checkbox_5",
    "willing_am_not": "Checkbox_6",
    # (14) Suspected perpetrator info
    "perp_first_name": "Text_110",
    "perp_middle_name": "Text_111",
    "perp_last_name": "Text_112",
    "perp_suffix": "Text_113",
    "perp_street": "Text_114",
    "perp_apt": "Text_115",
    "perp_city": "Text_116",
    "perp_state": "US_States_Collection_2",
    "perp_zip": "Text_117",
    "perp_country": "Text_118",
    "perp_phone1_area": "Text_119",
    "perp_phone1": "Text_120",
    "perp_phone2_area": "Text_121",
    "perp_phone2": "Text_122",
    # Additional info about perpetrator (multi-line)
    "perp_info_1": "Text_123",
    "perp_info_2": "Text_124",
    "perp_info_3": "Text_125",
    "perp_info_4": "Text_126",
    "perp_info_5": "Text_127",
    "perp_info_6": "Text_128",
    "perp_info_7": "Text_129",
    "perp_info_8": "Text_130",
    "perp_info_9": "Text_131",
    "perp_info_10": "Text_132",
    "perp_info_11": "Text_133",
}

# Page 3 - Additional Info & Documentation
FIELD_MAP_PAGE3 = {
    # Header
    "p3_victim_name": "Text_45",
    "p3_victim_phone_area": "Text_46",
    "p3_victim_phone": "Text_47",
    # (15) Additional crime info
    "crime_info_1": "Text_48",
    "crime_info_2": "Text_49",
    "crime_info_3": "Text_50",
    "crime_info_4": "Text_51",
    "crime_info_5": "Text_52",
    "crime_info_6": "Text_53",
    "crime_info_7": "Text_54",
    # (16) Documentation checkboxes
    "doc_photo_id": "Checkbox_39",
    "doc_proof_residence": "Checkbox_40",
    # (17) Inaccurate personal info
    "inaccurate_info_a": "Text_134",
    "inaccurate_info_b": "Text_135",
    "inaccurate_info_c": "Text_136",
    # (18) Fraudulent inquiries
    "inquiry_company_1": "Text_137",
    "inquiry_company_2": "Text_138",
    "inquiry_company_3": "Text_139",
}

# Page 4 - Account Details (3 accounts per page)
FIELD_MAP_PAGE4_ACCOUNT1 = {
    # Header
    "p4_victim_name": "Text_61",
    "p4_victim_phone_area": "Text_62",
    "p4_victim_phone": "Text_63",
    # Account 1
    "acct1_institution": "Text_64",
    "acct1_contact": "Text_140",
    "acct1_phone": "Text_141",
    "acct1_ext": "Text_142",
    "acct1_number": "Text_65",
    "acct1_routing": "Text_143",
    "acct1_check_nums": "Text_144",
    # Account type checkboxes
    "acct1_type_credit": "Checkbox_41",
    "acct1_type_bank": "Checkbox_42",
    "acct1_type_phone": "Checkbox_43",
    "acct1_type_loan": "Checkbox_44",
    "acct1_type_govt": "Checkbox_45",
    "acct1_type_internet": "Checkbox_46",
    "acct1_type_other": "Checkbox_47",
    # Fraud type
    "acct1_opened_fraud": "Checkbox_48",
    "acct1_tampered": "Checkbox_49",
    # Dates and amount
    "acct1_date_opened": "Date_3",
    "acct1_date_discovered": "Date_4",
    "acct1_amount": "Text_145",
}

FIELD_MAP_PAGE4_ACCOUNT2 = {
    "acct2_institution": "Text_146",
    "acct2_contact": "Text_147",
    "acct2_phone": "Text_148",
    "acct2_ext": "Text_149",
    "acct2_number": "Text_150",
    "acct2_routing": "Text_151",
    "acct2_check_nums": "Text_152",
    "acct2_type_credit": "Checkbox_50",
    "acct2_type_bank": "Checkbox_51",
    "acct2_type_phone": "Checkbox_52",
    "acct2_type_loan": "Checkbox_53",
    "acct2_type_govt": "Checkbox_54",
    "acct2_type_internet": "Checkbox_55",
    "acct2_type_other": "Checkbox_56",
    "acct2_opened_fraud": "Checkbox_57",
    "acct2_tampered": "Checkbox_58",
    "acct2_date_opened": "Date_5",
    "acct2_date_discovered": "Date_6",
    "acct2_amount": "US_Currency_1",
}

FIELD_MAP_PAGE4_ACCOUNT3 = {
    "acct3_institution": "Text_153",
    "acct3_contact": "Text_154",
    "acct3_phone": "Text_155",
    "acct3_ext": "Text_156",
    "acct3_number": "Text_157",
    "acct3_routing": "Text_158",
    "acct3_check_nums": "Text_159",
    "acct3_type_credit": "Checkbox_59",
    "acct3_type_bank": "Checkbox_60",
    "acct3_type_phone": "Checkbox_61",
    "acct3_type_loan": "Checkbox_62",
    "acct3_type_govt": "Checkbox_63",
    "acct3_type_internet": "Checkbox_64",
    "acct3_type_other": "Checkbox_65",
    "acct3_opened_fraud": "Checkbox_66",
    "acct3_tampered": "Checkbox_67",
    "acct3_date_opened": "Date_7",
    "acct3_date_discovered": "Date_8",
    "acct3_amount": "US_Currency_2",
}

# Page 5 - Law Enforcement Report
FIELD_MAP_PAGE5 = {
    # Header
    "p5_victim_name": "Text_73",
    "p5_victim_phone_area": "Text_74",
    "p5_victim_phone": "Text_75",
    # (20) Law enforcement report status
    "le_not_filed": "Checkbox_34",
    "le_unable": "Checkbox_35",
    "le_automated": "Checkbox_36",
    "le_in_person": "Checkbox_37",
    # Report details
    "le_department": "Text_76",
    "le_state": "Text_160",  # Dropdown
    "le_report_number": "Text_77",
    "le_filing_date": "Text_78",
    "le_officer_name": "Text_79",
    # Signature field (not fillable programmatically)
    # "le_officer_signature": "Signature_1",
    "le_badge_number": "Text_80",
    "le_phone_area": "Text_81",
    "le_phone": "Text_82",
    # Did victim receive copy - checkboxes in unnamed fields
    "ftc_complaint_number": "Text_83",
}

# Page 6 - Signature
FIELD_MAP_PAGE6 = {
    # Header
    "p6_victim_name": "Text_84",
    "p6_victim_phone_area": "Text_85",
    "p6_victim_phone": "Text_86",
    # (21) Signature section
    "signature_date": "Date_1",
    # Signature field (not fillable programmatically)
    # "victim_signature": "Signature_2",
    # (22) Notary/Witness
    # "notary_signature": "Text_87",  # Actually a sig field
    # "witness_signature": "Signature_4",
    "witness_name": "Text_88",
    "witness_date": "Text_89",
    "witness_phone": "Date_2",
}


def parse_phone(phone: str) -> tuple:
    """Parse phone number into area code and number."""
    if not phone:
        return ("", "")
    # Remove non-digits
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return (digits[:3], digits[3:])
    elif len(digits) == 11 and digits[0] == "1":
        return (digits[1:4], digits[4:])
    return ("", digits)


def parse_ssn(ssn: str) -> tuple:
    """Parse SSN into 3 parts."""
    if not ssn:
        return ("", "", "")
    digits = "".join(c for c in ssn if c.isdigit())
    if len(digits) == 9:
        return (digits[:3], digits[3:5], digits[5:])
    return ("", "", "")


def parse_address(address: str) -> dict:
    """Parse a full address string into components."""
    # This is a simplified parser - real implementation would use a library
    result = {
        "street": "",
        "apt": "",
        "city": "",
        "state": "",
        "zip": "",
        "country": "USA",
    }
    if not address:
        return result

    # Try to parse common formats
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        result["street"] = parts[0]
        result["city"] = parts[-2] if len(parts) > 2 else parts[1]
        # Last part usually has state + zip
        last = parts[-1].strip()
        state_zip = last.split()
        if len(state_zip) >= 2:
            result["state"] = state_zip[0]
            result["zip"] = state_zip[1] if len(state_zip) > 1 else ""
        else:
            result["state"] = last
    elif len(parts) == 2:
        result["street"] = parts[0]
        state_zip = parts[1].split()
        if len(state_zip) >= 2:
            result["city"] = " ".join(state_zip[:-2])
            result["state"] = state_zip[-2]
            result["zip"] = state_zip[-1]
    else:
        result["street"] = address

    return result


def get_account_type_field(account_type: str, prefix: str) -> str:
    """Map account type string to checkbox field name."""
    type_map = {
        "credit": f"{prefix}_type_credit",
        "credit card": f"{prefix}_type_credit",
        "bank": f"{prefix}_type_bank",
        "checking": f"{prefix}_type_bank",
        "savings": f"{prefix}_type_bank",
        "phone": f"{prefix}_type_phone",
        "utilities": f"{prefix}_type_phone",
        "loan": f"{prefix}_type_loan",
        "auto loan": f"{prefix}_type_loan",
        "mortgage": f"{prefix}_type_loan",
        "student loan": f"{prefix}_type_loan",
        "government": f"{prefix}_type_govt",
        "govt": f"{prefix}_type_govt",
        "internet": f"{prefix}_type_internet",
        "email": f"{prefix}_type_internet",
    }
    return type_map.get(account_type.lower(), f"{prefix}_type_other")


class FTCAffidavitFiller:
    """Service for filling FTC Identity Theft Affidavit PDFs."""

    def __init__(self):
        self.template_path = TEMPLATE_PATH

    def fill_affidavit(
        self,
        client_data: Dict[str, Any],
        accounts: List[Dict[str, Any]],
        police_report: Optional[Dict[str, Any]] = None,
        ftc_number: Optional[str] = None,
    ) -> bytes:
        """
        Fill the FTC affidavit with client and account data.

        Args:
            client_data: Dict with client info (name, dob, ssn, address, phone, email)
            accounts: List of account dicts with creditor, account_number, date_opened, balance
            police_report: Optional dict with department, report_number, filing_date, officer
            ftc_number: Optional FTC complaint reference number

        Returns:
            Filled PDF as bytes
        """
        template = PdfReader(self.template_path)

        # Build field values
        field_values = {}

        # Process client data
        self._fill_client_info(field_values, client_data)

        # Process accounts (up to 3 on page 4)
        self._fill_accounts(field_values, accounts)

        # Process police report if provided
        if police_report:
            self._fill_police_report(field_values, police_report)

        # FTC complaint number
        if ftc_number:
            field_values["Text_83"] = ftc_number

        # Set current date for signature
        today = datetime.now().strftime("%m/%d/%Y")
        field_values["Date_1"] = today

        # Fill form fields using pdfrw
        self._fill_pdf_fields(template, field_values)

        # Write to bytes
        output = io.BytesIO()
        writer = PdfWriter(output)
        writer.write(trailer=template)
        output.seek(0)

        return output.read()

    def _fill_pdf_fields(
        self, template: PdfReader, field_values: Dict[str, str]
    ) -> None:
        """Fill PDF form fields using pdfrw."""
        # Get all annotations from all pages
        for page in template.pages:
            annotations = page.get("/Annots")
            if annotations is None:
                continue

            for annotation in annotations:
                if annotation is None:
                    continue

                # Get the field name
                field_name = annotation.get("/T")
                if field_name is None:
                    continue

                # Clean up field name (remove parentheses if present)
                field_name = str(field_name)
                if field_name.startswith("(") and field_name.endswith(")"):
                    field_name = field_name[1:-1]

                # Check if we have a value for this field
                if field_name not in field_values:
                    continue

                value = field_values[field_name]
                if value is None:
                    continue

                # Get field type
                field_type = annotation.get("/FT")

                if field_type == PdfName.Btn:
                    # Checkbox - set to /Yes or /Off
                    if value and value != "/Off":
                        annotation.update(
                            PdfDict(
                                V=PdfName.Yes,
                                AS=PdfName.Yes,
                            )
                        )
                    else:
                        annotation.update(
                            PdfDict(
                                V=PdfName.Off,
                                AS=PdfName.Off,
                            )
                        )
                else:
                    # Text field - set value
                    annotation.update(
                        PdfDict(
                            V=f"({value})",
                            AP="",  # Clear appearance to force regeneration
                        )
                    )

        # Set NeedAppearances flag so PDF readers regenerate field appearances
        if template.Root.AcroForm:
            template.Root.AcroForm.update(PdfDict(NeedAppearances=PdfName("true")))

    def _fill_client_info(
        self, field_values: Dict[str, str], client: Dict[str, Any]
    ) -> None:
        """Fill client personal information fields."""
        # Parse name
        full_name = client.get("name", "")
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ""
        middle_name = name_parts[1] if len(name_parts) > 2 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        # Page 1 - About You (Now)
        field_values["Text_1"] = first_name
        field_values["Text_90"] = middle_name
        field_values["Text_91"] = last_name

        # DOB
        dob = client.get("dob", client.get("date_of_birth", ""))
        if isinstance(dob, datetime):
            dob = dob.strftime("%m/%d/%Y")
        field_values["Text_2"] = dob

        # SSN
        ssn = client.get("ssn", client.get("ssn_last_4", ""))
        ssn_parts = parse_ssn(ssn)
        field_values["Text_3"] = ssn_parts[0]
        field_values["Text_4"] = ssn_parts[1]
        field_values["Text_5"] = ssn_parts[2]

        # Address
        address = client.get("address", "")
        if isinstance(address, str):
            addr = parse_address(address)
        else:
            addr = address or {}

        field_values["Text_93"] = addr.get("street", client.get("street", ""))
        field_values["Text_8"] = addr.get("apt", client.get("apt", ""))
        field_values["Text_9"] = addr.get("city", client.get("city", ""))
        field_values["Text_95"] = addr.get("zip", client.get("zip", ""))
        field_values["Text_96"] = addr.get("country", "USA")

        # Phone
        phone = client.get("phone", client.get("day_phone", ""))
        area, number = parse_phone(phone)
        field_values["Text_11"] = area
        field_values["Text_12"] = number

        eve_phone = client.get("evening_phone", phone)
        eve_area, eve_number = parse_phone(eve_phone)
        field_values["Text_13"] = eve_area
        field_values["Text_14"] = eve_number

        # Email
        field_values["Text_15"] = client.get("email", "")

        # Fill header fields on other pages with victim name/phone
        victim_display = f"{first_name} {last_name}"
        for page_field in [
            ("Text_24", "Text_25", "Text_26"),  # Page 2
            ("Text_45", "Text_46", "Text_47"),  # Page 3
            ("Text_61", "Text_62", "Text_63"),  # Page 4
            ("Text_73", "Text_74", "Text_75"),  # Page 5
            ("Text_84", "Text_85", "Text_86"),  # Page 6
        ]:
            field_values[page_field[0]] = victim_display
            field_values[page_field[1]] = area
            field_values[page_field[2]] = number

        # Default declarations (did not authorize, did not receive benefit, willing to cooperate)
        field_values["Checkbox_2"] = "/Yes"  # Did NOT authorize
        field_values["Checkbox_4"] = "/Yes"  # Did NOT receive benefit
        field_values["Checkbox_5"] = "/Yes"  # AM willing to work with LE

        # Documentation checkboxes - assume they have ID and proof
        field_values["Checkbox_39"] = "/Yes"  # Photo ID
        field_values["Checkbox_40"] = "/Yes"  # Proof of residence

    def _fill_accounts(
        self, field_values: Dict[str, str], accounts: List[Dict[str, Any]]
    ) -> None:
        """Fill account details (up to 3 accounts on page 4)."""
        account_fields = [
            FIELD_MAP_PAGE4_ACCOUNT1,
            FIELD_MAP_PAGE4_ACCOUNT2,
            FIELD_MAP_PAGE4_ACCOUNT3,
        ]

        for i, account in enumerate(accounts[:3]):
            prefix = f"acct{i+1}"
            fields = account_fields[i]

            # Institution/Creditor name
            creditor = account.get("creditor_name", account.get("creditor", ""))
            field_values[fields[f"{prefix}_institution"]] = creditor

            # Account number
            acct_num = account.get("account_number", "")
            field_values[fields[f"{prefix}_number"]] = acct_num

            # Account type checkbox
            acct_type = account.get(
                "account_type", account.get("type", "credit")
            ).lower()
            type_field = get_account_type_field(acct_type, prefix)
            if type_field in fields:
                field_values[fields[type_field]] = "/Yes"

            # Fraud type - default to "opened fraudulently"
            field_values[fields[f"{prefix}_opened_fraud"]] = "/Yes"

            # Date opened/misused
            date_opened = account.get("date_opened", "")
            if isinstance(date_opened, datetime):
                date_opened = date_opened.strftime("%m/%Y")
            elif date_opened and "/" not in date_opened and "-" in date_opened:
                # Convert YYYY-MM-DD to MM/YYYY
                try:
                    dt = datetime.strptime(date_opened[:10], "%Y-%m-%d")
                    date_opened = dt.strftime("%m/%Y")
                except (ValueError, TypeError):
                    pass
            field_values[fields[f"{prefix}_date_opened"]] = date_opened

            # Date discovered - use today if not specified
            date_discovered = account.get(
                "date_discovered", datetime.now().strftime("%m/%Y")
            )
            field_values[fields[f"{prefix}_date_discovered"]] = date_discovered

            # Amount/Balance
            balance = account.get("balance", account.get("high_balance", ""))
            if balance:
                if isinstance(balance, (int, float)):
                    balance = f"${balance:,.2f}"
                elif not balance.startswith("$"):
                    balance = f"${balance}"
            field_values[fields[f"{prefix}_amount"]] = balance

    def _fill_police_report(
        self, field_values: Dict[str, str], report: Dict[str, Any]
    ) -> None:
        """Fill police report section."""
        # Mark that report was filed
        if report.get("automated"):
            field_values["Checkbox_36"] = "/Yes"  # Automated report
        else:
            field_values["Checkbox_37"] = "/Yes"  # In-person report

        # Department info
        field_values["Text_76"] = report.get("department", "")
        field_values["Text_77"] = report.get("report_number", "")
        field_values["Text_78"] = report.get("filing_date", "")
        field_values["Text_79"] = report.get("officer_name", "")
        field_values["Text_80"] = report.get("badge_number", "")

        phone = report.get("phone", "")
        area, number = parse_phone(phone)
        field_values["Text_81"] = area
        field_values["Text_82"] = number


def fill_ftc_affidavit(
    client_data: Dict[str, Any],
    accounts: List[Dict[str, Any]],
    police_report: Optional[Dict[str, Any]] = None,
    ftc_number: Optional[str] = None,
) -> bytes:
    """
    Convenience function to fill FTC affidavit.

    Args:
        client_data: Client information dict
        accounts: List of accounts to include
        police_report: Optional police report info
        ftc_number: Optional FTC complaint number

    Returns:
        Filled PDF as bytes
    """
    filler = FTCAffidavitFiller()
    return filler.fill_affidavit(client_data, accounts, police_report, ftc_number)
