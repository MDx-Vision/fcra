"""
FTC Identity Theft Affidavit PDF Generator

Generates a filled FTC Identity Theft Victim's Complaint and Affidavit
from scratch using reportlab. Based on the official FTC form layout.
Includes margin instructional notes matching the original FTC form.
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# Margin notes exactly as they appear in the official FTC form
MARGIN_NOTES = {
    "page1_ssn": (
        "Leave (3) blank until you provide this form to someone with a "
        "legitimate business need, like when you are filing your report "
        "at the police station or sending the form to a credit reporting "
        "agency to correct your credit report."
    ),
    "page1_skip": (
        "Skip (8) - (10) if your information has not changed since the fraud."
    ),
    "page2_suspect": (
        "(14): Enter what you know about anyone you believe was involved "
        "(even if you don't have complete information)."
    ),
    "page3_attach": ("(14) and (15): Attach additional sheets as needed."),
    "page3_docs": (
        "(16): Reminder: Attach copies of your identity documents when "
        "sending this form to creditors and credit reporting agencies."
    ),
    "page4_multiple": (
        "(19): If there were more than three frauds, copy this page blank, "
        "and attach as many additional copies as necessary."
    ),
    "page4_incomplete": (
        "Enter any applicable information that you have, even if it is "
        "incomplete or an estimate."
    ),
    "page4_two_frauds": (
        "If the thief committed two types of fraud at one company, list "
        "the company twice, giving the information about the two frauds "
        "separately."
    ),
    "page4_contact": (
        "Contact Person: Someone you dealt with, whom an investigator "
        "can call about this fraud."
    ),
    "page4_account": (
        "Account Number: The number of the credit or debit card, bank "
        "account, loan, or other account that was misused."
    ),
    "page4_dates": (
        "Dates: Indicate when the thief began to misuse your information "
        "and when you discovered the problem."
    ),
    "page4_amount": (
        "Amount Obtained: For instance, the total amount purchased with "
        "the card or withdrawn from the account."
    ),
    "page5_checkbox": (
        '(20): Check "I have not..." if you have not yet filed a report '
        'with law enforcement or you have chosen not to. Check "I was '
        'unable..." if you tried to file a report but law enforcement '
        "refused to take it."
    ),
    "page5_automated": (
        "Automated report: A law enforcement report filed through an "
        "automated system, for example, by telephone, mail, or the Internet, "
        "instead of a face-to-face interview with a law enforcement officer."
    ),
}


def _format_phone(phone: str) -> str:
    """Format phone number as (XXX) XXX-XXXX."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone


def _format_ssn(ssn: str) -> str:
    """Format SSN as XXX-XX-XXXX or show last 4."""
    if not ssn:
        return "___-__-____"
    digits = "".join(c for c in ssn if c.isdigit())
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    elif len(digits) == 4:
        return f"___-__-{digits}"
    return ssn


def _format_date(date_val) -> str:
    """Format date as MM/DD/YYYY."""
    if not date_val:
        return ""
    if isinstance(date_val, str):
        return date_val
    try:
        return date_val.strftime("%m/%d/%Y")
    except (AttributeError, ValueError):
        return str(date_val)


