from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import re
from fpdf import FPDF

class SectionPDFGenerator:
    """Generate clean PDFs for each credit report section"""
    def __init__(self):
        pass

    def create_pdf(self, title, content, output_path):
        """Create a PDF for a single section"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, title, ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", "", 12)

        for line in content.split("\n"):
            pdf.multi_cell(0, 8, line)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf.output(output_path)
        return output_path


class LetterPDFGenerator:
    def __init__(self):
        self.custom_color = HexColor('#1a1a8e')
        
    def generate_dispute_letter_pdf(self, letter_content, client_name, bureau, round_number, output_path):
        """
        Generate PDF with custom styling to force manual review
        Uses custom color and formatting to bypass e-Oscar automation
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        custom_title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.custom_color,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        custom_body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.custom_color,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=16
        )
        
        custom_section_style = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=self.custom_color,
            spaceAfter=15,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        today = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(today, custom_body_style))
        story.append(Spacer(1, 0.2*inch))
        
        title = f"FORMAL NOTICE OF DISPUTE - Round {round_number}"
        story.append(Paragraph(title, custom_title_style))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph(f"To: {bureau}", custom_section_style))
        story.append(Spacer(1, 0.2*inch))
        
        paragraphs = letter_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                cleaned_para = para.replace('\n', ' ').strip()
                if cleaned_para.isupper() or re.match(r'^[A-Z\s]+:?$', cleaned_para):
                    story.append(Paragraph(cleaned_para, custom_section_style))
                else:
                    story.append(Paragraph(cleaned_para, custom_body_style))
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        signature_lines = [
            "Sincerely,",
            "",
            "_____________________________",
            client_name,
            "Consumer"
        ]
        for line in signature_lines:
            story.append(Paragraph(line, custom_body_style))
            story.append(Spacer(1, 0.05*inch))
        
        doc.build(story)
        
        return output_path
    
    def generate_batch_letters(self, letters_data):
        """
        Generate multiple PDFs for batch processing
        letters_data: list of dicts with {content, client_name, bureau, round, output_path}
        """
        generated_files = []
        
        for letter in letters_data:
            try:
                filepath = self.generate_dispute_letter_pdf(
                    letter_content=letter['content'],
                    client_name=letter['client_name'],
                    bureau=letter['bureau'],
                    round_number=letter['round'],
                    output_path=letter['output_path']
                )
                generated_files.append({
                    'success': True,
                    'filepath': filepath,
                    'bureau': letter['bureau']
                })
            except Exception as e:
                generated_files.append({
                    'success': False,
                    'error': str(e),
                    'bureau': letter.get('bureau', 'Unknown')
                })
        
        return generated_files
