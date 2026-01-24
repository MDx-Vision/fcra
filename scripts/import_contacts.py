#!/usr/bin/env python3
"""Import contacts from CSV into the Client database."""

import csv
import sys
from datetime import datetime
from database import get_db, Client

def parse_date(date_str):
    """Parse various date formats."""
    if not date_str or date_str.strip() == '':
        return None

    # Try different formats
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def parse_ssn_last_four(ssn):
    """Extract last 4 digits from SSN."""
    if not ssn or ssn.strip() == '':
        return None
    # Remove dashes and spaces
    ssn_clean = ssn.replace('-', '').replace(' ', '').strip()
    if len(ssn_clean) >= 4:
        return ssn_clean[-4:]
    return None

def map_status(status_1):
    """Map CSV status to database status."""
    if not status_1:
        return 'signup'

    status_lower = status_1.lower().strip()
    if 'active' in status_lower:
        return 'active'
    elif 'inactive' in status_lower:
        return 'paused'
    elif 'cancel' in status_lower:
        return 'cancelled'
    elif 'lead' in status_lower:
        return 'signup'
    else:
        return 'signup'

def import_contacts(csv_path):
    """Import contacts from CSV file."""
    db = get_db()

    imported = 0
    skipped = 0
    errors = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Skip if no name
                    first_name = (row.get('first_name') or '').strip()
                    last_name = (row.get('last_name') or '').strip()

                    if not first_name and not last_name:
                        skipped += 1
                        continue

                    # Build full name
                    name = f"{first_name} {last_name}".strip()

                    # Check if already exists by legacy_system_id
                    contact_id = row.get('contact_id', '').strip()
                    if contact_id:
                        existing = db.query(Client).filter(Client.legacy_system_id == contact_id).first()
                        if existing:
                            skipped += 1
                            continue

                    # Get phone (prefer mobile, fallback to phone)
                    phone = row.get('mobile', '').strip() or row.get('phone', '').strip()

                    # Create client
                    client = Client(
                        name=name,
                        first_name=first_name,
                        last_name=last_name,
                        email=(row.get('email') or '').strip() or None,
                        phone=phone or None,
                        address_street=(row.get('address') or '').strip() or None,
                        address_city=(row.get('city') or '').strip() or None,
                        address_state=(row.get('state') or '').strip() or None,
                        address_zip=(row.get('postal_code') or '').strip() or None,
                        ssn_last_four=parse_ssn_last_four(row.get('social_security')),
                        date_of_birth=parse_date(row.get('dob')),
                        follow_up_date=parse_date(row.get('follow_up')),
                        credit_monitoring_service=(row.get('cr_provider') or '').strip() or None,
                        credit_monitoring_username=(row.get('cr_username') or '').strip() or None,
                        credit_monitoring_password_encrypted=(row.get('cr_password') or '').strip() or None,
                        legacy_system_id=contact_id or None,
                        status=map_status(row.get('status_1')),
                        imported_at=datetime.utcnow(),
                        import_notes=f"Imported from contacts.csv. Original status: {row.get('status_1', '')}. Affiliate: {row.get('affiliate', '')}"
                    )

                    db.add(client)
                    imported += 1

                    # Commit every 50 records
                    if imported % 50 == 0:
                        db.commit()
                        print(f"  Imported {imported} contacts...")

                except Exception as e:
                    errors.append(f"Row {imported + skipped + 1}: {str(e)}")
                    continue

        # Final commit
        db.commit()

        print(f"\n=== Import Complete ===")
        print(f"Imported: {imported}")
        print(f"Skipped:  {skipped} (duplicates or empty names)")
        print(f"Errors:   {len(errors)}")

        if errors:
            print("\nErrors:")
            for err in errors[:10]:
                print(f"  - {err}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")

        return imported, skipped, errors

    except Exception as e:
        print(f"Import failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'contacts.csv'
    print(f"Importing contacts from {csv_path}...")
    import_contacts(csv_path)
