"""
PDF Generation Service for FCRA Analysis Reports

Generates two types of PDFs:
1. Client Report - Professional, branded PDF for clients (HTML-based with WeasyPrint)
2. Legal Analysis - Detailed internal analysis for legal team (ReportLab)
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
import re

# Brightpath Ascend brand colors (matching email template)
PRIMARY_COLOR = "#319795"
SECONDARY_COLOR = "#84cc16"
DARK_COLOR = "#1a1a2e"


class FCRAPDFGenerator:
    """Generate professional FCRA analysis PDFs"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        # Client report styles
        self.styles.add(ParagraphStyle(
            name='ClientHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a5276'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='ClientSubHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#1a5276'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='ClientBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#2c3e50'),
            spaceAfter=8,
            fontName='Helvetica',
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='ClientHighlight',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#1a5276'),
            spaceAfter=8,
            fontName='Helvetica-Bold',
            leading=15
        ))

        # Legal report styles (formal serif fonts, no colors)
        self.styles.add(ParagraphStyle(
            name='LegalTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=HexColor('#000000'),
            spaceAfter=12,
            spaceBefore=0,
            fontName='Times-Bold',
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='LegalHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            textColor=HexColor('#000000'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Times-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='LegalSubHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=HexColor('#000000'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Times-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='LegalBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#000000'),
            spaceAfter=8,
            fontName='Times-Roman',
            leading=14,
            firstLineIndent=0
        ))

    def _add_branded_header(self, story, title, subtitle=None):
        """Add Brightpath Ascend branded header banner (matching email template)"""
        # Header banner with gradient effect (using primary color)
        header_text = '<font size=16 color=white><b>BRIGHTPATH ASCEND</b></font><br/>'
        header_text += '<font size=10 color=white>FCRA Litigation Analysis</font>'

        header_para = Paragraph(header_text, ParagraphStyle(
            'BrandHeader',
            fontSize=16,
            textColor=white,
            alignment=TA_CENTER,
            spaceAfter=0
        ))

        header_table = Table([[header_para]], colWidths=[6.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor(PRIMARY_COLOR)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))

        # Document title
        if title:
            story.append(Paragraph(title, self.styles['ClientHeader']))
        if subtitle:
            story.append(Paragraph(subtitle, self.styles['ClientBody']))
        story.append(Spacer(1, 0.2*inch))

    def _add_summary_box(self, story, violations_count, total_exposure, case_strength):
        """Add executive summary box (matching email template styling)"""
        # Determine case strength colors (matching email template)
        strength_colors = {
            'Strong': {'bg': '#dcfce7', 'text': '#166534', 'border': '#86efac'},
            'Moderate': {'bg': '#fef3c7', 'text': '#92400e', 'border': '#fcd34d'},
            'Weak': {'bg': '#fee2e2', 'text': '#991b1b', 'border': '#fca5a5'}
        }
        colors = strength_colors.get(case_strength, strength_colors['Moderate'])

        # Create three-column summary (matching email template layout)
        summary_data = [[
            Paragraph(f'<font size=32 color="{colors["text"]}"><b>{violations_count}</b></font><br/>'
                     f'<font size=10 color="{colors["text"]}">FCRA Violations</font>',
                     ParagraphStyle('sum1', alignment=TA_CENTER)),
            Paragraph(f'<font size=32 color="{colors["text"]}"><b>${total_exposure:,.0f}</b></font><br/>'
                     f'<font size=10 color="{colors["text"]}">Total Exposure</font>',
                     ParagraphStyle('sum2', alignment=TA_CENTER)),
            Paragraph(f'<font size=24 color="{colors["text"]}"><b>{case_strength}</b></font><br/>'
                     f'<font size=10 color="{colors["text"]}">Case Strength</font>',
                     ParagraphStyle('sum3', alignment=TA_CENTER))
        ]]

        summary_table = Table(summary_data, colWidths=[2.16*inch, 2.16*inch, 2.16*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor(colors['bg'])),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, HexColor(colors['border'])),
            ('LINEAFTER', (0, 0), (0, 0), 1, HexColor(colors['border'])),
            ('LINEAFTER', (1, 0), (1, 0), 1, HexColor(colors['border'])),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

    def _add_violations_cards(self, story, violations):
        """Add violation cards with styled borders (matching email template)"""
        story.append(Paragraph('Key Findings', self.styles['ClientSubHeader']))
        story.append(Spacer(1, 0.1*inch))

        # Group violations by bureau
        bureaus = {}
        for v in violations:
            bureau = v.bureau or 'Unknown'
            if bureau not in bureaus:
                bureaus[bureau] = []
            bureaus[bureau].append(v)

        for bureau, bureau_violations in bureaus.items():
            # Bureau header box with colored left border (matching email template)
            bureau_header = Paragraph(
                f'<font size=16 color="{DARK_COLOR}"><b>{bureau}</b></font>',
                ParagraphStyle('bureau_head', alignment=TA_LEFT, leftIndent=10)
            )
            bureau_table = Table([[bureau_header]], colWidths=[6.5*inch])
            bureau_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LINEABOVE', (0, 0), (0, 0), 4, HexColor(PRIMARY_COLOR)),
                ('ROUNDEDCORNERS', [0, 8, 8, 0]),
            ]))
            story.append(bureau_table)
            story.append(Spacer(1, 0.15*inch))

            # Show top violations for this bureau
            for v in bureau_violations[:10]:
                # Violation card (styled like email template)
                account = f'<font size=13 color="#1e293b"><b>• {v.account_name or "Account"}</b></font>'
                vtype = f'<font size=11 color="#64748b">{v.violation_type or "FCRA Violation"}</font>'
                desc = v.description or 'No description'
                if len(desc) > 200:
                    desc = desc[:200] + '...'
                desc_text = f'<font size=10 color="#64748b">{self._sanitize_text(desc)}</font>'

                violation_content = Paragraph(
                    f'{account}<br/>{vtype}<br/>{desc_text}',
                    ParagraphStyle('viol', leftIndent=5, spaceAfter=8, leading=14)
                )

                viol_table = Table([[violation_content]], colWidths=[6.3*inch])
                viol_table.setStyle(TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(viol_table)

            if len(bureau_violations) > 10:
                story.append(Paragraph(
                    f'<i><font color="#64748b">...and {len(bureau_violations) - 10} more violations</font></i>',
                    self.styles['ClientBody']
                ))
            story.append(Spacer(1, 0.25*inch))

    def _add_section_header(self, story, title):
        """Add styled section header (consistent throughout document)"""
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f'<font size=18 color="{DARK_COLOR}"><b>{title}</b></font>',
            self.styles['ClientSubHeader']
        ))
        story.append(Spacer(1, 0.15*inch))

    def _add_styled_damages_table(self, story, damages):
        """Add damages breakdown table (matching email template styling)"""
        self._add_section_header(story, 'Damages Breakdown')

        damages_data = [
            # Header row with dark background
            [Paragraph('<font color=white><b>Damage Type</b></font>',
                      ParagraphStyle('dh1', alignment=TA_LEFT)),
             Paragraph('<font color=white><b>Amount</b></font>',
                      ParagraphStyle('dh2', alignment=TA_RIGHT))],
            # Data rows
            [Paragraph('Statutory Damages', self.styles['ClientBody']),
             Paragraph(f'${damages.statutory_damages_total:,.0f}', self.styles['ClientBody'])],
            [Paragraph('Actual Damages', self.styles['ClientBody']),
             Paragraph(f'${damages.actual_damages_total:,.0f}', self.styles['ClientBody'])],
            [Paragraph('Punitive Damages (if willful)', self.styles['ClientBody']),
             Paragraph(f'${damages.punitive_damages_amount:,.0f}', self.styles['ClientBody'])],
            # Total row with emphasis
            [Paragraph(f'<font size=12 color="{PRIMARY_COLOR}"><b>Total Exposure</b></font>',
                      ParagraphStyle('dt', alignment=TA_LEFT)),
             Paragraph(f'<font size=12 color="{PRIMARY_COLOR}"><b>${damages.total_exposure:,.0f}</b></font>',
                      ParagraphStyle('da', alignment=TA_RIGHT))],
            [Paragraph('Settlement Target (65%)', self.styles['ClientBody']),
             Paragraph(f'${damages.settlement_target:,.0f}', self.styles['ClientBody'])]
        ]

        damages_table = Table(damages_data, colWidths=[4*inch, 2.5*inch])
        damages_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(DARK_COLOR)),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            # Alternating row colors
            ('BACKGROUND', (0, 1), (-1, 3), HexColor('#f8f9fa')),
            ('BACKGROUND', (0, 4), (-1, 4), HexColor('#e8f4f8')),  # Total row highlight
            ('BACKGROUND', (0, 5), (-1, 5), HexColor('#f8f9fa')),
            # Alignment
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, HexColor(DARK_COLOR)),
            ('LINEABOVE', (0, 4), (-1, 4), 2, HexColor(PRIMARY_COLOR)),  # Emphasize total
        ]))
        story.append(damages_table)
        story.append(Spacer(1, 0.3*inch))

    def _sanitize_text(self, text):
        """Sanitize text for PDF rendering"""
        if not text:
            return ""
        # Replace problematic characters
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '\x00': '',
            '\r': '',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def generate_client_report(self, output_path, client_name, violations, damages, case_score, analysis):
        """
        Generate client-facing PDF report with email template styling

        Args:
            output_path: Path to save PDF
            client_name: Client's name
            violations: List of Violation objects
            damages: Damages object
            case_score: CaseScore object
            analysis: Analysis object
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=0.5*inch, bottomMargin=0.75*inch)
        story = []

        # === PAGE 1: BRANDED HEADER & EXECUTIVE SUMMARY ===
        # Brightpath Ascend branded header banner
        self._add_branded_header(story, 'Your Credit Analysis Report',
                                f'Comprehensive FCRA Violations Analysis')

        # Client name and date
        story.append(Paragraph(f'<b>Prepared for:</b> {client_name}', self.styles['ClientBody']))
        story.append(Paragraph(f'<b>Report Date:</b> {datetime.now().strftime("%B %d, %Y")}',
                             self.styles['ClientBody']))
        story.append(Spacer(1, 0.25*inch))

        # Case summary box (colored, matching email template)
        violations_count = len(violations)
        total_exposure = damages.total_exposure if damages else 0
        case_strength = self._get_case_strength_label(case_score.total_score if case_score else 0)
        self._add_summary_box(story, violations_count, total_exposure, case_strength)

        # What This Means section
        self._add_section_header(story, 'What This Means')
        story.append(Paragraph(
            f'Our comprehensive analysis has identified <b><font color="{PRIMARY_COLOR}">{violations_count} '
            f'violations</font></b> of the Fair Credit Reporting Act (FCRA) across your credit reports. '
            f'These violations represent potential legal claims with a total exposure of '
            f'<b><font color="{PRIMARY_COLOR}">${total_exposure:,.0f}</font></b>.',
            self.styles['ClientBody']
        ))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            'The FCRA is a federal law that protects consumers by ensuring credit reporting agencies '
            'maintain accurate information. When they fail to do so, you may be entitled to statutory '
            'damages, actual damages, and attorney fees.',
            self.styles['ClientBody']
        ))

        # Key findings (violation cards)
        if violations:
            self._add_violations_cards(story, violations)

        # === NEXT STEPS ===
        self._add_section_header(story, 'Next Steps')
        next_steps = [
            '<b>Review this report</b> carefully. Note any accounts or violations you recognize, and '
            'gather supporting documentation.',
            '<b>Contact us</b> to discuss your case. We\'ll explain your options and the litigation process.',
            '<b>Gather documentation</b> including credit reports, denial letters, correspondence with '
            'creditors, and proof of identity theft (if applicable).',
            '<b>Act promptly</b>. FCRA claims have statute of limitations, typically 2-5 years depending '
            'on the violation type.'
        ]
        for i, step in enumerate(next_steps, 1):
            story.append(Paragraph(f'{i}. {step}', self.styles['ClientBody']))
            story.append(Spacer(1, 0.08*inch))

        # === DAMAGES BREAKDOWN ===
        if damages:
            self._add_styled_damages_table(story, damages)

        # === PAGE BREAK BEFORE FULL ANALYSIS ===
        story.append(PageBreak())

        # === FULL COMPREHENSIVE ANALYSIS (40-50 PAGES) ===
        if analysis.full_analysis:
            # Comprehensive analysis header
            self._add_branded_header(story, 'COMPREHENSIVE LITIGATION ANALYSIS',
                                   'Detailed Legal Analysis & Case Documentation')

            # Render full analysis text with styled sections
            lines = analysis.full_analysis.split('\n')
            in_section = False

            for line in lines:
                if line.strip():
                    # Detect section headers (all caps lines or lines ending with colon)
                    is_header = (line.strip().isupper() and len(line.strip()) < 100) or \
                               (line.strip().endswith(':') and len(line.strip()) < 80)

                    if is_header:
                        # Style as section header
                        if not in_section:
                            story.append(Spacer(1, 0.2*inch))
                        try:
                            story.append(Paragraph(
                                f'<font size=14 color="{DARK_COLOR}"><b>{self._sanitize_text(line)}</b></font>',
                                self.styles['ClientSubHeader']
                            ))
                            story.append(Spacer(1, 0.1*inch))
                            in_section = True
                        except:
                            pass
                    else:
                        # Regular content - check for special formatting
                        # Detect bullet points
                        if line.strip().startswith(('•', '-', '*')) or \
                           (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                            try:
                                story.append(Paragraph(
                                    f'<font color="#334155">{self._sanitize_text(line)}</font>',
                                    ParagraphStyle('bullet', parent=self.styles['ClientBody'],
                                                 leftIndent=15, spaceAfter=6)
                                ))
                            except:
                                pass
                        else:
                            # Regular paragraph - chunk long lines
                            if len(line) > 1000:
                                chunks = [line[i:i+1000] for i in range(0, len(line), 1000)]
                                for chunk in chunks:
                                    try:
                                        story.append(Paragraph(
                                            f'<font color="#334155">{self._sanitize_text(chunk)}</font>',
                                            self.styles['ClientBody']
                                        ))
                                    except:
                                        pass
                            else:
                                try:
                                    story.append(Paragraph(
                                        f'<font color="#334155">{self._sanitize_text(line)}</font>',
                                        self.styles['ClientBody']
                                    ))
                                except:
                                    pass
                else:
                    # Empty line - add spacing
                    story.append(Spacer(1, 0.1*inch))
                    in_section = False

        # === FOOTER ===
        story.append(Spacer(1, 0.5*inch))
        footer_table = Table([[
            Paragraph(
                f'<font size=9 color="#7f8c8d"><i>This report is confidential and prepared for {client_name}. '
                f'For questions or to discuss your case, contact Brightpath Ascend.</i></font>',
                ParagraphStyle('footer', alignment=TA_CENTER)
            )
        ]], colWidths=[6.5*inch])
        footer_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
        ]))
        story.append(footer_table)

        # Build PDF
        doc.build(story)
        return output_path

    def _get_case_strength_label(self, score):
        """Convert numeric score to label"""
        if score >= 8:
            return "Strong"
        elif score >= 5:
            return "Moderate"
        else:
            return "Developing"

    def generate_legal_analysis(self, output_path, client_name, violations, standing, damages,
                               case_score, analysis, full_analysis_text):
        """
        Generate detailed legal analysis PDF

        Args:
            output_path: Path to save PDF
            client_name: Client's name
            violations: List of Violation objects
            standing: Standing object
            damages: Damages object
            case_score: CaseScore object
            analysis: Analysis object
            full_analysis_text: Full stage 2 analysis text
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                              rightMargin=1*inch, leftMargin=1*inch,
                              topMargin=1*inch, bottomMargin=1*inch)
        story = []

        # Formal Legal Document Header
        story.append(Paragraph('FCRA LITIGATION ANALYSIS - CONFIDENTIAL', self.styles['LegalTitle']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f'<b>Client:</b> {client_name}', self.styles['LegalBody']))
        story.append(Paragraph(f'<b>Analysis ID:</b> {analysis.id}', self.styles['LegalBody']))
        story.append(Paragraph(f'<b>Date:</b> {analysis.created_at.strftime("%B %d, %Y")}',
                             self.styles['LegalBody']))
        story.append(Spacer(1, 0.3*inch))

        # Confidentiality notice
        story.append(Paragraph(
            '<i>This document contains confidential attorney work product and privileged information. '
            'It is prepared for internal legal review and potential submission to counsel. '
            'Unauthorized disclosure is prohibited.</i>',
            ParagraphStyle('notice', fontSize=9, textColor=HexColor('#000000'),
                         fontName='Times-Italic', alignment=TA_CENTER, spaceAfter=12)
        ))
        story.append(Spacer(1, 0.3*inch))

        # Case Score
        if case_score:
            story.append(Paragraph(f'I. CASE STRENGTH SCORE: {case_score.total_score}/10',
                                 self.styles['LegalHeader']))
            story.append(Spacer(1, 0.2*inch))

        # Violations
        story.append(Paragraph(f'II. VIOLATIONS IDENTIFIED: {len(violations)}', self.styles['LegalHeader']))
        story.append(Spacer(1, 0.1*inch))

        for v in violations:
            text = f"• {v.fcra_section} - {v.violation_type} ({v.bureau})"
            story.append(Paragraph(self._sanitize_text(text), self.styles['LegalBody']))

            desc = f"  {v.description or 'No description'}"
            story.append(Paragraph(self._sanitize_text(desc), self.styles['LegalBody']))

            willful = f"  Willful: {'Yes' if v.is_willful else 'No'}"
            story.append(Paragraph(willful, self.styles['LegalBody']))

            damages_range = f"  Statutory Damages: ${v.statutory_damages_min}-${v.statutory_damages_max}"
            story.append(Paragraph(damages_range, self.styles['LegalBody']))
            story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 0.2*inch))

        # Standing Analysis
        story.append(Paragraph('III. STANDING ANALYSIS', self.styles['LegalHeader']))
        if standing:
            story.append(Paragraph(f"• Concrete Harm: {'Yes' if standing.has_concrete_harm else 'No'}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Dissemination: {'Yes' if standing.has_dissemination else 'No'}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Causation: {'Yes' if standing.has_causation else 'No'}",
                                 self.styles['LegalBody']))
        story.append(Spacer(1, 0.2*inch))

        # Damages Calculation
        story.append(Paragraph('IV. DAMAGES CALCULATION', self.styles['LegalHeader']))
        if damages:
            story.append(Paragraph(f"• Actual Damages: ${damages.actual_damages_total:,.0f}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Statutory Damages: ${damages.statutory_damages_total:,.0f}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Punitive Damages: ${damages.punitive_damages_amount:,.0f}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Total Exposure: ${damages.total_exposure:,.0f}",
                                 self.styles['LegalBody']))
            story.append(Paragraph(f"• Settlement Target (65%): ${damages.settlement_target:,.0f}",
                                 self.styles['LegalBody']))
        story.append(Spacer(1, 0.3*inch))

        # Full Analysis with page break
        if full_analysis_text:
            story.append(PageBreak())
            story.append(Paragraph('V. COMPREHENSIVE LITIGATION ANALYSIS', self.styles['LegalHeader']))
            story.append(Spacer(1, 0.2*inch))

            # Split and add analysis text with formal legal formatting
            lines = full_analysis_text.split('\n')
            for line in lines:
                if line.strip():
                    # Check if line is a heading (all caps or ends with colon)
                    if line.strip().isupper() or (line.strip().endswith(':') and len(line.strip()) < 80):
                        # Style as subheader
                        try:
                            story.append(Paragraph(self._sanitize_text(line), self.styles['LegalSubHeader']))
                        except:
                            pass
                    else:
                        # Chunk long lines
                        if len(line) > 1000:
                            chunks = [line[i:i+1000] for i in range(0, len(line), 1000)]
                            for chunk in chunks:
                                try:
                                    story.append(Paragraph(self._sanitize_text(chunk), self.styles['LegalBody']))
                                except:
                                    pass
                        else:
                            try:
                                story.append(Paragraph(self._sanitize_text(line), self.styles['LegalBody']))
                            except:
                                pass
                else:
                    story.append(Spacer(1, 0.1*inch))

        # Build PDF
        doc.build(story)
        return output_path
