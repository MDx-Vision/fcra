"""
Internal Staff Analysis Memo Generator (3-5 pages)
Quick reference for staff review before approving cases.
"""
from .base import BasePDFBuilder
from reportlab.platypus import PageBreak, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, lightgrey
from datetime import datetime


class InternalMemoBuilder(BasePDFBuilder):
    """
    Generates 3-5 page internal staff analysis memos.
    
    Sections:
    1. Quick Assessment Summary
    2. Standing Analysis (TransUnion v. Ramirez)
    3. Violation Breakdown
    4. Top 10 Violations
    5. Willfulness Indicators
    6. Damages Calculation
    7. Defendant Analysis
    8. Red Flags / Concerns
    9. Strategy Recommendations
    """
    
    def generate(self, output_path, case_data):
        """
        Generate internal staff analysis memo.
        
        Args:
            output_path: Where to save the PDF
            case_data: Dict containing:
                - client_name: Client's full name
                - analysis_id: Analysis ID for reference
                - violations: List of violation dicts
                - standing: Standing dict
                - damages: Damages dict
                - case_score: CaseScore dict
                - credit_scores: Dict with bureau scores
                - analyst_notes: Any analyst observations
        """
        doc = self.create_document(output_path)
        story = []
        
        self._add_header(story, case_data)
        self._add_quick_assessment(story, case_data)
        self._add_standing_analysis(story, case_data)
        self._add_violation_breakdown(story, case_data)
        self._add_top_violations(story, case_data)
        self._add_willfulness_indicators(story, case_data)
        self._add_damages_calculation(story, case_data)
        self._add_defendant_analysis(story, case_data)
        self._add_red_flags(story, case_data)
        self._add_strategy_recommendations(story, case_data)
        
        doc.build(story)
        return output_path
    
    def _add_header(self, story, case_data):
        """Add memo header"""
        story.append(Spacer(1, 0.2*inch))
        
        header_data = [
            ["INTERNAL CASE ANALYSIS MEMO", ""],
            ["CONFIDENTIAL - FOR STAFF USE ONLY", ""],
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 18),
            ('FONTSIZE', (0, 1), (0, 1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 1), (0, 1), self.WARNING_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(header_table)
        
        story.append(Spacer(1, 0.2*inch))
        
        info_data = [
            ["Client:", case_data.get('client_name', 'Unknown')],
            ["Analysis ID:", str(case_data.get('analysis_id', 'N/A'))],
            ["Date:", datetime.now().strftime("%B %d, %Y at %I:%M %p")],
            ["Analyst:", "AI Analysis System"],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(info_table)
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_quick_assessment(self, story, case_data):
        """Add quick assessment summary"""
        self.add_section_header(story, "1. QUICK ASSESSMENT", level=2)
        
        case_score = case_data.get('case_score', {})
        damages = case_data.get('damages', {})
        violations = case_data.get('violations', [])
        standing = case_data.get('standing', {})
        
        total_score = case_score.get('total_score', 0) if case_score else 0
        case_strength = case_score.get('case_strength', 'Unknown') if case_score else 'Unknown'
        total_violations = len(violations)
        willful_count = sum(1 for v in violations if v.get('is_willful', False))
        total_exposure = damages.get('total_exposure', 0) if damages else 0
        
        if total_score >= 8:
            verdict = "STRONG CASE - Recommend proceeding to litigation track"
            verdict_color = HexColor('#22c55e')
        elif total_score >= 5:
            verdict = "MODERATE CASE - Standard dispute process, monitor progress"
            verdict_color = HexColor('#eab308')
        else:
            verdict = "WEAK CASE - Additional documentation needed before proceeding"
            verdict_color = self.WARNING_COLOR
        
        verdict_data = [[verdict]]
        verdict_table = Table(verdict_data, colWidths=[6*inch])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(verdict_table)
        story.append(Spacer(1, 0.2*inch))
        
        metrics_data = [
            ["Metric", "Value", "Assessment"],
            ["Case Score", f"{total_score}/10", case_strength],
            ["Total Violations", str(total_violations), "High" if total_violations >= 10 else "Moderate" if total_violations >= 5 else "Low"],
            ["Willful Violations", str(willful_count), "Excellent" if willful_count >= 3 else "Good" if willful_count >= 1 else "None"],
            ["Total Exposure", self.format_currency(total_exposure), "High" if total_exposure >= 50000 else "Moderate" if total_exposure >= 10000 else "Low"],
            ["Standing", "Established" if standing.get('has_concrete_harm') else "Needs Work", "Ready" if standing.get('has_concrete_harm') else "Action Required"],
        ]
        self.add_table(story, metrics_data, col_widths=[2*inch, 1.5*inch, 2*inch])
    
    def _add_standing_analysis(self, story, case_data):
        """Add TransUnion v. Ramirez standing analysis"""
        self.add_section_header(story, "2. STANDING ANALYSIS (Post-TransUnion v. Ramirez)", level=2)
        
        standing = case_data.get('standing', {})
        
        if not standing:
            self.add_paragraph(story, "No standing data available. Complete Stage 1 analysis first.", self.warning_style)
            return
        
        standing_data = [
            ["Element", "Status", "Details"],
            ["Concrete Harm", 
             "YES" if standing.get('has_concrete_harm') else "NO",
             (standing.get('concrete_harm_type', '') or 'Not documented')[:50]],
            ["Dissemination", 
             "YES" if standing.get('has_dissemination') else "NO",
             (standing.get('dissemination_details', '') or 'Not documented')[:50]],
            ["Causation", 
             "YES" if standing.get('has_causation') else "NO",
             (standing.get('causation_details', '') or 'Not documented')[:50]],
        ]
        self.add_table(story, standing_data, col_widths=[1.5*inch, 0.8*inch, 3.2*inch])
        
        has_all_three = (standing.get('has_concrete_harm') and 
                         standing.get('has_dissemination') and 
                         standing.get('has_causation'))
        
        if has_all_three:
            self.add_paragraph(story, "STANDING ESTABLISHED - All three elements present. Case ready for litigation track.", self.body_blue_style)
        else:
            missing = []
            if not standing.get('has_concrete_harm'):
                missing.append("concrete harm documentation")
            if not standing.get('has_dissemination'):
                missing.append("proof of dissemination")
            if not standing.get('has_causation'):
                missing.append("causation evidence")
            self.add_paragraph(story, f"ACTION REQUIRED: Need {', '.join(missing)} before litigation.", self.warning_style)
    
    def _add_violation_breakdown(self, story, case_data):
        """Add violation breakdown by section"""
        self.add_section_header(story, "3. VIOLATION BREAKDOWN BY FCRA SECTION", level=2)
        
        violations = case_data.get('violations', [])
        
        by_section = {}
        for v in violations:
            section = v.get('fcra_section', 'Other')
            by_section.setdefault(section, []).append(v)
        
        breakdown_data = [["FCRA Section", "Count", "Willful", "Damages Range"]]
        
        for section in sorted(by_section.keys()):
            section_violations = by_section[section]
            willful = sum(1 for v in section_violations if v.get('is_willful', False))
            min_damages = sum(v.get('statutory_damages_min', 100) for v in section_violations)
            max_damages = sum(v.get('statutory_damages_max', 1000) for v in section_violations)
            
            breakdown_data.append([
                section,
                str(len(section_violations)),
                str(willful),
                f"${min_damages:,} - ${max_damages:,}"
            ])
        
        if len(breakdown_data) > 1:
            self.add_table(story, breakdown_data, col_widths=[1.5*inch, 1*inch, 1*inch, 2*inch])
        else:
            self.add_paragraph(story, "No violations categorized yet.")
    
    def _add_top_violations(self, story, case_data):
        """Add top 10 violations"""
        self.add_section_header(story, "4. TOP 10 HIGHEST-VALUE VIOLATIONS", level=2)
        
        violations = case_data.get('violations', [])
        
        scored = []
        for v in violations:
            score = v.get('statutory_damages_max', 1000)
            if v.get('is_willful'):
                score *= 2
            scored.append((score, v))
        
        top_10 = sorted(scored, key=lambda x: x[0], reverse=True)[:10]
        
        if top_10:
            for i, (score, v) in enumerate(top_10, 1):
                self.add_paragraph(story,
                    f"<b>{i}. {v.get('account_name', 'Unknown')[:30]}</b> ({v.get('bureau', 'Unknown')}) - "
                    f"{v.get('fcra_section', 'N/A')}: {v.get('violation_type', 'Unknown')[:40]} "
                    f"{'[WILLFUL]' if v.get('is_willful') else ''}"
                )
        else:
            self.add_paragraph(story, "No violations to rank.")
    
    def _add_willfulness_indicators(self, story, case_data):
        """Add willfulness assessment"""
        self.add_section_header(story, "5. WILLFULNESS INDICATORS (Safeco v. Burr Standard)", level=2)
        
        violations = case_data.get('violations', [])
        willful = [v for v in violations if v.get('is_willful', False)]
        
        if willful:
            self.add_paragraph(story, f"Found {len(willful)} violations with willfulness indicators:")
            
            for v in willful[:5]:
                notes = v.get('willfulness_notes', 'Indicators not specified')
                self.add_paragraph(story, f"* {v.get('account_name', 'Unknown')}: {notes[:100]}")
            
            self.add_paragraph(story, 
                "PUNITIVE DAMAGES AVAILABLE - Willful violations allow recovery up to 4x statutory damages.",
                self.body_blue_style
            )
        else:
            self.add_paragraph(story, 
                "No clear willfulness indicators found. Focus on actual damages and statutory recovery."
            )
    
    def _add_damages_calculation(self, story, case_data):
        """Add damages summary"""
        self.add_section_header(story, "6. DAMAGES CALCULATION SUMMARY", level=2)
        
        damages = case_data.get('damages', {})
        
        if not damages:
            self.add_paragraph(story, "Damages not calculated yet.", self.warning_style)
            return
        
        damages_data = [
            ["Category", "Amount"],
            ["Actual Damages", self.format_currency(damages.get('actual_damages_total', 0))],
            ["Statutory Damages", self.format_currency(damages.get('statutory_damages_total', 0))],
            ["Punitive Damages", self.format_currency(damages.get('punitive_damages_amount', 0))],
            ["Attorney Fees (Est.)", self.format_currency(damages.get('attorney_fees_projection', 0))],
            ["TOTAL EXPOSURE", self.format_currency(damages.get('total_exposure', 0))],
            ["Settlement Target (65%)", self.format_currency(damages.get('settlement_target', 0))],
            ["Minimum Acceptable (50%)", self.format_currency(damages.get('minimum_acceptable', 0))],
        ]
        self.add_table(story, damages_data, col_widths=[3*inch, 2.5*inch])
    
    def _add_defendant_analysis(self, story, case_data):
        """Add defendant/bureau analysis"""
        self.add_section_header(story, "7. DEFENDANT ANALYSIS", level=2)
        
        violations = case_data.get('violations', [])
        
        by_bureau = {}
        for v in violations:
            bureau = v.get('bureau', 'Unknown')
            by_bureau.setdefault(bureau, []).append(v)
        
        for bureau, bureau_violations in sorted(by_bureau.items()):
            willful = sum(1 for v in bureau_violations if v.get('is_willful', False))
            
            self.add_paragraph(story,
                f"<b>{bureau}:</b> {len(bureau_violations)} violations ({willful} willful)"
            )
        
        if not by_bureau:
            self.add_paragraph(story, "No bureau-specific data available.")
    
    def _add_red_flags(self, story, case_data):
        """Add red flags and concerns"""
        self.add_section_header(story, "8. RED FLAGS / CONCERNS", level=2)
        
        standing = case_data.get('standing', {})
        violations = case_data.get('violations', [])
        case_score = case_data.get('case_score', {})
        
        red_flags = []
        
        if not standing.get('has_concrete_harm'):
            red_flags.append("Missing concrete harm documentation - critical for standing")
        
        if not standing.get('has_dissemination'):
            red_flags.append("No proof of dissemination to third parties")
        
        if len(violations) < 3:
            red_flags.append(f"Low violation count ({len(violations)}) - may not justify litigation costs")
        
        willful_count = sum(1 for v in violations if v.get('is_willful', False))
        if willful_count == 0:
            red_flags.append("No willful violations - limited punitive damages potential")
        
        total_score = case_score.get('total_score', 0) if case_score else 0
        if total_score < 5:
            red_flags.append(f"Low case score ({total_score}/10) - consider additional documentation")
        
        if red_flags:
            self.add_bullet_list(story, red_flags)
        else:
            self.add_paragraph(story, "No significant red flags identified. Case appears solid.", self.body_blue_style)
    
    def _add_strategy_recommendations(self, story, case_data):
        """Add strategy recommendations"""
        self.add_section_header(story, "9. STRATEGY RECOMMENDATIONS", level=2)
        
        case_score = case_data.get('case_score', {})
        standing = case_data.get('standing', {})
        dispute_round = case_data.get('dispute_round', 1)
        
        recommendation = case_score.get('recommendation', 'standard_disputes') if case_score else 'standard_disputes'
        
        recommendations = []
        
        if recommendation == 'litigate':
            recommendations = [
                "PROCEED TO LITIGATION TRACK - Strong case fundamentals",
                "Skip standard dispute rounds, prepare demand letters",
                "Consult with FCRA attorney for filing strategy",
                "Calculate final damages with attorney fee projections",
            ]
        elif standing.get('has_concrete_harm'):
            recommendations = [
                "Standard dispute process with escalation path",
                "Document all bureau responses carefully",
                "Prepare for MOV demands if disputes fail",
                "Monitor for additional violations during process",
            ]
        else:
            recommendations = [
                "GATHER DOCUMENTATION FIRST - Standing incomplete",
                "Request credit denial letters from client",
                "Document any adverse actions experienced",
                "Complete standing checklist before proceeding",
            ]
        
        self.add_numbered_list(story, recommendations)
        
        story.append(Spacer(1, 0.5*inch))
        
        self.add_paragraph(story,
            "END OF INTERNAL ANALYSIS MEMO - DO NOT SHARE WITH CLIENT",
            self.footer_style
        )
