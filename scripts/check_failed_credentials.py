#!/usr/bin/env python3
"""
Failed Credentials Diagnostic Tool

Analyzes failed credit pulls to identify patterns and suggest fixes.

Usage:
    python check_failed_credentials.py                    # Show all failures
    python check_failed_credentials.py --days 7           # Last 7 days only
    python check_failed_credentials.py --fix-missing-ssn  # Auto-prompt for missing SSN
    python check_failed_credentials.py --test-browser     # Test browser availability
"""

import sys
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List
from database import SessionLocal, CreditMonitoringCredential, Client
from services.encryption import decrypt_value

# Common error patterns and solutions
ERROR_PATTERNS = {
    'Login failed': {
        'causes': [
            'Invalid username or password',
            'Account locked or disabled',
            'Service changed login page structure'
        ],
        'fixes': [
            'Verify credentials by manual login',
            'Check if account needs reactivation',
            'Contact service provider'
        ]
    },
    'Failed to initialize browser': {
        'causes': [
            'Playwright not installed',
            'Chromium browser not available',
            'System permissions issue'
        ],
        'fixes': [
            'Run: playwright install chromium',
            'Check system permissions',
            'Restart the application'
        ]
    },
    'No SSN last 4': {
        'causes': [
            'SSN not provided when credential was created',
            'Service requires SSN for security questions'
        ],
        'fixes': [
            'Update credential with SSN last 4',
            'Use --fix-missing-ssn flag to update'
        ]
    },
    'Timeout': {
        'causes': [
            'Slow network connection',
            'Service website slow to respond',
            'Page structure changed'
        ],
        'fixes': [
            'Check network connectivity',
            'Retry import manually',
            'Increase timeout in code'
        ]
    },
    'Failed to download': {
        'causes': [
            'Page selectors changed',
            'Service updated website',
            'Report not available'
        ],
        'fixes': [
            'Check debug screenshots',
            'Update SERVICE_CONFIGS selectors',
            'Verify manual access works'
        ]
    }
}


def analyze_error(error_msg: str) -> Dict:
    """Match error message to known patterns"""
    if not error_msg:
        return {
            'pattern': 'Unknown',
            'causes': ['No error message recorded'],
            'fixes': ['Retry import with verbose logging']
        }

    error_lower = error_msg.lower()

    for pattern, info in ERROR_PATTERNS.items():
        if pattern.lower() in error_lower:
            return {
                'pattern': pattern,
                'causes': info['causes'],
                'fixes': info['fixes']
            }

    return {
        'pattern': 'Unknown',
        'causes': ['Uncommon error - needs investigation'],
        'fixes': [
            'Check debug screenshots',
            'Run with verbose logging',
            'Review services/credit_import_automation.py'
        ]
    }


