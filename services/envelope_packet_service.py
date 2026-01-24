"""
Envelope Packet Service for 5-Day Knock-Out Mailings

Creates organized, envelope-ready packets for each credit bureau containing:
- Cover sheet with bureau fraud address and document checklist
- Section 605B block request letter
- FTC Identity Theft Report
- Police report
- ID copy (placeholder for client to add)
- Proof of address (placeholder for client to add)

Integrates with SendCertifiedMail for automated mailing queue.
"""

import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from database import Client, SessionLocal
from services.sendcertified_service import (
    SendCertifiedService,
    get_sendcertified_service,
)

logger = logging.getLogger(__name__)


# Bureau fraud department addresses (for 5-Day Knockout under FCRA §605B)
BUREAU_FRAUD_ADDRESSES = {
    "Experian": {
        "name": "Experian Fraud Department",
        "street": "P.O. Box 9554",
        "city": "Allen",
        "state": "TX",
        "zip": "75013",
        "full": "P.O. Box 9554, Allen, TX 75013",
    },
    "Equifax": {
        "name": "Equifax Information Services LLC",
        "street": "P.O. Box 105069",
        "city": "Atlanta",
        "state": "GA",
        "zip": "30348",
        "full": "P.O. Box 105069, Atlanta, GA 30348",
    },
    "TransUnion": {
        "name": "TransUnion Fraud Victim Assistance Dept",
        "street": "P.O. Box 2000",
        "city": "Chester",
        "state": "PA",
        "zip": "19016",
        "full": "Fraud Victim Assistance Dept, P.O. Box 2000, Chester, PA 19016",
    },
}


