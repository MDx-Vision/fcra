"""Fixed LRM Import Script - Correct field mappings"""
import csv
from datetime import datetime
from database import SessionLocal, Client, ClientNote

def import_lrm_clients(csv_path):
    """Import clients from LRM CSV with correct field mappings"""

    results = {'total': 0, 'imported': 0, 'skipped': 0, 'errors': 0, 'error_details': []}

    # Status mapping
    status_map = {'C': 'active', 'I': 'paused', 'L': 'lead', 'X': 'cancelled'}

    db = SessionLocal()

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                results['total'] += 1

                try:
                    email = row.get('email', '').strip()

                    # Skip if no email
                    if not email:
                        results['skipped'] += 1
                        results['error_details'].append({
                            'row': row_num,
                            'name': f"{row.get('first_name', '')} {row.get('last_name', '')}",
                            'error': 'No email - skipped'
                        })
                        continue

                    # Check for duplicate
                    existing = db.query(Client).filter(Client.email == email).first()
                    if existing:
                        results['skipped'] += 1
                        continue

                    # Parse SSN - get last 4 only
                    ssn_raw = row.get('social_security', '').replace('-', '').replace(' ', '')
                    ssn_last_four = ssn_raw[-4:] if len(ssn_raw) >= 4 else None

                    # Parse date of birth
                    dob = None
                    dob_raw = row.get('dob', '').strip()
                    if dob_raw:
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                            try:
                                dob = datetime.strptime(dob_raw, fmt).date()
                                break
                            except:
                                pass

                    # Get phone (prefer phone, fallback to mobile)
                    phone = row.get('phone', '').strip() or row.get('mobile', '').strip()
                    # Clean phone
                    phone = ''.join(c for c in phone if c.isdigit())[:10] if phone else None

                    # Map status
                    lrm_type = row.get('type', 'L').strip().upper()
                    status = status_map.get(lrm_type, 'lead')

                    # Build name
                    first = row.get('first_name', '').strip()
                    last = row.get('last_name', '').strip()
                    name = f"{first} {last}".strip() or email

                    # Build import notes
                    notes_parts = []
                    if row.get('affiliate'):
                        notes_parts.append(f"Referred by: {row.get('affiliate')}")
                    if row.get('comment'):
                        notes_parts.append(f"Comment: {row.get('comment')}")
                    if row.get('dispute_center_notes'):
                        notes_parts.append(f"Dispute notes: {row.get('dispute_center_notes')}")

                    import_notes = f"Migrated from LRM on {datetime.now().strftime('%Y-%m-%d')}. LRM ID: {row.get('contact_id', 'unknown')}. Original status: {row.get('status_1', lrm_type)}"
                    if notes_parts:
                        import_notes += "\n" + "\n".join(notes_parts)

                    # Create client with CORRECT field names
                    client = Client(
                        name=name,
                        first_name=first or None,
                        last_name=last or None,
                        email=email,
                        phone=phone,
                        address_street=row.get('address', '').strip() or None,
                        address_city=row.get('city', '').strip() or None,
                        address_state=row.get('state', '').strip() or None,
                        address_zip=row.get('postal_code', '').strip() or None,
                        ssn_last_four=ssn_last_four,
                        date_of_birth=dob,
                        credit_monitoring_service=row.get('cr_provider', '').strip() or None,
                        credit_monitoring_username=row.get('cr_username', '').strip() or None,
                        credit_monitoring_password_encrypted=row.get('cr_password', '').strip() or None,
                        legacy_system_id=row.get('contact_id', '').strip() or None,
                        imported_at=datetime.now(),
                        import_notes=import_notes,
                        status=status,
                        dispute_status='new'
                    )

                    db.add(client)
                    db.flush()  # Get ID

                    results['imported'] += 1

                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append({
                        'row': row_num,
                        'email': row.get('email', 'N/A'),
                        'error': str(e)
                    })
                    db.rollback()
                    continue

            db.commit()

    except Exception as e:
        results['error_details'].append({'row': 0, 'error': str(e)})
        results['errors'] += 1
    finally:
        db.close()

    return results

if __name__ == '__main__':
    result = import_lrm_clients('contacts.csv')
    print("\n=== IMPORT RESULTS ===")
    print(f"Total rows: {result['total']}")
    print(f"Imported: {result['imported']}")
    print(f"Skipped (no email/duplicate): {result['skipped']}")
    print(f"Errors: {result['errors']}")
    if result['error_details'][:10]:
        print("\nFirst 10 issues:")
        for e in result['error_details'][:10]:
            print(f"  Row {e.get('row', '?')}: {e.get('error', 'Unknown')}")
