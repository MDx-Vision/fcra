"""
Round-Specific Letter Generator with RLPP Bundling
Generates R1-R4 dispute letters with escalating tone and strategy.
"""

from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Spacer

from .base import BasePDFBuilder


class RoundLetterBuilder(BasePDFBuilder):
    """
    Generates round-specific dispute letters with RLPP bundling strategy.

    R1: Initial Disputes - Strong opening with RLPP bundling (75-85% success)
    R2: MOV Demands - Cushman-style tangible ledger requests
    R3: Regulatory Complaints - CFPB, FTC, State AG
    R4: Pre-Arbitration - Final demands + AAA draft
    """

    BUREAU_ADDRESSES = {
        "Equifax": {
            "name": "Equifax Information Services LLC",
            "address": "P.O. Box 740256",
            "city": "Atlanta, GA 30374",
        },
        "Experian": {
            "name": "Experian",
            "address": "P.O. Box 4500",
            "city": "Allen, TX 75013",
        },
        "TransUnion": {
            "name": "TransUnion LLC",
            "address": "P.O. Box 2000",
            "city": "Chester, PA 19016",
        },
    }

    def generate_round_1(self, output_path, client_data, bureau):
        """Generate Round 1 initial dispute letter with RLPP bundling"""
        doc = self.create_document(output_path)
        story = []

        self._add_letter_header(story, client_data, bureau)
        self._add_r1_body(story, client_data, bureau)
        self._add_letter_footer(story, client_data)

        doc.build(story)
        return output_path

    def generate_round_2(self, output_path, client_data, bureau):
        """Generate Round 2 MOV demand letter"""
        doc = self.create_document(output_path)
        story = []

        self._add_letter_header(story, client_data, bureau)
        self._add_r2_body(story, client_data, bureau)
        self._add_letter_footer(story, client_data)

        doc.build(story)
        return output_path

    def generate_round_3(self, output_path, client_data, bureau):
        """Generate Round 3 regulatory complaint"""
        doc = self.create_document(output_path)
        story = []

        self._add_letter_header(story, client_data, bureau)
        self._add_r3_body(story, client_data, bureau)
        self._add_letter_footer(story, client_data)

        doc.build(story)
        return output_path

    def generate_round_4(self, output_path, client_data, bureau):
        """Generate Round 4 pre-arbitration demand"""
        doc = self.create_document(output_path)
        story = []

        self._add_letter_header(story, client_data, bureau)
        self._add_r4_body(story, client_data, bureau)
        self._add_letter_footer(story, client_data)

        doc.build(story)
        return output_path

    def generate_mov_demand(self, output_path, client_data, bureau):
        """Generate standalone Method of Verification demand"""
        return self.generate_round_2(output_path, client_data, bureau)

    def generate_cfpb_complaint(self, output_path, client_data, bureau):
        """Generate CFPB complaint template"""
        doc = self.create_document(output_path)
        story = []

        self._add_cfpb_header(story, client_data)
        self._add_cfpb_body(story, client_data, bureau)

        doc.build(story)
        return output_path

    def _add_letter_header(self, story, client_data, bureau):
        """Add standard letter header"""
        client_name = client_data.get("client_name", "Consumer")
        today = datetime.now().strftime("%B %d, %Y")

        self.add_paragraph(story, client_name, self.body_style)

        address = client_data.get("address", {})
        if address:
            self.add_paragraph(story, address.get("street", ""))
            self.add_paragraph(
                story,
                f"{address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}",
            )

        story.append(Spacer(1, 0.3 * inch))
        self.add_paragraph(story, today)
        story.append(Spacer(1, 0.3 * inch))

        bureau_info = self.BUREAU_ADDRESSES.get(bureau, {})
        self.add_paragraph(story, bureau_info.get("name", bureau))
        self.add_paragraph(story, bureau_info.get("address", ""))
        self.add_paragraph(story, bureau_info.get("city", ""))

        story.append(Spacer(1, 0.4 * inch))

        ssn_last4 = client_data.get("ssn_last_four", "XXXX")
        self.add_paragraph(story, f"Re: Formal Dispute - SSN ending in {ssn_last4}")
        story.append(Spacer(1, 0.3 * inch))

        self.add_paragraph(story, f"To Whom It May Concern:")
        story.append(Spacer(1, 0.2 * inch))

    def _add_letter_footer(self, story, client_data):
        """Add standard letter footer"""
        client_name = client_data.get("client_name", "Consumer")

        story.append(Spacer(1, 0.4 * inch))
        self.add_paragraph(story, "Sincerely,")
        story.append(Spacer(1, 0.5 * inch))
        self.add_paragraph(story, "_______________________________________")
        self.add_paragraph(story, client_name)
        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(story, "Enclosures:")
        enclosures = [
            "Copy of government-issued identification",
            "Proof of current address",
            "Supporting documentation as referenced",
        ]
        self.add_bullet_list(story, enclosures)

    def _add_r1_body(self, story, client_data, bureau):
        """Add Round 1 dispute letter body with RLPP bundling"""
        violations = client_data.get("violations", [])
        bureau_violations = [
            v for v in violations if v.get("bureau", "").lower() == bureau.lower()
        ]

        self.add_paragraph(
            story,
            "I am writing pursuant to my rights under the Fair Credit Reporting Act, 15 U.S.C. "
            "Section 1681 et seq., to formally dispute the following information appearing on my "
            "credit report, which I believe to be inaccurate, incomplete, misleading, and/or "
            "unverifiable.",
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(
            story,
            "<b>LEGAL NOTICE:</b> Under Section 611 of the FCRA, you are required to conduct a "
            "reasonable investigation of my dispute and remove or modify any information that "
            "cannot be verified as accurate. Failure to do so within thirty (30) days will "
            "constitute willful noncompliance, exposing your company to statutory and punitive "
            "damages under Sections 616 and 617 of the FCRA.",
            self.body_blue_style,
        )

        story.append(Spacer(1, 0.3 * inch))
        self.add_section_header(story, "DISPUTED ITEMS - RLPP BUNDLE", level=2)

        if bureau_violations:
            for i, v in enumerate(bureau_violations, 1):
                self.add_section_header(
                    story,
                    f"Item {i}: {v.get('account_name', 'Unknown Account')}",
                    level=3,
                )

                dispute_text = f"""
                FCRA Violation: {v.get('fcra_section', 'N/A')} - {v.get('violation_type', 'Unknown')}

                Reason for Dispute: {v.get('description', 'Information is inaccurate, incomplete, or unverifiable.')}

                Requested Action: Immediately delete this tradeline or provide documentary evidence proving the accuracy of ALL data elements including dates, balances, payment history, and account status.
                """
                self.add_paragraph(story, dispute_text)
                story.append(Spacer(1, 0.1 * inch))
        else:
            self.add_paragraph(
                story,
                "[No specific violations identified for this bureau - review required]",
            )

        story.append(Spacer(1, 0.3 * inch))

        self.add_section_header(story, "DEMANDS UNDER FCRA", level=2)

        demands = [
            "Conduct a reasonable reinvestigation of all disputed items within 30 days per Section 611(a)(1)",
            "Contact each information furnisher and verify accuracy of all disputed data elements",
            "Delete or modify any information that cannot be independently verified",
            "Provide me with written notice of the results within 5 business days of completion",
            "Provide a free copy of my updated credit report reflecting any changes",
            "Provide the Method of Verification used for any items not deleted, per Section 611(a)(7)",
        ]
        self.add_numbered_list(story, demands)

        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(
            story,
            "<b>WARNING:</b> Failure to comply with these requirements will be documented and may "
            "result in: (1) filing of complaints with the CFPB, FTC, and State Attorney General; "
            "(2) formal demand letters seeking statutory and punitive damages; and (3) legal action "
            "in federal court to enforce my rights under the FCRA.",
            self.warning_style,
        )

    def _add_r2_body(self, story, client_data, bureau):
        """Add Round 2 MOV demand letter body"""
        violations = client_data.get("violations", [])
        bureau_violations = [
            v for v in violations if v.get("bureau", "").lower() == bureau.lower()
        ]
        previous_dispute_date = client_data.get(
            "previous_dispute_date", "previous dispute"
        )

        self.add_paragraph(
            story,
            f"I am writing as a follow-up to my formal dispute submitted on {previous_dispute_date}. "
            "I have received your investigation results; however, you have failed to delete the "
            "disputed items despite my demonstration that the information is inaccurate, incomplete, "
            "or unverifiable.",
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(
            story, "METHOD OF VERIFICATION DEMAND (Cushman v. TransUnion)", level=2
        )

        self.add_paragraph(
            story,
            "Pursuant to 15 U.S.C. Section 1681i(a)(7) and the Ninth Circuit's holding in "
            "<i>Cushman v. TransUnion Corp.</i>, I hereby demand that you provide me with the "
            "complete method of verification used to investigate each disputed item, including:",
        )

        mov_demands = [
            "The name, address, and telephone number of each furnisher contacted",
            "The specific documents, records, or ledgers reviewed",
            "The date and method of each verification attempt",
            "The identity of the person(s) who conducted the investigation",
            "Copies of any tangible documentation relied upon to verify accuracy",
            "The specific Metro 2 data fields that were verified and how",
        ]
        self.add_numbered_list(story, mov_demands)

        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(
            story,
            "<b>TANGIBLE LEDGER DEMAND:</b> A mere confirmation from the furnisher that the "
            "information is 'accurate' does NOT constitute a reasonable investigation. You must "
            "obtain and review TANGIBLE documentation - original contracts, payment ledgers, "
            "account statements, and other physical evidence proving the accuracy of each "
            "disputed data element.",
            self.body_blue_style,
        )

        story.append(Spacer(1, 0.2 * inch))

        if bureau_violations:
            self.add_section_header(
                story, "ITEMS REQUIRING METHOD OF VERIFICATION", level=2
            )

            for i, v in enumerate(bureau_violations[:10], 1):
                self.add_paragraph(
                    story,
                    f"{i}. {v.get('account_name', 'Unknown')} - {v.get('violation_type', 'Disputed')}",
                )

        story.append(Spacer(1, 0.3 * inch))

        self.add_paragraph(
            story,
            "<b>LEGAL NOTICE:</b> Your failure to provide the requested Method of Verification "
            "information, or your reliance on 'automated' verification without obtaining tangible "
            "documentation, will constitute willful noncompliance with the FCRA. This will expose "
            "your company to statutory damages of $100-$1,000 per violation, punitive damages, "
            "and attorney fees under 15 U.S.C. Sections 1681n and 1681o.",
            self.warning_style,
        )

    def _add_r3_body(self, story, client_data, bureau):
        """Add Round 3 regulatory complaint template"""
        violations = client_data.get("violations", [])

        self.add_paragraph(
            story,
            "This letter constitutes formal notice that I will be filing complaints with federal "
            "and state regulatory agencies regarding your continued willful noncompliance with "
            "the Fair Credit Reporting Act.",
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "HISTORY OF NONCOMPLIANCE", level=2)

        timeline = [
            "Round 1 Dispute: Submitted formal dispute identifying inaccurate information",
            "Bureau Response: Failed to conduct reasonable investigation",
            "Round 2 MOV Demand: Requested method of verification and tangible documentation",
            "Bureau Response: Failed to provide required verification information",
        ]
        self.add_numbered_list(story, timeline)

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "REGULATORY COMPLAINTS TO BE FILED", level=2)

        self.add_paragraph(
            story,
            "Within the next 10 days, I will be submitting formal complaints to the following "
            "regulatory agencies documenting your FCRA violations:",
        )

        agencies = [
            "Consumer Financial Protection Bureau (CFPB) - consumerfinance.gov/complaint",
            "Federal Trade Commission (FTC) - reportfraud.ftc.gov",
            "State Attorney General Consumer Protection Division",
        ]
        self.add_bullet_list(story, agencies)

        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(
            story,
            "<b>FINAL OPPORTUNITY TO COMPLY:</b> Before filing these complaints, I am giving "
            "you ONE FINAL OPPORTUNITY to delete the disputed inaccurate information. You have "
            "15 days from the date of this letter to remove the items listed below. If the items "
            "are not deleted, I will proceed with regulatory complaints AND prepare for legal action.",
            self.body_blue_style,
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "VIOLATIONS SUMMARY", level=2)

        bureau_violations = [
            v for v in violations if v.get("bureau", "").lower() == bureau.lower()
        ]
        if bureau_violations:
            for i, v in enumerate(bureau_violations[:8], 1):
                self.add_paragraph(
                    story,
                    f"{i}. {v.get('account_name', 'Unknown')} - {v.get('fcra_section', 'N/A')}: {v.get('violation_type', '')}",
                )

    def _add_r4_body(self, story, client_data, bureau):
        """Add Round 4 pre-arbitration demand"""
        violations = client_data.get("violations", [])
        damages = client_data.get("damages", {})

        self.add_paragraph(
            story,
            "This letter constitutes a FORMAL PRE-LITIGATION DEMAND and notice of my intent "
            "to pursue all available legal remedies for your continued willful violations of "
            "the Fair Credit Reporting Act.",
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "STATEMENT OF FACTS", level=2)

        self.add_paragraph(
            story,
            "Over the course of multiple dispute rounds, your company has demonstrated a "
            "pattern of willful noncompliance with the FCRA by: (1) failing to conduct reasonable "
            "investigations of disputed information; (2) refusing to provide Method of Verification "
            "documentation; (3) continuing to report information that is inaccurate, incomplete, "
            "and/or unverifiable; and (4) causing ongoing concrete harm to me as a consumer.",
        )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "DAMAGES CLAIM", level=2)

        if damages:
            total_exposure = damages.get("total_exposure", 0)
            settlement_target = damages.get("settlement_target", 0)

            self.add_paragraph(
                story,
                f"Based on my analysis, my total damages claim against your company is valued at "
                f"approximately {self.format_currency(total_exposure)}, including:",
            )

            damages_list = [
                f"Actual Damages: {self.format_currency(damages.get('actual_damages_total', 0))}",
                f"Statutory Damages: {self.format_currency(damages.get('statutory_damages_total', 0))}",
                f"Punitive Damages: {self.format_currency(damages.get('punitive_damages_amount', 0))}",
                f"Estimated Attorney Fees: {self.format_currency(damages.get('attorney_fees_projection', 0))}",
            ]
            self.add_bullet_list(story, damages_list)

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "SETTLEMENT DEMAND", level=2)

        if damages:
            self.add_paragraph(
                story,
                f"I am prepared to resolve this matter for {self.format_currency(damages.get('settlement_target', 0))} "
                f"if paid within 30 days of this letter, in exchange for: (1) immediate deletion of "
                f"all disputed items; (2) placement of a permanent suppression on my file; and "
                f"(3) payment of the settlement amount.",
                self.body_blue_style,
            )

        story.append(Spacer(1, 0.2 * inch))

        self.add_section_header(story, "INTENT TO FILE", level=2)

        self.add_paragraph(
            story,
            "<b>IF THIS DEMAND IS NOT SATISFIED WITHIN 30 DAYS</b>, I will file a demand for "
            "arbitration with the American Arbitration Association under the FCRA's arbitration "
            "provisions, or alternatively, file a complaint in federal district court. "
            "This is your final opportunity to resolve this matter without litigation.",
            self.warning_style,
        )

        violations_count = len(
            [v for v in violations if v.get("bureau", "").lower() == bureau.lower()]
        )
        self.add_paragraph(
            story, f"\nNumber of documented FCRA violations: {violations_count}"
        )

    def _add_cfpb_header(self, story, client_data):
        """Add CFPB complaint header"""
        self.add_section_header(story, "CFPB COMPLAINT TEMPLATE", level=1)
        self.add_paragraph(
            story, f"Complainant: {client_data.get('client_name', 'Consumer')}"
        )
        self.add_paragraph(story, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        story.append(Spacer(1, 0.3 * inch))

    def _add_cfpb_body(self, story, client_data, bureau):
        """Add CFPB complaint body"""
        violations = client_data.get("violations", [])

        self.add_section_header(story, "Company Complained About", level=2)
        bureau_info = self.BUREAU_ADDRESSES.get(bureau, {})
        self.add_paragraph(story, bureau_info.get("name", bureau))

        self.add_section_header(story, "Issue Category", level=2)
        self.add_paragraph(
            story,
            "Credit Reporting - Improper use of your report / Problem with investigation",
        )

        self.add_section_header(story, "Description of Problem", level=2)

        desc = f"""
        I have submitted multiple disputes to {bureau} regarding inaccurate information on my credit
        report. Despite providing documentation and specific identification of errors, {bureau} has
        failed to conduct a reasonable investigation as required by Section 611 of the Fair Credit
        Reporting Act (15 U.S.C. 1681i).

        After my initial dispute, {bureau} responded by claiming the disputed items were "verified"
        without providing any evidence of a meaningful investigation. When I requested the Method
        of Verification pursuant to Section 611(a)(7), {bureau} either ignored my request or provided
        generic responses that did not address my specific concerns.

        This pattern of behavior constitutes willful noncompliance with the FCRA and has caused me
        concrete harm including [describe specific harm - credit denials, higher interest rates, etc.].
        """
        self.add_paragraph(story, desc)

        self.add_section_header(story, "Violations Documented", level=2)

        bureau_violations = [
            v for v in violations if v.get("bureau", "").lower() == bureau.lower()
        ]
        for i, v in enumerate(bureau_violations[:10], 1):
            self.add_paragraph(
                story,
                f"{i}. {v.get('account_name', 'Unknown')} - {v.get('fcra_section', 'N/A')}",
            )

        self.add_section_header(story, "Desired Resolution", level=2)

        resolutions = [
            "Immediate deletion of all inaccurately reported information",
            "Written confirmation that items have been deleted from all databases",
            "Provision of the Method of Verification used in previous investigations",
            "Monetary compensation for damages caused by continued violations",
        ]
        self.add_numbered_list(story, resolutions)
