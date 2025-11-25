"""
Base PDF builder with common styles and utilities.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.colors import HexColor, black, white, lightgrey, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from datetime import datetime
import os


class BasePDFBuilder:
    """Base class for all PDF generators with common styles"""
    
    COMPANY_NAME = "Brightpath Ascend Group"
    COMPANY_ADDRESS = "1185 Avenue of the Americas 3rd Floor New York NY"
    COMPANY_PHONE = "(917) 909-4051"
    COMPANY_EMAIL = "support@brightpathascendgroup.com"
    COMPANY_WEBSITE = "http://www.brightpathascendgroup.com"
    
    PRIMARY_COLOR = HexColor('#1a1a2e')
    ACCENT_COLOR = HexColor('#4ade80')
    BLUE_COLOR = HexColor('#1a1a8e')
    WARNING_COLOR = HexColor('#dc2626')
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        self.heading1_style = ParagraphStyle(
            'CustomH1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=25,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        self.heading2_style = ParagraphStyle(
            'CustomH2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        self.heading3_style = ParagraphStyle(
            'CustomH3',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=black,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=16
        )
        
        self.body_blue_style = ParagraphStyle(
            'CustomBodyBlue',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.BLUE_COLOR,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=16
        )
        
        self.bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=black,
            spaceAfter=6,
            leftIndent=20,
            fontName='Helvetica',
            leading=14
        )
        
        self.warning_style = ParagraphStyle(
            'CustomWarning',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.WARNING_COLOR,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            leading=14
        )
        
        self.center_style = ParagraphStyle(
            'CustomCenter',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica'
        )
        
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#64748b'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
    
    def sanitize_text(self, text):
        """Remove or replace Unicode characters that Helvetica doesn't support"""
        if not text:
            return ""
        
        replacements = {
            '•': '*', '◦': '-', '∙': '*', '○': 'o',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '—': ' - ', '–': '-', '…': '...',
            '™': '(TM)', '®': '(R)', '©': '(C)',
            '€': 'EUR', '£': 'GBP', '¥': 'JPY', '°': 'deg',
            '×': 'x', '÷': '/', '≠': '!=', '≤': '<=', '≥': '>=',
            '✓': '[Y]', '✗': '[N]', '✔': '[Y]', '✘': '[N]',
            '→': '->', '←': '<-', '↑': '^', '↓': 'v',
            '✂': '[CUT]', '📋': '[DOC]', '⚠': '[!]', '❌': '[X]', '✅': '[OK]',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        text = ''.join(c if ord(c) < 128 else '' for c in text)
        return text
    
    def create_document(self, output_path, pagesize=letter):
        """Create a SimpleDocTemplate with standard margins"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return SimpleDocTemplate(
            output_path,
            pagesize=pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
    
    def add_cover_page(self, story, title, client_name, report_date=None):
        """Add a standard cover page"""
        if report_date is None:
            report_date = datetime.now().strftime("%B %d, %Y")
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(self.sanitize_text(title), self.title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Prepared for", self.subtitle_style))
        story.append(Paragraph(f"<b>{self.sanitize_text(client_name)}</b>", self.title_style))
        story.append(Paragraph(f"({report_date})", self.subtitle_style))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(f"By {self.COMPANY_NAME}", self.center_style))
        story.append(Paragraph(self.COMPANY_ADDRESS, self.center_style))
        story.append(Paragraph(f"Phone: {self.COMPANY_PHONE}", self.center_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(self.COMPANY_EMAIL, self.center_style))
        story.append(Paragraph(self.COMPANY_WEBSITE, self.center_style))
        story.append(PageBreak())
    
    def add_section_header(self, story, title, level=1):
        """Add a section header"""
        if level == 1:
            story.append(Paragraph(self.sanitize_text(title), self.heading1_style))
        elif level == 2:
            story.append(Paragraph(self.sanitize_text(title), self.heading2_style))
        else:
            story.append(Paragraph(self.sanitize_text(title), self.heading3_style))
    
    def add_paragraph(self, story, text, style=None):
        """Add a paragraph with optional style"""
        if style is None:
            style = self.body_style
        story.append(Paragraph(self.sanitize_text(text), style))
    
    def add_bullet_list(self, story, items):
        """Add a bullet list"""
        for item in items:
            story.append(Paragraph(f"* {self.sanitize_text(item)}", self.bullet_style))
    
    def add_numbered_list(self, story, items):
        """Add a numbered list"""
        for i, item in enumerate(items, 1):
            story.append(Paragraph(f"{i}. {self.sanitize_text(item)}", self.bullet_style))
    
    def add_table(self, story, data, col_widths=None):
        """Add a styled table"""
        if col_widths is None:
            col_widths = [2*inch] * len(data[0]) if data else []
        
        sanitized_data = [[self.sanitize_text(str(cell)) for cell in row] for row in data]
        
        table = Table(sanitized_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f1f5f9')),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def add_info_box(self, story, title, content, box_color=None):
        """Add an info box with title and content"""
        if box_color is None:
            box_color = HexColor('#f0f9ff')
        
        box_data = [[Paragraph(f"<b>{self.sanitize_text(title)}</b>", self.heading3_style)],
                    [Paragraph(self.sanitize_text(content), self.body_style)]]
        
        table = Table(box_data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), box_color),
            ('BOX', (0, 0), (-1, -1), 1, self.PRIMARY_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def format_currency(self, amount):
        """Format amount as currency"""
        try:
            return f"${float(amount):,.2f}"
        except:
            return "$0.00"
    
    def format_date(self, date_obj):
        """Format date for display"""
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime("%B %d, %Y")
        return str(date_obj) if date_obj else "N/A"