def check_failed_credentials(days: int = None) -> Dict:
    """
    Query all failed imports and analyze patterns

    Args:
        days: Only include failures from last N days (None = all time)

    Returns:
        Dictionary with failure analysis
    """
    db = SessionLocal()

    try:
        query = db.query(CreditMonitoringCredential).filter(
            CreditMonitoringCredential.last_import_status == 'failed'
        )

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(CreditMonitoringCredential.last_import_at >= cutoff)

        failed_creds = query.all()

        print("=" * 80)
        print(f" FAILED CREDENTIAL ANALYSIS")
        if days:
            print(f" Last {days} days")
        print("=" * 80)
        print(f"\nFound {len(failed_creds)} failed import(s)\n")

        if not failed_creds:
            print("✅ No failed imports found!")
            return {'total': 0, 'failures': []}

        # Analyze each failure
        failures = []
        for i, cred in enumerate(failed_creds, 1):
            client = db.query(Client).filter_by(id=cred.client_id).first()

            failure_info = {
                'credential_id': cred.id,
                'client_id': cred.client_id,
                'client_name': client.name if client else f"Client {cred.client_id}",
                'service': cred.service_name,
                'username': cred.username,
                'has_ssn': bool(cred.ssn_last4_encrypted),
                'last_attempt': cred.last_import_at,
                'error_message': cred.last_import_error,
                'error_analysis': analyze_error(cred.last_import_error)
            }
            failures.append(failure_info)

            # Print detailed info
            print(f"{'─' * 80}")
            print(f"#{i} - Client: {failure_info['client_name']} (ID: {cred.client_id})")
            print(f"{'─' * 80}")
            print(f"Service:       {cred.service_name}")
            print(f"Username:      {cred.username}")
            print(f"Has SSN:       {'Yes' if failure_info['has_ssn'] else '❌ NO (may be required)'}")
            print(f"Last Attempt:  {cred.last_import_at or 'Never'}")
            print(f"Error:         {cred.last_import_error or 'No error message'}")

            analysis = failure_info['error_analysis']
            print(f"\n📋 Error Pattern: {analysis['pattern']}")
            print(f"\n💡 Possible Causes:")
            for cause in analysis['causes']:
                print(f"   • {cause}")
            print(f"\n🔧 Suggested Fixes:")
            for fix in analysis['fixes']:
                print(f"   • {fix}")
            print()

        # Summary statistics
        print("=" * 80)
        print(" SUMMARY STATISTICS")
        print("=" * 80)

        # Group by error pattern
        error_counts = Counter([f['error_analysis']['pattern'] for f in failures])
        print(f"\nErrors by Pattern:")
        for pattern, count in error_counts.most_common():
            print(f"  {count}x {pattern}")

        # Group by service
        service_counts = Counter([f['service'] for f in failures])
        print(f"\nFailures by Service:")
        for service, count in service_counts.most_common():
            print(f"  {count}x {service}")

        # Check for missing SSN
        missing_ssn = [f for f in failures if not f['has_ssn']]
        if missing_ssn:
            print(f"\n⚠️  {len(missing_ssn)} credential(s) missing SSN last 4:")
            for f in missing_ssn:
                print(f"   • Client {f['client_id']}: {f['client_name']} - {f['service']}")

        return {
            'total': len(failed_creds),
            'failures': failures,
            'error_counts': dict(error_counts),
            'service_counts': dict(service_counts),
            'missing_ssn': len(missing_ssn)
        }

    finally:
        db.close()


def test_browser_availability():
    """Test if Playwright browser is available"""
    from services.credit_import_automation import test_browser_availability as test_browser

    print("\n" + "=" * 80)
    print(" BROWSER AVAILABILITY TEST")
    print("=" * 80)

    available, message = test_browser()

    if available:
        print("✅ Browser Available")
        print(f"   {message}")
    else:
        print("❌ Browser NOT Available")
        print(f"   {message}")
        print("\nTo fix:")
        print("   1. Install Playwright: pip install playwright")
        print("   2. Install Chromium: playwright install chromium")

    return available


def fix_missing_ssn():
    """Prompt user to add SSN for credentials missing it"""
    from services.encryption import encrypt_value

    db = SessionLocal()

    try:
        failed_creds = db.query(CreditMonitoringCredential).filter(
            CreditMonitoringCredential.last_import_status == 'failed',
            CreditMonitoringCredential.ssn_last4_encrypted == None
        ).all()

        if not failed_creds:
            print("✅ No credentials missing SSN")
            return

        print(f"\nFound {len(failed_creds)} credential(s) with failed imports and missing SSN\n")

        for cred in failed_creds:
            client = db.query(Client).filter_by(id=cred.client_id).first()
            client_name = client.name if client else f"Client {cred.client_id}"

            print(f"\nClient: {client_name}")
            print(f"Service: {cred.service_name}")
            print(f"Username: {cred.username}")

            # Check if client has SSN in legacy field
            if client and client.ssn_last_four:
                response = input(f"Use client's SSN last 4 ({client.ssn_last_four})? [Y/n]: ")
                if response.lower() != 'n':
                    ssn_last4 = client.ssn_last_four
                else:
                    ssn_last4 = input("Enter SSN last 4 (or skip): ")
            else:
                ssn_last4 = input("Enter SSN last 4 (or press Enter to skip): ")

            if ssn_last4 and ssn_last4.strip():
                ssn_last4 = ssn_last4.strip()

                # Validate
                if not ssn_last4.isdigit() or len(ssn_last4) != 4:
                    print("  ❌ Invalid - must be 4 digits")
                    continue

                # Encrypt and save
                encrypted = encrypt_value(ssn_last4)
                cred.ssn_last4_encrypted = encrypted
                cred.last_import_status = 'pending'  # Reset to retry
                cred.last_import_error = None
                db.commit()

                print(f"  ✅ Updated SSN for credential {cred.id}")

    finally:
        db.close()


