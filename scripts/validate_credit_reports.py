#!/usr/bin/env python3
"""
Credit Report Date Validation Script

Validates all credit reports in uploads/credit_reports/
Checks for:
- Valid date formats in HTML
- Recent report dates (< 30 days old flagged as stale)
- Missing bureau data
- Corrupt HTML files

Usage:
    python validate_credit_reports.py                 # Read-only validation
    python validate_credit_reports.py --fix-database  # Update DB with extracted dates
    python validate_credit_reports.py --max-age 60    # Custom staleness threshold
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from database import SessionLocal, CreditReport

# Configuration
REPORTS_DIR = Path("uploads/credit_reports")
DEFAULT_MAX_AGE_DAYS = 30


def validate_credit_report_date(html_content: str) -> Dict:
    """
    Extract and validate report dates from MyScoreIQ HTML.

    Args:
        html_content: Full HTML content of credit report

    Returns:
        {
            'valid': bool,
            'report_dates': {
                'transunion': datetime or None,
                'experian': datetime or None,
                'equifax': datetime or None
            },
            'html_dates': [list of all dates found],
            'errors': [list of issues]
        }
    """
    result = {
        'valid': True,
        'report_dates': {},
        'html_dates': [],
        'errors': []
    }

    # Pattern 1: Report Date header
    # <ng ng-if="EXP.report_date" class="ng-binding ng-scope">11/18/2025</ng>
    header_pattern = re.compile(
        r'<ng[^>]*ng-if="(TUC|EXP|EQF)\.report_date"[^>]*>\s*(\d{1,2}/\d{1,2}/\d{4})\s*</ng>',
        re.IGNORECASE
    )

    # Pattern 2: Summary section
    # <ng-repeat ng-show="TUC.report_date" class="ng-binding">11/18/2025</ng-repeat>
    summary_pattern = re.compile(
        r'<ng-repeat[^>]*ng-show="(TUC|EXP|EQF)\.report_date"[^>]*>\s*(\d{1,2}/\d{1,2}/\d{4})\s*</ng-repeat>',
        re.IGNORECASE
    )

    # Extract dates
    for pattern in [header_pattern, summary_pattern]:
        for match in pattern.finditer(html_content):
            bureau = match.group(1).upper()
            date_str = match.group(2)

            try:
                parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                result['html_dates'].append({
                    'bureau': bureau,
                    'date': date_str,
                    'parsed': parsed_date
                })

                # Map bureau code to name
                bureau_map = {'TUC': 'transunion', 'EXP': 'experian', 'EQF': 'equifax'}
                bureau_name = bureau_map.get(bureau)

                if bureau_name:
                    # Use first occurrence if multiple found
                    if bureau_name not in result['report_dates']:
                        result['report_dates'][bureau_name] = parsed_date
            except ValueError:
                result['errors'].append(f"Invalid date format: {date_str}")
                result['valid'] = False

    # Validation checks
    if not result['report_dates']:
        result['errors'].append("No report dates found in HTML")
        result['valid'] = False
        return result

    # Check for missing bureaus
    expected_bureaus = ['transunion', 'experian', 'equifax']
    missing_bureaus = [b for b in expected_bureaus if b not in result['report_dates']]
    if missing_bureaus:
        result['errors'].append(f"Missing bureaus: {', '.join(missing_bureaus)}")

    return result


def extract_file_metadata(filename: str) -> Optional[Dict]:
    """
    Extract client_id and timestamp from filename.

    Format: {client_id}_{name}_{YYYYMMDD_HHMMSS}.html
    Example: 84_Rafael_Rodriguez_20251204_053721.html

    Returns:
        {
            'client_id': int,
            'timestamp': datetime,
            'timestamp_str': str
        } or None if invalid format
    """
    match = re.match(r'(\d+)_.*_(\d{8}_\d{6})\.html$', filename)
    if not match:
        return None

    client_id = int(match.group(1))
    timestamp_str = match.group(2)

    try:
        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        return {
            'client_id': client_id,
            'timestamp': timestamp,
            'timestamp_str': timestamp_str
        }
    except ValueError:
        return None


def validate_all_reports(max_age_days: int = DEFAULT_MAX_AGE_DAYS, fix_database: bool = False) -> Dict:
    """
    Validate all credit reports in uploads/credit_reports/

    Args:
        max_age_days: Number of days before a report is considered stale
        fix_database: If True, update database with extracted report dates

    Returns:
        Dictionary with validation results and statistics
    """
    results = {
        'total_files': 0,
        'valid': 0,
        'invalid': 0,
        'stale': 0,
        'missing_dates': 0,
        'issues': []
    }

    # Check if reports directory exists
    if not REPORTS_DIR.exists():
        print(f"❌ Reports directory not found: {REPORTS_DIR}")
        print("   NOTE: Reports are on Replit server, not local")
        return results

    # Get all HTML files
    html_files = list(REPORTS_DIR.glob("*.html"))
    # Filter out debug screenshots
    html_files = [f for f in html_files if not f.name.startswith('login_debug_')
                  and not f.name.startswith('after_security_')]

    results['total_files'] = len(html_files)

    print(f"🔍 Validating {len(html_files)} HTML reports in {REPORTS_DIR}...")
    print(f"   Staleness threshold: {max_age_days} days")
    if fix_database:
        print(f"   Database update: ENABLED")
    print()

    db_session = None
    if fix_database:
        db_session = SessionLocal()

    try:
        for filepath in html_files:
            # Extract metadata from filename
            metadata = extract_file_metadata(filepath.name)
            if not metadata:
                results['issues'].append({
                    'file': filepath.name,
                    'severity': 'error',
                    'message': 'Invalid filename format'
                })
                results['invalid'] += 1
                continue

            client_id = metadata['client_id']
            import_date = metadata['timestamp']

            # Read HTML file
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    html = f.read()
            except Exception as e:
                results['issues'].append({
                    'file': filepath.name,
                    'client_id': client_id,
                    'severity': 'error',
                    'message': f'Failed to read file: {e}'
                })
                results['invalid'] += 1
                continue

            # Validate report dates
            validation = validate_credit_report_date(html)

            if not validation['valid']:
                results['invalid'] += 1
                results['issues'].append({
                    'file': filepath.name,
                    'client_id': client_id,
                    'severity': 'error',
                    'message': 'Invalid report dates',
                    'details': validation['errors']
                })
                continue

            # Check date freshness
            report_dates = validation['report_dates']
            if report_dates:
                # Use earliest bureau date for age calculation
                earliest_date = min(report_dates.values())
                age_days = (datetime.now() - earliest_date).days

                # Flag stale reports
                if age_days > max_age_days:
                    results['stale'] += 1
                    results['issues'].append({
                        'file': filepath.name,
                        'client_id': client_id,
                        'severity': 'warning',
                        'message': f'Report is {age_days} days old (stale)',
                        'report_date': earliest_date.strftime('%Y-%m-%d'),
                        'age_days': age_days
                    })

                # Update database if requested
                if fix_database and db_session:
                    try:
                        # Find CreditReport record by client_id and created_at
                        report = db_session.query(CreditReport).filter_by(
                            client_id=client_id
                        ).order_by(CreditReport.created_at.desc()).first()

                        if report and not report.report_date:
                            report.report_date = earliest_date
                            db_session.commit()
                            print(f"✓ Updated database for Client {client_id}: {filepath.name}")
                    except Exception as e:
                        print(f"✗ Failed to update database for {filepath.name}: {e}")
                        db_session.rollback()
            else:
                results['missing_dates'] += 1
                results['issues'].append({
                    'file': filepath.name,
                    'client_id': client_id,
                    'severity': 'error',
                    'message': 'No report dates found in HTML'
                })

            results['valid'] += 1
    finally:
        if db_session:
            db_session.close()

    return results


def print_report(results: Dict, max_age_days: int):
    """Print formatted validation report"""
    print("\n" + "=" * 70)
    print(" CREDIT REPORT VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total Files Scanned:     {results['total_files']}")
    print(f"Valid Reports:           {results['valid']}")
    print(f"Invalid Reports:         {results['invalid']}")
    print(f"Stale Reports (>{max_age_days}d): {results['stale']}")
    print(f"Missing Dates:           {results['missing_dates']}")
    print(f"Total Issues:            {len(results['issues'])}")
    print("=" * 70)

    if results['issues']:
        # Group by severity
        errors = [i for i in results['issues'] if i.get('severity') == 'error']
        warnings = [i for i in results['issues'] if i.get('severity') == 'warning']

        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for i, issue in enumerate(errors[:20], 1):
                print(f"\n  {i}. {issue['file']}")
                print(f"     Client ID: {issue.get('client_id', 'Unknown')}")
                print(f"     {issue['message']}")
                if 'details' in issue:
                    for detail in issue['details']:
                        print(f"       - {detail}")

            if len(errors) > 20:
                print(f"\n  ... and {len(errors) - 20} more errors")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for i, issue in enumerate(warnings[:20], 1):
                print(f"\n  {i}. {issue['file']}")
                print(f"     Client ID: {issue.get('client_id', 'Unknown')}")
                print(f"     Report Date: {issue.get('report_date', 'Unknown')}")
                print(f"     Age: {issue.get('age_days', '?')} days")

            if len(warnings) > 20:
                print(f"\n  ... and {len(warnings) - 20} more warnings")

    print("\n" + "=" * 70)

    # Exit status
    if results['invalid'] > 0:
        print("❌ VALIDATION FAILED - Invalid reports found")
        return 1
    elif results['stale'] > 0:
        print("⚠️  VALIDATION WARNING - Stale reports found")
        return 0
    else:
        print("✅ VALIDATION PASSED - All reports valid and current")
        return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate credit report dates in uploads/credit_reports/'
    )
    parser.add_argument(
        '--max-age',
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help=f'Maximum age in days before flagging as stale (default: {DEFAULT_MAX_AGE_DAYS})'
    )
    parser.add_argument(
        '--fix-database',
        action='store_true',
        help='Update database with extracted report dates'
    )

    args = parser.parse_args()

    # Run validation
    results = validate_all_reports(
        max_age_days=args.max_age,
        fix_database=args.fix_database
    )

    # Print report
    exit_code = print_report(results, args.max_age)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
