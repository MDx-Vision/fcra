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
import os

# WeasyPrint imports - lazy loaded to allow import of HTML generators without WeasyPrint
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    HTML = None
    CSS = None
    FontConfiguration = None
    WEASYPRINT_AVAILABLE = False


def html_to_pdf(html_content, output_path, base_url=None):
    """
    Convert Apple-style HTML to PDF using WeasyPrint.

    Args:
        html_content (str): Complete HTML string with embedded CSS
        output_path (str): Path to save the PDF file
        base_url (str, optional): Base URL for resolving relative paths

    Returns:
        str: Path to the generated PDF

    Features:
        - Preserves Apple-style CSS (gradients, fonts, colors)
        - Supports @page rules for print layout
        - Handles Google Fonts (Playfair Display, DM Sans)
        - Print-optimized with page breaks and color preservation

    Usage:
        html = generate_client_report_html(...)
        pdf_path = html_to_pdf(html, '/path/to/output.pdf')
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError(
            "WeasyPrint is not installed. "
            "Install with: pip install weasyprint"
        )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Configure font handling for Google Fonts
    font_config = FontConfiguration()

    # Add print-specific CSS to preserve colors and handle page breaks
    print_css = CSS(string='''
        @page {
            size: letter;
            margin: 0;
        }
        body {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .page {
            page-break-after: always;
        }
        .no-break {
            page-break-inside: avoid;
        }
    ''', font_config=font_config)

    # Generate PDF
    html_obj = HTML(string=html_content, base_url=base_url)
    html_obj.write_pdf(
        output_path,
        stylesheets=[print_css],
        font_config=font_config
    )

    return output_path


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
    # Calculate metrics from database objects
    case_number = f"BAG-FCRA-{analysis.id:04d}"
    violation_count = len(violations)

    # Count willful violations
    willful_count = sum(1 for v in violations if v.is_willful)
    willfulness_percentage = int((willful_count / violation_count * 100)) if violation_count > 0 else 0

    # Get unique defendants
    defendants = set()
    for v in violations:
        if v.bureau:
            defendants.add(v.bureau)
    defendant_count = len(defendants)

    # Get unique accounts
    accounts = set(v.account_name for v in violations if v.account_name)
    account_count = len(accounts)

    # Calculate settlement target
    settlement_target = damages.settlement_target if damages else 0

    # Group violations by category
    violation_categories = {}
    for v in violations:
        category = v.violation_type or 'Unknown'
        if category not in violation_categories:
            violation_categories[category] = []
        violation_categories[category].append(v)

    # Find impossible contradictions
    contradiction_violations = [v for v in violations if 'contradiction' in (v.violation_type or '').lower() or 'impossible' in (v.description or '').lower()]

    # Standing components
    has_dissemination = standing.has_dissemination if standing else False
    has_concrete_harm = standing.has_concrete_harm if standing else False
    has_causation = standing.has_causation if standing else False
    standing_score = standing.standing_score if standing else 0

    # Case scores
    total_score = case_score.total_score if case_score else 0
    willfulness_score = case_score.willfulness_score if case_score else 0

    # Credit scores
    tu_score = credit_scores.get('tu') if credit_scores else 'N/A'
    ex_score = credit_scores.get('ex') if credit_scores else 'N/A'
    eq_score = credit_scores.get('eq') if credit_scores else 'N/A'

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Internal Analysis - {analysis.client_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    :root {{
      --navy-dark: #0a2540;
      --navy-light: #1a365d;
      --teal: #0d9488;
      --teal-light: #14b8a6;
      --gold: #f59e0b;
      --success: #10b981;
      --error: #ef4444;
      --gray-50: #fafaf9;
      --gray-100: #f5f5f4;
      --gray-200: #e7e5e4;
      --gray-600: #57534e;
      --gray-900: #1c1917;
    }}

    body {{
      font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
      color: var(--gray-900);
      background: #ffffff;
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }}

    h1, h2, h3, h4 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-weight: 600;
      color: var(--navy-dark);
      margin-bottom: 1rem;
    }}

    h1 {{ font-size: 2.5rem; margin-bottom: 1.5rem; }}
    h2 {{ font-size: 2rem; margin-top: 2rem; }}
    h3 {{ font-size: 1.5rem; margin-top: 1.5rem; }}

    .header {{
      background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy-light) 100%);
      color: white;
      padding: 3rem 2rem;
      border-radius: 12px;
      margin-bottom: 2rem;
    }}

    .header h1 {{
      color: white;
      margin-bottom: 0.5rem;
    }}

    .case-info {{
      opacity: 0.9;
      font-size: 0.95rem;
    }}

    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin: 2rem 0;
    }}

    .metric-card {{
      background: var(--gray-50);
      padding: 1.5rem;
      border-radius: 8px;
      border: 2px solid var(--gray-200);
    }}

    .metric-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--gray-600);
      margin-bottom: 0.5rem;
    }}

    .metric-value {{
      font-family: 'Playfair Display', serif;
      font-size: 2rem;
      font-weight: 700;
      color: var(--navy-dark);
    }}

    .metric-card.success .metric-value {{ color: var(--success); }}
    .metric-card.warning .metric-value {{ color: var(--gold); }}
    .metric-card.primary .metric-value {{ color: var(--teal); }}

    .section {{
      margin: 2rem 0;
      padding: 1.5rem;
      background: white;
      border-radius: 8px;
      border: 1px solid var(--gray-200);
    }}

    .violation-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }}

    .violation-table th {{
      background: var(--gray-100);
      padding: 0.75rem;
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid var(--gray-300);
      font-size: 0.875rem;
    }}

    .violation-table td {{
      padding: 0.75rem;
      border-bottom: 1px solid var(--gray-200);
    }}

    .violation-table tr:hover {{
      background: var(--gray-50);
    }}

    .badge {{
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .badge.willful {{
      background: #fee2e2;
      color: #991b1b;
    }}

    .badge.negligent {{
      background: #fef3c7;
      color: #92400e;
    }}

    .status-indicator {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}

    .status-dot.green {{ background: var(--success); }}
    .status-dot.red {{ background: var(--error); }}
    .status-dot.yellow {{ background: var(--gold); }}

    .action-items {{
      background: #f0fdfa;
      border-left: 4px solid var(--teal);
      padding: 1.5rem;
      margin: 1rem 0;
      border-radius: 4px;
    }}

    .action-items h3 {{
      color: var(--teal);
      margin-top: 0;
    }}

    .action-items ul {{
      margin-left: 1.5rem;
    }}

    .action-items li {{
      margin: 0.5rem 0;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Internal Analysis: {analysis.client_name}</h1>
    <div class="case-info">
      Case #{case_number} | Generated {datetime.now().strftime('%B %d, %Y')} | Round {analysis.dispute_round}
    </div>
  </div>

  <!-- Key Metrics -->
  <div class="metrics-grid">
    <div class="metric-card primary">
      <div class="metric-label">Case Strength</div>
      <div class="metric-value">{total_score}/10</div>
    </div>
    <div class="metric-card success">
      <div class="metric-label">Standing Score</div>
      <div class="metric-value">{standing_score}/10</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Violations</div>
      <div class="metric-value">{violation_count}</div>
    </div>
    <div class="metric-card warning">
      <div class="metric-label">Willfulness</div>
      <div class="metric-value">{willfulness_percentage}%</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Defendants</div>
      <div class="metric-value">{defendant_count}</div>
    </div>
    <div class="metric-card success">
      <div class="metric-label">Target Value</div>
      <div class="metric-value">${settlement_target // 1000 if settlement_target > 0 else 0}K</div>
    </div>
  </div>

  <!-- Section 1: Standing Analysis -->
  <div class="section">
    <h2>1. Standing Analysis (TransUnion v. Ramirez)</h2>
    <p><strong>Overall Standing Score:</strong> {standing_score}/10</p>

    <table class="violation-table">
      <tr>
        <th>Element</th>
        <th>Status</th>
        <th>Assessment</th>
      </tr>
      <tr>
        <td><strong>Dissemination</strong></td>
        <td>
          <span class="status-indicator">
            <span class="status-dot {'green' if has_dissemination else 'red'}"></span>
            {'Yes' if has_dissemination else 'No'}
          </span>
        </td>
        <td>{standing.dissemination_details if standing and standing.dissemination_details else 'Assessment pending'}</td>
      </tr>
      <tr>
        <td><strong>Concrete Harm</strong></td>
        <td>
          <span class="status-indicator">
            <span class="status-dot {'green' if has_concrete_harm else 'red'}"></span>
            {'Yes' if has_concrete_harm else 'No'}
          </span>
        </td>
        <td>{standing.concrete_harm_details if standing and standing.concrete_harm_details else 'Assessment pending'}</td>
      </tr>
      <tr>
        <td><strong>Causation</strong></td>
        <td>
          <span class="status-indicator">
            <span class="status-dot {'green' if has_causation else 'red'}"></span>
            {'Yes' if has_causation else 'No'}
          </span>
        </td>
        <td>{standing.causation_details if standing and standing.causation_details else 'Assessment pending'}</td>
      </tr>
    </table>
  </div>

  <!-- Section 2: Violation Summary -->
  <div class="section">
    <h2>2. Violation Summary</h2>
    <p><strong>Total Violations:</strong> {violation_count} | <strong>Willful:</strong> {willful_count} ({willfulness_percentage}%)</p>

    <table class="violation-table">
      <thead>
        <tr>
          <th>Violation Type</th>
          <th>FCRA Section</th>
          <th>Count</th>
          <th>Willfulness</th>
        </tr>
      </thead>
      <tbody>
"""

    # Add violation rows
    for category, category_violations in violation_categories.items():
        willful_in_category = sum(1 for v in category_violations if v.is_willful)
        fcra_sections = set(v.fcra_section for v in category_violations if v.fcra_section)
        fcra_section = ', '.join(fcra_sections) if fcra_sections else 'N/A'

        html += f"""
        <tr>
          <td>{category}</td>
          <td>{fcra_section}</td>
          <td>{len(category_violations)}</td>
          <td>
            <span class="badge {'willful' if willful_in_category > 0 else 'negligent'}">
              {willful_in_category} Willful
            </span>
          </td>
        </tr>
"""

    html += """
      </tbody>
    </table>
  </div>

  <!-- Section 3: Critical Violations -->
  <div class="section">
    <h2>3. Critical Violations (Impossible Contradictions)</h2>
"""

    if contradiction_violations:
        html += f"""
    <p><strong>{len(contradiction_violations)} impossible contradictions found</strong> - These are the strongest violations.</p>
    <table class="violation-table">
      <thead>
        <tr>
          <th>Account</th>
          <th>Bureau</th>
          <th>Description</th>
          <th>FCRA §</th>
        </tr>
      </thead>
      <tbody>
"""
        for v in contradiction_violations[:10]:  # Limit to 10
            html += f"""
        <tr>
          <td>{v.account_name or 'N/A'}</td>
          <td>{v.bureau or 'N/A'}</td>
          <td>{v.description[:100] if v.description else 'N/A'}...</td>
          <td>{v.fcra_section or 'N/A'}</td>
        </tr>
"""
        html += """
      </tbody>
    </table>
"""
    else:
        html += """
    <p>No impossible contradictions identified in this analysis.</p>
"""

    html += """
  </div>

  <!-- Section 4: Willfulness Assessment -->
  <div class="section">
    <h2>4. Willfulness Assessment (Safeco Standard)</h2>
    <p><strong>Willfulness Score:</strong> {willfulness_score}/10</p>
    <p><strong>Percentage:</strong> {willfulness_percentage}% of violations show willfulness</p>

    <p style="margin-top: 1rem;">
      <strong>Analysis:</strong> {'High willfulness indicates potential for punitive damages. Defendants show pattern of deliberate FCRA violations.' if willfulness_percentage > 50 else 'Moderate willfulness. Some violations may warrant statutory damages enhancements.'}
    </p>
  </div>

  <!-- Section 5: Damages Calculation -->
  <div class="section">
    <h2>5. Damages Calculation</h2>
""".format(
        willfulness_score=willfulness_score,
        willfulness_percentage=willfulness_percentage
    )

    if damages:
        html += f"""
    <table class="violation-table">
      <tr>
        <th>Category</th>
        <th>Conservative</th>
        <th>Target</th>
        <th>Aggressive</th>
      </tr>
      <tr>
        <td>Statutory Damages</td>
        <td>${damages.statutory_damages_total * 0.5:,.0f}</td>
        <td>${damages.statutory_damages_total:,.0f}</td>
        <td>${damages.statutory_damages_total * 1.5:,.0f}</td>
      </tr>
      <tr>
        <td>Punitive Damages</td>
        <td>${(damages.punitive_damages_amount or 0) * 0.5:,.0f}</td>
        <td>${damages.punitive_damages_amount or 0:,.0f}</td>
        <td>${(damages.punitive_damages_amount or 0) * 2:,.0f}</td>
      </tr>
      <tr>
        <td>Actual Damages</td>
        <td>${damages.actual_damages_amount or 0:,.0f}</td>
        <td>${damages.actual_damages_amount or 0:,.0f}</td>
        <td>${damages.actual_damages_amount or 0:,.0f}</td>
      </tr>
      <tr>
        <td><strong>Total Settlement Target</strong></td>
        <td><strong>${settlement_target * 0.5:,.0f}</strong></td>
        <td><strong>${settlement_target:,.0f}</strong></td>
        <td><strong>${settlement_target * 1.5:,.0f}</strong></td>
      </tr>
    </table>
"""
    else:
        html += """
    <p>Damages calculation pending.</p>
"""

    html += """
  </div>

  <!-- Section 6: Defendant Targeting -->
  <div class="section">
    <h2>6. Defendant Targeting</h2>
    <p><strong>Total Defendants:</strong> {defendant_count}</p>
    <ul style="margin-left: 2rem; margin-top: 1rem;">
""".format(defendant_count=defendant_count)

    for defendant in sorted(defendants):
        defendant_violations = [v for v in violations if v.bureau == defendant]
        html += f"""
      <li><strong>{defendant}</strong> - {len(defendant_violations)} violations</li>
"""

    html += """
    </ul>
  </div>

  <!-- Section 7: Action Items -->
  <div class="action-items">
    <h3>Pre-Approval Action Items</h3>
    <ul>
      <li>Review standing elements for completeness</li>
      <li>Verify all violations are properly categorized</li>
      <li>Confirm defendant identification is accurate</li>
      <li>Validate damages calculations</li>
    </ul>
  </div>

  <div class="action-items">
    <h3>Post-Approval Next Steps</h3>
    <ul>
      <li>Generate client-facing report</li>
      <li>Prepare Round {analysis.dispute_round} dispute letters</li>
      <li>Draft legal memorandum if litigation recommended</li>
      <li>Schedule client consultation</li>
    </ul>
  </div>

  <!-- Section 8: RLPP Timeline -->
  <div class="section">
    <h2>8. Recommended Litigation Path & Timeline</h2>
    <table class="violation-table">
      <tr>
        <th>Phase</th>
        <th>Timeline</th>
        <th>Key Actions</th>
      </tr>
      <tr>
        <td><strong>Pre-Litigation</strong></td>
        <td>Weeks 1-4</td>
        <td>Round {analysis.dispute_round} dispute letters, bureau investigations</td>
      </tr>
      <tr>
        <td><strong>Demand Letter</strong></td>
        <td>Week 5-6</td>
        <td>Formal demand to defendants, settlement negotiations</td>
      </tr>
      <tr>
        <td><strong>Complaint Filing</strong></td>
        <td>Week 7-8</td>
        <td>File federal complaint if no settlement</td>
      </tr>
      <tr>
        <td><strong>Discovery</strong></td>
        <td>Months 3-6</td>
        <td>Interrogatories, depositions, document requests</td>
      </tr>
      <tr>
        <td><strong>Settlement/Trial</strong></td>
        <td>Months 6-12</td>
        <td>Mediation or trial preparation</td>
      </tr>
    </table>
  </div>

  <div style="margin-top: 3rem; padding-top: 2rem; border-top: 2px solid var(--gray-200); text-align: center; color: var(--gray-600); font-size: 0.875rem;">
    <p>Brightpath Ascend Group | Internal Use Only | Case #{case_number}</p>
    <p>Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  </div>
</body>
</html>""".format(case_number=case_number)

    return html


