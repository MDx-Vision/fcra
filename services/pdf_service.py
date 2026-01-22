"""
PDF Generation Service for FCRA Analysis Reports

Generates two types of PDFs:
1. Client Report - Professional, branded PDF for clients (using WeasyPrint)
2. Legal Analysis - Detailed internal analysis for legal team (using ReportLab)
"""

import os
import re
from datetime import datetime

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from weasyprint import HTML

# Brightpath Ascend brand colors (matching email template)
PRIMARY_COLOR = "#319795"  # Teal/cyan
SECONDARY_COLOR = "#84cc16"  # Lime green
DARK_COLOR = "#1a1a2e"  # Dark navy


class FCRAPDFGenerator:
    """Generate professional FCRA analysis PDFs"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        # Client report styles
        self.styles.add(
            ParagraphStyle(
                name="ClientHeader",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=HexColor("#1a5276"),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ClientSubHeader",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=HexColor("#1a5276"),
                spaceAfter=10,
                spaceBefore=10,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ClientBody",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=HexColor("#2c3e50"),
                spaceAfter=8,
                fontName="Helvetica",
                leading=14,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ClientHighlight",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=HexColor("#1a5276"),
                spaceAfter=8,
                fontName="Helvetica-Bold",
                leading=15,
            )
        )

        # Legal report styles (formal serif fonts, no colors)
        self.styles.add(
            ParagraphStyle(
                name="LegalTitle",
                parent=self.styles["Heading1"],
                fontSize=14,
                textColor=HexColor("#000000"),
                spaceAfter=12,
                spaceBefore=0,
                fontName="Times-Bold",
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="LegalHeader",
                parent=self.styles["Heading1"],
                fontSize=12,
                textColor=HexColor("#000000"),
                spaceAfter=10,
                spaceBefore=10,
                fontName="Times-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="LegalSubHeader",
                parent=self.styles["Heading2"],
                fontSize=11,
                textColor=HexColor("#000000"),
                spaceAfter=8,
                spaceBefore=8,
                fontName="Times-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="LegalBody",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=HexColor("#000000"),
                spaceAfter=8,
                fontName="Times-Roman",
                leading=14,
                firstLineIndent=0,
            )
        )

    def _add_branded_header(self, story, title, subtitle=None):
        """Add Brightpath Ascend branded header banner (matching email template)"""
        # Teal header banner with white text (matching email template)
        header_text = "<font size=16 color=white><b>BRIGHTPATH ASCEND</b></font><br/>"
        header_text += "<font size=10 color=white>FCRA Litigation Analysis</font>"

        header_para = Paragraph(
            header_text,
            ParagraphStyle(
                "BrandHeader",
                fontSize=16,
                textColor=white,
                alignment=TA_CENTER,
                spaceAfter=0,
            ),
        )

        header_table = Table([[header_para]], colWidths=[6.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        HexColor(PRIMARY_COLOR),
                    ),  # Teal background
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 0.3 * inch))

        # Document title
        if title:
            story.append(Paragraph(title, self.styles["ClientHeader"]))
        if subtitle:
            story.append(Paragraph(subtitle, self.styles["ClientBody"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Spacer(1, 0.2 * inch))

    def _add_summary_box(self, story, violations_count, total_exposure, case_strength):
        """Add executive summary box with color-coded case strength (matching email template)"""
        # Color-coded case strength boxes (matching email template)
        strength_colors = {
            "Strong": {"bg": "#dcfce7", "text": "#166534", "border": "#86efac"},
            "Moderate": {"bg": "#fef3c7", "text": "#92400e", "border": "#fcd34d"},
            "Weak": {"bg": "#fee2e2", "text": "#991b1b", "border": "#fca5a5"},
            "Developing": {"bg": "#fef3c7", "text": "#92400e", "border": "#fcd34d"},
        }
        colors = strength_colors.get(case_strength, strength_colors["Moderate"])

        # Three-column summary layout (matching email template)
        summary_data = [
            [
                Paragraph(
                    f'<font size=32 color="{colors["text"]}"><b>{violations_count}</b></font><br/>'
                    f'<font size=10 color="{colors["text"]}">FCRA Violations</font>',
                    ParagraphStyle("sum1", alignment=TA_CENTER),
                ),
                Paragraph(
                    f'<font size=32 color="{colors["text"]}"><b>${total_exposure:,.0f}</b></font><br/>'
                    f'<font size=10 color="{colors["text"]}">Total Exposure</font>',
                    ParagraphStyle("sum2", alignment=TA_CENTER),
                ),
                Paragraph(
                    f'<font size=24 color="{colors["text"]}"><b>{case_strength}</b></font><br/>'
                    f'<font size=10 color="{colors["text"]}">Case Strength</font>',
                    ParagraphStyle("sum3", alignment=TA_CENTER),
                ),
            ]
        ]

        summary_table = Table(
            summary_data, colWidths=[2.16 * inch, 2.16 * inch, 2.16 * inch]
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor(colors["bg"])),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 15),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                    ("BOX", (0, 0), (-1, -1), 2, HexColor(colors["border"])),
                    ("LINEAFTER", (0, 0), (0, 0), 1, HexColor(colors["border"])),
                    ("LINEAFTER", (1, 0), (1, 0), 1, HexColor(colors["border"])),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

    def _add_violations_table(self, story, violations):
        """Add violations table"""
        story.append(Paragraph("Violations Identified", self.styles["ClientSubHeader"]))
        story.append(Spacer(1, 0.1 * inch))

        # Group violations by bureau
        bureaus = {}
        for v in violations:
            bureau = v.bureau or "Unknown"
            if bureau not in bureaus:
                bureaus[bureau] = []
            bureaus[bureau].append(v)

        for bureau, bureau_violations in bureaus.items():
            story.append(Paragraph(f"<b>{bureau}</b>", self.styles["ClientHighlight"]))

            for v in bureau_violations[
                :10
            ]:  # Limit to top 10 per bureau for client report
                violation_data = [
                    [
                        Paragraph(
                            f"<b>{v.fcra_section}</b>", self.styles["ClientBody"]
                        ),
                        Paragraph(v.violation_type or "N/A", self.styles["ClientBody"]),
                    ],
                    [
                        Paragraph(
                            v.description or "No description", self.styles["ClientBody"]
                        ),
                        "",
                    ],
                ]

                violation_table = Table(violation_data, colWidths=[2 * inch, 4 * inch])
                violation_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (1, 0), HexColor("#e8f4f8")),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#1a5276")),
                        ]
                    )
                )
                story.append(violation_table)
                story.append(Spacer(1, 0.1 * inch))

            if len(bureau_violations) > 10:
                story.append(
                    Paragraph(
                        f"<i>...and {len(bureau_violations) - 10} more violations</i>",
                        self.styles["ClientBody"],
                    )
                )
            story.append(Spacer(1, 0.2 * inch))

    def _sanitize_text(self, text):
        """Sanitize text for PDF rendering"""
        if not text:
            return ""
        # Replace problematic characters
        replacements = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            "\x00": "",
            "\r": "",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def generate_client_report(
        self, output_path, client_name, violations, damages, case_score, analysis
    ):
        """
        Generate client-facing PDF report using WeasyPrint (40-50 pages, NO dispute letters)

        Args:
            output_path: Path to save PDF
            client_name: Client's name
            violations: List of Violation objects
            damages: Damages object
            case_score: CaseScore object
            analysis: Analysis object
        """
        # Parse full_analysis and STOP before dispute letters
        analysis_text = ""
        if analysis.full_analysis:
            lines = analysis.full_analysis.split("\n")
            for line in lines:
                # Stop if we hit dispute letter sections
                if any(
                    marker in line.upper()
                    for marker in [
                        "DISPUTE LETTER",
                        "START OF DISPUTE",
                        "ROUND 1 LETTER",
                        "CERTIFIED MAIL",
                        "DEAR SIR/MADAM",
                        "--- DISPUTE LETTER ---",
                        "LETTER TO",
                        "RE: DISPUTE",
                    ]
                ):
                    break
                analysis_text += line + "\n"

        # Convert markdown to HTML
        analysis_content = self._markdown_to_html(analysis_text)

        # Extract data
        violations_count = len(violations) if violations else 0
        total_exposure = damages.total_exposure if damages else 0
        settlement_target = damages.settlement_target if damages else 0
        case_strength = self._get_case_strength_label(
            case_score.total_score if case_score else 0
        )

        # Build HTML with COMPLETE styling from reference template
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Credit Analysis Report - {client_name}</title>
  <style>
    @media print {{
      .page-break {{ page-break-before: always; }}
      .no-break {{ page-break-inside: avoid; }}
      body {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      padding: 0;
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #333;
      background-color: #fff;
    }}

    .page {{
      max-width: 8.5in;
      margin: 0 auto;
      padding: 0.75in 1in;
      background-color: white;
      min-height: 11in;
    }}

    /* COVER PAGE */
    .cover-page {{
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      min-height: 10in;
      padding: 1in;
    }}
    .cover-logo {{
      width: 120px;
      height: 120px;
      margin-bottom: 20px;
    }}
    .cover-company {{
      font-size: 18pt;
      font-weight: bold;
      color: #0d9488;
      letter-spacing: 2px;
      margin-bottom: 5px;
    }}
    .cover-tagline {{
      font-size: 11pt;
      color: #666;
      margin-bottom: 60px;
    }}
    .cover-title {{
      font-size: 28pt;
      font-weight: bold;
      color: #1e3a5f;
      margin-bottom: 10px;
    }}
    .cover-subtitle {{
      font-size: 14pt;
      color: #666;
      margin-bottom: 60px;
    }}
    .cover-client {{
      font-size: 16pt;
      color: #333;
      margin-bottom: 10px;
    }}
    .cover-meta {{
      font-size: 11pt;
      color: #666;
    }}
    .cover-meta div {{
      margin: 5px 0;
    }}
    .cover-confidential {{
      margin-top: 80px;
      padding: 15px 30px;
      border: 2px solid #c41e3a;
      color: #c41e3a;
      font-weight: bold;
      font-size: 12pt;
    }}

    /* HEADERS */
    .page-header {{
      border-bottom: 2px solid #0d9488;
      padding-bottom: 10px;
      margin-bottom: 25px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .page-header-left {{
      font-size: 10pt;
      color: #0d9488;
      font-weight: bold;
    }}
    .page-header-right {{
      font-size: 9pt;
      color: #666;
      text-align: right;
    }}

    /* SECTION HEADERS */
    h1 {{
      font-size: 20pt;
      color: #1e3a5f;
      margin: 0 0 20px 0;
      padding-bottom: 10px;
      border-bottom: 3px solid #0d9488;
    }}
    h2 {{
      font-size: 14pt;
      color: #1e3a5f;
      margin: 25px 0 15px 0;
      padding-bottom: 5px;
      border-bottom: 1px solid #ccc;
    }}
    h3 {{
      font-size: 12pt;
      color: #0d9488;
      margin: 20px 0 10px 0;
    }}

    /* CALL-OUT BOXES */
    .callout {{
      background-color: #f8f9fa;
      border-left: 4px solid #0d9488;
      padding: 15px 20px;
      margin: 20px 0;
    }}
    .callout.warning {{
      background-color: #fff8e1;
      border-color: #ffc107;
    }}
    .callout.danger {{
      background-color: #ffebee;
      border-color: #dc3545;
    }}
    .callout.success {{
      background-color: #e8f5e9;
      border-color: #28a745;
    }}
    .callout-title {{
      font-weight: bold;
      color: #1e3a5f;
      margin-bottom: 8px;
    }}

    /* TABLES */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
      font-size: 10pt;
    }}
    th {{
      background-color: #1e3a5f;
      color: white;
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
    }}
    td {{
      border: 1px solid #ddd;
      padding: 10px 12px;
      vertical-align: top;
    }}
    tr:nth-child(even) {{
      background-color: #f9f9f9;
    }}

    /* SUMMARY BOX */
    .summary-box {{
      background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
      color: white;
      padding: 25px;
      border-radius: 8px;
      margin: 20px 0;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      text-align: center;
    }}
    .summary-item .label {{
      font-size: 10pt;
      opacity: 0.8;
      text-transform: uppercase;
    }}
    .summary-item .value {{
      font-size: 24pt;
      font-weight: bold;
    }}

    /* LISTS */
    ul, ol {{
      margin: 10px 0 10px 20px;
      padding: 0;
    }}
    li {{
      margin: 8px 0;
    }}

    /* PAGE FOOTER */
    .page-footer {{
      margin-top: auto;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      font-size: 9pt;
      color: #888;
      display: flex;
      justify-content: space-between;
    }}

    /* TOC */
    .toc-item {{
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px dotted #ccc;
    }}
    .toc-section {{
      font-weight: bold;
      color: #1e3a5f;
    }}
    .toc-page {{
      color: #666;
    }}

    /* ACCOUNT CARD */
    .account-card {{
      border: 1px solid #ddd;
      border-radius: 8px;
      margin: 20px 0;
      overflow: hidden;
    }}
    .account-header {{
      background-color: #1e3a5f;
      color: white;
      padding: 12px 15px;
      font-weight: bold;
    }}
    .account-body {{
      padding: 15px;
    }}
    .account-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px;
      margin: 10px 0;
    }}
    .account-field {{
      font-size: 10pt;
    }}
    .account-field .label {{
      color: #666;
      font-size: 9pt;
    }}
    .violation-badge {{
      display: inline-block;
      background-color: #dc3545;
      color: white;
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 9pt;
      font-weight: bold;
    }}

    /* TIMELINE */
    .timeline {{
      position: relative;
      padding-left: 30px;
    }}
    .timeline:before {{
      content: '';
      position: absolute;
      left: 10px;
      top: 0;
      bottom: 0;
      width: 2px;
      background-color: #0d9488;
    }}
    .timeline-item {{
      position: relative;
      margin: 20px 0;
    }}
    .timeline-item:before {{
      content: '';
      position: absolute;
      left: -24px;
      top: 5px;
      width: 12px;
      height: 12px;
      background-color: #0d9488;
      border-radius: 50%;
    }}
    .timeline-title {{
      font-weight: bold;
      color: #1e3a5f;
    }}
    .timeline-date {{
      font-size: 10pt;
      color: #666;
    }}

    p {{
      margin: 12px 0;
      text-align: justify;
    }}

    .highlight {{
      background-color: #fff3cd;
      padding: 2px 5px;
    }}

    .text-center {{ text-align: center; }}
    .text-right {{ text-align: right; }}
    .mt-20 {{ margin-top: 20px; }}
    .mb-20 {{ margin-bottom: 20px; }}
  </style>
</head>
<body>

<!-- ==================== COVER PAGE ==================== -->
<div class="page cover-page">
  <div class="cover-company">BRIGHTPATH ASCEND GROUP</div>
  <div class="cover-tagline">FCRA Litigation Services</div>

  <div class="cover-title">Confidential Credit<br>Analysis Report</div>
  <div class="cover-subtitle">Fair Credit Reporting Act Violation Assessment</div>

  <div class="cover-client">Prepared for: <strong>{client_name}</strong></div>

  <div class="cover-meta">
    <div><strong>Report Date:</strong> {datetime.now().strftime("%B %d, %Y")}</div>
    <div><strong>Case Number:</strong> BAG-FCRA-{analysis.id}</div>
  </div>

  <div class="cover-confidential">⚠️ CONFIDENTIAL — FOR CLIENT USE ONLY</div>
</div>

<!-- ==================== TABLE OF CONTENTS ==================== -->
<div class="page page-break">
  <div class="page-header">
    <div class="page-header-left">BRIGHTPATH ASCEND GROUP</div>
    <div class="page-header-right">BAG-FCRA-{analysis.id} | {client_name.split()[-1] if client_name else 'Client'}</div>
  </div>

  <h1>Table of Contents</h1>

  <div class="toc-item"><span class="toc-section">Section 1: Executive Summary</span><span class="toc-page">3</span></div>
  <div class="toc-item"><span class="toc-section">Section 2: Understanding Your Rights</span><span class="toc-page">5</span></div>
  <div class="toc-item"><span class="toc-section">Section 3: Comprehensive Analysis</span><span class="toc-page">9</span></div>
  <div class="toc-item"><span class="toc-section">Section 4: Next Steps</span><span class="toc-page">42</span></div>
  <div class="toc-item"><span class="toc-section">Appendix A: Glossary of Terms</span><span class="toc-page">46</span></div>
</div>

<!-- ==================== SECTION 1: EXECUTIVE SUMMARY ==================== -->
<div class="page page-break">
  <div class="page-header">
    <div class="page-header-left">BRIGHTPATH ASCEND GROUP</div>
    <div class="page-header-right">Section 1: Executive Summary</div>
  </div>

  <h1>Section 1: Executive Summary</h1>

  <p>Dear {client_name.split()[0] if client_name else 'Client'},</p>

  <p>Thank you for choosing Brightpath Ascend Group to analyze your credit reports. We have completed a comprehensive forensic examination of your credit files from all three major credit reporting agencies.</p>

  <p><strong>Our analysis has identified significant violations of the Fair Credit Reporting Act (FCRA)</strong> that are negatively impacting your credit profile and potentially causing you financial harm.</p>

  <div class="summary-box">
    <div class="summary-grid">
      <div class="summary-item">
        <div class="label">Violations Identified</div>
        <div class="value">{violations_count}+</div>
      </div>
      <div class="summary-item">
        <div class="label">Estimated Case Value</div>
        <div class="value">${total_exposure:,.0f}</div>
      </div>
      <div class="summary-item">
        <div class="label">Settlement Probability</div>
        <div class="value">75-85%</div>
      </div>
    </div>
  </div>

  <h2>What This Means</h2>
  <p>Our analysis has identified <strong>{violations_count} violations</strong> of the Fair Credit Reporting Act (FCRA) in your credit reports. These violations represent potential legal claims with a total exposure of <strong>${total_exposure:,.0f}</strong>.</p>

  <p>The FCRA is a federal law that protects consumers by ensuring credit reporting agencies maintain accurate information. When they fail to do so, you may be entitled to compensation including statutory damages ($100-$1,000 per violation), punitive damages, actual damages, and attorney fees.</p>

  <div class="callout success">
    <div class="callout-title">✓ PROCEED WITH FCRA CLAIMS</div>
    <p>Based on our analysis, we recommend proceeding with formal FCRA disputes using our proven strategy. Settlement probability for cases like yours is <strong>75-85%</strong> within 60-120 days.</p>
  </div>
</div>

<!-- COMPREHENSIVE ANALYSIS -->
<div class="page page-break">
  <div class="page-header">
    <div class="page-header-left">BRIGHTPATH ASCEND GROUP</div>
    <div class="page-header-right">Comprehensive Analysis</div>
  </div>

  <h1>Comprehensive Litigation Analysis</h1>

  <div style="line-height: 1.8;">
    {analysis_content}
  </div>
</div>

<!-- NEXT STEPS -->
<div class="page page-break">
  <div class="page-header">
    <div class="page-header-left">BRIGHTPATH ASCEND GROUP</div>
    <div class="page-header-right">Next Steps</div>
  </div>

  <h1>Next Steps</h1>

  <h2>What We Need From You</h2>
  <div class="callout">
    <div class="callout-title">Action Items</div>
    <ol>
      <li><strong>Review this report</strong> — Make sure you understand the violations we've identified</li>
      <li><strong>Provide approval</strong> — Reply to our email to confirm you want to proceed</li>
      <li><strong>Gather denial letters</strong> — Any credit denial or adverse action notices strengthen your case</li>
      <li><strong>Sign engagement documents</strong> — We'll send you our engagement letter</li>
    </ol>
  </div>

  <h2>What Happens After You Approve</h2>
  <p><strong>Within 48 hours:</strong> We prepare customized dispute letters for all defendants</p>
  <p><strong>Within 5 business days:</strong> All letters sent via certified mail</p>
  <p><strong>60-120 days:</strong> Expected resolution through settlement or formal proceedings</p>

  <h2>Contact Information</h2>
  <p><strong>Email:</strong> cases@brightpathascend.com</p>
  <p><strong>Website:</strong> www.brightpathascend.com</p>

  <div style="margin-top: 40px; padding: 20px; background-color: #1e3a5f; color: white; border-radius: 8px; text-align: center;">
    <div style="font-size: 14pt; font-weight: bold;">BRIGHTPATH ASCEND GROUP</div>
    <div style="font-size: 11pt; opacity: 0.9; margin-top: 5px;">Protecting Your Rights Under the Fair Credit Reporting Act</div>
    <div style="margin-top: 15px; font-size: 10pt; opacity: 0.8;">
      Report Date: {datetime.now().strftime("%B %d, %Y")} | Confidential
    </div>
  </div>
</div>

</body>
</html>"""

        # Convert HTML to PDF using WeasyPrint
        HTML(string=html_content).write_pdf(output_path)
        return output_path

    def _escape_html(self, text):
        """Escape HTML special characters"""
        if not text:
            return ""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _markdown_to_html(self, text):
        """Convert markdown to styled HTML"""
        if not text:
            return ""

        # Split into lines for processing
        lines = text.split("\n")
        html_lines = []
        in_list = False
        in_table = False
        table_rows = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append("<br/>")
                continue

            # Headers
            if stripped.startswith("###"):
                text = stripped[3:].strip()
                html_lines.append(f"<h3>{self._escape_html(text)}</h3>")
            elif stripped.startswith("##"):
                text = stripped[2:].strip()
                html_lines.append(f"<h2>{self._escape_html(text)}</h2>")
            elif stripped.startswith("#"):
                text = stripped[1:].strip()
                html_lines.append(f"<h1>{self._escape_html(text)}</h1>")

            # Horizontal rules
            elif stripped.startswith("---") or stripped.startswith("___"):
                html_lines.append(
                    '<hr style="border: 1px solid #ccc; margin: 20px 0;">'
                )

            # Lists
            elif stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                text = stripped[2:].strip()
                # Apply inline formatting
                text = self._apply_inline_formatting(text)
                html_lines.append(f"<li>{text}</li>")

            # Numbered lists
            elif re.match(r"^\d+\.\s", stripped):
                text = re.sub(r"^\d+\.\s", "", stripped)
                text = self._apply_inline_formatting(text)
                html_lines.append(f"<li>{text}</li>")

            # Tables (simple detection)
            elif "|" in stripped:
                # Skip for now, handle simple cases
                continue

            # Regular paragraphs
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                text = self._apply_inline_formatting(stripped)
                html_lines.append(f"<p>{text}</p>")

        if in_list:
            html_lines.append("</ul>")

        return "\n".join(html_lines)

    def _apply_inline_formatting(self, text):
        """Apply bold, italic, and other inline markdown formatting"""
        # Escape HTML first
        text = self._escape_html(text)

        # Bold: **text** or __text__
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

        # Italic: *text* or _text_ (but not inside words)
        text = re.sub(r"\*([^*]+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"\b_([^_]+?)_\b", r"<em>\1</em>", text)

        # Code: `code`
        text = re.sub(
            r"`([^`]+?)`",
            r'<code style="background: #f4f4f4; padding: 2px 4px; border-radius: 3px;">\1</code>',
            text,
        )

        return text

    def _get_case_strength_label(self, score):
        """Convert numeric score to label"""
        if score >= 8:
            return "Strong"
        elif score >= 5:
            return "Moderate"
        else:
            return "Developing"

    def generate_legal_analysis(
        self,
        output_path,
        client_name,
        violations,
        standing,
        damages,
        case_score,
        analysis,
        full_analysis_text,
    ):
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
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )
        story = []

        # Formal Legal Document Header
        story.append(
            Paragraph(
                "FCRA LITIGATION ANALYSIS - CONFIDENTIAL", self.styles["LegalTitle"]
            )
        )
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(f"<b>Client:</b> {client_name}", self.styles["LegalBody"])
        )
        story.append(
            Paragraph(f"<b>Analysis ID:</b> {analysis.id}", self.styles["LegalBody"])
        )
        story.append(
            Paragraph(
                f'<b>Date:</b> {analysis.created_at.strftime("%B %d, %Y")}',
                self.styles["LegalBody"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Confidentiality notice
        story.append(
            Paragraph(
                "<i>This document contains confidential attorney work product and privileged information. "
                "It is prepared for internal legal review and potential submission to counsel. "
                "Unauthorized disclosure is prohibited.</i>",
                ParagraphStyle(
                    "notice",
                    fontSize=9,
                    textColor=HexColor("#000000"),
                    fontName="Times-Italic",
                    alignment=TA_CENTER,
                    spaceAfter=12,
                ),
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Case Score
        if case_score:
            story.append(
                Paragraph(
                    f"I. CASE STRENGTH SCORE: {case_score.total_score}/10",
                    self.styles["LegalHeader"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

        # Violations
        story.append(
            Paragraph(
                f"II. VIOLATIONS IDENTIFIED: {len(violations)}",
                self.styles["LegalHeader"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        for v in violations:
            text = f"• {v.fcra_section} - {v.violation_type} ({v.bureau})"
            story.append(Paragraph(self._sanitize_text(text), self.styles["LegalBody"]))

            desc = f"  {v.description or 'No description'}"
            story.append(Paragraph(self._sanitize_text(desc), self.styles["LegalBody"]))

            willful = f"  Willful: {'Yes' if v.is_willful else 'No'}"
            story.append(Paragraph(willful, self.styles["LegalBody"]))

            damages_range = f"  Statutory Damages: ${v.statutory_damages_min}-${v.statutory_damages_max}"
            story.append(Paragraph(damages_range, self.styles["LegalBody"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.2 * inch))

        # Standing Analysis
        story.append(Paragraph("III. STANDING ANALYSIS", self.styles["LegalHeader"]))
        if standing:
            story.append(
                Paragraph(
                    f"• Concrete Harm: {'Yes' if standing.has_concrete_harm else 'No'}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Dissemination: {'Yes' if standing.has_dissemination else 'No'}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Causation: {'Yes' if standing.has_causation else 'No'}",
                    self.styles["LegalBody"],
                )
            )
        story.append(Spacer(1, 0.2 * inch))

        # Damages Calculation
        story.append(Paragraph("IV. DAMAGES CALCULATION", self.styles["LegalHeader"]))
        if damages:
            story.append(
                Paragraph(
                    f"• Actual Damages: ${damages.actual_damages_total:,.0f}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Statutory Damages: ${damages.statutory_damages_total:,.0f}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Punitive Damages: ${damages.punitive_damages_amount:,.0f}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Total Exposure: ${damages.total_exposure:,.0f}",
                    self.styles["LegalBody"],
                )
            )
            story.append(
                Paragraph(
                    f"• Settlement Target (65%): ${damages.settlement_target:,.0f}",
                    self.styles["LegalBody"],
                )
            )
        story.append(Spacer(1, 0.3 * inch))

        # Full Analysis with page break
        if full_analysis_text:
            story.append(PageBreak())
            story.append(
                Paragraph(
                    "V. COMPREHENSIVE LITIGATION ANALYSIS", self.styles["LegalHeader"]
                )
            )
            story.append(Spacer(1, 0.2 * inch))

            # Split and add analysis text with formal legal formatting
            lines = full_analysis_text.split("\n")
            for line in lines:
                if line.strip():
                    # Check if line is a heading (all caps or ends with colon)
                    if line.strip().isupper() or (
                        line.strip().endswith(":") and len(line.strip()) < 80
                    ):
                        # Style as subheader
                        try:
                            story.append(
                                Paragraph(
                                    self._sanitize_text(line),
                                    self.styles["LegalSubHeader"],
                                )
                            )
                        except:
                            pass
                    else:
                        # Chunk long lines
                        if len(line) > 1000:
                            chunks = [
                                line[i : i + 1000] for i in range(0, len(line), 1000)
                            ]
                            for chunk in chunks:
                                try:
                                    story.append(
                                        Paragraph(
                                            self._sanitize_text(chunk),
                                            self.styles["LegalBody"],
                                        )
                                    )
                                except:
                                    pass
                        else:
                            try:
                                story.append(
                                    Paragraph(
                                        self._sanitize_text(line),
                                        self.styles["LegalBody"],
                                    )
                                )
                            except:
                                pass
                else:
                    story.append(Spacer(1, 0.1 * inch))

        # Build PDF
        doc.build(story)
        return output_path

    def generate_envelope_cover_sheet(
        self,
        bureau: str,
        bureau_address: str,
        client_name: str,
        client_address: str,
        documents: list,
        police_case_number: str = None,
        ftc_reference_number: str = None,
    ) -> bytes:
        """
        Generate a cover sheet PDF for 5-Day Knock-Out envelope packets.

        Args:
            bureau: Bureau name (Experian, Equifax, TransUnion)
            bureau_address: Bureau fraud department address
            client_name: Client's full name
            client_address: Client's mailing address
            documents: List of document names included in the packet
            police_case_number: Police report case number
            ftc_reference_number: FTC complaint reference number

        Returns:
            PDF bytes
        """
        from io import BytesIO
        from datetime import datetime

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    @page {{
      size: letter;
      margin: 0.75in;
    }}
    body {{
      font-family: Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.5;
      color: #1a1a2e;
    }}
    .header {{
      background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
      color: white;
      padding: 20px;
      margin: -0.75in -0.75in 20px -0.75in;
      text-align: center;
    }}
    .header h1 {{
      margin: 0;
      font-size: 18pt;
    }}
    .header .subtitle {{
      font-size: 11pt;
      opacity: 0.9;
      margin-top: 5px;
    }}
    .warning-box {{
      background-color: #fef3c7;
      border: 2px solid #f59e0b;
      border-radius: 8px;
      padding: 15px;
      margin: 20px 0;
    }}
    .warning-box h3 {{
      color: #b45309;
      margin: 0 0 10px 0;
      font-size: 12pt;
    }}
    .section {{
      margin: 25px 0;
    }}
    .section h2 {{
      color: #1e3a5f;
      font-size: 14pt;
      border-bottom: 2px solid #0d9488;
      padding-bottom: 5px;
      margin-bottom: 15px;
    }}
    .address-box {{
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 15px;
      margin: 15px 0;
    }}
    .address-label {{
      font-size: 10pt;
      color: #64748b;
      text-transform: uppercase;
      margin-bottom: 5px;
    }}
    .address-content {{
      font-size: 12pt;
      font-weight: bold;
    }}
    .checklist {{
      list-style: none;
      padding: 0;
    }}
    .checklist li {{
      padding: 10px 15px;
      margin: 8px 0;
      background-color: #f8fafc;
      border-left: 4px solid #0d9488;
      border-radius: 0 4px 4px 0;
    }}
    .checklist li::before {{
      content: "☐ ";
      font-size: 14pt;
      color: #0d9488;
    }}
    .case-info {{
      display: flex;
      gap: 20px;
      margin: 15px 0;
    }}
    .case-info-item {{
      flex: 1;
      background-color: #eff6ff;
      border-radius: 8px;
      padding: 15px;
      text-align: center;
    }}
    .case-info-label {{
      font-size: 10pt;
      color: #1e40af;
      text-transform: uppercase;
    }}
    .case-info-value {{
      font-size: 14pt;
      font-weight: bold;
      color: #1e3a5f;
      margin-top: 5px;
    }}
    .footer {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
      font-size: 9pt;
      color: #64748b;
      text-align: center;
    }}
    .legal-notice {{
      background-color: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 8px;
      padding: 15px;
      margin: 20px 0;
      font-size: 10pt;
    }}
    .legal-notice strong {{
      color: #dc2626;
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>⚠️ FCRA §605B IDENTITY THEFT DISPUTE</h1>
  <div class="subtitle">FRAUD DEPARTMENT - CERTIFIED MAIL REQUIRED</div>
</div>

<div class="warning-box">
  <h3>⚡ IMPORTANT: 4 BUSINESS DAY DEADLINE</h3>
  <p>Under FCRA §605B(a), credit bureaus MUST block disputed information within <strong>4 BUSINESS DAYS</strong> of receiving this packet (not 30 days). Failure to comply subjects the bureau to statutory damages of $100-$1,000 per violation.</p>
</div>

<div class="section">
  <h2>📮 SEND TO FRAUD DEPARTMENT</h2>
  <div class="address-box">
    <div class="address-label">Bureau Fraud Address</div>
    <div class="address-content">
      {bureau} Fraud Department<br>
      {bureau_address.replace(', ', '<br>')}
    </div>
  </div>
</div>

<div class="section">
  <h2>👤 FROM (CONSUMER)</h2>
  <div class="address-box">
    <div class="address-label">Consumer Address</div>
    <div class="address-content">
      {client_name}<br>
      {client_address.replace(', ', '<br>') if client_address else 'Address on file'}
    </div>
  </div>
</div>

<div class="case-info">
  <div class="case-info-item">
    <div class="case-info-label">Police Case #</div>
    <div class="case-info-value">{police_case_number or 'Attached'}</div>
  </div>
  <div class="case-info-item">
    <div class="case-info-label">FTC Reference #</div>
    <div class="case-info-value">{ftc_reference_number or 'Attached'}</div>
  </div>
  <div class="case-info-item">
    <div class="case-info-label">Date Mailed</div>
    <div class="case-info-value">{datetime.now().strftime('%m/%d/%Y')}</div>
  </div>
</div>

<div class="section">
  <h2>📋 DOCUMENT CHECKLIST - Verify Before Sealing</h2>
  <ul class="checklist">
    {''.join([f'<li>{doc}</li>' for doc in documents])}
  </ul>
</div>

<div class="legal-notice">
  <strong>LEGAL NOTICE:</strong> This packet contains an identity theft dispute pursuant to FCRA §605B.
  The consumer has filed a police report (case #{police_case_number or 'attached'}) and FTC Identity Theft Report
  (reference #{ftc_reference_number or 'attached'}). Per 15 U.S.C. §1681c-2(a), you are required to block this
  information within 4 business days of receipt.
</div>

<div class="footer">
  <p>Generated by Brightpath Ascend Group | {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  <p>This cover sheet should be placed on TOP of all documents in the envelope.</p>
</div>

</body>
</html>"""

        # Convert HTML to PDF bytes using WeasyPrint
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        return pdf_buffer.getvalue()
