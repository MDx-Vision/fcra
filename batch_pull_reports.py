"""Batch pull credit reports for all active clients with credentials"""
import time
from database import SessionLocal, Client
from services.credit_import_automation import run_import_sync, test_browser_availability

# Normalize service names to match SERVICE_CONFIGS
SERVICE_NAME_MAP = {
    'myscoreiq': 'MyScoreIQ.com',
    'myscoreiq.com': 'MyScoreIQ.com',
    'myfreescorenow': 'MyFreeScoreNow.com',
    'myfreescorenow.com': 'MyFreeScoreNow.com',
    'identityiq': 'IdentityIQ.com',
    'identityiq.com': 'IdentityIQ.com',
    'smartcredit': 'SmartCredit.com',
    'smartcredit.com': 'SmartCredit.com',
}

def normalize_service_name(name):
    """Convert various service name formats to canonical form"""
    if not name:
        return None
    lower = name.lower().strip()
    return SERVICE_NAME_MAP.get(lower, name)

def batch_pull_reports(limit=None, dry_run=False):
    """Pull reports for all active clients with credentials"""
    
    db = SessionLocal()
    
    # Get active clients with credentials
    clients = db.query(Client).filter(
        Client.status == 'active',
        Client.credit_monitoring_username != None,
        Client.credit_monitoring_password_encrypted != None
    ).all()
    
    print(f"=== BATCH CREDIT PULL ===")
    print(f"Found {len(clients)} active clients with credentials")
    
    if limit:
        clients = clients[:limit]
        print(f"Limited to first {limit} clients")
    
    results = {'success': 0, 'failed': 0, 'skipped': 0, 'errors': []}
    
    for i, client in enumerate(clients, 1):
        service = normalize_service_name(client.credit_monitoring_service)
        
        if not service:
            print(f"[{i}/{len(clients)}] {client.name}: SKIPPED - no service configured")
            results['skipped'] += 1
            continue
        
        print(f"\n[{i}/{len(clients)}] {client.name}")
        print(f"  Service: {service}")
        print(f"  Username: {client.credit_monitoring_username}")
        print(f"  SSN Last 4: {client.ssn_last_four or 'N/A'}")
        
        if dry_run:
            print(f"  DRY RUN - would pull report")
            results['success'] += 1
            continue
        
        try:
            result = run_import_sync(
                service_name=service,
                username=client.credit_monitoring_username,
                password=client.credit_monitoring_password_encrypted,
                ssn_last4=client.ssn_last_four or '',
                client_id=client.id,
                client_name=client.name
            )
            
            if result.get('success'):
                print(f"  ✓ SUCCESS - {result.get('report_path', 'report saved')}")
                if result.get('scores'):
                    print(f"  Scores: {result['scores']}")
                results['success'] += 1
            else:
                print(f"  ✗ FAILED - {result.get('error', 'unknown error')}")
                results['failed'] += 1
                results['errors'].append({
                    'client': client.name,
                    'error': result.get('error')
                })
            
            # Small delay between pulls to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ ERROR - {str(e)}")
            results['failed'] += 1
            results['errors'].append({
                'client': client.name,
                'error': str(e)
            })
    
    db.close()
    
    print(f"\n=== RESULTS ===")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    
    return results

if __name__ == '__main__':
    import sys
    
    # First test browser
    print("Testing browser availability...")
    available, msg = test_browser_availability()
    if not available:
        print(f"Browser not available: {msg}")
        print("Run: playwright install chromium")
        sys.exit(1)
    print("Browser OK\n")
    
    # Run with dry_run=True first to see what would happen
    batch_pull_reports(dry_run=True)
