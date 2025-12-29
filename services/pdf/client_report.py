"""
40-50 Page Comprehensive Client Report Generator
Matches V2.8 format with full FCRA analysis sections.
"""

from datetime import datetime

from reportlab.lib.colors import HexColor, lightgrey
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Spacer, Table, TableStyle

from .base import BasePDFBuilder


class ClientReportBuilder(BasePDFBuilder):
    """
    Generates comprehensive 40-50 page client reports matching V2.8 format.

    Sections:
    1. Cover Page & Table of Contents
    2. Executive Summary (2-3 pages)
    3. Understanding Your FCRA Rights (3-4 pages)
    4. Credit Bureau Analysis (per bureau, 3-5 pages each)
    5. Violation Categories (detailed breakdown by FCRA section, 8-12 pages)
    6. Account-by-Account Analysis (5-10 pages)
    7. Legal Framework (3-4 pages)
    8. Damages Assessment (3-5 pages)
    9. Strategic Recommendations (2-3 pages)
    10. Next Steps (1-2 pages)
    11. Appendix (supporting documents)
    """

    def generate(self, output_path, client_data):
        """
        Generate comprehensive client report.

        Args:
            output_path: Where to save the PDF
            client_data: Dict containing:
                - client_name: Client's full name
                - report_date: Date of report
                - credit_scores: Dict with equifax, experian, transunion scores
                - violations: List of violation dicts
                - standing: Standing dict
                - damages: Damages dict
                - case_score: CaseScore dict
                - accounts: List of account dicts for account-by-account
                - dispute_round: Current dispute round
        """
        doc = self.create_document(output_path)
        story = []

        client_name = client_data.get("client_name", "Client")
        report_date = client_data.get(
            "report_date", datetime.now().strftime("%B %d, %Y")
        )

        self._add_cover_page(story, client_name, report_date)
        self._add_table_of_contents(story)
        self._add_executive_summary(story, client_data)
        self._add_fcra_rights(story)
        self._add_bureau_analysis(story, client_data)
        self._add_violation_categories(story, client_data)
        self._add_account_analysis(story, client_data)
        self._add_legal_framework(story)
        self._add_damages_assessment(story, client_data)
        self._add_strategic_recommendations(story, client_data)
        self._add_next_steps(story, client_data)
        self._add_appendix(story, client_data)

        doc.build(story)
        return output_path

    def _add_cover_page(self, story, client_name, report_date):
        """Add professional cover page"""
        self.add_cover_page(
            story, "COMPREHENSIVE CREDIT ANALYSIS REPORT", client_name, report_date
        )

    def _add_table_of_contents(self, story):
        """Add table of contents"""
        self.add_section_header(story, "TABLE OF CONTENTS", level=1)

        toc_items = [
            ("1. Executive Summary", "Overview of findings and recommended actions"),
            (
                "2. Understanding Your FCRA Rights",
                "Your legal protections under federal law",
            ),
            ("3. Credit Bureau Analysis", "Bureau-by-bureau breakdown of your reports"),
            ("4. Violation Categories", "Detailed analysis of FCRA violations found"),
            ("5. Account-by-Account Analysis", "Individual account review and issues"),
            ("6. Legal Framework", "Relevant laws and precedents"),
            ("7. Damages Assessment", "Calculation of potential recovery"),
            ("8. Strategic Recommendations", "Recommended dispute strategy"),
            ("9. Next Steps", "Action items and timeline"),
            ("10. Appendix", "Supporting documentation"),
        ]

        for title, desc in toc_items:
            self.add_paragraph(story, f"<b>{title}</b> - {desc}")

        story.append(PageBreak())

    def _add_executive_summary(self, story, client_data):
        """Add 2-3 page executive summary"""
        self.add_section_header(story, "SECTION 1: EXECUTIVE SUMMARY", level=1)

        violations = client_data.get("violations", [])
        standing = client_data.get("standing", {})
        damages = client_data.get("damages", {})
        case_score = client_data.get("case_score", {})

        self.add_paragraph(
            story, f"Dear {client_data.get('client_name', 'Valued Client').split()[0]},"
        )
        story.append(Spacer(1, 0.2 * inch))

        self.add_paragraph(
            story,
            "This comprehensive analysis of your credit reports from all three major credit bureaus "
            "(Equifax, Experian, and TransUnion) has revealed significant findings that require your "
            "immediate attention. Our forensic review has identified multiple violations of the Fair "
            "Credit Reporting Act (FCRA) that may entitle you to substantial compensation.",
        )

        self.add_section_header(story, "Key Findings Summary", level=2)

        total_violations = len(violations)
        willful_count = sum(1 for v in violations if v.get("is_willful", False))
        total_exposure = damages.get("total_exposure", 0) if damages else 0

        findings_data = [
            ["Finding", "Value"],
            ["Total FCRA Violations Identified", str(total_violations)],
            ["Willful Violations (Higher Damages)", str(willful_count)],
            ["Potential Total Recovery", self.format_currency(total_exposure)],
            [
                "Case Strength Score",
                f"{case_score.get('total_score', 'N/A')}/10" if case_score else "N/A",
            ],
            [
                "Standing for Lawsuit",
                (
                    "Established"
                    if standing.get("has_concrete_harm")
                    else "Needs Documentation"
                ),
            ],
        ]
        self.add_table(story, findings_data, col_widths=[3 * inch, 2.5 * inch])

        self.add_section_header(
            story, "Standing Analysis (Post-TransUnion v. Ramirez)", level=2
        )

        if standing:
            standing_items = [
                f"Concrete Harm: {'Documented' if standing.get('has_concrete_harm') else 'Needs Documentation'} - {standing.get('concrete_harm_type', 'Not specified')}",
                f"Dissemination: {'Confirmed' if standing.get('has_dissemination') else 'Unconfirmed'} - Third-party access to inaccurate report",
                f"Causation: {'Established' if standing.get('has_causation') else 'Needs Proof'} - Direct link between errors and harm",
            ]
            self.add_bullet_list(story, standing_items)
        else:
            self.add_paragraph(
                story, "Standing analysis not yet completed. See Section 4 for details."
            )

        self.add_section_header(story, "Damages Overview", level=2)

        if damages:
            damages_breakdown = [
                f"Actual Damages: {self.format_currency(damages.get('actual_damages_total', 0))} (credit denials, higher interest, emotional distress)",
                f"Statutory Damages: {self.format_currency(damages.get('statutory_damages_total', 0))} ($100-$1,000 per violation)",
                f"Punitive Damages: {self.format_currency(damages.get('punitive_damages_amount', 0))} (for willful violations)",
                f"Settlement Target: {self.format_currency(damages.get('settlement_target', 0))} (65% of total exposure)",
            ]
            self.add_bullet_list(story, damages_breakdown)

        self.add_section_header(story, "Recommended Action", level=2)

        recommendation = (
            case_score.get("recommendation", "proceed_with_disputes")
            if case_score
            else "proceed_with_disputes"
        )

        if recommendation == "litigate":
            self.add_paragraph(
                story,
                "Based on our analysis, your case presents STRONG litigation potential. We recommend "
                "proceeding with formal dispute letters followed by pre-litigation demands if the "
                "bureaus fail to correct the errors within the statutory timeframe.",
                self.warning_style,
            )
        else:
            self.add_paragraph(
                story,
                "We recommend proceeding with our proven dispute process. The violations identified "
                "in this report provide a strong foundation for demanding corrections from the credit "
                "bureaus under the FCRA's maximum procedure requirements.",
            )

        story.append(PageBreak())

    def _add_fcra_rights(self, story):
        """Add 3-4 pages on FCRA rights"""
        self.add_section_header(
            story, "SECTION 2: UNDERSTANDING YOUR FCRA RIGHTS", level=1
        )

        self.add_paragraph(
            story,
            "The Fair Credit Reporting Act (15 U.S.C. 1681 et seq.) is a federal law that gives you "
            "powerful rights to dispute inaccurate information on your credit reports and hold "
            "credit bureaus and data furnishers accountable when they fail to follow reasonable "
            "procedures to ensure accuracy.",
        )

        self.add_section_header(story, "Your Key Rights Under the FCRA", level=2)

        rights = [
            (
                "Right to Accuracy (Section 607(b))",
                "Credit bureaus must follow reasonable procedures to assure maximum possible accuracy "
                "of information in your consumer report.",
            ),
            (
                "Right to Dispute (Section 611)",
                "You have the right to dispute any information you believe is inaccurate, incomplete, "
                "or unverifiable. The bureau must investigate within 30 days.",
            ),
            (
                "Right to Reinvestigation Results (Section 611(a)(6))",
                "After investigation, the bureau must provide you written notice of results and a "
                "free copy of your report if changes were made.",
            ),
            (
                "Right to Sue (Section 616 & 617)",
                "You may sue in federal court for willful or negligent noncompliance with the FCRA "
                "and recover actual damages, statutory damages, punitive damages, and attorney fees.",
            ),
            (
                "Protection from Obsolete Information (Section 605)",
                "Most negative information must be removed after 7 years (10 years for bankruptcies).",
            ),
        ]

        for title, content in rights:
            self.add_section_header(story, title, level=3)
            self.add_paragraph(story, content)

        self.add_section_header(story, "Key FCRA Sections and Violations", level=2)

        sections_data = [
            ["FCRA Section", "Requirement", "Statutory Damages"],
            ["Section 605(a)", "Obsolete information removal", "$100-$1,000"],
            ["Section 605(b)", "Identity theft block compliance", "$100-$1,000"],
            ["Section 607(b)", "Maximum accuracy procedures", "$100-$1,000"],
            ["Section 611", "Reinvestigation within 30 days", "$100-$1,000"],
            ["Section 623", "Furnisher accuracy duties", "$100-$1,000"],
        ]
        self.add_table(
            story, sections_data, col_widths=[1.5 * inch, 2.5 * inch, 1.5 * inch]
        )

        self.add_section_header(story, "The TransUnion v. Ramirez Standard", level=2)

        self.add_paragraph(
            story,
            "Following the Supreme Court's 2021 decision in TransUnion LLC v. Ramirez, plaintiffs "
            "must demonstrate 'concrete harm' to have standing to sue. This means you must show "
            "actual, real-world consequences from the FCRA violations - not just technical "
            "inaccuracies. Examples of concrete harm include:",
        )

        harm_examples = [
            "Credit denials or adverse terms due to inaccurate information",
            "Higher interest rates on loans or credit cards",
            "Denial of employment, housing, or insurance",
            "Emotional distress, anxiety, or embarrassment from credit issues",
            "Time and money spent correcting errors",
            "Dissemination of false information to third parties",
        ]
        self.add_bullet_list(story, harm_examples)

        story.append(PageBreak())

    def _add_bureau_analysis(self, story, client_data):
        """Add per-bureau analysis section"""
        self.add_section_header(story, "SECTION 3: CREDIT BUREAU ANALYSIS", level=1)

        violations = client_data.get("violations", [])
        credit_scores = client_data.get("credit_scores", {})

        bureaus = ["Equifax", "Experian", "TransUnion"]

        for bureau in bureaus:
            self.add_section_header(story, f"{bureau} Report Analysis", level=2)

            score = credit_scores.get(bureau.lower(), "Not Available")
            bureau_violations = [
                v for v in violations if v.get("bureau", "").lower() == bureau.lower()
            ]

            self.add_paragraph(story, f"<b>Credit Score:</b> {score}")
            self.add_paragraph(
                story, f"<b>Violations Found:</b> {len(bureau_violations)}"
            )

            if bureau_violations:
                violation_data = [["Account", "FCRA Section", "Violation Type"]]
                for v in bureau_violations[:10]:
                    violation_data.append(
                        [
                            v.get("account_name", "Unknown")[:30],
                            v.get("fcra_section", "N/A"),
                            v.get("violation_type", "Unknown")[:25],
                        ]
                    )
                self.add_table(
                    story, violation_data, col_widths=[2 * inch, 1.2 * inch, 2 * inch]
                )
            else:
                self.add_paragraph(story, "No violations identified for this bureau.")

            story.append(Spacer(1, 0.3 * inch))

        story.append(PageBreak())

    def _add_violation_categories(self, story, client_data):
        """Add detailed violation categories breakdown"""
        self.add_section_header(story, "SECTION 4: VIOLATION CATEGORIES", level=1)

        violations = client_data.get("violations", [])

        by_section = {}
        for v in violations:
            section = v.get("fcra_section", "Other")
            by_section.setdefault(section, []).append(v)

        self.add_paragraph(
            story,
            "The following is a detailed breakdown of all FCRA violations identified in your "
            "credit reports, organized by the specific section of the Fair Credit Reporting Act "
            "that was violated.",
        )

        for section, section_violations in sorted(by_section.items()):
            self.add_section_header(
                story,
                f"FCRA {section} Violations ({len(section_violations)} found)",
                level=2,
            )

            section_descriptions = {
                "605": "Obsolete or prohibited information that should have been removed",
                "607(b)": "Failure to follow reasonable procedures for maximum accuracy",
                "611": "Failure to properly reinvestigate disputed information",
                "623": "Furnisher failed to investigate or correct inaccurate data",
            }

            desc = section_descriptions.get(section, "Violation of FCRA requirements")
            self.add_paragraph(story, f"<i>{desc}</i>")

            for i, v in enumerate(section_violations, 1):
                self.add_section_header(
                    story, f"{i}. {v.get('account_name', 'Unknown Account')}", level=3
                )

                details = [
                    f"Bureau: {v.get('bureau', 'Unknown')}",
                    f"Violation Type: {v.get('violation_type', 'Not specified')}",
                    f"Description: {v.get('description', 'No description available')}",
                    f"Willful: {'Yes - higher damages available' if v.get('is_willful') else 'No'}",
                    f"Statutory Damages: ${v.get('statutory_damages_min', 100)} - ${v.get('statutory_damages_max', 1000)}",
                ]
                self.add_bullet_list(story, details)

            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    def _add_account_analysis(self, story, client_data):
        """Add account-by-account analysis"""
        self.add_section_header(
            story, "SECTION 5: ACCOUNT-BY-ACCOUNT ANALYSIS", level=1
        )

        violations = client_data.get("violations", [])

        by_account = {}
        for v in violations:
            account = v.get("account_name", "Unknown")
            by_account.setdefault(account, []).append(v)

        self.add_paragraph(
            story,
            "This section provides a detailed analysis of each account that contains inaccurate, "
            "incomplete, or unverifiable information across your credit reports.",
        )

        for account, account_violations in sorted(by_account.items()):
            self.add_section_header(story, f"Account: {account}", level=2)

            bureaus_affected = list(
                set(v.get("bureau", "Unknown") for v in account_violations)
            )
            self.add_paragraph(
                story, f"<b>Bureaus Affected:</b> {', '.join(bureaus_affected)}"
            )
            self.add_paragraph(
                story, f"<b>Total Violations:</b> {len(account_violations)}"
            )

            issues = list(
                set(v.get("violation_type", "Unknown") for v in account_violations)
            )
            self.add_paragraph(story, "<b>Issues Identified:</b>")
            self.add_bullet_list(story, issues)

            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    def _add_legal_framework(self, story):
        """Add legal framework section"""
        self.add_section_header(story, "SECTION 6: LEGAL FRAMEWORK", level=1)

        self.add_paragraph(
            story,
            "Your dispute strategy is grounded in well-established federal law and precedent. "
            "The following legal authorities support your claims:",
        )

        self.add_section_header(story, "Primary Statutes", level=2)

        statutes = [
            (
                "Fair Credit Reporting Act (15 U.S.C. 1681 et seq.)",
                "The primary federal law governing credit reporting, providing private right of action for violations.",
            ),
            (
                "Fair Debt Collection Practices Act (15 U.S.C. 1692 et seq.)",
                "Prohibits abusive debt collection practices and governs collector reporting to bureaus.",
            ),
        ]

        for title, desc in statutes:
            self.add_section_header(story, title, level=3)
            self.add_paragraph(story, desc)

        self.add_section_header(story, "Key Precedents", level=2)

        precedents = [
            (
                "TransUnion LLC v. Ramirez (2021)",
                "Supreme Court established that plaintiffs must show 'concrete harm' for Article III standing.",
            ),
            (
                "Safeco Insurance Co. v. Burr (2007)",
                "Supreme Court defined 'willfulness' standard for FCRA violations, requiring reckless disregard.",
            ),
            (
                "Cushman v. TransUnion (9th Cir. 2000)",
                "Established consumer's right to request 'method of verification' from bureaus.",
            ),
        ]

        for title, desc in precedents:
            self.add_section_header(story, title, level=3)
            self.add_paragraph(story, desc)

        story.append(PageBreak())

    def _add_damages_assessment(self, story, client_data):
        """Add damages calculation section"""
        self.add_section_header(story, "SECTION 7: DAMAGES ASSESSMENT", level=1)

        damages = client_data.get("damages", {})
        violations = client_data.get("violations", [])

        self.add_paragraph(
            story,
            "The following is a detailed calculation of potential damages you may recover "
            "based on the FCRA violations identified in your credit reports.",
        )

        self.add_section_header(story, "Statutory Damages (Per Violation)", level=2)

        if damages:
            stat_data = [
                ["Category", "Count", "Amount"],
                [
                    "Section 605 Violations",
                    str(damages.get("section_605b_count", 0)),
                    self.format_currency(damages.get("section_605b_amount", 0)),
                ],
                [
                    "Section 607(b) Violations",
                    str(damages.get("section_607b_count", 0)),
                    self.format_currency(damages.get("section_607b_amount", 0)),
                ],
                [
                    "Section 611 Violations",
                    str(damages.get("section_611_count", 0)),
                    self.format_currency(damages.get("section_611_amount", 0)),
                ],
                [
                    "Section 623 Violations",
                    str(damages.get("section_623_count", 0)),
                    self.format_currency(damages.get("section_623_amount", 0)),
                ],
                [
                    "TOTAL STATUTORY",
                    "",
                    self.format_currency(damages.get("statutory_damages_total", 0)),
                ],
            ]
            self.add_table(
                story, stat_data, col_widths=[2.5 * inch, 1 * inch, 1.5 * inch]
            )

        self.add_section_header(story, "Actual Damages", level=2)

        if damages:
            actual_data = [
                ["Type", "Amount"],
                [
                    "Credit Denials",
                    self.format_currency(damages.get("credit_denials_amount", 0)),
                ],
                [
                    "Higher Interest Rates",
                    self.format_currency(damages.get("higher_interest_amount", 0)),
                ],
                [
                    "Credit Monitoring Costs",
                    self.format_currency(damages.get("credit_monitoring_amount", 0)),
                ],
                [
                    "Time & Stress",
                    self.format_currency(damages.get("time_stress_amount", 0)),
                ],
                [
                    "Other Actual Damages",
                    self.format_currency(damages.get("other_actual_amount", 0)),
                ],
                [
                    "TOTAL ACTUAL",
                    self.format_currency(damages.get("actual_damages_total", 0)),
                ],
            ]
            self.add_table(story, actual_data, col_widths=[3 * inch, 2 * inch])

        self.add_section_header(story, "Punitive Damages", level=2)

        willful_count = sum(1 for v in violations if v.get("is_willful", False))

        if damages and willful_count > 0:
            self.add_paragraph(
                story,
                f"Based on {willful_count} willful violations identified, you may be entitled to "
                f"punitive damages. Using a conservative {damages.get('willfulness_multiplier', 1)}x multiplier: "
                f"{self.format_currency(damages.get('punitive_damages_amount', 0))}",
            )
        else:
            self.add_paragraph(
                story,
                "No willful violations identified for punitive damages at this time.",
            )

        self.add_section_header(story, "Total Recovery Potential", level=2)

        if damages:
            total_exposure = damages.get("total_exposure", 0)
            settlement_target = damages.get("settlement_target", 0)

            self.add_info_box(
                story,
                "TOTAL POTENTIAL RECOVERY",
                f"Total Exposure: {self.format_currency(total_exposure)}\n\n"
                f"Recommended Settlement Target (65%): {self.format_currency(settlement_target)}\n\n"
                f"Minimum Acceptable (50%): {self.format_currency(damages.get('minimum_acceptable', 0))}",
            )

        story.append(PageBreak())

    def _add_strategic_recommendations(self, story, client_data):
        """Add strategic recommendations section"""
        self.add_section_header(story, "SECTION 8: STRATEGIC RECOMMENDATIONS", level=1)

        case_score = client_data.get("case_score", {})
        violations = client_data.get("violations", [])
        dispute_round = client_data.get("dispute_round", 1)

        self.add_paragraph(
            story,
            "Based on our comprehensive analysis, we recommend the following dispute strategy "
            "to maximize your chances of success and potential recovery.",
        )

        self.add_section_header(story, "Recommended Strategy", level=2)

        if dispute_round == 1:
            strategy = [
                "Submit comprehensive dispute letters to all three credit bureaus",
                "Use RLPP (Rapid Legal Protection Protocol) bundling for maximum impact",
                "Include all identified violations with supporting documentation",
                "Request method of verification for all disputed items",
                "Set 30-day response deadline per FCRA requirements",
            ]
        elif dispute_round == 2:
            strategy = [
                "Submit Method of Verification (MOV) demands citing Cushman v. TransUnion",
                "Request tangible documentation of investigation procedures",
                "Escalate tone to indicate awareness of legal rights",
                "Document bureau failures to properly investigate",
            ]
        elif dispute_round == 3:
            strategy = [
                "File regulatory complaints with CFPB, FTC, and State Attorney General",
                "Document all prior dispute attempts and bureau responses",
                "Prepare pre-litigation demand letters",
                "Consider consultation with FCRA attorney",
            ]
        else:
            strategy = [
                "Send formal pre-arbitration demands",
                "Draft AAA arbitration filing if necessary",
                "Calculate final damages with attorney fee projections",
                "Prepare for potential settlement negotiations",
            ]

        self.add_bullet_list(story, strategy)

        self.add_section_header(story, "Priority Violations to Target", level=2)

        high_value = sorted(
            violations, key=lambda x: x.get("statutory_damages_max", 0), reverse=True
        )[:5]

        if high_value:
            self.add_paragraph(
                story, "Focus dispute efforts on these high-value violations:"
            )
            for i, v in enumerate(high_value, 1):
                self.add_paragraph(
                    story,
                    f"{i}. {v.get('account_name', 'Unknown')} ({v.get('bureau', 'Unknown')}) - "
                    f"{v.get('fcra_section', 'N/A')}: {v.get('violation_type', 'Unknown')}",
                )

        story.append(PageBreak())

    def _add_next_steps(self, story, client_data):
        """Add next steps section"""
        self.add_section_header(story, "SECTION 9: NEXT STEPS", level=1)

        dispute_round = client_data.get("dispute_round", 1)

        self.add_paragraph(
            story,
            "The following action items outline the immediate next steps in your credit repair journey.",
        )

        self.add_section_header(story, "Immediate Actions (Next 7 Days)", level=2)

        if dispute_round == 1:
            immediate = [
                "Review and sign dispute letters attached to this package",
                "Gather supporting documentation (denial letters, payment records)",
                "Make copies of all documents for your records",
                "Send letters via certified mail with return receipt requested",
                "Note the mailing date - bureaus have 30 days to respond",
            ]
        else:
            immediate = [
                "Review bureau responses from previous round",
                "Identify items that were not properly investigated",
                "Sign escalation letters attached to this package",
                "Document any new harm caused by continued inaccuracies",
            ]

        self.add_numbered_list(story, immediate)

        self.add_section_header(story, "Timeline", level=2)

        timeline = [
            ("Day 1-7", "Send dispute letters, retain proof of mailing"),
            ("Day 8-30", "Bureaus investigate disputed items"),
            ("Day 31-35", "Receive and review bureau responses"),
            ("Day 36-45", "Prepare next round if items not deleted"),
        ]

        for period, action in timeline:
            self.add_paragraph(story, f"<b>{period}:</b> {action}")

        self.add_section_header(story, "Your Responsibilities", level=2)

        responsibilities = [
            "DO NOT apply for new credit during the dispute process",
            "DO NOT pay collections without consulting us first",
            "DO keep all current accounts in good standing",
            "DO respond promptly to any requests for information",
            "DO document any credit denials or adverse actions",
        ]
        self.add_bullet_list(story, responsibilities)

        story.append(PageBreak())

    def _add_appendix(self, story, client_data):
        """Add appendix section"""
        self.add_section_header(story, "SECTION 10: APPENDIX", level=1)

        self.add_paragraph(
            story,
            "The following appendices contain supporting documentation and reference materials "
            "for your credit dispute case.",
        )

        appendices = [
            ("Appendix A", "Sample Dispute Letter Templates"),
            ("Appendix B", "FCRA Full Text Reference"),
            ("Appendix C", "Credit Bureau Contact Information"),
            ("Appendix D", "State-Specific Consumer Protection Laws"),
            ("Appendix E", "Glossary of Credit Terms"),
        ]

        for title, desc in appendices:
            self.add_section_header(story, f"{title}: {desc}", level=2)
            self.add_paragraph(story, f"[{desc} - See attached documents]")

        story.append(Spacer(1, 1 * inch))

        self.add_paragraph(
            story,
            f"This report was prepared by {self.COMPANY_NAME}. For questions or assistance, "
            f"contact us at {self.COMPANY_PHONE} or {self.COMPANY_EMAIL}.",
            self.footer_style,
        )
