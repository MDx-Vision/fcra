"""
FCRA Document Generators
Apple-style HTML generators for Internal Analysis and Client Email

INSTALLATION:
1. Copy this file to ~/workspace/document_generators.py
2. Add import to app.py: from document_generators import generate_internal_analysis_html, generate_client_email_html
3. Add the routes below to app.py

ROUTES TO ADD TO app.py:
------------------------

# Add this import at top of app.py:
from document_generators import generate_internal_analysis_html, generate_client_email_html

# Add these routes:

@app.route('/api/analysis/<int:analysis_id>/internal-analysis')
def get_internal_analysis_html(analysis_id):
    '''Generate Apple-style Internal Analysis HTML'''
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        # Try to get credit scores from credit report
        credit_scores = None
        if analysis.credit_report_id:
            # Could parse from credit report if stored
            pass
        
        html = generate_internal_analysis_html(
            analysis=analysis,
            violations=violations,
            standing=standing,
            damages=damages,
            case_score=case_score,
            credit_scores=credit_scores
        )
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/<int:analysis_id>/client-email')
def get_client_email_html(analysis_id):
    '''Generate Apple-style Client Email HTML'''
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        html = generate_client_email_html(
            analysis=analysis,
            violations=violations,
            standing=standing,
            damages=damages,
            case_score=case_score
        )
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

------------------------
END OF ROUTES TO ADD
"""

from datetime import datetime