class EnvelopePacketService:
    """
    Creates envelope-ready packets for 5-Day Knock-Out mailings.
    Each packet is organized per bureau with cover sheet and all required documents.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for documents"""
        self.styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor("#1a1a2e"),
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="BureauAddress",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=6,
                leftIndent=0,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ChecklistItem",
                parent=self.styles["Normal"],
                fontSize=11,
                alignment=TA_LEFT,
                spaceAfter=8,
                leftIndent=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ImportantNote",
                parent=self.styles["Normal"],
                fontSize=10,
                alignment=TA_LEFT,
                backColor=colors.HexColor("#fff3cd"),
                borderPadding=10,
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#0066cc"),
                spaceBefore=15,
                spaceAfter=10,
            )
        )

    def create_cover_sheet(
        self,
        bureau: str,
        client_name: str,
        accounts_disputed: List[Dict[str, Any]],
        packet_date: Optional[datetime] = None,
    ) -> bytes:
        """
        Create a cover sheet for a bureau packet.

        Args:
            bureau: Bureau name (Experian, Equifax, TransUnion)
            client_name: Client's full name
            accounts_disputed: List of accounts being disputed
            packet_date: Date for the packet (defaults to today)

        Returns:
            PDF bytes for the cover sheet
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        elements = []
        packet_date = packet_date or datetime.now()
        bureau_info = BUREAU_FRAUD_ADDRESSES.get(bureau, {})

        # Header
        elements.append(Paragraph(f"5-DAY KNOCK-OUT PACKET", self.styles["CoverTitle"]))
        elements.append(
            Paragraph(
                f"<b>FCRA §605B Identity Theft Block Request</b>",
                ParagraphStyle(
                    name="Subtitle",
                    parent=self.styles["Normal"],
                    fontSize=14,
                    alignment=TA_CENTER,
                    spaceAfter=20,
                ),
            )
        )
        elements.append(
            HRFlowable(
                width="100%",
                thickness=2,
                color=colors.HexColor("#0066cc"),
                spaceAfter=20,
            )
        )

        # Bureau Address Section
        elements.append(Paragraph("SEND TO:", self.styles["SectionHeader"]))
        elements.append(
            Paragraph(
                f"<b>{bureau_info.get('name', bureau)}</b>",
                self.styles["BureauAddress"],
            )
        )
        elements.append(
            Paragraph(bureau_info.get("street", ""), self.styles["BureauAddress"])
        )
        elements.append(
            Paragraph(
                f"{bureau_info.get('city', '')}, {bureau_info.get('state', '')} {bureau_info.get('zip', '')}",
                self.styles["BureauAddress"],
            )
        )
        elements.append(Spacer(1, 20))

        # Client Info
        elements.append(Paragraph("FROM:", self.styles["SectionHeader"]))
        elements.append(
            Paragraph(f"<b>{client_name}</b>", self.styles["BureauAddress"])
        )
        elements.append(
            Paragraph(
                f"Date: {packet_date.strftime('%B %d, %Y')}",
                self.styles["BureauAddress"],
            )
        )
        elements.append(Spacer(1, 20))

        # Document Checklist
        elements.append(Paragraph("DOCUMENT CHECKLIST:", self.styles["SectionHeader"]))
        elements.append(
            Paragraph(
                "<i>Verify all documents are included before mailing:</i>",
                self.styles["Normal"],
            )
        )
        elements.append(Spacer(1, 10))

        checklist_items = [
            ("1.", "Section 605B Block Request Letter", True),
            ("2.", "FTC Identity Theft Report (Affidavit)", True),
            ("3.", "Police Report (or FTC Report if no police report)", True),
            ("4.", "Copy of Government-Issued ID", False),
            ("5.", "Proof of Address (utility bill, bank statement)", False),
        ]

        checklist_data = []
        for num, item, included in checklist_items:
            checkbox = "☑" if included else "☐"
            status = "(INCLUDED)" if included else "(ADD BEFORE MAILING)"
            checklist_data.append([checkbox, f"{num} {item}", status])

        checklist_table = Table(
            checklist_data,
            colWidths=[0.4 * inch, 4 * inch, 2 * inch],
        )
        checklist_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(checklist_table)
        elements.append(Spacer(1, 20))

        # Accounts Being Disputed
        elements.append(Paragraph("ACCOUNTS DISPUTED:", self.styles["SectionHeader"]))

        if accounts_disputed:
            account_data = [["#", "Creditor/Account", "Type", "Account #"]]
            for i, acct in enumerate(accounts_disputed[:15], 1):  # Limit to 15 accounts
                account_data.append(
                    [
                        str(i),
                        acct.get("creditor", "Unknown")[:30],
                        acct.get("type", "Account")[:15],
                        acct.get("account_number", "N/A")[:12],
                    ]
                )

            account_table = Table(
                account_data,
                colWidths=[0.5 * inch, 3 * inch, 1.5 * inch, 1.5 * inch],
            )
            account_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(account_table)
        else:
            elements.append(
                Paragraph(
                    "See attached letter for disputed accounts.", self.styles["Normal"]
                )
            )

        elements.append(Spacer(1, 25))

        # Important Notes
        elements.append(Paragraph("IMPORTANT NOTES:", self.styles["SectionHeader"]))
        notes = [
            "<b>DEADLINE:</b> Under FCRA §605B, the bureau must BLOCK these items within 4 BUSINESS DAYS of receiving this packet with all required documents.",
            "<b>CERTIFIED MAIL:</b> Send via Certified Mail with Return Receipt Requested. Keep tracking number for your records.",
            "<b>COPIES:</b> Keep copies of ALL documents for your records before mailing.",
            "<b>ID REQUIREMENTS:</b> Include a clear copy of your driver's license, state ID, or passport.",
            "<b>PROOF OF ADDRESS:</b> Include a recent utility bill, bank statement, or other official document showing your current address.",
        ]

        for note in notes:
            elements.append(
                Paragraph(
                    f"• {note}",
                    ParagraphStyle(
                        name="NoteItem",
                        parent=self.styles["Normal"],
                        fontSize=10,
                        spaceAfter=8,
                        leftIndent=15,
                    ),
                )
            )

        elements.append(Spacer(1, 30))

        # Footer
        elements.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#cccccc"),
                spaceAfter=10,
            )
        )
        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 5-Day Knock-Out Strategy | FCRA §605B",
                ParagraphStyle(
                    name="Footer",
                    parent=self.styles["Normal"],
                    fontSize=8,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor("#888888"),
                ),
            )
        )

        doc.build(elements)
        return buffer.getvalue()

    def create_placeholder_page(
        self,
        title: str,
        instructions: List[str],
    ) -> bytes:
        """
        Create a placeholder page for documents the client needs to add.

        Args:
            title: Title of the placeholder (e.g., "GOVERNMENT ID COPY")
            instructions: List of instruction strings

        Returns:
            PDF bytes for the placeholder page
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        elements = []

        # Border box
        elements.append(Spacer(1, 2 * inch))
        elements.append(
            Paragraph(
                f"<b>{title}</b>",
                ParagraphStyle(
                    name="PlaceholderTitle",
                    parent=self.styles["Heading1"],
                    fontSize=24,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor("#cc0000"),
                ),
            )
        )
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph(
                "⚠️ REPLACE THIS PAGE WITH YOUR DOCUMENT ⚠️",
                ParagraphStyle(
                    name="Warning",
                    parent=self.styles["Normal"],
                    fontSize=16,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor("#cc6600"),
                ),
            )
        )
        elements.append(Spacer(1, 40))

        for instruction in instructions:
            elements.append(
                Paragraph(
                    f"• {instruction}",
                    ParagraphStyle(
                        name="Instruction",
                        parent=self.styles["Normal"],
                        fontSize=12,
                        alignment=TA_LEFT,
                        spaceAfter=12,
                        leftIndent=40,
                    ),
                )
            )

        doc.build(elements)
        return buffer.getvalue()

    def create_bureau_packet(
        self,
        bureau: str,
        client: Client,
        accounts: List[Dict[str, Any]],
        letter_content: str,
        ftc_report_content: Optional[str] = None,
        police_report_content: Optional[str] = None,
        include_placeholders: bool = True,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Create a complete envelope packet for a single bureau.

        Args:
            bureau: Bureau name (Experian, Equifax, TransUnion)
            client: Client object
            accounts: List of accounts to dispute for this bureau
            letter_content: The §605B letter content (HTML or text)
            ftc_report_content: FTC report content (optional)
            police_report_content: Police report content (optional)
            include_placeholders: Whether to include placeholder pages for ID/address

        Returns:
            Tuple of (PDF bytes, metadata dict)
        """
        from PyPDF2 import PdfMerger, PdfReader

        merger = PdfMerger()
        documents_included = []

        # 1. Cover Sheet
        cover_pdf = self.create_cover_sheet(
            bureau=bureau,
            client_name=client.name,
            accounts_disputed=accounts,
        )
        merger.append(io.BytesIO(cover_pdf))
        documents_included.append("Cover Sheet")

        # 2. §605B Letter (convert HTML to PDF)
        letter_pdf = self._html_to_pdf(letter_content, title=f"605B Letter - {bureau}")
        merger.append(io.BytesIO(letter_pdf))
        documents_included.append("§605B Block Request Letter")

        # 3. FTC Report (if provided)
        if ftc_report_content:
            ftc_pdf = self._html_to_pdf(
                ftc_report_content, title="FTC Identity Theft Report"
            )
            merger.append(io.BytesIO(ftc_pdf))
            documents_included.append("FTC Identity Theft Report")

        # 4. Police Report (if provided)
        if police_report_content:
            police_pdf = self._html_to_pdf(police_report_content, title="Police Report")
            merger.append(io.BytesIO(police_pdf))
            documents_included.append("Police Report")

        # 5. ID Placeholder
        if include_placeholders:
            id_placeholder = self.create_placeholder_page(
                title="GOVERNMENT-ISSUED ID COPY",
                instructions=[
                    "Remove this page and replace with a clear copy of your:",
                    "  - Driver's License, OR",
                    "  - State ID Card, OR",
                    "  - U.S. Passport",
                    "",
                    "The ID must show your full name and photo.",
                    "Make sure all text is legible in the copy.",
                ],
            )
            merger.append(io.BytesIO(id_placeholder))
            documents_included.append("ID Placeholder (NEEDS CLIENT DOCUMENT)")

        # 6. Proof of Address Placeholder
        if include_placeholders:
            address_placeholder = self.create_placeholder_page(
                title="PROOF OF ADDRESS",
                instructions=[
                    "Remove this page and replace with a recent document showing your address:",
                    "  - Utility bill (electric, gas, water) dated within 60 days",
                    "  - Bank or credit card statement dated within 60 days",
                    "  - Government correspondence",
                    "",
                    "The document must show your full name and current address.",
                    "The address must match what's on your credit report.",
                ],
            )
            merger.append(io.BytesIO(address_placeholder))
            documents_included.append(
                "Address Proof Placeholder (NEEDS CLIENT DOCUMENT)"
            )

        # Merge all PDFs
        output = io.BytesIO()
        merger.write(output)
        merger.close()

        bureau_info = BUREAU_FRAUD_ADDRESSES.get(bureau, {})

        metadata = {
            "bureau": bureau,
            "client_id": client.id,
            "client_name": client.name,
            "recipient_name": bureau_info.get("name", bureau),
            "recipient_address": {
                "street": bureau_info.get("street", ""),
                "city": bureau_info.get("city", ""),
                "state": bureau_info.get("state", ""),
                "zip": bureau_info.get("zip", ""),
            },
            "accounts_count": len(accounts),
            "documents_included": documents_included,
            "page_count": self._count_pages(output.getvalue()),
            "created_at": datetime.now().isoformat(),
            "needs_client_documents": include_placeholders,
        }

        return output.getvalue(), metadata

    def create_all_bureau_packets(
        self,
        client: Client,
        accounts_by_bureau: Dict[str, List[Dict[str, Any]]],
        letters_by_bureau: Dict[str, str],
        ftc_report_content: Optional[str] = None,
        police_report_content: Optional[str] = None,
    ) -> Dict[str, Tuple[bytes, Dict[str, Any]]]:
        """
        Create packets for all bureaus that have accounts to dispute.

        Args:
            client: Client object
            accounts_by_bureau: Dict mapping bureau name to list of accounts
            letters_by_bureau: Dict mapping bureau name to letter content
            ftc_report_content: FTC report (shared across all bureaus)
            police_report_content: Police report (shared across all bureaus)

        Returns:
            Dict mapping bureau name to (PDF bytes, metadata)
        """
        packets = {}

        for bureau in ["Experian", "Equifax", "TransUnion"]:
            accounts = accounts_by_bureau.get(bureau, [])
            letter_content = letters_by_bureau.get(bureau)

            if accounts and letter_content:
                pdf_bytes, metadata = self.create_bureau_packet(
                    bureau=bureau,
                    client=client,
                    accounts=accounts,
                    letter_content=letter_content,
                    ftc_report_content=ftc_report_content,
                    police_report_content=police_report_content,
                )
                packets[bureau] = (pdf_bytes, metadata)
                logger.info(
                    f"Created packet for {bureau}: {metadata['page_count']} pages, {len(accounts)} accounts"
                )

        return packets

    def queue_to_sendcertified(
        self,
        pdf_bytes: bytes,
        metadata: Dict[str, Any],
        client_id: int,
    ) -> Dict[str, Any]:
        """
        Queue a packet to SendCertifiedMail for automated mailing.

        Args:
            pdf_bytes: The complete packet PDF
            metadata: Packet metadata including recipient info
            client_id: Client ID for tracking

        Returns:
            Dict with success status and order details
        """
        service = get_sendcertified_service()

        if not service.is_configured():
            return {
                "success": False,
                "error": "SendCertified is not configured. Please configure API credentials first.",
                "queued": False,
            }

        result = service.create_mailing(
            recipient=metadata["recipient_name"],
            address=metadata["recipient_address"],
            document_content=pdf_bytes,
            mail_class="certified_return_receipt",
            client_id=client_id,
            letter_type="5day_knockout",
            bureau=metadata["bureau"],
        )

        return {
            "success": result["success"],
            "error": result.get("error"),
            "queued": result["success"],
            "tracking_number": result.get("tracking_number"),
            "order_id": result.get("order_id"),
            "label_id": result.get("label_id"),
            "estimated_delivery": result.get("estimated_delivery"),
            "cost": result.get("cost"),
        }

    def queue_all_packets(
        self,
        packets: Dict[str, Tuple[bytes, Dict[str, Any]]],
        client_id: int,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Queue all bureau packets to SendCertifiedMail.

        Args:
            packets: Dict from create_all_bureau_packets
            client_id: Client ID for tracking

        Returns:
            Dict mapping bureau name to queue result
        """
        results = {}

        for bureau, (pdf_bytes, metadata) in packets.items():
            result = self.queue_to_sendcertified(
                pdf_bytes=pdf_bytes,
                metadata=metadata,
                client_id=client_id,
            )
            results[bureau] = result

            if result["success"]:
                logger.info(
                    f"Queued {bureau} packet: tracking {result.get('tracking_number')}"
                )
            else:
                logger.error(f"Failed to queue {bureau} packet: {result.get('error')}")

        return results

    def _html_to_pdf(self, html_content: str, title: str = "Document") -> bytes:
        """Convert HTML content to PDF"""
        from bs4 import BeautifulSoup

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        elements = []

        # Parse HTML and convert to reportlab elements
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")

        # Split into paragraphs and add
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if para:
                # Check if it looks like a heading
                if len(para) < 60 and para.isupper():
                    elements.append(Paragraph(para, self.styles["Heading2"]))
                elif para.startswith("RE:") or para.startswith("Date:"):
                    elements.append(Paragraph(para, self.styles["Normal"]))
                else:
                    elements.append(
                        Paragraph(para.replace("\n", "<br/>"), self.styles["Normal"])
                    )
                elements.append(Spacer(1, 6))

        doc.build(elements)
        return buffer.getvalue()

    def _count_pages(self, pdf_bytes: bytes) -> int:
        """Count pages in a PDF"""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(pdf_bytes))
            return len(reader.pages)
        except Exception:
            return 0


def get_envelope_packet_service() -> EnvelopePacketService:
    """Factory function to get EnvelopePacketService instance"""
    return EnvelopePacketService()
