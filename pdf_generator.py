from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.colors import HexColor, black, white, lightgrey
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
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
        
    def sanitize_text_for_pdf(self, text):
        """Remove or replace Unicode characters that Helvetica doesn't support"""
        if not text:
            return ""
        
        # Replace smart quotes and other problematic Unicode chars
        replacements = {
            '•': '*',      # bullet -> asterisk
            '◦': '-',      # white bullet
            '∙': '*',      # bullet operator
            '○': 'o',      # white circle
            '"': '"',      # smart double quote
            '"': '"',      # smart double quote
            ''': "'",      # smart single quote
            ''': "'",      # smart single quote
            '—': ' - ',    # em dash
            '–': '-',      # en dash
            '…': '...',    # ellipsis
            '™': '(TM)',   # trademark
            '®': '(R)',    # registered
            '©': '(C)',    # copyright
            '€': 'EUR',    # euro
            '£': 'GBP',    # pound
            '¥': 'JPY',    # yen
            '°': 'deg',    # degree
            '×': 'x',      # multiplication
            '÷': '/',      # division
            '≠': '!=',     # not equal
            '≤': '<=',     # less than or equal
            '≥': '>=',     # greater than or equal
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        # Remove any remaining non-ASCII chars
        text = ''.join(c if ord(c) < 128 else '' for c in text)
        return text
    
    def generate_dispute_letter_pdf(self, letter_content, client_name, bureau, round_number, output_path):
        """
        Generate PDF with custom styling to force manual review
        Uses custom color and formatting to bypass e-Oscar automation
        """
        # Sanitize content for Helvetica font compatibility
        letter_content = self.sanitize_text_for_pdf(letter_content)
        client_name = self.sanitize_text_for_pdf(client_name)
        bureau = self.sanitize_text_for_pdf(bureau)
        
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


class CreditAnalysisPDFGenerator:
    """Generate basic credit analysis reports like the sample Jahnell Parkinson report"""
    
    def __init__(self):
        self.company_name = "Brightpath Ascend Group"
        self.company_address = "1185 Avenue of the Americas 3rd Floor New York NY"
        self.company_phone = "(917) 909-4051"
        self.company_email = "support@brightpathascendgroup.com"
        self.company_website = "http://www.brightpathascendgroup.com"
        self.primary_color = HexColor('#1a1a2e')
        self.accent_color = HexColor('#4ade80')
    
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
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        text = ''.join(c if ord(c) < 128 else '' for c in text)
        return text
    
    def generate_credit_analysis_pdf(self, client_name, report_date, credit_scores, negative_items, output_path):
        """
        Generate a professional credit analysis report
        
        Args:
            client_name: Client's full name
            report_date: Date of the report
            credit_scores: Dict with keys 'equifax', 'experian', 'transunion'
            negative_items: List of dicts with keys: account_name, bureau, type, balance, status, notes
            output_path: Where to save the PDF
        """
        client_name = self.sanitize_text(client_name)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=self.primary_color,
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'Subheading',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=self.primary_color,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=11,
            textColor=black,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=16
        )
        
        center_style = ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica'
        )
        
        story.append(Paragraph("CREDIT ANALYSIS REPORT", title_style))
        story.append(Paragraph("Prepared for", subtitle_style))
        story.append(Paragraph(f"<b>{client_name}</b>", title_style))
        story.append(Paragraph(f"(on {report_date})", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"By {self.company_name}", center_style))
        story.append(Paragraph(self.company_address, center_style))
        story.append(Paragraph(f"Phone: {self.company_phone}", center_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(self.company_email, center_style))
        story.append(Paragraph(self.company_website, center_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph(f"Dear {client_name.split()[0] if ' ' in client_name else client_name},", body_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"On behalf of everyone here at {self.company_name}, I'd like to take this opportunity to welcome "
            "you as a potential new client! We would be thrilled to have you with us.", body_style))
        story.append(Paragraph(
            "Credit is our passion. We understand how important your credit is for your future, and we will work "
            "tirelessly to ensure we can help you achieve your financial goals.", body_style))
        story.append(Paragraph(
            "This credit analysis report provides an overview of your credit as potential lenders see it today. It "
            "lists the items that negatively affect your score and explains how we use the power of the law to "
            "improve your credit. It also includes a simple step-by-step plan to speed up the process.", body_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("This credit analysis report is broken down into the following five sections:", body_style))
        story.append(Spacer(1, 0.1*inch))
        sections = [
            "1. Credit Score Basics",
            "2. What's Included in Your Credit Report",
            "3. Analysis of Your Accounts",
            "4. An Overview of Our Process",
            "5. Your Part in the Process"
        ]
        for section in sections:
            story.append(Paragraph(f"    {section}", body_style))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"{client_name.split()[0] if ' ' in client_name else client_name}, thank you again for entrusting "
            f"{self.company_name} with restoring your good credit. We are honored to help you achieve your financial goals.",
            body_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("To Your Success,", body_style))
        story.append(Paragraph(f"<b>{self.company_name}</b>", body_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph("PART 1 - CREDIT SCORE BASICS", heading_style))
        
        score_data = [
            ['Equifax', 'Experian', 'TransUnion'],
            [str(credit_scores.get('equifax', '-')), 
             str(credit_scores.get('experian', '-')), 
             str(credit_scores.get('transunion', '-'))]
        ]
        score_table = Table(score_data, colWidths=[2*inch, 2*inch, 2*inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 24),
            ('TEXTCOLOR', (0, 1), (-1, 1), self.primary_color),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, lightgrey),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("What Is A Credit Score?", subheading_style))
        story.append(Paragraph(
            "A credit score is a number a mathematical formula generates to predict creditworthiness. Credit "
            "scores range from 300-850. The higher your score is, the more likely you are to get a loan. The "
            "lower your score is, the less likely you are to get a loan. If you have a low credit score and manage "
            "to get approved for credit, your interest rate will be much higher than someone with a good credit "
            "score. So, having a high credit score will save you many thousands of dollars.", body_style))
        
        story.append(Paragraph("Credit Score Ranges And Their Meaning", subheading_style))
        ranges = [
            ("800 and Higher (Excellent)", "With a credit score in this range, no lender will ever disapprove your loan application."),
            ("700 - 799 (Very Good)", "27% of the United States population belongs to this range. You will enjoy good rates."),
            ("680 - 699 (Good)", "This is the average credit score range. Approvals are practically guaranteed."),
            ("620 - 679 (OK or Fair)", "You might find that quoted rates aren't the best, but you can still get approved."),
            ("580 - 619 (Poor)", "You can still get loans, but terms and interest rates won't be appealing."),
            ("500 - 579 (Bad)", "Getting a loan is difficult. Rates will be very high and terms very strict."),
            ("499 and Lower (Very Bad)", "You need serious assistance handling your credit.")
        ]
        for title, desc in ranges:
            story.append(Paragraph(f"<b>{title}</b> - {desc}", body_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph("PART 2 - WHAT'S INCLUDED IN YOUR CREDIT REPORT", heading_style))
        
        sections_content = [
            ("Personal Data", "Your current and previous addresses, employers, full name variations, social security number, and date of birth. Keeping this information accurate helps avoid credit profile mergers with others."),
            ("Public Records", "Judgments, bankruptcies, foreclosures, evictions - these are credit report killers. They cause the worst damage and weigh heavily on your scores."),
            ("Inquiries", "Each time your credit is 'hard-pulled' by a potential creditor, it costs you score points. Soft pulls do not affect your score."),
            ("Accounts and Tradelines", "All revolving and installment accounts including credit cards, mortgages, auto loans, student loans, and personal loans."),
            ("Collection Accounts", "Unpaid charged-off accounts sold to collection agencies. We do NOT advise paying these without verification of accuracy and a written deletion agreement."),
            ("Credit Utilization", "As a rule of thumb, keep your balances at 30% or less of available credit to maximize your score.")
        ]
        for title, content in sections_content:
            story.append(Paragraph(f"<b>{title}</b>", subheading_style))
            story.append(Paragraph(content, body_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph("PART 3 - ANALYSIS OF YOUR ACCOUNTS", heading_style))
        story.append(Paragraph(
            "Below is a summary of the negative items found on your credit report. These items are negatively "
            "impacting your credit scores and need to be addressed.", body_style))
        story.append(Spacer(1, 0.2*inch))
        
        if negative_items:
            for i, item in enumerate(negative_items, 1):
                item_name = self.sanitize_text(item.get('account_name', 'Unknown Account'))
                bureau = self.sanitize_text(item.get('bureau', 'Unknown'))
                item_type = self.sanitize_text(item.get('type', 'Negative Item'))
                balance = item.get('balance', 'N/A')
                status = self.sanitize_text(item.get('status', 'Unknown'))
                notes = self.sanitize_text(item.get('notes', ''))
                
                story.append(Paragraph(f"<b>{i}. {item_name}</b>", subheading_style))
                item_details = f"Bureau: {bureau} | Type: {item_type} | Balance: ${balance if isinstance(balance, (int, float)) else balance} | Status: {status}"
                story.append(Paragraph(item_details, body_style))
                if notes:
                    story.append(Paragraph(f"<i>Notes: {notes}</i>", body_style))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No negative items found on your credit report at this time.", body_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph("PART 4 - AN OVERVIEW OF OUR PROCESS", heading_style))
        story.append(Paragraph(
            "Our proven dispute process uses the power of consumer protection laws, including the Fair Credit "
            "Reporting Act (FCRA), to challenge inaccurate, misleading, or unverifiable information on your "
            "credit reports.", body_style))
        story.append(Spacer(1, 0.2*inch))
        
        process_steps = [
            ("Step 1: Analysis", "We thoroughly analyze your credit reports from all three bureaus to identify disputable items."),
            ("Step 2: Strategy", "We develop a customized dispute strategy based on your specific situation and goals."),
            ("Step 3: Disputes", "We prepare and send professionally written dispute letters to the credit bureaus."),
            ("Step 4: Monitoring", "We track bureau responses and monitor your credit for changes."),
            ("Step 5: Escalation", "If necessary, we escalate disputes using Method of Verification (MOV) requests and pre-litigation tactics.")
        ]
        for title, desc in process_steps:
            story.append(Paragraph(f"<b>{title}</b>", subheading_style))
            story.append(Paragraph(desc, body_style))
        
        story.append(PageBreak())
        
        story.append(Paragraph("PART 5 - YOUR PART IN THE PROCESS", heading_style))
        story.append(Paragraph(
            "While we handle the dispute process for you, there are important steps you should take to maximize "
            "your results:", body_style))
        story.append(Spacer(1, 0.2*inch))
        
        client_steps = [
            "DO NOT apply for new credit while in our program (each inquiry can cost you points)",
            "DO NOT pay collections or charge-offs without consulting us first",
            "DO keep your credit card balances below 30% of your limits",
            "DO make all current payments on time",
            "DO respond promptly when we request information or documents",
            "DO monitor your credit reports for changes and notify us of any updates"
        ]
        for step in client_steps:
            story.append(Paragraph(f"* {step}", body_style))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Questions? Contact Us!", heading_style))
        story.append(Paragraph(f"Email: {self.company_email}", body_style))
        story.append(Paragraph(f"Phone: {self.company_phone}", body_style))
        story.append(Paragraph(f"Website: {self.company_website}", body_style))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.build(story)
        
        return output_path