def generate_internal_analysis_html(analysis, violations, standing, damages, case_score, credit_scores=None):
    """
    Generate Apple-style Internal Analysis HTML from database objects.
    
    Args:
        analysis: Analysis model instance
        violations: List of Violation model instances
        standing: Standing model instance (can be None)
        damages: Damages model instance (can be None)
        case_score: CaseScore model instance (can be None)
        credit_scores: Dict with 'tu', 'ex', 'eq' scores (optional)
    
    Returns:
        HTML string of the complete Internal Analysis document
    """
    
    # ===== EXTRACT DATA =====
    client_name = analysis.client_name or "Unknown Client"
    case_number = f"BAG-FCRA-2025-{analysis.id:04d}"
    report_date = datetime.now().strftime("%B %d, %Y")
    
    # Credit scores
    tu_score = credit_scores.get('tu', '---') if credit_scores else '---'
    ex_score = credit_scores.get('ex', '---') if credit_scores else '---'
    eq_score = credit_scores.get('eq', '---') if credit_scores else '---'
    
    # Calculate average score for display
    scores = []
    for s in [tu_score, ex_score, eq_score]:
        if isinstance(s, (int, float)):
            scores.append(s)
        elif isinstance(s, str) and s.isdigit():
            scores.append(int(s))
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    
    # ===== CASE METRICS =====
    violation_count = len(violations)
    
    # Get unique defendants (bureaus + furnishers)
    defendants = set()
    for v in violations:
        if v.bureau:
            defendants.add(v.bureau)
        if v.account_name and v.account_name not in ['Multiple Accounts', 'N/A']:
            defendants.add(v.account_name.split()[0])
    defendant_count = max(len(defendants), 3)
    
    # Count impossible contradictions
    contradiction_count = sum(1 for v in violations 
                             if v.violation_type and 'contradiction' in v.violation_type.lower())
    
    # Case strength from CaseScore or calculate
    if case_score:
        case_strength = case_score.total_score or 0
        standing_score_val = case_score.standing_score or 0
        willfulness_score = case_score.willfulness_score or 0
    else:
        case_strength = min(10, violation_count + (2 if standing and standing.has_concrete_harm else 0))
        standing_score_val = 0
        if standing:
            standing_score_val += 3 if standing.has_dissemination else 0
            standing_score_val += 4 if standing.has_concrete_harm else 0
            standing_score_val += 3 if standing.has_causation else 0
        willfulness_score = sum(1 for v in violations if v.is_willful) * 2
    
    # Willfulness percentage
    willful_count = sum(1 for v in violations if v.is_willful)
    willfulness_pct = int((willful_count / violation_count * 100)) if violation_count > 0 else 0
    
    # Estimated value
    if damages and damages.settlement_target:
        est_value = int(damages.settlement_target / 1000)
    else:
        est_value = int((violation_count * 1500) / 1000)
    
    # ===== DECISION LOGIC =====
    if case_strength >= 7 and standing_score_val >= 6:
        decision_class = "proceed"
        decision_text = "✓ PROCEED"
        decision_reason = "Strong case, proceed immediately"
        settlement_prob = 85
    elif case_strength >= 5 and standing_score_val >= 4:
        decision_class = "caution"
        decision_text = "⚠ ACCEPT WITH CONDITIONS"
        decision_reason = "Need denial letters or more evidence before proceeding"
        settlement_prob = 65
    else:
        decision_class = "reject"
        decision_text = "✕ DECLINE"
        decision_reason = "Insufficient violations or standing for litigation"
        settlement_prob = 25
    
    # ===== STANDING ANALYSIS =====
    if standing:
        diss_confirmed = standing.has_dissemination
        diss_score = 8 if diss_confirmed else 3
        diss_status = "confirmed" if diss_confirmed else "conditional"
        diss_evidence = standing.dissemination_details or "Check inquiries section"
        diss_action = "None needed" if diss_confirmed else "Request denial letters"
        
        harm_confirmed = standing.has_concrete_harm
        harm_score = 9 if harm_confirmed else 4
        harm_status = "confirmed" if harm_confirmed else "conditional"
        harm_evidence = standing.concrete_harm_details or "Document any denials"
        harm_action = "None needed" if harm_confirmed else "Get denial documentation"
        
        cause_confirmed = standing.has_causation
        cause_score = 8 if cause_confirmed else 5
        cause_status = "confirmed" if cause_confirmed else "conditional"
        cause_evidence = standing.causation_details or "Link violations to harm"
        cause_action = "None needed" if cause_confirmed else "Establish timeline"
    else:
        diss_score, diss_status, diss_evidence, diss_action = 5, "conditional", "No data", "Analyze inquiries"
        harm_score, harm_status, harm_evidence, harm_action = 4, "conditional", "No data", "Request denial letters"
        cause_score, cause_status, cause_evidence, cause_action = 5, "conditional", "No data", "Establish timeline"
    
    # Standing verdict
    if standing_score_val >= 8:
        standing_box_class = "strong"
        standing_verdict = "STRONG — Proceed with confidence"
        standing_analysis = "All three standing elements are confirmed. Case has solid Article III standing under TransUnion v. Ramirez."
    elif standing_score_val >= 5:
        standing_box_class = "moderate"
        standing_verdict = "MODERATE — Strengthen before proceeding"
        standing_analysis = "Some standing elements need strengthening. Recommend obtaining denial letters and documenting harm before filing."
    else:
        standing_box_class = "weak"
        standing_verdict = "WEAK — Significant standing risk"
        standing_analysis = "Standing is questionable under TransUnion v. Ramirez. May face dismissal without concrete harm documentation."
    
    # ===== VIOLATION ROWS =====
    violation_categories = {}
    for v in violations:
        cat = v.violation_type or "Other"
        if cat not in violation_categories:
            violation_categories[cat] = {
                'count': 0,
                'severity': 'medium',
                'defendants': set(),
                'fcra_section': v.fcra_section or '§ 1681e(b)'
            }
        violation_categories[cat]['count'] += 1
        if v.bureau:
            violation_categories[cat]['defendants'].add(v.bureau)
        if v.is_willful:
            violation_categories[cat]['severity'] = 'critical'
    
    violation_rows_html = ""
    for cat, data in violation_categories.items():
        severity_class = f"badge-{data['severity']}"
        defendants_str = ", ".join(list(data['defendants'])[:3]) or "Multiple"
        violation_rows_html += f"""
        <tr>
          <td>{cat}</td>
          <td>{data['count']}</td>
          <td><span class="badge {severity_class}">{data['severity'].upper()}</span></td>
          <td>{defendants_str}</td>
          <td>{data['fcra_section']}</td>
        </tr>"""
    
    # ===== CONTRADICTION ROWS =====
    contradiction_rows_html = ""
    contradiction_violations = [v for v in violations if v.violation_type and 'contradiction' in v.violation_type.lower()]
    
    if contradiction_violations:
        for v in contradiction_violations[:5]:
            account = v.account_name or "Unknown Account"
            contradiction_rows_html += f"""
        <tr>
          <td>{account[:30]}</td>
          <td>$---</td>
          <td><span class="status-error">Varies</span></td>
          <td><span class="status-error">Varies</span></td>
          <td><span class="status-error">Varies</span></td>
          <td><span class="badge badge-critical">CRITICAL</span></td>
        </tr>"""
    else:
        contradiction_rows_html = """
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted);">No impossible contradictions detected</td>
        </tr>"""
    
    # ===== WILLFULNESS ANALYSIS =====
    impossible_present = "✓ Yes" if contradiction_count > 0 else "✕ No"
    impossible_analysis = f"{contradiction_count} impossible contradictions found" if contradiction_count > 0 else "No impossible scenarios detected"
    
    pattern_present = "✓ Yes" if violation_count >= 3 else "✕ No"
    pattern_analysis = f"{violation_count} violations across multiple accounts suggests pattern" if violation_count >= 3 else "Insufficient pattern evidence"
    
    sophistication_present = "✓ Yes"
    sophistication_analysis = "Major CRAs and national furnishers are sophisticated parties"
    
    metro2_present = "✓ Yes" if any('metro' in (v.description or '').lower() for v in violations) else "— Unknown"
    metro2_analysis = "Metro 2® compliance is mandatory for all furnishers"
    
    prior_present = "✓ Yes" if willful_count > 0 else "— Unknown"
    prior_analysis = f"{willful_count} violations flagged as willful" if willful_count > 0 else "No prior knowledge evidence"
    
    # Willfulness box
    if willfulness_pct >= 70:
        willfulness_box_class = "strong"
        willfulness_conclusion = "High probability of willfulness. Punitive damages likely recoverable."
    elif willfulness_pct >= 40:
        willfulness_box_class = "moderate"
        willfulness_conclusion = "Moderate willfulness indicators. Punitive damages possible with additional evidence."
    else:
        willfulness_box_class = "weak"
        willfulness_conclusion = "Low willfulness probability. Focus on statutory damages."
    
    # ===== DAMAGES CALCULATION =====
    if damages:
        stat_cons = f"{int(damages.statutory_damages_total * 0.5):,}" if damages.statutory_damages_total else "2,000"
        stat_mod = f"{int(damages.statutory_damages_total):,}" if damages.statutory_damages_total else "5,000"
        stat_agg = f"{int(damages.statutory_damages_total * 1.5):,}" if damages.statutory_damages_total else "10,000"
        
        pun_cons = f"{int(damages.punitive_damages_amount * 0.5):,}" if damages.punitive_damages_amount else "5,000"
        pun_mod = f"{int(damages.punitive_damages_amount):,}" if damages.punitive_damages_amount else "15,000"
        pun_agg = f"{int(damages.punitive_damages_amount * 1.5):,}" if damages.punitive_damages_amount else "30,000"
        
        act_cons = f"{int(damages.actual_damages_total * 0.5):,}" if damages.actual_damages_total else "1,000"
        act_mod = f"{int(damages.actual_damages_total):,}" if damages.actual_damages_total else "3,000"
        act_agg = f"{int(damages.actual_damages_total * 1.5):,}" if damages.actual_damages_total else "5,000"
        
        fee_cons = "5,000"
        fee_mod = "10,000"
        fee_agg = "20,000"
        
        total_cons = f"{int((damages.statutory_damages_total or 4000) * 0.5 + (damages.punitive_damages_amount or 10000) * 0.5 + (damages.actual_damages_total or 2000) * 0.5 + 5000):,}"
        total_mod = f"{int((damages.statutory_damages_total or 4000) + (damages.punitive_damages_amount or 10000) + (damages.actual_damages_total or 2000) + 10000):,}"
        total_agg = f"{int((damages.statutory_damages_total or 4000) * 1.5 + (damages.punitive_damages_amount or 10000) * 1.5 + (damages.actual_damages_total or 2000) * 1.5 + 20000):,}"
    else:
        base = violation_count * 1000
        stat_cons, stat_mod, stat_agg = f"{base:,}", f"{base*2:,}", f"{base*3:,}"
        pun_cons, pun_mod, pun_agg = f"{base*2:,}", f"{base*4:,}", f"{base*6:,}"
        act_cons, act_mod, act_agg = "1,000", "3,000", "5,000"
        fee_cons, fee_mod, fee_agg = "5,000", "10,000", "20,000"
        total_cons = f"{base*3 + 6000:,}"
        total_mod = f"{base*6 + 13000:,}"
        total_agg = f"{base*9 + 25000:,}"
    
    settlement_target = f"{int(damages.settlement_target):,}" if damages and damages.settlement_target else f"{violation_count * 3000:,}"
    
    # ===== DEFENDANT ROWS =====
    defendant_rows_html = ""
    defendant_priority = [
        ("Tier 1", "Equifax", 3, "§ 1681e(b)", "$8,000"),
        ("Tier 1", "Experian", 3, "§ 1681e(b)", "$8,000"),
        ("Tier 1", "TransUnion", 3, "§ 1681e(b)", "$8,000"),
    ]
    
    furnishers = set()
    for v in violations:
        if v.account_name and v.account_name not in ['Multiple Accounts', 'N/A', 'Unknown']:
            furnishers.add(v.account_name.split()[0])
    
    for i, f in enumerate(list(furnishers)[:3]):
        tier = "Tier 2" if i < 2 else "Tier 3"
        defendant_priority.append((tier, f, 1, "§ 1681s-2(b)", "$3,000"))
    
    for tier, defendant, viol_count, basis, target in defendant_priority:
        tier_class = tier.lower().replace(" ", "")
        defendant_rows_html += f"""
        <tr>
          <td><span class="badge badge-{tier_class}">{tier}</span></td>
          <td>{defendant}</td>
          <td>{viol_count}</td>
          <td>{basis}</td>
          <td>{target}</td>
        </tr>"""
    
    pre_approval_items = """
              <li>Verify credit scores are current</li>
              <li>Request denial letters from client</li>
              <li>Confirm all violations are accurate</li>
              <li>Check statute of limitations dates</li>"""
    
    post_approval_items = """
              <li>Generate Round 1 dispute letters</li>
              <li>Send via certified mail</li>
              <li>Set 30-day calendar reminders</li>
              <li>Prepare client communication</li>"""
    
    # ===== BUILD HTML =====
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Internal Analysis - {client_name}</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --brand-teal: #0d9488;
      --brand-teal-dark: #0f766e;
      --brand-navy: #1e3a5f;
      --brand-navy-dark: #0a2540;
      --text-primary: #1a1a2e;
      --text-secondary: #4a5568;
      --text-muted: #718096;
      --bg-cream: #faf9f7;
      --bg-white: #ffffff;
      --border-subtle: #e8e6e3;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'DM Sans', -apple-system, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: var(--text-primary);
      background: var(--bg-cream);
    }}
    .page {{
      max-width: 8.5in;
      margin: 20px auto;
      background: var(--bg-white);
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }}
    .header {{
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      padding: 25px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .brand-name {{
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--brand-teal);
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    .doc-type {{
      font-family: 'Playfair Display', serif;
      font-size: 13px;
      color: rgba(255,255,255,0.6);
    }}
    .staff-badge {{
      background: #dc2626;
      color: white;
      padding: 6px 14px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 3px;
    }}
    .client-bar {{
      background: var(--bg-cream);
      padding: 18px 40px;
      border-bottom: 1px solid var(--border-subtle);
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }}
    .info-item label {{
      font-size: 9px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }}
    .info-item p {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      margin-top: 2px;
    }}
    .exec-summary {{
      background: linear-gradient(135deg, var(--brand-navy-dark) 0%, var(--brand-navy) 100%);
      margin: 25px 40px;
      border-radius: 8px;
      padding: 25px;
    }}
    .exec-title {{
      font-family: 'Playfair Display', serif;
      font-size: 14px;
      color: rgba(255,255,255,0.6);
      margin-bottom: 20px;
      text-align: center;
    }}
    .exec-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
    }}
    .exec-item {{
      text-align: center;
      padding: 12px;
      background: rgba(255,255,255,0.05);
      border-radius: 6px;
    }}
    .exec-label {{
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--brand-teal);
      margin-bottom: 6px;
    }}
    .exec-value {{
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      font-weight: 700;
      color: white;
    }}
    .decision-box {{
      margin: 0 40px 25px;
      padding: 25px 30px;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .decision-box.proceed {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); }}
    .decision-box.caution {{ background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); }}
    .decision-box.reject {{ background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); }}
    .decision-text {{
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      font-weight: 700;
      color: white;
    }}
    .decision-sub {{
      font-size: 12px;
      color: rgba(255,255,255,0.8);
      margin-top: 4px;
    }}
    .decision-right {{
      text-align: right;
      color: white;
    }}
    .decision-prob-label {{ font-size: 11px; opacity: 0.8; }}
    .decision-prob-value {{ font-size: 24px; font-weight: 700; }}
    .quick-stats {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      margin: 0 40px 25px;
    }}
    .quick-stat {{
      background: var(--bg-cream);
      padding: 15px;
      border-radius: 6px;
      text-align: center;
    }}
    .quick-stat-value {{
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      font-weight: 700;
      color: var(--brand-teal);
    }}
    .quick-stat-label {{
      font-size: 9px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .content {{ padding: 0 40px 40px; }}
    .section {{ margin-bottom: 30px; }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--brand-teal);
    }}
    .section-number {{
      width: 26px;
      height: 26px;
      background: var(--brand-navy);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 700;
    }}
    .section-title {{
      font-family: 'Playfair Display', serif;
      font-size: 17px;
      font-weight: 600;
      color: var(--brand-navy);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin: 15px 0;
    }}
    th {{
      background: var(--brand-navy);
      color: white;
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    th:first-child {{ border-radius: 5px 0 0 0; }}
    th:last-child {{ border-radius: 0 5px 0 0; }}
    td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    tr:hover {{ background: var(--bg-cream); }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .badge-critical {{ background: #fef2f2; color: #dc2626; }}
    .badge-high {{ background: #fff7ed; color: #ea580c; }}
    .badge-medium {{ background: #fefce8; color: #ca8a04; }}
    .badge-low {{ background: #f0fdf4; color: #16a34a; }}
    .badge-confirmed {{ background: #f0fdf4; color: #16a34a; }}
    .badge-conditional {{ background: #fefce8; color: #ca8a04; }}
    .badge-missing {{ background: #fef2f2; color: #dc2626; }}
    .badge-tier1 {{ background: #dc2626; color: white; }}
    .badge-tier2 {{ background: #f59e0b; color: white; }}
    .badge-tier3 {{ background: #16a34a; color: white; }}
    .assessment-box {{
      padding: 15px 20px;
      border-radius: 6px;
      margin: 15px 0;
      border-left: 4px solid;
    }}
    .assessment-box.strong {{ background: #f0fdf4; border-color: #16a34a; }}
    .assessment-box.moderate {{ background: #fefce8; border-color: #ca8a04; }}
    .assessment-box.weak {{ background: #fef2f2; border-color: #dc2626; }}
    .assessment-title {{ font-weight: 600; margin-bottom: 5px; }}
    .assessment-text {{ font-size: 13px; color: var(--text-secondary); }}
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 25px;
    }}
    .col h4 {{
      color: var(--brand-navy);
      font-size: 13px;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .col ul {{
      padding-left: 20px;
      color: var(--text-secondary);
      font-size: 13px;
    }}
    .col li {{ margin-bottom: 6px; }}
    .status-error {{
      color: #dc2626;
      background: #fef2f2;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: 600;
    }}
    .footer {{
      background: var(--brand-navy-dark);
      padding: 18px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .footer-brand {{
      font-size: 10px;
      font-weight: 600;
      color: var(--brand-teal);
      letter-spacing: 1px;
      text-transform: uppercase;
    }}
    .footer-info {{
      font-size: 10px;
      color: rgba(255,255,255,0.4);
    }}
    @media print {{
      body {{ background: white; }}
      .page {{ box-shadow: none; margin: 0; }}
    }}
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div>
      <div class="brand-name">Brightpath Ascend Group</div>
      <div class="doc-type">Internal Case Analysis</div>
    </div>
    <div class="staff-badge">Staff Only — Not for Client</div>
  </div>
  <div class="client-bar">
    <div class="info-item">
      <label>Client</label>
      <p>{client_name}</p>
    </div>
    <div class="info-item">
      <label>Case Number</label>
      <p>{case_number}</p>
    </div>
    <div class="info-item">
      <label>Report Date</label>
      <p>{report_date}</p>
    </div>
    <div class="info-item">
      <label>Scores</label>
      <p>TU: {tu_score} | EX: {ex_score} | EQ: {eq_score}</p>
    </div>
  </div>
  <div class="exec-summary">
    <div class="exec-title">Executive Summary</div>
    <div class="exec-grid">
      <div class="exec-item">
        <div class="exec-label">Case Strength</div>
        <div class="exec-value">{case_strength}/10</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Standing</div>
        <div class="exec-value">{standing_score_val}/10</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Willfulness</div>
        <div class="exec-value">{willfulness_pct}%</div>
      </div>
      <div class="exec-item">
        <div class="exec-label">Est. Value</div>
        <div class="exec-value">${est_value}K</div>
      </div>
    </div>
  </div>
  <div class="decision-box {decision_class}">
    <div>
      <div class="decision-text">{decision_text}</div>
      <div class="decision-sub">{decision_reason}</div>
    </div>
    <div class="decision-right">
      <div class="decision-prob-label">Settlement Probability</div>
      <div class="decision-prob-value">{settlement_prob}%</div>
    </div>
  </div>
  <div class="quick-stats">
    <div class="quick-stat">
      <div class="quick-stat-value">{violation_count}</div>
      <div class="quick-stat-label">Violations</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">{defendant_count}</div>
      <div class="quick-stat-label">Defendants</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">{contradiction_count}</div>
      <div class="quick-stat-label">Contradictions</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">{avg_score}</div>
      <div class="quick-stat-label">Avg Score</div>
    </div>
    <div class="quick-stat">
      <div class="quick-stat-value">90</div>
      <div class="quick-stat-label">Est. Days</div>
    </div>
  </div>
  <div class="content">
    <div class="section">
      <div class="section-header">
        <div class="section-number">1</div>
        <div class="section-title">Standing Analysis (TransUnion v. Ramirez)</div>
      </div>
      <table>
        <tr>
          <th>Element</th>
          <th>Status</th>
          <th>Score</th>
          <th>Evidence</th>
          <th>Action Needed</th>
        </tr>
        <tr>
          <td><strong>Dissemination</strong></td>
          <td><span class="badge badge-{diss_status}">{diss_status.upper()}</span></td>
          <td>{diss_score}/10</td>
          <td>{diss_evidence}</td>
          <td>{diss_action}</td>
        </tr>
        <tr>
          <td><strong>Concrete Harm</strong></td>
          <td><span class="badge badge-{harm_status}">{harm_status.upper()}</span></td>
          <td>{harm_score}/10</td>
          <td>{harm_evidence}</td>
          <td>{harm_action}</td>
        </tr>
        <tr>
          <td><strong>Causation</strong></td>
          <td><span class="badge badge-{cause_status}">{cause_status.upper()}</span></td>
          <td>{cause_score}/10</td>
          <td>{cause_evidence}</td>
          <td>{cause_action}</td>
        </tr>
      </table>
      <div class="assessment-box {standing_box_class}">
        <div class="assessment-title">Standing Verdict: {standing_verdict}</div>
        <div class="assessment-text">{standing_analysis}</div>
      </div>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">2</div>
        <div class="section-title">Violation Summary</div>
      </div>
      <table>
        <tr>
          <th>Category</th>
          <th>Count</th>
          <th>Severity</th>
          <th>Defendants</th>
          <th>FCRA Section</th>
        </tr>
        {violation_rows_html}
      </table>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">3</div>
        <div class="section-title">Critical Violations — Impossible Contradictions</div>
      </div>
      <table>
        <tr>
          <th>Account</th>
          <th>Balance</th>
          <th>TransUnion</th>
          <th>Experian</th>
          <th>Equifax</th>
          <th>Violation</th>
        </tr>
        {contradiction_rows_html}
      </table>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">4</div>
        <div class="section-title">Willfulness Assessment (Safeco Standard)</div>
      </div>
      <table>
        <tr>
          <th>Factor</th>
          <th>Present?</th>
          <th>Weight</th>
          <th>Analysis</th>
        </tr>
        <tr>
          <td>Objectively Impossible Scenarios</td>
          <td>{impossible_present}</td>
          <td>High</td>
          <td>{impossible_analysis}</td>
        </tr>
        <tr>
          <td>Pattern of Violations</td>
          <td>{pattern_present}</td>
          <td>High</td>
          <td>{pattern_analysis}</td>
        </tr>
        <tr>
          <td>Defendant Sophistication</td>
          <td>{sophistication_present}</td>
          <td>Medium</td>
          <td>{sophistication_analysis}</td>
        </tr>
        <tr>
          <td>Metro 2® Certification</td>
          <td>{metro2_present}</td>
          <td>High</td>
          <td>{metro2_analysis}</td>
        </tr>
        <tr>
          <td>Prior Industry Knowledge</td>
          <td>{prior_present}</td>
          <td>High</td>
          <td>{prior_analysis}</td>
        </tr>
      </table>
      <div class="assessment-box {willfulness_box_class}">
        <div class="assessment-title">Willfulness Probability: {willfulness_pct}%</div>
        <div class="assessment-text">{willfulness_conclusion}</div>
      </div>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">5</div>
        <div class="section-title">Damages Calculation</div>
      </div>
      <table>
        <tr>
          <th>Component</th>
          <th>Conservative</th>
          <th>Moderate</th>
          <th>Aggressive</th>
        </tr>
        <tr>
          <td>Statutory Damages</td>
          <td>${stat_cons}</td>
          <td>${stat_mod}</td>
          <td>${stat_agg}</td>
        </tr>
        <tr>
          <td>Punitive Damages</td>
          <td>${pun_cons}</td>
          <td>${pun_mod}</td>
          <td>${pun_agg}</td>
        </tr>
        <tr>
          <td>Actual Damages</td>
          <td>${act_cons}</td>
          <td>${act_mod}</td>
          <td>${act_agg}</td>
        </tr>
        <tr>
          <td>Attorney Fees (Est.)</td>
          <td>${fee_cons}</td>
          <td>${fee_mod}</td>
          <td>${fee_agg}</td>
        </tr>
        <tr style="background: var(--brand-navy); color: white;">
          <td><strong>TOTAL</strong></td>
          <td><strong>${total_cons}</strong></td>
          <td><strong>${total_mod}</strong></td>
          <td><strong>${total_agg}</strong></td>
        </tr>
      </table>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">6</div>
        <div class="section-title">Defendant Targeting</div>
      </div>
      <table>
        <tr>
          <th>Priority</th>
          <th>Defendant</th>
          <th>Violations</th>
          <th>Primary Basis</th>
          <th>Settlement Target</th>
        </tr>
        {defendant_rows_html}
        <tr style="background: var(--bg-cream); font-weight: 600;">
          <td colspan="2">TOTAL</td>
          <td>{violation_count}</td>
          <td></td>
          <td>${settlement_target}</td>
        </tr>
      </table>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">7</div>
        <div class="section-title">Action Items</div>
      </div>
      <div class="two-col">
        <div class="col">
          <h4>Pre-Approval (Before Client Docs)</h4>
          <ul>
            {pre_approval_items}
          </ul>
        </div>
        <div class="col">
          <h4>Post-Approval (After Client Signs)</h4>
          <ul>
            {post_approval_items}
          </ul>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="section-header">
        <div class="section-number">8</div>
        <div class="section-title">RLPP Timeline</div>
      </div>
      <table>
        <tr>
          <th>Phase</th>
          <th>Days</th>
          <th>Action</th>
          <th>Expected Outcome</th>
        </tr>
        <tr>
          <td><strong>Round 1</strong></td>
          <td>1-30</td>
          <td>Formal disputes to all defendants</td>
          <td>Initial responses, some deletions</td>
        </tr>
        <tr>
          <td><strong>Round 2</strong></td>
          <td>31-60</td>
          <td>MOV demands for verified items</td>
          <td>Additional deletions, evidence gathering</td>
        </tr>
        <tr>
          <td><strong>Round 3</strong></td>
          <td>61-90</td>
          <td>Regulatory complaints (CFPB/FTC/AG)</td>
          <td>Regulatory pressure, settlement offers</td>
        </tr>
        <tr>
          <td><strong>Round 4</strong></td>
          <td>91-120</td>
          <td>Pre-arbitration demands</td>
          <td>Final deletions or litigation referral</td>
        </tr>
      </table>
    </div>
  </div>
  <div class="footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-info">Case: {case_number} | Confidential — Internal Use Only</div>
  </div>
</div>
</body>
</html>"""
    
    return html


def generate_client_email_html(analysis, violations, standing, damages, case_score, credit_scores=None):
    """
    Generate Apple-style Client Email HTML from database objects.
    """
    
    client_name = analysis.client_name or "Valued Client"
    client_first_name = client_name.split()[0]
    case_number = f"BAG-FCRA-2025-{analysis.id:04d}"
    
    violation_count = len(violations)
    accounts = set(v.account_name for v in violations if v.account_name)
    account_count = len(accounts) if accounts else violation_count
    
    if case_score and case_score.total_score:
        if case_score.total_score >= 7:
            settlement_rate = 85
        elif case_score.total_score >= 5:
            settlement_rate = 70
        else:
            settlement_rate = 50
    else:
        settlement_rate = 75
    
    if damages and damages.settlement_target:
        est_value = int(damages.settlement_target / 1000)
        value_low = int(damages.settlement_target * 0.6 / 1000)
        value_high = int(damages.settlement_target * 1.4 / 1000)
    else:
        est_value = int(violation_count * 2)
        value_low = int(violation_count * 1.5)
        value_high = int(violation_count * 3)
    
    value_range = f"${value_low}K - ${value_high}K"
    
    contradiction_count = sum(1 for v in violations if v.violation_type and 'contradiction' in v.violation_type.lower())
    
    if contradiction_count > 0:
        key_finding_text = f"We identified {contradiction_count} impossible contradictions in your credit reports — accounts showing mutually exclusive statuses across bureaus. These are clear FCRA violations that credit bureaus cannot defend."
    elif violation_count > 5:
        key_finding_text = f"We found {violation_count} FCRA violations across your credit reports. This pattern of inaccuracies suggests systemic reporting failures that violate your federal rights."
    else:
        key_finding_text = f"Your credit reports contain {violation_count} documentable violations of the Fair Credit Reporting Act. You have the right to accurate credit reporting, and we can help enforce that right."
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Analysis is Ready - {client_name}</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --brand-teal: #0d9488;
      --brand-teal-dark: #0f766e;
      --brand-teal-light: #14b8a6;
      --brand-navy: #1e3a5f;
      --brand-navy-dark: #0a2540;
      --text-primary: #1a1a2e;
      --text-secondary: #4a5568;
      --text-muted: #718096;
      --bg-cream: #faf9f7;
      --bg-white: #ffffff;
      --border-subtle: #e8e6e3;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 16px;
      line-height: 1.7;
      color: var(--text-primary);
      background: linear-gradient(180deg, #f0f0f0 0%, #e8e6e3 100%);
      padding: 40px 20px;
    }}
    .email-wrapper {{ max-width: 600px; margin: 0 auto; }}
    .email-container {{
      background: var(--bg-white);
      border-radius: 3px;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(10, 37, 64, 0.12);
    }}
    .email-hero {{
      position: relative;
      background: var(--brand-navy-dark);
      padding: 48px 40px;
      text-align: center;
    }}
    .email-hero::after {{
      content: '';
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--brand-teal), var(--brand-teal-light), var(--brand-teal));
    }}
    .brand-name {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 6px;
      color: var(--brand-teal-light);
      text-transform: uppercase;
      margin-bottom: 12px;
    }}
    .hero-title {{
      font-family: 'Playfair Display', serif;
      font-size: 17px;
      color: rgba(255, 255, 255, 0.7);
    }}
    .email-body {{ padding: 45px 40px; }}
    .greeting {{
      font-family: 'Playfair Display', serif;
      font-size: 20px;
      color: var(--brand-navy);
      margin-bottom: 24px;
    }}
    .intro-text {{
      font-size: 16px;
      color: var(--text-secondary);
      margin-bottom: 16px;
      line-height: 1.75;
    }}
    .intro-text strong {{
      color: var(--brand-navy);
      font-weight: 600;
    }}
    .key-finding {{
      background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%);
      border-radius: 3px;
      padding: 28px 30px;
      margin: 32px 0;
      border-left: 4px solid var(--brand-teal);
    }}
    .key-finding-label {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      color: var(--brand-teal);
      margin-bottom: 10px;
    }}
    .key-finding-text {{
      font-size: 16px;
      color: var(--text-primary);
      line-height: 1.65;
    }}
    .stats-container {{
      background: var(--bg-cream);
      border-radius: 3px;
      padding: 12px;
      margin: 32px 0;
    }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }}
    .stat-card {{
      text-align: center;
      padding: 18px 6px;
      background: var(--bg-white);
      border-radius: 2px;
    }}
    .stat-number {{
      font-size: 22px;
      font-weight: 700;
      color: var(--brand-teal);
      margin-bottom: 6px;
    }}
    .stat-label {{
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      color: var(--text-muted);
    }}
    .value-card {{
      background: var(--brand-navy-dark);
      border-radius: 3px;
      padding: 40px;
      margin: 32px 0;
      text-align: center;
    }}
    .value-label {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: var(--brand-teal-light);
      margin-bottom: 12px;
    }}
    .value-amount {{
      font-family: 'Playfair Display', serif;
      font-size: 42px;
      font-weight: 700;
      color: white;
    }}
    .cta-section {{
      text-align: center;
      margin: 40px 0 32px;
    }}
    .cta-title {{
      font-family: 'Playfair Display', serif;
      font-size: 24px;
      font-weight: 700;
      color: var(--brand-navy);
      margin-bottom: 8px;
    }}
    .cta-text {{
      font-size: 15px;
      color: var(--text-muted);
      margin-bottom: 24px;
    }}
    .cta-button {{
      display: inline-block;
      background: var(--brand-teal);
      color: white;
      padding: 18px 48px;
      text-decoration: none;
      font-size: 15px;
      font-weight: 700;
      border-radius: 4px;
      box-shadow: 0 4px 14px rgba(13, 148, 136, 0.4);
    }}
    .signature {{
      margin-top: 40px;
      padding-top: 28px;
      border-top: 1px solid var(--border-subtle);
      text-align: center;
    }}
    .signature-name {{
      font-family: 'Playfair Display', serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--brand-navy);
    }}
    .signature-contact {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 8px;
    }}
    .email-footer {{
      background: var(--brand-navy-dark);
      padding: 30px 40px;
      text-align: center;
    }}
    .footer-brand {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--brand-teal-light);
      text-transform: uppercase;
    }}
    .footer-disclaimer {{
      font-size: 10px;
      color: rgba(255, 255, 255, 0.3);
      margin-top: 10px;
    }}
  </style>
</head>
<body>
<div class="email-wrapper">
  <div class="email-container">
    <div class="email-hero">
      <div class="brand-name">Brightpath Ascend Group</div>
      <div class="hero-title">Your Credit Analysis is Complete</div>
    </div>
    <div class="email-body">
      <p class="greeting">{client_first_name},</p>
      <p class="intro-text">Your analysis is complete. <strong>We found violations.</strong> Real ones. The kind that get results.</p>
      <p class="intro-text">This isn't credit repair. It's federal consumer protection — and the law is on your side.</p>
      <div class="key-finding">
        <div class="key-finding-label">Key Finding</div>
        <p class="key-finding-text">{key_finding_text}</p>
      </div>
      <div class="stats-container">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{violation_count}</div>
            <div class="stat-label">Violations</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${est_value}K</div>
            <div class="stat-label">Case Value</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{settlement_rate}%</div>
            <div class="stat-label">Settlement</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{account_count}</div>
            <div class="stat-label">Accounts</div>
          </div>
        </div>
      </div>
      <div class="value-card">
        <div class="value-label">Your Case Value</div>
        <div class="value-amount">{value_range}</div>
      </div>
      <div class="cta-section">
        <div class="cta-title">Ready?</div>
        <p class="cta-text">Reply "APPROVED" and we start immediately.</p>
        <a href="mailto:support@brightpathascend.com?subject=APPROVED%20-%20{case_number}" class="cta-button">I'm In →</a>
      </div>
      <div class="signature">
        <div class="signature-name">Brightpath Ascend Group</div>
        <div class="signature-contact">
          support@brightpathascend.com<br>
          (917) 909-4051
        </div>
      </div>
    </div>
    <div class="email-footer">
      <div class="footer-brand">Brightpath Ascend Group</div>
      <div class="footer-disclaimer">
        Confidential | Case: {case_number}
      </div>
    </div>
  </div>
</div>
</body>
</html>"""
    
    return html
