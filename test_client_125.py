#!/usr/bin/env python3
"""Test MyFreeScoreNow import for client 125 (Shaun Smith)"""

import sys
import logging
from datetime import datetime
from database import SessionLocal, CreditMonitoringCredential, Client
from services.credit_import_automation import run_import_sync, test_browser_availability
from services.encryption import decrypt_value

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_client_125():
    """Test MyFreeScoreNow import for client 125"""

    print("=" * 80)
    print(" TESTING MYFREESCORENOW IMPORT - CLIENT 125 (SHAUN SMITH)")
    print("=" * 80)

    # Step 1: Test browser availability
    print("\n1️⃣  Testing browser availability...")
    available, msg = test_browser_availability()
    if not available:
        print(f"❌ Browser not available: {msg}")
        print("   Fix: playwright install chromium")
        return {'success': False, 'error': 'Browser not available'}
    print(f"✅ Browser available: {msg}")

    # Step 2: Query database for credentials
    print("\n2️⃣  Querying database for client 125 credentials...")
    db = SessionLocal()

    try:
        # Get client
        client = db.query(Client).filter_by(id=125).first()
        if not client:
            print("❌ Client 125 not found")
            return {'success': False, 'error': 'Client not found'}

        print(f"✅ Client found: {client.name}")
        print(f"   Email: {client.email}")
        print(f"   Status: {client.status}")

        # Get MyFreeScoreNow credentials
        credentials = db.query(CreditMonitoringCredential).filter_by(
            client_id=125,
            service_name='MyFreeScoreNow.com'
        ).all()

        if not credentials:
            print("❌ No MyFreeScoreNow credentials found for client 125")
            return {'success': False, 'error': 'No credentials found'}

        print(f"✅ Found {len(credentials)} credential(s)")

        # Use first active credential
        cred = None
        for c in credentials:
            if c.is_active:
                cred = c
                break

        if not cred:
            cred = credentials[0]  # Use first if none active

        print(f"\n📋 Credential Details:")
        print(f"   Credential ID: {cred.id}")
        print(f"   Service: {cred.service_name}")
        print(f"   Username: {cred.username}")
        print(f"   Has SSN: {'Yes' if cred.ssn_last4_encrypted else 'No'}")
        print(f"   Is Active: {cred.is_active}")
        print(f"   Last Status: {cred.last_import_status or 'Never run'}")
        print(f"   Last Attempt: {cred.last_import_at or 'Never'}")
        if cred.last_import_error:
            print(f"   Last Error: {cred.last_import_error}")

        # Step 3: Decrypt credentials
        print("\n3️⃣  Decrypting credentials...")
        try:
            password = decrypt_value(cred.password_encrypted)
            ssn_last4 = decrypt_value(cred.ssn_last4_encrypted) if cred.ssn_last4_encrypted else ''
            print("✅ Credentials decrypted successfully")
            print(f"   Password length: {len(password)} characters")
            print(f"   SSN last 4: {'****' if ssn_last4 else 'Not provided'}")
        except Exception as e:
            print(f"❌ Failed to decrypt credentials: {e}")
            return {'success': False, 'error': f'Decryption failed: {e}'}

        # Step 4: Run import
        print("\n4️⃣  Running import with updated MyFreeScoreNow automation...")
        print("   This may take 60-90 seconds...")

        start_time = datetime.now()

        try:
            result = run_import_sync(
                service_name=cred.service_name,
                username=cred.username,
                password=password,
                ssn_last4=ssn_last4,
                client_id=client.id,
                client_name=client.name
            )
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"❌ Import raised exception after {duration:.1f}s: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'duration': duration}

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n⏱️  Import completed in {duration:.1f} seconds")

        # Step 5: Analyze results
        print("\n5️⃣  Analyzing results...")

        if result.get('success'):
            print("✅ IMPORT SUCCESSFUL!")
            print(f"\n📄 Report saved:")
            print(f"   Path: {result.get('report_path')}")

            if result.get('scores'):
                scores = result['scores']
                print(f"\n📊 Credit Scores Extracted:")
                if scores.get('transunion'):
                    print(f"   TransUnion: {scores['transunion']}")
                if scores.get('experian'):
                    print(f"   Experian:   {scores['experian']}")
                if scores.get('equifax'):
                    print(f"   Equifax:    {scores['equifax']}")

                score_count = sum(1 for v in scores.values() if v)
                if score_count >= 3:
                    print(f"   ✅ All 3 bureau scores extracted")
                else:
                    print(f"   ⚠️  Only {score_count}/3 scores extracted")
            else:
                print("   ⚠️  No scores extracted")

            if result.get('accounts'):
                print(f"\n💳 Accounts Found: {len(result['accounts'])}")
                if len(result['accounts']) > 0:
                    print(f"   Sample accounts:")
                    for i, acc in enumerate(result['accounts'][:3], 1):
                        print(f"   {i}. {acc.get('creditor', 'Unknown')} - {acc.get('account_type', 'Unknown')}")
                    if len(result['accounts']) > 3:
                        print(f"   ... and {len(result['accounts']) - 3} more")
            else:
                print("   ⚠️  No accounts extracted")

            # Update credential status
            print("\n📝 Updating credential status in database...")
            cred.last_import_status = 'success'
            cred.last_import_at = datetime.utcnow()
            cred.last_import_error = None
            cred.last_report_path = result.get('report_path')
            db.commit()
            print("   ✅ Database updated")

        else:
            print("❌ IMPORT FAILED")
            error = result.get('error', 'Unknown error')
            print(f"   Error: {error}")

            # Update credential status
            print("\n📝 Updating credential status in database...")
            cred.last_import_status = 'failed'
            cred.last_import_at = datetime.utcnow()
            cred.last_import_error = error
            db.commit()
            print("   ✅ Database updated with error")

            # Check for debug screenshots
            print("\n🔍 Checking for debug screenshots...")
            from pathlib import Path
            reports_dir = Path("uploads/credit_reports")
            if reports_dir.exists():
                screenshots = sorted(reports_dir.glob("login_debug_*.png"), reverse=True)[:3]
                if screenshots:
                    print(f"   Found {len(screenshots)} recent debug screenshot(s):")
                    for ss in screenshots:
                        print(f"   - {ss.name}")
                    print(f"   To view: open {screenshots[0]}")
                else:
                    print("   No debug screenshots found")

        return result

    finally:
        db.close()

if __name__ == '__main__':
    try:
        result = test_client_125()

        print("\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)

        if result.get('success'):
            print("✅ MyFreeScoreNow import SUCCESSFUL for client 125")
            print("   The fix is working correctly!")
            sys.exit(0)
        else:
            print("❌ MyFreeScoreNow import FAILED for client 125")
            print(f"   Error: {result.get('error')}")
            print("   Review the logs above for debugging info")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
