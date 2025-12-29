"""
Brightpath Ascend Group - Branded PDF Builder
Uses fpdf2 with gradients, styled tables, and professional formatting
"""

import os
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos
from fpdf.fonts import FontFace

try:
    from fpdf.pattern import LinearGradient

    HAS_GRADIENTS = True
except ImportError:
    HAS_GRADIENTS = False


class BrightpathColors:
    """Brightpath Ascend Group brand colors"""

    TEAL = (0, 128, 128)
    TEAL_DARK = (0, 100, 100)
    LIME = (50, 205, 50)
    LIME_LIGHT = (144, 238, 144)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    DARK_GRAY = (51, 51, 51)
    MEDIUM_GRAY = (102, 102, 102)
    LIGHT_GRAY = (240, 240, 240)
    ALERT_RED = (220, 53, 69)
    SUCCESS_GREEN = (40, 167, 69)
    WARNING_ORANGE = (255, 193, 7)
    INFO_BLUE = (0, 123, 255)

    TEAL_HEX = "#008080"
    LIME_HEX = "#32CD32"
    GRADIENT_START = "#008080"
    GRADIENT_END = "#32CD32"


class BrightpathPDF(FPDF):
    """
    Professional Brightpath Ascend Group branded PDF builder
    Features: Gradient headers, styled tables, checkboxes, professional typography
    """

    def __init__(self, title="", subtitle="", show_header=True, show_footer=True):
        super().__init__()
        self.doc_title = title
        self.doc_subtitle = subtitle
        self.show_header = show_header
        self.show_footer = show_footer
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(left=20, top=20, right=20)
        self.add_page()

    def header(self):
        if not self.show_header:
            return

        start_y = self.get_y()
        header_height = 35

        if HAS_GRADIENTS:
            try:
                gradient = LinearGradient(
                    self,
                    from_x=0,
                    from_y=start_y,
                    to_x=self.w,
                    to_y=start_y,
                    colors=[BrightpathColors.TEAL_HEX, BrightpathColors.LIME_HEX],
                )
                with self.use_pattern(gradient):
                    self.rect(0, 0, self.w, header_height, style="F")
            except Exception:
                self.set_fill_color(*BrightpathColors.TEAL)
                self.rect(0, 0, self.w, header_height, style="F")
        else:
            self.set_fill_color(*BrightpathColors.TEAL)
            self.rect(0, 0, self.w, header_height, style="F")

        self.set_y(8)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*BrightpathColors.WHITE)
        self.cell(
            0,
            10,
            "BRIGHTPATH ASCEND GROUP",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.set_font("Helvetica", "", 9)
        self.cell(
            0,
            5,
            "Consumer Protection & FCRA Litigation Specialists",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.set_text_color(*BrightpathColors.BLACK)
        self.set_y(header_height + 5)

    def footer(self):
        if not self.show_footer:
            return

        self.set_y(-20)

        self.set_draw_color(*BrightpathColors.TEAL)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), self.w - 20, self.get_y())

        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BrightpathColors.MEDIUM_GRAY)
        self.cell(
            0,
            5,
            f"Page {self.page_no()}",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_font("Helvetica", "I", 7)
        self.cell(
            0,
            4,
            "Brightpath Ascend Group | Consumer Protection & FCRA Litigation",
            align="C",
        )

        self.set_text_color(*BrightpathColors.BLACK)

    def add_document_title(self, title, subtitle=None):
        """Add a centered document title with optional subtitle"""
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*BrightpathColors.DARK_GRAY)
        self.multi_cell(0, 8, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if subtitle:
            self.set_font("Helvetica", "", 11)
            self.set_text_color(*BrightpathColors.MEDIUM_GRAY)
            self.multi_cell(
                0, 6, subtitle, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )

        self.ln(5)
        self.set_text_color(*BrightpathColors.BLACK)

    def add_alert_box(self, text, alert_type="critical"):
        """Add a highlighted alert box"""
        colors = {
            "critical": (BrightpathColors.ALERT_RED, (255, 240, 240)),
            "warning": (BrightpathColors.WARNING_ORANGE, (255, 250, 230)),
            "success": (BrightpathColors.SUCCESS_GREEN, (240, 255, 240)),
            "info": (BrightpathColors.INFO_BLUE, (240, 248, 255)),
        }

        border_color, fill_color = colors.get(alert_type, colors["info"])

        self.set_fill_color(*fill_color)
        self.set_draw_color(*border_color)
        self.set_line_width(1)

        start_y = self.get_y()
        box_height = 20

        self.rect(20, start_y, self.w - 40, box_height, style="DF")

        self.set_xy(25, start_y + 5)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*border_color)

        icon = "■■" if alert_type == "critical" else "■"
        self.cell(0, 10, f"{icon} {text}", align="C")

        self.set_y(start_y + box_height + 5)
        self.set_text_color(*BrightpathColors.BLACK)
        self.set_line_width(0.2)

    def add_section_header(self, title, with_gradient=True):
        """Add a styled section header"""
        self.ln(3)

        if with_gradient and HAS_GRADIENTS:
            try:
                start_y = self.get_y()
                gradient = LinearGradient(
                    self,
                    from_x=20,
                    from_y=start_y,
                    to_x=self.w - 20,
                    to_y=start_y,
                    colors=[BrightpathColors.TEAL_HEX, BrightpathColors.LIME_HEX],
                )
                with self.use_pattern(gradient):
                    self.rect(20, start_y, self.w - 40, 10, style="F")
                self.set_xy(25, start_y + 2)
                self.set_font("Helvetica", "B", 11)
                self.set_text_color(*BrightpathColors.WHITE)
                self.cell(0, 6, title.upper())
                self.set_y(start_y + 12)
            except Exception:
                self._add_solid_section_header(title)
        else:
            self._add_solid_section_header(title)

        self.set_text_color(*BrightpathColors.BLACK)
        self.ln(2)

    def _add_solid_section_header(self, title):
        """Fallback solid color section header"""
        self.set_fill_color(*BrightpathColors.TEAL)
        start_y = self.get_y()
        self.rect(20, start_y, self.w - 40, 10, style="F")
        self.set_xy(25, start_y + 2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BrightpathColors.WHITE)
        self.cell(0, 6, title.upper())
        self.set_y(start_y + 12)

    def add_info_table(self, data, col_widths=None):
        """
        Add a two-column info table (label: value)
        data: list of tuples [(label, value), ...]
        """
        self.set_font("Helvetica", "", 10)

        if col_widths is None:
            col_widths = [60, self.w - 80]

        for label, value in data:
            self.set_x(20)

            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*BrightpathColors.DARK_GRAY)
            self.cell(col_widths[0], 7, f"{label}:", new_x=XPos.RIGHT)

            self.set_font("Helvetica", "", 10)
            self.set_text_color(*BrightpathColors.BLACK)
            self.cell(col_widths[1], 7, str(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(3)

    def add_data_table(self, headers, rows, col_widths=None, highlight_header=True):
        """
        Add a full data table with headers
        headers: list of header strings
        rows: list of lists (row data)
        """
        if col_widths is None:
            available_width = self.w - 40
            col_widths = [available_width / len(headers)] * len(headers)

        header_style = (
            FontFace(
                emphasis="BOLD",
                color=BrightpathColors.WHITE,
                fill_color=BrightpathColors.TEAL,
            )
            if highlight_header
            else None
        )

        self.set_x(20)
        self.set_font("Helvetica", "", 10)

        with self.table(
            col_widths=col_widths,
            headings_style=header_style,
            line_height=7,
            padding=2,
            borders_layout="SINGLE_TOP_LINE" if not highlight_header else "ALL",
        ) as table:
            header_row = table.row()
            for h in headers:
                header_row.cell(h)

            for row_data in rows:
                data_row = table.row()
                for cell in row_data:
                    data_row.cell(str(cell))

        self.ln(5)

    def add_checklist_item(self, text, checked=False, date=None, indent=0):
        """Add a checklist item with checkbox"""
        self.set_x(20 + indent)

        checkbox = "■" if checked else "□"

        self.set_font("Helvetica", "B", 11)
        if checked:
            self.set_text_color(*BrightpathColors.SUCCESS_GREEN)
        else:
            self.set_text_color(*BrightpathColors.DARK_GRAY)
        self.cell(8, 7, checkbox, new_x=XPos.RIGHT)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BrightpathColors.BLACK)

        if date:
            text_width = self.w - 80 - indent
            self.cell(text_width, 7, text, new_x=XPos.RIGHT)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*BrightpathColors.MEDIUM_GRAY)
            self.cell(30, 7, date, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_text_color(*BrightpathColors.BLACK)

    def add_checklist(self, items, title=None):
        """
        Add a full checklist section
        items: list of dicts with keys: text, checked (bool), date (optional)
        """
        if title:
            self.add_section_header(title)

        for item in items:
            self.add_checklist_item(
                text=item.get("text", ""),
                checked=item.get("checked", False),
                date=item.get("date"),
                indent=item.get("indent", 0),
            )

        self.ln(3)

    def add_bullet_list(self, items, title=None):
        """Add a bulleted list"""
        if title:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*BrightpathColors.DARK_GRAY)
            self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BrightpathColors.BLACK)

        for item in items:
            self.set_x(25)
            self.cell(5, 6, "•", new_x=XPos.RIGHT)
            self.multi_cell(0, 6, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(3)

    def add_cost_table(self, items, title="ESTIMATED COSTS"):
        """
        Add a cost estimation table
        items: list of tuples [(description, cost_string), ...]
        """
        self.add_section_header(title)

        self.set_font("Helvetica", "", 10)

        total_width = self.w - 40
        desc_width = total_width * 0.7
        cost_width = total_width * 0.3

        self.set_x(20)
        self.set_fill_color(*BrightpathColors.LIGHT_GRAY)
        self.set_font("Helvetica", "B", 10)
        self.cell(desc_width, 8, "Item", border=1, fill=True, new_x=XPos.RIGHT)
        self.cell(
            cost_width,
            8,
            "Cost",
            border=1,
            fill=True,
            align="R",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.set_font("Helvetica", "", 10)
        for desc, cost in items:
            self.set_x(20)
            self.cell(desc_width, 7, desc, border=1, new_x=XPos.RIGHT)
            self.cell(
                cost_width,
                7,
                cost,
                border=1,
                align="R",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

        self.ln(5)

    def add_motivational_footer(self, text):
        """Add a motivational message at the bottom"""
        self.ln(5)

        self.set_fill_color(*BrightpathColors.LIGHT_GRAY)
        start_y = self.get_y()

        self.rect(20, start_y, self.w - 40, 15, style="F")

        self.set_xy(25, start_y + 4)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*BrightpathColors.TEAL_DARK)
        self.multi_cell(self.w - 50, 6, text, align="C")

        self.set_text_color(*BrightpathColors.BLACK)

    def add_paragraph(self, text, bold=False, indent=0):
        """Add a paragraph of text"""
        self.set_x(20 + indent)
        if bold:
            self.set_font("Helvetica", "B", 10)
        else:
            self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def add_horizontal_line(self):
        """Add a horizontal divider line"""
        self.ln(3)
        self.set_draw_color(*BrightpathColors.MEDIUM_GRAY)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.ln(5)
        self.set_line_width(0.2)

    def add_signature_block(self, name="", date="", title=""):
        """Add a signature block"""
        self.ln(10)

        self.set_draw_color(*BrightpathColors.DARK_GRAY)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 100, self.get_y())
        self.ln(2)

        self.set_font("Helvetica", "", 10)
        self.set_x(20)
        self.cell(
            80, 6, name if name else "Signature", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )

        if title:
            self.set_font("Helvetica", "I", 9)
            self.set_x(20)
            self.cell(80, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(5)
        self.set_x(20)
        self.set_font("Helvetica", "", 10)
        self.cell(
            80,
            6,
            f"Date: {date if date else '_______________'}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.set_line_width(0.2)

    def save(self, filepath):
        """Save the PDF to a file"""
        os.makedirs(
            os.path.dirname(filepath) if os.path.dirname(filepath) else ".",
            exist_ok=True,
        )
        self.output(filepath)
        return filepath


def create_action_plan_pdf(
    client_name,
    case_info,
    deadlines,
    week1_tasks,
    week2_tasks,
    hearing_tasks,
    what_to_bring,
    costs,
    output_path,
):
    """
    Create an Action Plan PDF like the attached example

    Args:
        client_name: Client's full name
        case_info: dict with keys: plaintiff, defendant, amount, court, hearing_date, fcra_value
        deadlines: list of critical deadline strings
        week1_tasks: list of dicts with text, checked, date keys
        week2_tasks: list of dicts with text, checked, date keys
        hearing_tasks: list of dicts with text, checked keys
        what_to_bring: list of strings
        costs: list of tuples (description, cost_string)
        output_path: where to save the PDF
    """
    pdf = BrightpathPDF()

    pdf.add_document_title(
        f"{client_name.upper()} CASE ACTION PLAN", "Timeline & Checklist"
    )

    if case_info.get("case_number"):
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*BrightpathColors.MEDIUM_GRAY)
        pdf.cell(
            0,
            6,
            f"Case No. {case_info['case_number']}",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_text_color(*BrightpathColors.BLACK)
        pdf.ln(5)

    for deadline in deadlines:
        pdf.add_alert_box(deadline, alert_type="critical")

    pdf.add_section_header("CASE OVERVIEW")

    overview_data = [
        ("Plaintiff", case_info.get("plaintiff", "N/A")),
        ("Defendant", case_info.get("defendant", client_name)),
        ("Amount Claimed", case_info.get("amount", "N/A")),
        ("Court", case_info.get("court", "N/A")),
        ("Hearing Date", case_info.get("hearing_date", "N/A")),
        ("FCRA Violation Value", case_info.get("fcra_value", "N/A")),
    ]
    pdf.add_info_table(overview_data)

    if week1_tasks:
        pdf.add_checklist(week1_tasks, title="WEEK 1: IMMEDIATE ACTIONS")

    if week2_tasks:
        pdf.add_checklist(week2_tasks, title="WEEK 2: PREPARATION")

    if hearing_tasks:
        pdf.add_checklist(
            hearing_tasks, title=f"HEARING DAY: {case_info.get('hearing_date', '')}"
        )

    if what_to_bring:
        pdf.add_section_header("WHAT TO BRING TO HEARING")
        pdf.add_bullet_list(what_to_bring)

    if costs:
        pdf.add_cost_table(costs)

    pdf.add_motivational_footer(
        f"Remember: You have significant FCRA exposure on your side. "
        f"Follow this plan, stay organized, and remain confident."
    )

    return pdf.save(output_path)


def create_case_summary_pdf(
    client_name, case_data, violations, damages, recommendations, output_path
):
    """
    Create a Case Summary PDF
    """
    pdf = BrightpathPDF()

    pdf.add_document_title(f"FCRA CASE SUMMARY", f"Prepared for: {client_name}")

    pdf.add_section_header("CLIENT INFORMATION")
    client_info = [
        ("Name", client_name),
        ("Case ID", case_data.get("case_id", "N/A")),
        (
            "Analysis Date",
            case_data.get("analysis_date", datetime.now().strftime("%B %d, %Y")),
        ),
        ("Case Score", f"{case_data.get('case_score', 'N/A')}/10"),
    ]
    pdf.add_info_table(client_info)

    if violations:
        pdf.add_section_header("VIOLATIONS IDENTIFIED")
        headers = ["Violation Type", "Bureau", "Severity", "Damages"]
        rows = []
        for v in violations:
            rows.append(
                [
                    v.get("type", "Unknown"),
                    v.get("bureau", "N/A"),
                    v.get("severity", "Medium"),
                    f"${v.get('damages', 0):,.2f}",
                ]
            )
        pdf.add_data_table(headers, rows)

    if damages:
        pdf.add_section_header("DAMAGES CALCULATION")
        damage_info = [
            ("Statutory Damages", f"${damages.get('statutory', 0):,.2f}"),
            ("Actual Damages", f"${damages.get('actual', 0):,.2f}"),
            ("Punitive Damages", f"${damages.get('punitive', 0):,.2f}"),
            ("Total Estimated", f"${damages.get('total', 0):,.2f}"),
        ]
        pdf.add_info_table(damage_info)

    if recommendations:
        pdf.add_section_header("RECOMMENDED ACTIONS")
        pdf.add_bullet_list(recommendations)

    return pdf.save(output_path)
