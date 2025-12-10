#!/usr/bin/env python3
"""
Test script for MyFreeScoreNow automation fixes

This script tests the updated MyFreeScoreNow credit import automation
to verify that the selector issues have been resolved.

Usage:
    python test_myfreescorenow.py --client-id 123         # Test specific client
    python test_myfreescorenow.py --dry-run               # Show what would be tested
    python test_myfreescorenow.py --browser-test          # Just test browser availability
"""

import sys
import argparse
from datetime import datetime
from database import SessionLocal, CreditMonitoringCredential, Client
from services.credit_import_automation import run_import_sync, test_browser_availability
from services.encryption import decrypt_value


def test_browser():
    """Test if Playwright browser is available"""
    print("\n" + "=" * 70)
    print(" BROWSER AVAILABILITY TEST")
    print("=" * 70)

    available, message = test_browser_availability()

    if available:
        print("✅ Browser Available")
        print(f"   {message}")
        return True
    else:
        print("❌ Browser NOT Available")
        print(f"   {message}")
        print("\n🔧 To fix:")
        print("   1. Install Playwright: pip install playwright")
        print("   2. Install Chromium: playwright install chromium")
        return False


def get_myfreescorenow_credentials(client_id=None):
    """Get all MyFreeScoreNow credentials, optionally filtered by client_id"""
    db = SessionLocal()

    try:
        query = db.query(CreditMonitoringCredential).filter_by(
            service_name='MyFreeScoreNow.com',
            is_active=True
        )

        if client_id:
            query = query.filter_by(client_id=client_id)

        credentials = query.all()

        print(f"\n📋 Found {len(credentials)} active MyFreeScoreNow credential(s)")

        results = []
        for cred in credentials:
            client = db.query(Client).filter_by(id=cred.client_id).first()
            results.append({
                'credential': cred,
                'client': client
            })

        return results
    finally:
        db.close()


def test_single_import(credential_info, dry_run=False):
    """Test import for a single credential"""
    cred = credential_info['credential']
    client = credential_info['client']

    client_name = client.name if client else f"Client {cred.client_id}"

    print("\n" + "=" * 70)
    print(f" TESTING IMPORT: {client_name}")
    print("=" * 70)
    print(f"Client ID:      {cred.client_id}")
    print(f"Service:        {cred.service_name}")
    print(f"Username:       {cred.username}")
    print(f"Has SSN:        {'Yes' if cred.ssn_last4_encrypted else 'No'}")
    print(f"Last Status:    {cred.last_import_status or 'Never run'}")
    print(f"Last Attempt:   {cred.last_import_at or 'Never'}")
    if cred.last_import_error:
        print(f"Last Error:     {cred.last_import_error}")

    if dry_run:
        print("\n🔍 DRY RUN - Would attempt import with updated selectors")
        return {'success': True, 'dry_run': True}

    print("\n🚀 Starting import...")

    try:
        # Decrypt credentials
        password = decrypt_value(cred.password_encrypted)
        ssn_last4 = decrypt_value(cred.ssn_last4_encrypted) if cred.ssn_last4_encrypted else ''

        # Run import
        start_time = datetime.now()
        result = run_import_sync(
            service_name=cred.service_name,
            username=cred.username,
            password=password,
            ssn_last4=ssn_last4,
            client_id=cred.client_id,
            client_name=client_name
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n⏱️  Duration: {duration:.1f} seconds")

        if result.get('success'):
            print("✅ IMPORT SUCCESSFUL")
            print(f"   Report Path: {result.get('report_path')}")

            if result.get('scores'):
                scores = result['scores']
                print(f"\n📊 Credit Scores:")
                if scores.get('transunion'):
                    print(f"   TransUnion: {scores['transunion']}")
                if scores.get('experian'):
                    print(f"   Experian:   {scores['experian']}")
                if scores.get('equifax'):
                    print(f"   Equifax:    {scores['equifax']}")

            if result.get('accounts'):
                print(f"\n💳 Accounts Found: {len(result['accounts'])}")
        else:
            print("❌ IMPORT FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description='Test MyFreeScoreNow automation fixes'
    )
    parser.add_argument(
        '--client-id',
        type=int,
        help='Test specific client ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be tested without actually running imports'
    )
    parser.add_argument(
        '--browser-test',
        action='store_true',
        help='Only test browser availability'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all MyFreeScoreNow credentials (use with caution)'
    )

    args = parser.parse_args()

    # Always test browser first
    if not test_browser():
        print("\n⚠️  Cannot proceed without browser. Fix browser setup first.")
        return 1

    if args.browser_test:
        # Just browser test, exit
        return 0

    # Get credentials to test
    credentials = get_myfreescorenow_credentials(client_id=args.client_id)

    if not credentials:
        print("\n❌ No MyFreeScoreNow credentials found")
        if args.client_id:
            print(f"   For client ID: {args.client_id}")
        return 1

    # Display what will be tested
    print("\n" + "=" * 70)
    print(" TEST PLAN")
    print("=" * 70)
    for i, cred_info in enumerate(credentials, 1):
        client_name = cred_info['client'].name if cred_info['client'] else f"Client {cred_info['credential'].client_id}"
        print(f"{i}. {client_name} (ID: {cred_info['credential'].client_id})")

    if not args.all and len(credentials) > 1:
        print(f"\n⚠️  Found {len(credentials)} credentials. Use --all to test all, or --client-id to test one.")
        return 1

    # Run tests
    results = []
    for cred_info in credentials:
        result = test_single_import(cred_info, dry_run=args.dry_run)
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    if args.dry_run:
        print("Dry run completed - no actual imports performed")
    else:
        success_count = sum(1 for r in results if r.get('success'))
        failed_count = len(results) - success_count

        print(f"Total Tests:    {len(results)}")
        print(f"Successful:     {success_count}")
        print(f"Failed:         {failed_count}")

        if failed_count > 0:
            print("\n❌ Some imports failed. Check logs above for details.")
            return 1
        else:
            print("\n✅ All imports successful!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
