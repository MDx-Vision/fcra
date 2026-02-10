#!/usr/bin/env python3
"""
Batch Credit Report Import Script
Imports credit reports for all clients with credentials, one at a time.
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://localhost/fcra?sslmode=disable'
os.environ['FCRA_ENCRYPTION_KEY'] = 'KML5PemZHFpNI_klNCZ4sliZPqJH5iLW4ynQSwHs-xg='

from database import SessionLocal, Client, CreditMonitoringCredential
from services.credit_import_automation import CreditImportAutomation
from services.encryption import decrypt_value

async def run_single_import(client, cred, automation):
    """Run a single import and return the result."""
    client_name = f"{client.first_name} {client.last_name}"

    # Decrypt password
    try:
        password = decrypt_value(cred.password_encrypted)
    except Exception as e:
        return {'success': False, 'error': f'Password decryption failed: {str(e)}'}

    # Get SSN last 4 (decrypt if encrypted)
    ssn_last4 = ''
    if cred.ssn_last4_encrypted:
        try:
            ssn_last4 = decrypt_value(cred.ssn_last4_encrypted)
        except:
            ssn_last4 = cred.ssn_last4_encrypted  # May be plaintext

    try:
        result = await automation.import_report(
            service_name=cred.service_name,
            username=cred.username,
            password=password,
            ssn_last4=ssn_last4,
            client_id=client.id,
            client_name=client_name
        )
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def run_imports():
    db = SessionLocal()

    # Get all clients with credentials
    clients_with_creds = db.query(Client, CreditMonitoringCredential).join(
        CreditMonitoringCredential, Client.id == CreditMonitoringCredential.client_id
    ).all()

    total = len(clients_with_creds)
    print(f"\n{'='*60}")
    print(f"CREDIT REPORT IMPORT - {total} CLIENTS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    results = {
        'success': [],
        'failed': []
    }

    for i, (client, cred) in enumerate(clients_with_creds, 1):
        client_name = f"{client.first_name} {client.last_name}"
        print(f"[{i}/{total}] {client_name} ({cred.service_name})...", end=" ", flush=True)

        try:
            automation = CreditImportAutomation()
            result = await run_single_import(client, cred, automation)

            if result.get('success'):
                scores = result.get('scores', {})
                tu = scores.get('transunion', 'N/A')
                ex = scores.get('experian', 'N/A')
                eq = scores.get('equifax', 'N/A')
                print(f"SUCCESS - TU:{tu} EX:{ex} EQ:{eq}")
                results['success'].append({
                    'client_id': client.id,
                    'name': client_name,
                    'service': cred.service_name,
                    'scores': scores,
                    'path': result.get('report_path', result.get('path'))
                })

                # Update credential with last import info
                cred.last_import_at = datetime.utcnow()
                cred.last_report_path = result.get('report_path', result.get('path'))
                db.commit()
            else:
                error = result.get('error', 'Unknown error')
                print(f"FAILED - {error[:60]}")
                results['failed'].append({
                    'client_id': client.id,
                    'name': client_name,
                    'service': cred.service_name,
                    'error': error
                })

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"ERROR - {error_msg}")
            results['failed'].append({
                'client_id': client.id,
                'name': client_name,
                'service': cred.service_name,
                'error': error_msg
            })

        # Small delay between imports
        await asyncio.sleep(2)

    db.close()

    # Print final report
    print(f"\n{'='*60}")
    print("FINAL REPORT")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"{'='*60}\n")

    if results['success']:
        print("SUCCESSFUL IMPORTS:")
        print("-" * 60)
        for r in results['success']:
            scores = r['scores']
            print(f"  {r['name']} - TU:{scores.get('transunion','N/A')} EX:{scores.get('experian','N/A')} EQ:{scores.get('equifax','N/A')}")

    if results['failed']:
        print("\nFAILED IMPORTS:")
        print("-" * 60)
        for r in results['failed']:
            print(f"  {r['name']} ({r['service']})")
            print(f"    Error: {r['error'][:80]}")

    # Save results to file
    report_path = f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")

    return results

if __name__ == "__main__":
    asyncio.run(run_imports())