def generate_client_email_html(analysis, violations, standing, damages, case_score, credit_scores=None):
    """
    Generate Apple-style Client Email HTML from database objects.
    Email-optimized (not print-friendly) - single page summary.

    Args:
        analysis: Analysis model instance
        violations: List of Violation model instances
        standing: Standing model instance (can be None)
        damages: Damages model instance (can be None)
        case_score: CaseScore model instance (can be None)
        credit_scores: Dict with 'tu', 'ex', 'eq' scores (optional)

    Returns:
        HTML string of client email (email-optimized, not print)
    """
    # Calculate metrics
    case_number = f"BAG-FCRA-{analysis.id:04d}"
    violation_count = len(violations)
    willful_count = sum(1 for v in violations if v.is_willful)
    willfulness_pct = int((willful_count / violation_count * 100)) if violation_count > 0 else 0

    # Get unique accounts and defendants
    accounts = set(v.account_name for v in violations if v.account_name)
    account_count = len(accounts)

    defendants = set()
    for v in violations:
        if v.bureau:
            defendants.add(v.bureau)
    defendant_count = len(defendants)

    # Settlement target
    settlement_target = damages.settlement_target if damages else 0
    settlement_min = int(settlement_target * 0.7)
    settlement_max = int(settlement_target * 1.3)

    # Standing and scores
    standing_score = standing.standing_score if standing else 0
    total_score = case_score.total_score if case_score else 0

    # Find most compelling violation
    compelling_violation = None
    for v in violations:
        if 'contradiction' in (v.violation_type or '').lower() or 'impossible' in (v.description or '').lower():
            compelling_violation = v
            break
    if not compelling_violation and violations:
        compelling_violation = violations[0]

    # Settlement probability
    if total_score >= 8:
        settlement_probability = "High (80-90%)"
    elif total_score >= 6:
        settlement_probability = "Moderate (60-80%)"
    else:
        settlement_probability = "Variable (40-60%)"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Credit Analysis is Complete - {analysis.client_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">

  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    :root {{
      --navy-dark: #0a2540;
      --navy-light: #1a365d;
      --teal: #0d9488;
      --teal-light: #14b8a6;
      --gold: #f59e0b;
      --success: #10b981;
    }}

    body {{
      font-family: 'DM Sans', -apple-system, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      background: #f8fafc;
      margin: 0;
      padding: 0;
    }}

    .email-container {{
      max-width: 600px;
      margin: 0 auto;
      background: white;
    }}

    .email-header {{
      background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy-light) 100%);
      color: white;
      padding: 2.5rem 2rem;
      text-align: center;
    }}

    .email-header h1 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }}

    .email-body {{
      padding: 2rem;
    }}

    .greeting {{
      font-size: 1.125rem;
      margin-bottom: 1.5rem;
      color: var(--navy-dark);
    }}

    .key-finding {{
      background: #f0f9ff;
      border-left: 4px solid var(--teal);
      padding: 1.25rem;
      margin: 1.5rem 0;
      border-radius: 4px;
    }}

    .key-finding h3 {{
      font-family: 'Playfair Display', serif;
      color: var(--teal);
      margin-bottom: 0.5rem;
      font-size: 1.125rem;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      margin: 1.5rem 0;
    }}

    .stat-card {{
      background: #fafaf9;
      padding: 1rem;
      border-radius: 8px;
      text-align: center;
      border: 1px solid #e7e5e4;
    }}

    .stat-label {{
      font-size: 0.75rem;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 0.25rem;
    }}

    .stat-value {{
      font-family: 'Playfair Display', serif;
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--navy-dark);
    }}

    .value-card {{
      background: linear-gradient(135deg, var(--teal) 0%, var(--teal-light) 100%);
      color: white;
      padding: 1.5rem;
      border-radius: 12px;
      text-align: center;
      margin: 1.5rem 0;
    }}

    .value-card h3 {{
      font-size: 0.875rem;
      margin-bottom: 0.5rem;
      opacity: 0.9;
    }}

    .value-amount {{
      font-family: 'Playfair Display', serif;
      font-size: 2.5rem;
      font-weight: 700;
      margin: 0.5rem 0;
    }}

    .value-range {{
      font-size: 0.875rem;
      opacity: 0.9;
    }}

    .cta-section {{
      background: #fafaf9;
      padding: 1.5rem;
      border-radius: 8px;
      text-align: center;
      margin: 1.5rem 0;
    }}

    .cta-button {{
      display: inline-block;
      background: var(--teal);
      color: white;
      padding: 0.875rem 2rem;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 600;
      margin-top: 1rem;
      transition: all 0.2s;
    }}

    .cta-button:hover {{
      background: var(--teal-light);
      transform: translateY(-1px);
    }}

    .email-footer {{
      background: var(--navy-dark);
      color: white;
      padding: 1.5rem 2rem;
      text-align: center;
      font-size: 0.875rem;
    }}

    .footer-brand {{
      font-family: 'Playfair Display', serif;
      font-size: 1.125rem;
      margin-bottom: 0.5rem;
    }}

    .footer-disclaimer {{
      opacity: 0.8;
      font-size: 0.75rem;
      margin-top: 0.5rem;
    }}
  </style>