class FTCAffidavitGenerator:
    """Generates FTC Identity Theft Affidavit PDFs from scratch."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="FTCTitle",
                parent=self.styles["Heading1"],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="FTCSectionHeader",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=colors.white,
                backColor=colors.HexColor("#4a4a4a"),
                borderPadding=6,
                spaceAfter=8,
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="FieldLabel",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="FieldValue",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Checkbox",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica",
            )
        )
        # Margin note style - matches FTC form side instructions
        self.styles.add(
            ParagraphStyle(
                name="MarginNote",
                parent=self.styles["Normal"],
                fontSize=8,
                fontName="Helvetica-Oblique",
                textColor=colors.HexColor("#555555"),
                leading=10,
            )
        )

    def generate(
        self,
        client_data: Dict[str, Any],
        accounts: List[Dict[str, Any]],
        police_report: Optional[Dict[str, Any]] = None,
        ftc_number: Optional[str] = None,
    ) -> bytes:
        """
        Generate the FTC affidavit PDF.

        Args:
            client_data: Client info (name, dob, ssn, address, phone, email)
            accounts: List of fraudulent accounts
            police_report: Police report info (optional)
            ftc_number: FTC complaint number (optional)

        Returns:
            PDF as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Build document content
        story = []

        # Page 1: About You
        story.extend(self._build_page1(client_data))
        story.append(PageBreak())

        # Page 2: Declarations
        story.extend(self._build_page2(client_data))
        story.append(PageBreak())

        # Page 3: Documentation & Account Info
        story.extend(self._build_page3(client_data, accounts))
        story.append(PageBreak())

        # Page 4: Account Details
        story.extend(self._build_page4(client_data, accounts))
        story.append(PageBreak())

        # Page 5: Law Enforcement Report
        story.extend(self._build_page5(client_data, police_report, ftc_number))
        story.append(PageBreak())

        # Page 6: Signature
        story.extend(self._build_page6(client_data))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _header(self, name: str, phone: str, page: int) -> Table:
        """Create page header with victim name and phone."""
        data = [
            [f"Victim's Name: {name}", f"Phone: {_format_phone(phone)}", f"Page {page}"]
        ]
        t = Table(data, colWidths=[3.5 * inch, 2.5 * inch, 1 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                ]
            )
        )
        return t

    def _section_header(self, text: str) -> Paragraph:
        """Create a dark section header."""
        return Paragraph(f"<b>{text}</b>", self.styles["FTCSectionHeader"])

    def _field_row(self, label: str, value: str, width: float = 7.5) -> Table:
        """Create a labeled field row."""
        data = [
            [
                Paragraph(f"<b>{label}:</b>", self.styles["FieldLabel"]),
                Paragraph(value or "_" * 40, self.styles["FieldValue"]),
            ]
        ]
        t = Table(data, colWidths=[2 * inch, (width - 2) * inch])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return t

    def _checkbox(self, checked: bool, label: str) -> str:
        """Return checkbox text."""
        box = "[X]" if checked else "[  ]"
        return f"{box} {label}"

    def _with_margin_note(self, content: list, note_key: str) -> Table:
        """
        Create a two-column layout with margin note on the right side.

        Args:
            content: List of flowables for the main content
            note_key: Key to look up in MARGIN_NOTES dict

        Returns:
            Table with content on left, margin note on right
        """
        note_text = MARGIN_NOTES.get(note_key, "")
        if not note_text:
            # No margin note, just return content as-is in a table
            return Table([[content]], colWidths=[7.5 * inch])

        note_para = Paragraph(f"<i>{note_text}</i>", self.styles["MarginNote"])

        # Main content in left column (5.8"), margin note in right column (1.7")
        data = [[content, note_para]]
        t = Table(data, colWidths=[5.8 * inch, 1.7 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ("LEFTPADDING", (1, 0), (1, 0), 8),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f9f9f9")),
                ]
            )
        )
        return t

    def _margin_note_block(self, note_key: str) -> Paragraph:
        """Create a standalone margin note paragraph."""
        note_text = MARGIN_NOTES.get(note_key, "")
        return Paragraph(f"<i>{note_text}</i>", self.styles["MarginNote"])

    def _build_page1(self, client: Dict[str, Any]) -> list:
        """Build Page 1: About You (the victim)."""
        story = []

        # Title and subtitle
        story.append(
            Paragraph("Average time to complete: 10 minutes", self.styles["SmallText"])
        )
        story.append(
            Paragraph(
                "<b>Identity Theft Victim's Complaint and Affidavit</b>",
                self.styles["FTCTitle"],
            )
        )
        story.append(
            Paragraph(
                "A voluntary form for filing a report with law enforcement, and disputes with "
                "credit reporting agencies and creditors about identity theft-related problems. "
                "Visit ftc.gov/idtheft to use a secure online version that you can print for your records.",
                self.styles["SmallText"],
            )
        )
        story.append(Spacer(1, 10))

        # Instructions
        story.append(
            Paragraph(
                "<b>Before completing this form:</b><br/>"
                "1. Place a fraud alert on your credit reports, and review the reports for signs of fraud.<br/>"
                "2. Close the accounts that you know, or believe, have been tampered with or opened fraudulently.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 10))

        # Section: About You (Now)
        story.append(self._section_header("About You (the victim)"))
        story.append(Paragraph("<b>Now</b>", self.styles["FieldLabel"]))
        story.append(Spacer(1, 8))

        # Parse name
        name = client.get("name", "")
        name_parts = name.split() if name else []
        if len(name_parts) >= 3:
            first, middle, last = (
                name_parts[0],
                " ".join(name_parts[1:-1]),
                name_parts[-1],
            )
        elif len(name_parts) == 2:
            first, middle, last = name_parts[0], "", name_parts[1]
        elif len(name_parts) == 1:
            first, middle, last = name_parts[0], "", ""
        else:
            first = middle = last = ""

        # Get all field values
        dob = _format_date(client.get("dob", "")) or "____ / ____ / ________"
        ssn = _format_ssn(client.get("ssn", ""))
        dl_state = client.get("dl_state", "") or "____"
        dl_number = client.get("dl_number", "") or "____________________"
        addr = client.get("address", "") or "_" * 40
        apt = client.get("apt", "") or ""
        city = client.get("city", "") or "_" * 18
        state = client.get("state", "") or "____"
        zip_code = client.get("zip", "") or "_____"
        addr_since = client.get("address_since", "") or "____/____"
        phone = _format_phone(client.get("phone", "")) or "(____) ____-______"
        email = client.get("email", "") or "_" * 30
        name_display = (
            f"{first}"
            + ("" if not middle else f" {middle}")
            + ("" if not last else f" {last}")
        )
        name_display = name_display or "_" * 35

        # Build all form rows (1-7) in one aligned table
        form_data = [
            [
                Paragraph("<b>(1)</b>", self.styles["FieldValue"]),
                Paragraph("My full legal name:", self.styles["FieldValue"]),
                Paragraph(name_display, self.styles["FieldValue"]),
            ],
            [
                Paragraph("<b>(2)</b>", self.styles["FieldValue"]),
                Paragraph("My date of birth:", self.styles["FieldValue"]),
                Paragraph(dob, self.styles["FieldValue"]),
            ],
            [
                Paragraph("<b>(3)</b>", self.styles["FieldValue"]),
                Paragraph("My Social Security number:", self.styles["FieldValue"]),
                Paragraph(ssn, self.styles["FieldValue"]),
            ],
            [
                Paragraph("<b>(4)</b>", self.styles["FieldValue"]),
                Paragraph("My driver's license:", self.styles["FieldValue"]),
                Paragraph(f"{dl_state} / {dl_number}", self.styles["FieldValue"]),
            ],
        ]

        form_table = Table(form_data, colWidths=[0.35 * inch, 1.9 * inch, 3.3 * inch])
        form_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )

        # Margin note for SSN
        margin_note = Paragraph(
            f"<i>{MARGIN_NOTES['page1_ssn']}</i>", self.styles["MarginNote"]
        )

        # Two-column layout: form on left, margin note on right
        layout = Table([[form_table, margin_note]], colWidths=[5.6 * inch, 1.9 * inch])
        layout.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (1, 0), (1, 0), 10),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f9f9f9")),
                ]
            )
        )
        story.append(layout)

        # (5) Address - aligned with items above
        addr_form = [
            [
                Paragraph("<b>(5)</b>", self.styles["FieldValue"]),
                Paragraph("My current street address:", self.styles["FieldValue"]),
                Paragraph(addr, self.styles["FieldValue"]),
                Paragraph(apt, self.styles["FieldValue"]),
            ],
            [
                "",
                "",
                Paragraph(
                    "<font size='7' color='gray'>Number &amp; Street Name</font>",
                    self.styles["FieldValue"],
                ),
                Paragraph(
                    "<font size='7' color='gray'>Apt/Suite</font>",
                    self.styles["FieldValue"],
                ),
            ],
            [
                "",
                "",
                Paragraph(
                    f"{city}, {state} {zip_code}, USA", self.styles["FieldValue"]
                ),
                "",
            ],
            [
                "",
                "",
                Paragraph(
                    "<font size='7' color='gray'>City, State, Zip Code, Country</font>",
                    self.styles["FieldValue"],
                ),
                "",
            ],
        ]
        addr_table = Table(
            addr_form, colWidths=[0.35 * inch, 1.9 * inch, 2.6 * inch, 0.7 * inch]
        )
        addr_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ("LINEBELOW", (2, 0), (3, 0), 0.5, colors.black),
                    ("LINEBELOW", (2, 2), (2, 2), 0.5, colors.black),
                ]
            )
        )
        story.append(addr_table)

        # (6) Address since - aligned
        addr_since_form = [
            [
                Paragraph("<b>(6)</b>", self.styles["FieldValue"]),
                Paragraph(
                    "I have lived at this address since:", self.styles["FieldValue"]
                ),
                Paragraph(addr_since, self.styles["FieldValue"]),
            ],
        ]
        addr_since_table = Table(
            addr_since_form, colWidths=[0.35 * inch, 2.4 * inch, 2.8 * inch]
        )
        addr_since_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(addr_since_table)

        # (7) Phone & Email - aligned table
        phone_form = [
            [
                Paragraph("<b>(7)</b>", self.styles["FieldValue"]),
                Paragraph("My daytime phone:", self.styles["FieldValue"]),
                Paragraph(phone, self.styles["FieldValue"]),
            ],
            [
                "",
                Paragraph("My evening phone:", self.styles["FieldValue"]),
                Paragraph(phone, self.styles["FieldValue"]),
            ],
            [
                "",
                Paragraph("My email:", self.styles["FieldValue"]),
                Paragraph(email, self.styles["FieldValue"]),
            ],
        ]
        phone_table = Table(phone_form, colWidths=[0.35 * inch, 1.5 * inch, 3.7 * inch])
        phone_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(phone_table)
        story.append(Spacer(1, 10))

        # At the Time of the Fraud section with margin note
        fraud_content = [
            Paragraph("<b>At the Time of the Fraud</b>", self.styles["FieldLabel"]),
            Spacer(1, 6),
            Paragraph(
                "<b>(8)</b> My full legal name was: " + "_" * 40,
                self.styles["FieldValue"],
            ),
            Paragraph(
                "<b>(9)</b> My address was: " + "_" * 47, self.styles["FieldValue"]
            ),
            Paragraph(
                "<b>(10)</b> My phone/email: " + "_" * 44, self.styles["FieldValue"]
            ),
        ]
        fraud_note = Paragraph(
            f"<i>{MARGIN_NOTES['page1_skip']}</i>", self.styles["MarginNote"]
        )
        fraud_layout = Table(
            [[fraud_content, fraud_note]], colWidths=[5.9 * inch, 1.6 * inch]
        )
        fraud_layout.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (1, 0), (1, 0), 10),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f9f9f9")),
                ]
            )
        )
        story.append(fraud_layout)

        # Footer with OMB number
        story.append(Spacer(1, 12))
        story.append(
            Paragraph(
                "The Paperwork Reduction Act requires the FTC to display a valid control number "
                "(in this case, OMB control #3084-0047) before we can collect – or sponsor the "
                "collection of – your information, or require you to provide it.",
                self.styles["SmallText"],
            )
        )

        return story

    def _build_page2(self, client: Dict[str, Any]) -> list:
        """Build Page 2: Declarations."""
        story = []

        name = client.get("name", "")
        phone = client.get("phone", "")
        story.append(self._header(name, phone, 2))
        story.append(Spacer(1, 10))

        story.append(self._section_header("About You (the victim) (Continued)"))
        story.append(Paragraph("<b>Declarations</b>", self.styles["FieldLabel"]))
        story.append(Spacer(1, 10))

        # Declaration 11 - "did not" should be checked for identity theft victims
        story.append(
            Paragraph(
                "(11) I &nbsp;&nbsp;[&nbsp;&nbsp;] did &nbsp;&nbsp;OR&nbsp;&nbsp; <b>[X] did not</b> &nbsp;&nbsp;authorize anyone to use my name or personal "
                "information to obtain money, credit, loans, goods, or services — or for any other "
                "purpose — as described in this report.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 10))

        # Declaration 12 - "did not" for victims
        story.append(
            Paragraph(
                "(12) I &nbsp;&nbsp;[&nbsp;&nbsp;] did &nbsp;&nbsp;OR&nbsp;&nbsp; <b>[X] did not</b> &nbsp;&nbsp;receive any money, goods, services, or other "
                "benefit as a result of the events described in this report.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 10))

        # Declaration 13
        story.append(
            Paragraph(
                "(13) I &nbsp;&nbsp;<b>[X] am</b> &nbsp;&nbsp;OR&nbsp;&nbsp; [&nbsp;&nbsp;] am not &nbsp;&nbsp;willing to work with law enforcement if charges "
                "are brought against the person(s) who committed the fraud.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 16))

        # About the Fraud section with margin note
        story.append(self._section_header("About the Fraud"))
        story.append(Spacer(1, 8))

        suspect_section = [
            Paragraph(
                "(14) I believe the following person used my information or identification documents "
                "to open new accounts, use my existing accounts, or commit other fraud.",
                self.styles["FieldValue"],
            ),
            Spacer(1, 8),
            Paragraph(
                "Name: <u>&nbsp;" + "_" * 55 + "&nbsp;</u>", self.styles["FieldValue"]
            ),
            Paragraph(
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size='7' color='gray'>First &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Middle &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Last &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Suffix</font>",
                self.styles["FieldValue"],
            ),
            Spacer(1, 6),
            Paragraph(
                "Address: <u>&nbsp;" + "_" * 52 + "&nbsp;</u>",
                self.styles["FieldValue"],
            ),
            Paragraph(
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size='7' color='gray'>Number & Street Name &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Apt/Suite</font>",
                self.styles["FieldValue"],
            ),
            Paragraph(
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<u>&nbsp;"
                + "_" * 52
                + "&nbsp;</u>",
                self.styles["FieldValue"],
            ),
            Paragraph(
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size='7' color='gray'>City &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; State &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Zip Code &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Country</font>",
                self.styles["FieldValue"],
            ),
            Spacer(1, 6),
            Paragraph(
                "Phone Numbers: (____) _______________ &nbsp;&nbsp;(____) _______________",
                self.styles["FieldValue"],
            ),
            Spacer(1, 10),
            Paragraph(
                "<b>Additional information about this person:</b>",
                self.styles["FieldLabel"],
            ),
        ]
        story.append(self._with_margin_note(suspect_section, "page2_suspect"))

        # Blank lines for additional info - fewer lines
        for _ in range(5):
            story.append(
                Paragraph(
                    "<u>&nbsp;" + "_" * 90 + "&nbsp;</u>", self.styles["FieldValue"]
                )
            )

        return story

    def _build_page3(self, client: Dict[str, Any], accounts: List[Dict]) -> list:
        """Build Page 3: Documentation & Account Info."""
        story = []

        name = client.get("name", "")
        phone = client.get("phone", "")
        story.append(self._header(name, phone, 3))
        story.append(Spacer(1, 10))

        # Additional crime info with margin note
        crime_section = [
            Paragraph(
                "(15) Additional information about the crime (for example, how the identity thief "
                "gained access to your information or which documents or information were used):",
                self.styles["FieldValue"],
            ),
        ]
        story.append(self._with_margin_note(crime_section, "page3_attach"))

        for _ in range(4):
            story.append(
                Paragraph(
                    "<u>&nbsp;" + "_" * 90 + "&nbsp;</u>", self.styles["FieldValue"]
                )
            )
        story.append(Spacer(1, 12))

        # Documentation section with margin note
        story.append(self._section_header("Documentation"))
        story.append(Spacer(1, 8))

        doc_section = [
            Paragraph(
                "(16) I can verify my identity with these documents:",
                self.styles["FieldValue"],
            ),
            Spacer(1, 6),
            Paragraph(
                "<b>[X]</b> A valid government-issued photo identification card (for example, my driver's "
                "license, state-issued ID card, or my passport).",
                self.styles["FieldValue"],
            ),
            Paragraph(
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size='7' color='gray'>If you are under 16 and don't have a photo-ID, a copy of your birth certificate or "
                "a copy of your official school record showing your enrollment and legal address is acceptable.</font>",
                self.styles["FieldValue"],
            ),
            Spacer(1, 6),
            Paragraph(
                "<b>[X]</b> Proof of residency during the time the disputed charges occurred, the loan "
                "was made, or the other event took place (for example, a copy of a rental/lease "
                "agreement in my name, a utility bill, or an insurance bill).",
                self.styles["FieldValue"],
            ),
        ]
        story.append(self._with_margin_note(doc_section, "page3_docs"))
        story.append(Spacer(1, 14))

        # About the Information or Accounts
        story.append(self._section_header("About the Information or Accounts"))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                "(17) The following personal information (like my name, address, Social Security number, or date of "
                "birth) in my credit report is inaccurate as a result of this identity theft:",
                self.styles["FieldValue"],
            )
        )
        story.append(
            Paragraph(
                "(A) <u>&nbsp;" + "_" * 70 + "&nbsp;</u>", self.styles["FieldValue"]
            )
        )
        story.append(
            Paragraph(
                "(B) <u>&nbsp;" + "_" * 70 + "&nbsp;</u>", self.styles["FieldValue"]
            )
        )
        story.append(
            Paragraph(
                "(C) <u>&nbsp;" + "_" * 70 + "&nbsp;</u>", self.styles["FieldValue"]
            )
        )
        story.append(Spacer(1, 10))

        story.append(
            Paragraph(
                "(18) Credit inquiries from these companies appear on my credit report as a result of this identity theft:",
                self.styles["FieldValue"],
            )
        )
        # List inquiry companies from accounts if type is inquiry
        inquiries = [a for a in accounts if a.get("type", "").lower() == "inquiry"]
        for i, inq in enumerate(inquiries[:3], 1):
            cname = inq.get("creditor_name", "")
            story.append(
                Paragraph(
                    (
                        f"Company Name: <u>&nbsp;&nbsp;<b>{cname}</b>&nbsp;&nbsp;</u>"
                        if cname
                        else "Company Name: <u>&nbsp;" + "_" * 40 + "&nbsp;</u>"
                    ),
                    self.styles["FieldValue"],
                )
            )
        # Fill remaining slots
        for _ in range(3 - len(inquiries[:3])):
            story.append(
                Paragraph(
                    "Company Name: <u>&nbsp;" + "_" * 40 + "&nbsp;</u>",
                    self.styles["FieldValue"],
                )
            )

        return story

    def _build_page4(self, client: Dict[str, Any], accounts: List[Dict]) -> list:
        """Build Page 4: Account Details."""
        story = []

        name = client.get("name", "")
        phone = client.get("phone", "")
        story.append(self._header(name, phone, 4))
        story.append(Spacer(1, 8))

        # Main instruction with first margin note
        intro_section = [
            Paragraph(
                "(19) Below are details about the different frauds committed using my personal information.",
                self.styles["FieldValue"],
            ),
        ]
        story.append(self._with_margin_note(intro_section, "page4_multiple"))
        story.append(Spacer(1, 8))

        # Build compact margin notes
        margin_notes_text = (
            f"<i><b>(19):</b><br/>"
            f"{MARGIN_NOTES['page4_incomplete']}<br/><br/>"
            f"{MARGIN_NOTES['page4_two_frauds']}<br/><br/>"
            f"<b>Contact Person:</b> Someone you dealt with, whom an investigator can call about this fraud.<br/><br/>"
            f"<b>Account Number:</b> The number of the credit or debit card, bank account, loan, or other account that was misused.<br/><br/>"
            f"<b>Dates:</b> Indicate when the thief began to misuse your information and when you discovered the problem.<br/><br/>"
            f"<b>Amount Obtained:</b> For instance, the total amount purchased with the card or withdrawn from the account.</i>"
        )
        margin_para = Paragraph(margin_notes_text, self.styles["MarginNote"])

        # Filter out inquiries - just show tradelines
        tradelines = [a for a in accounts if a.get("type", "").lower() != "inquiry"]

        # Build account blocks - show up to 3
        account_blocks = []
        accounts_to_show = (
            tradelines[:3] if tradelines else [{}]
        )  # At least one empty block

        for i, account in enumerate(accounts_to_show, 1):
            account_blocks.append(self._build_account_block(account, i))
            if i < len(accounts_to_show):
                account_blocks.append(Spacer(1, 8))

        # Create two-column layout: accounts on left, margin notes on right
        data = [[account_blocks, margin_para]]
        layout_table = Table(data, colWidths=[5.5 * inch, 1.8 * inch])
        layout_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ("LEFTPADDING", (1, 0), (1, 0), 8),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f9f9f9")),
                ]
            )
        )
        story.append(layout_table)

        return story

    def _build_account_block(self, account: Dict, num: int) -> Table:
        """Build a single account detail block matching FTC form layout."""
        creditor = account.get("creditor_name", "") or account.get("creditor", "")
        acct_num = account.get("account_number", "")
        acct_type = account.get("account_type", "") or account.get("type", "credit")
        date_opened = account.get("date_opened", "")
        balance = account.get("balance", "") or account.get("high_balance", "")

        # Format balance
        if balance:
            try:
                if isinstance(balance, (int, float)):
                    balance = f"${balance:,.2f}"
                elif not str(balance).startswith("$"):
                    balance = f"${balance}"
            except (ValueError, TypeError):
                pass

        # Format date
        if date_opened:
            if isinstance(date_opened, str) and "-" in date_opened:
                try:
                    from datetime import datetime as dt

                    d = dt.strptime(date_opened[:10], "%Y-%m-%d")
                    date_opened = d.strftime("%m/%Y")
                except (ValueError, TypeError):
                    pass

        today = datetime.now().strftime("%m/%Y")

        # Determine account type checkboxes
        type_lower = acct_type.lower() if acct_type else ""
        is_credit = type_lower in ("credit", "credit card", "revolving")
        is_bank = type_lower in ("bank", "checking", "savings")
        is_phone = type_lower in ("phone", "utilities", "phone/utilities")
        is_loan = type_lower in (
            "loan",
            "auto loan",
            "mortgage",
            "student loan",
            "installment",
        )
        is_govt = type_lower in ("government", "government benefits")
        is_internet = type_lower in ("internet", "email", "internet or email")

        # Row 1: Institution name
        row1 = [
            Paragraph(
                f"<b>Name of Institution:</b> <u>&nbsp;{creditor or '_' * 20}&nbsp;</u>",
                self.styles["FieldValue"],
            ),
            Paragraph("Contact: ____________", self.styles["SmallText"]),
            Paragraph("Phone: ________", self.styles["SmallText"]),
        ]

        # Row 2: Account number
        row2 = [
            Paragraph(
                f"<b>Account Number:</b> <u>&nbsp;{acct_num or '_' * 18}&nbsp;</u>",
                self.styles["FieldValue"],
            ),
            Paragraph("Routing #: __________", self.styles["SmallText"]),
            Paragraph("Check #(s): _____", self.styles["SmallText"]),
        ]

        # Row 3: Account type checkboxes (single row)
        row3_text = (
            f"<b>Account Type:</b> "
            f"{'<b>[X]</b>' if is_credit else '[&nbsp;]'} Credit &nbsp;"
            f"{'<b>[X]</b>' if is_bank else '[&nbsp;]'} Bank &nbsp;"
            f"{'<b>[X]</b>' if is_phone else '[&nbsp;]'} Phone/Utilities &nbsp;"
            f"{'<b>[X]</b>' if is_loan else '[&nbsp;]'} Loan &nbsp;"
            f"{'<b>[X]</b>' if is_govt else '[&nbsp;]'} Govt Benefits &nbsp;"
            f"{'<b>[X]</b>' if is_internet else '[&nbsp;]'} Internet/Email &nbsp;"
            f"[&nbsp;] Other"
        )
        row3 = [Paragraph(row3_text, self.styles["SmallText"]), "", ""]

        # Row 4: Select ONE + checkboxes
        row4 = [
            Paragraph(
                "<b>Select ONE:</b> &nbsp;&nbsp;<b>[X]</b> This account was opened fraudulently. &nbsp;&nbsp;[&nbsp;] This was an existing account that someone tampered with.",
                self.styles["FieldValue"],
            ),
            "",
            "",
        ]

        # Row 5: Dates and amount
        row5 = [
            Paragraph(
                f"<b>Date Opened/Misused:</b><br/><u>&nbsp;{date_opened or '__/__'}&nbsp;</u> <font size='6'>(mm/yyyy)</font>",
                self.styles["FieldValue"],
            ),
            Paragraph(
                f"<b>Date Discovered:</b><br/><u>&nbsp;{today}&nbsp;</u> <font size='6'>(mm/yyyy)</font>",
                self.styles["FieldValue"],
            ),
            Paragraph(
                f"<b>Total Amount ($):</b><br/><u>&nbsp;{balance or '$______'}&nbsp;</u>",
                self.styles["FieldValue"],
            ),
        ]

        data = [row1, row2, row3, row4, row5]

        t = Table(data, colWidths=[2.0 * inch, 1.6 * inch, 1.4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#cccccc")),
                    ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#cccccc")),
                    ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.HexColor("#cccccc")),
                    ("LINEBELOW", (0, 3), (-1, 3), 0.5, colors.HexColor("#cccccc")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("SPAN", (0, 2), (-1, 2)),
                    ("SPAN", (0, 3), (-1, 3)),
                ]
            )
        )
        return t

    def _build_page5(
        self,
        client: Dict[str, Any],
        police_report: Optional[Dict[str, Any]],
        ftc_number: Optional[str],
    ) -> list:
        """Build Page 5: Law Enforcement Report."""
        story = []

        name = client.get("name", "")
        phone = client.get("phone", "")
        story.append(self._header(name, phone, 5))
        story.append(Spacer(1, 10))

        story.append(self._section_header("Your Law Enforcement Report"))
        story.append(Spacer(1, 6))

        # Main intro with margin notes
        intro_section = [
            Paragraph(
                "(20) One way to get a credit reporting agency to quickly block identity theft-related "
                "information from appearing on your credit report is to submit a detailed law enforcement "
                'report ("Identity Theft Report"). You can obtain an Identity Theft Report by taking this '
                "form to your local law enforcement office, along with your supporting documentation. Ask "
                "an officer to witness your signature and complete the rest of the information in this section. "
                "It's important to get your report number, whether or not you are able to file in person or "
                "get a copy of the official law enforcement report. Attach a copy of any confirmation letter "
                "or official law enforcement report you receive when sending this form to credit reporting agencies.",
                self.styles["FieldValue"],
            ),
        ]
        story.append(self._with_margin_note(intro_section, "page5_checkbox"))
        story.append(Spacer(1, 10))

        # Determine which checkbox to check
        has_report = police_report and police_report.get("report_number")
        is_automated = police_report.get("automated", True) if police_report else True

        # Checkboxes with margin note for automated
        checkbox_section = [
            Paragraph("<b>Select ONE:</b>", self.styles["FieldLabel"]),
            Spacer(1, 4),
            Paragraph(
                f"{'[  ]' if has_report else '<b>[X]</b>'} I have not filed a law enforcement report.",
                self.styles["FieldValue"],
            ),
            Paragraph(
                "[  ] I was unable to file any law enforcement report.",
                self.styles["FieldValue"],
            ),
            Paragraph(
                f"{'<b>[X]</b>' if has_report and is_automated else '[  ]'} I filed an automated report with the law enforcement agency listed below.",
                self.styles["FieldValue"],
            ),
            Paragraph(
                f"{'<b>[X]</b>' if has_report and not is_automated else '[  ]'} I filed my report in person with the law enforcement officer and agency listed below.",
                self.styles["FieldValue"],
            ),
        ]
        story.append(self._with_margin_note(checkbox_section, "page5_automated"))
        story.append(Spacer(1, 12))

        # Police report details
        dept = police_report.get("department", "") if police_report else ""
        state = police_report.get("state", "") if police_report else ""
        report_num = police_report.get("report_number", "") if police_report else ""
        filing_date = police_report.get("filing_date", "") if police_report else ""
        officer = police_report.get("officer_name", "") if police_report else ""
        badge = police_report.get("badge_number", "") if police_report else ""
        officer_phone = police_report.get("officer_phone", "") if police_report else ""

        # Department and State
        dept_data = [
            [
                Paragraph(
                    f"<b>Law Enforcement Department:</b> {dept or '________________________'}",
                    self.styles["FieldValue"],
                ),
                Paragraph(
                    f"<b>State:</b> {state or '____'}", self.styles["FieldValue"]
                ),
            ]
        ]
        dept_table = Table(dept_data, colWidths=[4.5 * inch, 2 * inch])
        dept_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ]
            )
        )
        story.append(dept_table)
        story.append(Spacer(1, 6))

        # Report number and filing date
        report_data = [
            [
                Paragraph(
                    f"<b>Report Number:</b> {report_num or '________________'}",
                    self.styles["FieldValue"],
                ),
                Paragraph(
                    f"<b>Filing Date (mm/dd/yyyy):</b> {filing_date or '____/____/______'}",
                    self.styles["FieldValue"],
                ),
            ]
        ]
        report_table = Table(report_data, colWidths=[3.5 * inch, 3 * inch])
        report_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ]
            )
        )
        story.append(report_table)
        story.append(Spacer(1, 6))

        # Officer name and signature
        officer_data = [
            [
                Paragraph(
                    f"<b>Officer's Name (please print):</b> {officer or '____________________'}",
                    self.styles["FieldValue"],
                ),
                Paragraph(
                    "<b>Officer's Signature:</b> ____________________",
                    self.styles["FieldValue"],
                ),
            ]
        ]
        officer_table = Table(officer_data, colWidths=[3.5 * inch, 3 * inch])
        officer_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ]
            )
        )
        story.append(officer_table)
        story.append(Spacer(1, 6))

        # Badge number and phone
        badge_data = [
            [
                Paragraph(
                    f"<b>Badge Number:</b> {badge or '____________'}",
                    self.styles["FieldValue"],
                ),
                Paragraph(
                    f"<b>Phone Number:</b> {_format_phone(officer_phone) if officer_phone else '(____) ___-_____'}",
                    self.styles["FieldValue"],
                ),
            ]
        ]
        badge_table = Table(badge_data, colWidths=[3.5 * inch, 3 * inch])
        badge_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ]
            )
        )
        story.append(badge_table)
        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "Did the victim receive a copy of the report from the law enforcement officer?  [  ] Yes   OR   [  ] No",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                f"<b>Victim's FTC complaint number (if available):</b> {ftc_number or '________________________'}",
                self.styles["FieldValue"],
            )
        )

        return story

    def _build_page6(self, client: Dict[str, Any]) -> list:
        """Build Page 6: Signature."""
        story = []

        name = client.get("name", "")
        phone = client.get("phone", "")
        story.append(self._header(name, phone, 6))
        story.append(Spacer(1, 10))

        story.append(self._section_header("Signature"))
        story.append(Spacer(1, 6))

        story.append(
            Paragraph(
                "<b>As applicable, sign and date IN THE PRESENCE OF a law enforcement officer, a notary, or a witness.</b>",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                "(21) I certify that, to the best of my knowledge and belief, all of the information on and "
                "attached to this complaint is true, correct, and complete and made in good faith. I understand "
                "that this complaint or the information it contains may be made available to federal, state, "
                "and/or local law enforcement agencies for such action within their jurisdiction as they deem "
                "appropriate. I understand that knowingly making any false or fraudulent statement or "
                "representation to the government may violate federal, state, or local criminal statutes, "
                "and may result in a fine, imprisonment, or both.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 20))

        # Signature line
        today = datetime.now().strftime("%m/%d/%Y")
        sig_data = [
            ["_" * 45, "_" * 25],
            ["Signature", "Date Signed (mm/dd/yyyy)"],
        ]
        sig_table = Table(sig_data, colWidths=[4 * inch, 2.5 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTSIZE", (0, 1), (-1, 1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.gray),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]
            )
        )
        story.append(sig_table)
        story.append(Spacer(1, 20))

        # Affidavit section
        story.append(self._section_header("Your Affidavit"))
        story.append(Spacer(1, 6))

        story.append(
            Paragraph(
                "(22) If you do not choose to file a report with law enforcement, you may use this form as an "
                "Identity Theft Affidavit to prove to each of the companies where the thief misused your "
                "information that you are not responsible for the fraud. While many companies accept this "
                "affidavit, others require that you submit different forms. Check with each company to see if it "
                "accepts this form. You should also check to see if it requires notarization. If so, sign in the "
                "presence of a notary. If it does not, please have one witness (non-relative) sign that you "
                "completed and signed this Affidavit.",
                self.styles["FieldValue"],
            )
        )
        story.append(Spacer(1, 16))

        # Notary section
        story.append(Paragraph("<b>Notary:</b>", self.styles["FieldLabel"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph("_" * 60, self.styles["FieldValue"]))
        story.append(Spacer(1, 16))

        # Witness section
        story.append(Paragraph("<b>Witness:</b>", self.styles["FieldLabel"]))
        story.append(Spacer(1, 6))
        witness_data = [
            ["_" * 40, "_" * 40],
            ["Signature", "Printed Name"],
        ]
        witness_table1 = Table(witness_data, colWidths=[3.25 * inch, 3.25 * inch])
        witness_table1.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTSIZE", (0, 1), (-1, 1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.gray),
                ]
            )
        )
        story.append(witness_table1)
        story.append(Spacer(1, 10))

        witness_data2 = [
            ["_" * 40, "_" * 40],
            ["Date", "Telephone Number"],
        ]
        witness_table2 = Table(witness_data2, colWidths=[3.25 * inch, 3.25 * inch])
        witness_table2.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTSIZE", (0, 1), (-1, 1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.gray),
                ]
            )
        )
        story.append(witness_table2)

        return story


def generate_ftc_affidavit(
    client_data: Dict[str, Any],
    accounts: List[Dict[str, Any]],
    police_report: Optional[Dict[str, Any]] = None,
    ftc_number: Optional[str] = None,
) -> bytes:
    """
    Generate FTC Identity Theft Affidavit PDF.

    Args:
        client_data: Client info dict
        accounts: List of account dicts
        police_report: Police report info (optional)
        ftc_number: FTC complaint number (optional)

    Returns:
        PDF as bytes
    """
    generator = FTCAffidavitGenerator()
    return generator.generate(client_data, accounts, police_report, ftc_number)
