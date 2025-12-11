"""
PDF Generation Service for FCRA Analysis Reports

Generates two types of PDFs:
1. Client Report - Professional, branded PDF for clients
2. Legal Analysis - Detailed internal analysis for legal team
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os


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

    def _add_header(self, story, title, subtitle=None):
        """Add branded header to document"""
        # Company name in header color
        header_data = [[Paragraph('<b>BRIGHTPATH ASCEND</b><br/><font size=10>FCRA Litigation Analysis</font>',
                                 ParagraphStyle('header', fontSize=14, textColor=HexColor('#1a5276'), alignment=TA_CENTER))]]
        header_table = Table(header_data, colWidths=[6.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#d5e8f0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#1a5276'))
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))

        # Title
        story.append(Paragraph(title, self.styles['ClientHeader']))
        if subtitle:
            story.append(Paragraph(subtitle, self.styles['ClientBody']))
        story.append(Spacer(1, 0.2*inch))

    def _add_summary_box(self, story, violations_count, total_exposure, case_strength):
        """Add executive summary box"""
        summary_data = [
            [Paragraph('<b>CASE SUMMARY</b>', self.styles['ClientHighlight']), ''],
            [Paragraph('Violations Found:', self.styles['ClientBody']),
             Paragraph(f'<b>{violations_count}</b>', self.styles['ClientHighlight'])],
            [Paragraph('Total Exposure:', self.styles['ClientBody']),
             Paragraph(f'<b>${total_exposure:,.0f}</b>', self.styles['ClientHighlight'])],
            [Paragraph('Case Strength:', self.styles['ClientBody']),
             Paragraph(f'<b>{case_strength}</b>', self.styles['ClientHighlight'])]
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f8ff')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#1a5276')),
            ('LINEABOVE', (0, 1), (-1, 1), 1, HexColor('#1a5276'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

    def _add_violations_table(self, story, violations):
        """Add violations table"""
        story.append(Paragraph('Violations Identified', self.styles['ClientSubHeader']))
        story.append(Spacer(1, 0.1*inch))

        # Group violations by bureau
        bureaus = {}
        for v in violations:
            bureau = v.bureau or 'Unknown'
            if bureau not in bureaus:
                bureaus[bureau] = []
            bureaus[bureau].append(v)

        for bureau, bureau_violations in bureaus.items():
            story.append(Paragraph(f'<b>{bureau}</b>', self.styles['ClientHighlight']))

            for v in bureau_violations[:10]:  # Limit to top 10 per bureau for client report
                violation_data = [
                    [Paragraph(f'<b>{v.fcra_section}</b>', self.styles['ClientBody']),
                     Paragraph(v.violation_type or 'N/A', self.styles['ClientBody'])],
                    [Paragraph(v.description or 'No description', self.styles['ClientBody']), '']
                ]

                violation_table = Table(violation_data, colWidths=[2*inch, 4*inch])
                violation_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), HexColor('#e8f4f8')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#1a5276'))
                ]))
                story.append(violation_table)
                story.append(Spacer(1, 0.1*inch))

            if len(bureau_violations) > 10:
                story.append(Paragraph(f'<i>...and {len(bureau_violations) - 10} more violations</i>',
                                     self.styles['ClientBody']))
            story.append(Spacer(1, 0.2*inch))

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
        Generate client-facing PDF report

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
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []

        # Header
        self._add_header(story, 'Your FCRA Analysis Report', f'Prepared for: {client_name}')

        # Date
        story.append(Paragraph(f'Report Date: {datetime.now().strftime("%B %d, %Y")}',
                             self.styles['ClientBody']))
        story.append(Spacer(1, 0.3*inch))

        # Summary box
        violations_count = len(violations)
        total_exposure = damages.total_exposure if damages else 0
        case_strength = self._get_case_strength_label(case_score.total_score if case_score else 0)

        self._add_summary_box(story, violations_count, total_exposure, case_strength)

        # Executive Summary
        story.append(Paragraph('What This Means', self.styles['ClientSubHeader']))
        story.append(Paragraph(
            f'Our analysis has identified <b>{violations_count} violations</b> of the Fair Credit '
            f'Reporting Act (FCRA) in your credit reports. These violations represent potential legal '
            f'claims with a total exposure of <b>${total_exposure:,.0f}</b>.',
            self.styles['ClientBody']
        ))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            'The FCRA is a federal law that protects consumers by ensuring credit reporting agencies '
            'maintain accurate information. When they fail to do so, you may be entitled to compensation.',
            self.styles['ClientBody']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Violations table
        if violations:
            self._add_violations_table(story, violations)

        # Damages breakdown
        if damages:
            story.append(Paragraph('Damages Breakdown', self.styles['ClientSubHeader']))
            story.append(Spacer(1, 0.1*inch))

            damages_data = [
                [Paragraph('<b>Damage Type</b>', self.styles['ClientBody']),
                 Paragraph('<b>Amount</b>', self.styles['ClientBody'])],
                [Paragraph('Statutory Damages', self.styles['ClientBody']),
                 Paragraph(f'${damages.statutory_damages_total:,.0f}', self.styles['ClientBody'])],
                [Paragraph('Actual Damages', self.styles['ClientBody']),
                 Paragraph(f'${damages.actual_damages_total:,.0f}', self.styles['ClientBody'])],
                [Paragraph('Punitive Damages (if willful)', self.styles['ClientBody']),
                 Paragraph(f'${damages.punitive_damages_amount:,.0f}', self.styles['ClientBody'])],
                [Paragraph('<b>Total Exposure</b>', self.styles['ClientHighlight']),
                 Paragraph(f'<b>${damages.total_exposure:,.0f}</b>', self.styles['ClientHighlight'])],
                [Paragraph('Settlement Target (65%)', self.styles['ClientBody']),
                 Paragraph(f'${damages.settlement_target:,.0f}', self.styles['ClientBody'])]
            ]

            damages_table = Table(damages_data, colWidths=[4*inch, 2*inch])
            damages_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('BACKGROUND', (0, 1), (-1, -2), HexColor('#f8f9fa')),
                ('BACKGROUND', (0, -2), (-1, -2), HexColor('#e8f4f8')),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 1, HexColor('#1a5276')),
                ('LINEABOVE', (0, -2), (-1, -2), 2, HexColor('#1a5276'))
            ]))
            story.append(damages_table)
            story.append(Spacer(1, 0.3*inch))

        # Next steps
        story.append(Paragraph('Next Steps', self.styles['ClientSubHeader']))
        story.append(Paragraph(
            '1. <b>Review this report</b> carefully and note any questions you may have.',
            self.styles['ClientBody']
        ))
        story.append(Paragraph(
            '2. <b>Contact us</b> to discuss your case and potential legal action.',
            self.styles['ClientBody']
        ))
        story.append(Paragraph(
            '3. <b>Gather documentation</b> including credit reports, denial letters, and correspondence.',
            self.styles['ClientBody']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Add page break before full analysis
        story.append(PageBreak())

        # FULL COMPREHENSIVE ANALYSIS (40-50 pages)
        if analysis.full_analysis:
            # Section header
            story.append(Paragraph('COMPREHENSIVE LITIGATION ANALYSIS', self.styles['ClientHeader']))
            story.append(Spacer(1, 0.2*inch))

            # Render full analysis text with Brightpath styling
            lines = analysis.full_analysis.split('\n')
            for line in lines:
                if line.strip():
                    # Check if line is a heading (all caps or ends with colon)
                    if line.strip().isupper() or (line.strip().endswith(':') and len(line.strip()) < 80):
                        # Style as subheader
                        try:
                            story.append(Paragraph(self._sanitize_text(line), self.styles['ClientSubHeader']))
                        except:
                            pass
                    else:
                        # Chunk very long lines (>1000 chars) to avoid ReportLab errors
                        if len(line) > 1000:
                            chunks = [line[i:i+1000] for i in range(0, len(line), 1000)]
                            for chunk in chunks:
                                try:
                                    story.append(Paragraph(self._sanitize_text(chunk), self.styles['ClientBody']))
                                except:
                                    pass
                        else:
                            try:
                                story.append(Paragraph(self._sanitize_text(line), self.styles['ClientBody']))
                            except:
                                pass
                else:
                    story.append(Spacer(1, 0.1*inch))

        # Footer on last page
        story.append(Spacer(1, 0.5*inch))
        footer_text = f'<i>This report is confidential and prepared for {client_name}. '
        footer_text += 'For questions, contact Brightpath Ascend.</i>'
        story.append(Paragraph(footer_text,
                             ParagraphStyle('footer', fontSize=9, textColor=HexColor('#7f8c8d'),
                                          alignment=TA_CENTER)))

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