</head>
<body>
<div class="email-container">
  <div class="email-header">
    <h1>Your Credit Analysis is Complete</h1>
    <div>Case #{case_number} | {analysis.client_name}</div>
  </div>

  <div class="email-body">
    <div class="greeting">
      <strong>Dear {analysis.client_name.split()[0]},</strong>
    </div>

    <p style="margin-bottom: 1rem;">
      We've completed a comprehensive analysis of your credit report and found <strong>{violation_count} violations</strong> of the Fair Credit Reporting Act (FCRA).
    </p>
"""

    if compelling_violation:
        html += f"""
    <div class="key-finding">
      <h3>Most Compelling Violation</h3>
      <p><strong>{compelling_violation.violation_type or 'FCRA Violation'}</strong></p>
      <p style="margin-top: 0.5rem; font-size: 0.875rem;">
        {compelling_violation.description[:200] if compelling_violation.description else 'Critical violation identified in your credit report.'}...
      </p>
    </div>
"""

    html += f"""
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Violations Found</div>
        <div class="stat-value">{violation_count}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Case Strength</div>
        <div class="stat-value">{total_score}/10</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Settlement Probability</div>
        <div class="stat-value" style="font-size: 1rem;">{settlement_probability.split()[0]}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Affected Accounts</div>
        <div class="stat-value">{account_count}</div>
      </div>
    </div>

    <div class="value-card">
      <h3>ESTIMATED CASE VALUE</h3>
      <div class="value-amount">${settlement_target // 1000}K</div>
      <div class="value-range">Settlement Range: ${settlement_min:,} - ${settlement_max:,}</div>
    </div>

    <p style="margin: 1.5rem 0;">
      <strong>What happens next?</strong>
    </p>

    <ol style="margin-left: 1.5rem; margin-bottom: 1.5rem;">
      <li style="margin-bottom: 0.5rem;">Review the detailed analysis attached to this email</li>
      <li style="margin-bottom: 0.5rem;">Reply to this email with "<strong>APPROVED</strong>" to proceed</li>
      <li style="margin-bottom: 0.5rem;">We'll file dispute letters on your behalf (Round {analysis.dispute_round})</li>
      <li style="margin-bottom: 0.5rem;">Track progress through your client portal</li>
    </ol>

    <div class="cta-section">
      <p><strong>Ready to fix your credit report?</strong></p>
      <p style="font-size: 0.875rem; margin-top: 0.5rem;">Reply to this email or click below to approve and proceed.</p>
      <a href="mailto:support@brightpathascend.com?subject=APPROVED%20-%20Case%20{case_number}" class="cta-button">
        Reply APPROVED
      </a>
    </div>

    <p style="margin-top: 1.5rem; font-size: 0.875rem; color: #64748b;">
      <strong>Questions?</strong> Our team is here to help. Reply to this email or call us at (555) 123-4567.
    </p>
  </div>

  <div class="email-footer">
    <div class="footer-brand">Brightpath Ascend Group</div>
    <div class="footer-disclaimer">
      Confidential | Case: {case_number}
    </div>
  </div>
</div>
</body>
</html>"""

    return html


def generate_client_report_html(analysis, violations, standing, damages, case_score, credit_scores=None):
    """
    Generate 7-page Apple-style client report HTML.
    Print-optimized PDF-ready document for client delivery.

    Pages:
        1. Cover (client name, case number, date)
        2. Executive Summary (case strength, standing, est. value, key finding)
        3. Your Rights (FCRA §§604, 605, 607, 609, 611, 623)
        4. Violation Summary (table of all violations)
        5. Account Analysis (account cards with bureau comparisons)
        6. Damages & Strategy (statutory/actual damages, settlement target)
        7. Next Steps (timeline, CTA)

    Args:
        analysis: Analysis model instance
        violations: List[Violation] - filtered violations
        standing: Standing model instance
        damages: Damages model instance
        case_score: CaseScore model instance
        credit_scores: Dict with 'tu', 'ex', 'eq' scores (optional)

    Returns:
        str: Complete HTML document (ready for WeasyPrint)
    """
    # Calculate metrics
    case_number = f"BAG-FCRA-2025-{analysis.id:04d}"
    date_generated = datetime.now().strftime('%B %d, %Y')
    violation_count = len(violations)
    willful_count = sum(1 for v in violations if v.is_willful)
    willfulness_pct = int((willful_count / violation_count * 100)) if violation_count > 0 else 0

    # Get unique defendants and accounts
    defendants = set()
    accounts = {}
    for v in violations:
        if v.bureau:
            defendants.add(v.bureau)
        if v.furnisher:
            defendants.add(v.furnisher)
        if v.account_name:
            if v.account_name not in accounts:
                accounts[v.account_name] = {'violations': [], 'bureaus': {}}
            accounts[v.account_name]['violations'].append(v)
            if v.bureau:
                accounts[v.account_name]['bureaus'][v.bureau] = {
                    'status': v.description or 'Unknown'
                }

    # Standing and scores
    standing_score = standing.standing_score if standing else 0
    total_score = case_score.total_score if case_score else 0

    # Settlement target
    settlement_target = damages.settlement_target if damages else 0

    # Build HTML (copy structure from FCRA_PROMPT_11_CLIENT_REPORT.md)
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Client Report - {analysis.client_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        /* Apple-style CSS from reference template */
        :root {{
            --navy-dark: #0a2540;
            --navy-light: #1a365d;
            --teal: #0d9488;
            --teal-light: #14b8a6;
            --gold: #f59e0b;
            --success: #10b981;
            --error: #ef4444;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'DM Sans', -apple-system, sans-serif;
            color: #1e293b;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        h1, h2, h3 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 600;
        }}

        .page {{
            width: 8.5in;
            min-height: 11in;
            padding: 0.75in;
            background: white;
            page-break-after: always;
        }}

        /* Cover Page */
        .cover {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy-light) 100%);
            color: white;
        }}

        .cover h1 {{
            font-size: 48px;
            margin-bottom: 24px;
            color: white;
        }}

        .cover .client-name {{
            font-size: 32px;
            margin-bottom: 48px;
        }}

        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin: 24px 0;
        }}

        .metric-card {{
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #e2e8f0;
        }}

        .metric-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-family: 'Playfair Display', serif;
            font-size: 36px;
            font-weight: 700;
            color: var(--navy-dark);
        }}

        /* Violation Table */
        .violation-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
        }}

        .violation-table th {{
            background: #f1f5f9;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e1;
            font-size: 14px;
        }}

        .violation-table td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }}

        /* Account Cards */
        .account-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin: 24px 0;
        }}

        .account-card {{
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            background: #fafaf9;
        }}

        .account-card h3 {{
            font-size: 18px;
            margin-bottom: 12px;
            color: var(--navy-dark);
        }}

        .bureau-status {{
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 14px;
            flex-wrap: wrap;
        }}

        .bureau-status div {{
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>
    <!-- Page 1: Cover -->
    <div class="page cover">
        <h1>FCRA Analysis Report</h1>
        <div class="client-name">{analysis.client_name}</div>
        <div>Case #{case_number}</div>
        <div>{datetime.now().strftime('%B %d, %Y')}</div>
    </div>

    <!-- Page 2: Executive Summary -->
    <div class="page">
        <h1>Executive Summary</h1>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Case Strength</div>
                <div class="metric-value">{total_score}/10</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Standing Score</div>
                <div class="metric-value">{standing_score}/10</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Violations Found</div>
                <div class="metric-value">{violation_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Estimated Value</div>
                <div class="metric-value">${settlement_target // 1000 if settlement_target > 0 else 0}K</div>
            </div>
        </div>

        <h2>Key Finding</h2>
        <p>Based on our analysis, your credit report contains {violation_count} violations of the Fair Credit Reporting Act.
        {willful_count} of these violations ({willfulness_pct}%) appear to be willful, which could increase damages.</p>

        <h2 style="margin-top: 32px;">What This Means for You</h2>
        <p>These violations give you legal standing to dispute inaccurate information and potentially recover damages. We recommend proceeding with Round {analysis.dispute_round} dispute letters to the credit bureaus.</p>
    </div>

    <!-- Page 3: Your Rights -->
    <div class="page">
        <h1>Your Rights Under the FCRA</h1>
        <p>The Fair Credit Reporting Act (FCRA) gives you important rights regarding your credit information:</p>

        <h2 style="margin-top: 24px;">Key Protections</h2>
        <ul style="margin-left: 32px; line-height: 2;">
            <li><strong>§604 - Permissible Purposes:</strong> Your credit report can only be accessed for legitimate purposes</li>
            <li><strong>§605 - Obsolete Information:</strong> Most negative information must be removed after 7 years</li>
            <li><strong>§607 - Accuracy Requirements:</strong> All information must be accurate and complete</li>
            <li><strong>§609 - Disclosure Rights:</strong> You have the right to know what's in your file</li>
            <li><strong>§611 - Dispute Rights:</strong> You can dispute inaccurate or incomplete information</li>
            <li><strong>§623 - Furnisher Duties:</strong> Creditors must report accurate information</li>
        </ul>

        <h2 style="margin-top: 32px;">Your Legal Remedies</h2>
        <p>When these rights are violated, you may be entitled to:</p>
        <ul style="margin-left: 32px; margin-top: 16px;">
            <li>Statutory damages ($100-$1,000 per violation)</li>
            <li>Actual damages for proven harm</li>
            <li>Punitive damages for willful violations</li>
            <li>Attorney fees and costs</li>
        </ul>
    </div>

    <!-- Page 4: Violation Summary -->
    <div class="page">
        <h1>Violation Summary</h1>

        <table class="violation-table">
            <thead>
                <tr>
                    <th>Violation Type</th>
                    <th>FCRA Section</th>
                    <th>Count</th>
                    <th>Willful</th>
                </tr>
            </thead>
            <tbody>
"""

    # Group violations by type
    violation_types = {}
    for v in violations:
        vtype = v.violation_type or 'Unknown'
        if vtype not in violation_types:
            violation_types[vtype] = {'count': 0, 'willful': 0, 'section': v.fcra_section or 'N/A'}
        violation_types[vtype]['count'] += 1
        if v.is_willful:
            violation_types[vtype]['willful'] += 1

    for vtype, data in violation_types.items():
        html += f"""
                <tr>
                    <td>{vtype}</td>
                    <td>{data['section']}</td>
                    <td>{data['count']}</td>
                    <td>{'Yes' if data['willful'] > 0 else 'No'}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>

        <h2 style="margin-top: 32px;">Most Critical Violations</h2>
        <p>The violations marked as "Willful" show patterns of deliberate non-compliance with FCRA requirements. These carry potential for enhanced damages.</p>
    </div>

    <!-- Page 5: Account Analysis -->
    <div class="page">
        <h1>Account Analysis</h1>
        <p style="margin-bottom: 24px;">Bureau-by-bureau comparison of {len(accounts)} affected accounts:</p>

        <div class="account-grid">
"""

    for account_name, account_data in list(accounts.items())[:8]:  # Limit to 8 accounts
        html += f"""
            <div class="account-card">
                <h3>{account_name}</h3>
                <div class="bureau-status">
"""
        for bureau in ['Equifax', 'Experian', 'TransUnion']:
            status = account_data['bureaus'].get(bureau, {}).get('status', 'N/A')
            html += f"                    <div><strong>{bureau}:</strong> {status[:30]}</div>\n"

        html += """
                </div>
            </div>
"""

    html += """
        </div>

        <p style="margin-top: 24px;"><strong>Note:</strong> Discrepancies between bureaus often indicate FCRA violations, as furnishers are required to report consistent, accurate information.</p>
    </div>

    <!-- Page 6: Damages & Strategy -->
    <div class="page">
        <h1>Damages & Settlement Strategy</h1>

        <h2>Estimated Damages</h2>
        <table class="violation-table">
            <tr>
                <th>Category</th>
                <th>Conservative</th>
                <th>Moderate</th>
                <th>Aggressive</th>
            </tr>
"""

    if damages:
        conservative = settlement_target * 0.5
        moderate = settlement_target
        aggressive = settlement_target * 1.5

        html += f"""
            <tr>
                <td>Statutory Damages</td>
                <td>${conservative:,.0f}</td>
                <td>${moderate:,.0f}</td>
                <td>${aggressive:,.0f}</td>
            </tr>
            <tr>
                <td>Settlement Target</td>
                <td><strong>${conservative:,.0f}</strong></td>
                <td><strong>${moderate:,.0f}</strong></td>
                <td><strong>${aggressive:,.0f}</strong></td>
            </tr>
"""

    html += """
        </table>

        <h2 style="margin-top: 32px;">Recommended Strategy</h2>
        <p><strong>Phase 1: Dispute Letters</strong> - We'll file formal disputes with the credit bureaus (Round {round_number})</p>
        <p style="margin-top: 12px;"><strong>Phase 2: Bureau Investigation</strong> - Bureaus have 30-45 days to investigate</p>
        <p style="margin-top: 12px;"><strong>Phase 3: Evaluation</strong> - Review results and determine next steps (demand letter or litigation)</p>
    </div>

    <!-- Page 7: Next Steps -->
    <div class="page">
        <h1>Next Steps</h1>

        <h2>Timeline</h2>
        <ol style="margin-left: 32px; line-height: 2.5; margin-bottom: 32px;">
            <li><strong>Week 1-2:</strong> Review and approve this analysis</li>
            <li><strong>Week 3-4:</strong> File initial dispute letters to all three bureaus</li>
            <li><strong>Week 5-8:</strong> Bureau investigation period (30-45 days required by law)</li>
            <li><strong>Week 9+:</strong> Evaluate results and determine next steps</li>
        </ol>

        <h2>What We Need From You</h2>
        <ul style="margin-left: 32px; line-height: 2.5; margin-bottom: 32px;">
            <li>Review and approve this analysis</li>
            <li>Provide any additional documentation (if requested)</li>
            <li>Authorize dispute letter generation</li>
            <li>Respond to bureau correspondence (we'll guide you)</li>
        </ul>

        <h2>How to Proceed</h2>
        <p style="margin-bottom: 16px;">Reply to the email that accompanied this report with <strong>"APPROVED"</strong> to authorize us to proceed with Round {round_number} dispute letters.</p>

        <p style="margin-top: 32px;"><strong>Questions?</strong> Contact us at:</p>
        <p>Email: support@brightpathascend.com</p>
        <p>Phone: (555) 123-4567</p>

        <div style="margin-top: 48px; padding-top: 24px; border-top: 2px solid #e2e8f0;">
            <p style="text-align: center; color: #64748b; font-size: 14px;">
                <strong>Brightpath Ascend Group</strong><br>
                Confidential Client Report | Case #{case_number}<br>
                Generated {date_generated}
            </p>
        </div>
    </div>
</body>
</html>""".format(round_number=analysis.dispute_round, case_number=case_number, date_generated=date_generated)

    return html