def retry_failed_imports(dry_run: bool = True):
    """
    Retry all failed imports

    Args:
        dry_run: If True, only show what would be retried
    """
    from services.credit_import_automation import run_import_sync
    from services.encryption import decrypt_value

    db = SessionLocal()

    try:
        failed_creds = db.query(CreditMonitoringCredential).filter(
            CreditMonitoringCredential.last_import_status == 'failed',
            CreditMonitoringCredential.is_active == True
        ).all()

        print(f"\n{'DRY RUN: ' if dry_run else ''}Retrying {len(failed_creds)} failed import(s)\n")

        results = {'success': 0, 'failed': 0}

        for i, cred in enumerate(failed_creds, 1):
            client = db.query(Client).filter_by(id=cred.client_id).first()
            client_name = client.name if client else f"Client {cred.client_id}"

            print(f"[{i}/{len(failed_creds)}] {client_name} - {cred.service_name}")

            if dry_run:
                print("  (Dry run - would retry)")
                continue

            try:
                password = decrypt_value(cred.password_encrypted)
                ssn_last4 = decrypt_value(cred.ssn_last4_encrypted) if cred.ssn_last4_encrypted else ''

                result = run_import_sync(
                    service_name=cred.service_name,
                    username=cred.username,
                    password=password,
                    ssn_last4=ssn_last4,
                    client_id=cred.client_id,
                    client_name=client_name
                )

                if result['success']:
                    cred.last_import_status = 'success'
                    cred.last_import_at = datetime.utcnow()
                    cred.last_import_error = None
                    cred.last_report_path = result.get('report_path')
                    print(f"  ✅ SUCCESS")
                    results['success'] += 1
                else:
                    cred.last_import_status = 'failed'
                    cred.last_import_error = result.get('error')
                    print(f"  ❌ FAILED: {result.get('error')}")
                    results['failed'] += 1

                db.commit()

            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                results['failed'] += 1

        if not dry_run:
            print(f"\nResults: {results['success']} success, {results['failed']} failed")

    finally:
        db.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Diagnose failed credit import credentials'
    )
    parser.add_argument(
        '--days',
        type=int,
        help='Only show failures from last N days (default: all time)'
    )
    parser.add_argument(
        '--fix-missing-ssn',
        action='store_true',
        help='Interactively add SSN for credentials missing it'
    )
    parser.add_argument(
        '--test-browser',
        action='store_true',
        help='Test browser availability'
    )
    parser.add_argument(
        '--retry',
        action='store_true',
        help='Retry all failed imports (use with --execute to actually run)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute retry (otherwise dry run)'
    )

    args = parser.parse_args()

    if args.test_browser:
        test_browser_availability()

    if args.fix_missing_ssn:
        fix_missing_ssn()

    if args.retry:
        retry_failed_imports(dry_run=not args.execute)

    if not (args.fix_missing_ssn or args.test_browser or args.retry):
        # Default: just show analysis
        check_failed_credentials(days=args.days)


if __name__ == '__main__':
    main()
