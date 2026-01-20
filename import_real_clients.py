#!/usr/bin/env python3
"""
Import real clients from contacts.csv using curl
1. Delete all existing test clients
2. Import real contacts from CSV (with optional address validation)
3. Create 3 demo clients with seed data for SOP purposes
"""

import csv
import subprocess
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
VALIDATE_ADDRESSES = False  # Set to True to validate addresses via USPS during import
SESSION_COOKIE = ".eJw9jLEKgDAMRH9FMovg2klxcneXoBECTSxtBEH8d6tgx3v37i6YA0VBJTVwFg-qIRlu20yC7MGBUbKOTpTgqVl2gV_gFVxbgrIx-pQHQ18URaGXjNWUX6p-FdZSxt2_JX7wfgDyti7y.aW6TUQ.vb1YY3qB-1VmkZGZPFz30333QVc"

# Type mapping from CSV to our stages
TYPE_MAP = {
    "C": "active",      # Active Client
    "L": "lead",        # Lead
    "X": "cancelled",   # Canceled
    "I": "cancelled",   # Inactive -> treat as cancelled
    "O": "lead",        # Other -> treat as lead
}


def curl_get(endpoint):
    """Make a GET request using curl"""
    cmd = [
        "curl", "-s",
        "-H", f"Cookie: session={SESSION_COOKIE}",
        f"{BASE_URL}{endpoint}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None


def curl_post(endpoint, data=None, timeout=30):
    """Make a POST request using curl"""
    cmd = [
        "curl", "-s",
        "-X", "POST",
        "-H", f"Cookie: session={SESSION_COOKIE}",
        "-H", "Content-Type: application/json",
        "--max-time", str(timeout),
    ]
    if data:
        cmd.extend(["-d", json.dumps(data)])
    cmd.append(f"{BASE_URL}{endpoint}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout}


def validate_address(street, city, state, zip_code):
    """Validate an address using USPS API via our endpoint"""
    if not VALIDATE_ADDRESSES:
        return None  # Skip validation

    if not street or not city or not state:
        return None

    result = curl_post("/api/address/validate", {
        "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code or ""
    })

    if result.get("success") and result.get("is_valid"):
        validated = result.get("validated_address", {})
        return {
            "street": validated.get("street", street),
            "city": validated.get("city", city),
            "state": validated.get("state", state),
            "zip": validated.get("full_zip", zip_code),
            "was_corrected": result.get("was_corrected", False)
        }
    return None


def create_credential(client_id, service_name, username, password):
    """Create credit monitoring credential for a client"""
    if not all([client_id, service_name, username, password]):
        return False

    result = curl_post("/api/credit-import/credentials", {
        "client_id": client_id,
        "service_name": service_name,
        "username": username,
        "password": password,
        "import_frequency": "manual"
    })
    return result.get("success", False)


def get_all_clients():
    """Get all current clients from database"""
    data = curl_get("/api/clients")
    if data:
        return data.get("clients", [])
    return []


def delete_client(client_id):
    """Delete a client by ID"""
    result = curl_post(f"/api/clients/{client_id}/delete")
    return result.get("success", False)


def create_client(data):
    """Create a new client"""
    result = curl_post("/api/clients/create", data)
    return result.get("success", False), result


def parse_dob(dob_str):
    """Parse DOB from various formats"""
    if not dob_str:
        return None

    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(dob_str.strip(), fmt).date().isoformat()
        except:
            continue
    return None


def extract_ssn_last4(ssn_str):
    """Extract last 4 digits from SSN"""
    if not ssn_str:
        return None
    # Remove any non-digit characters
    digits = ''.join(c for c in ssn_str if c.isdigit())
    if len(digits) >= 4:
        return digits[-4:]
    return None


def clean_ssn(ssn_str):
    """Clean SSN to just digits with dashes (XXX-XX-XXXX format)"""
    if not ssn_str:
        return None
    # Remove any non-digit characters
    digits = ''.join(c for c in ssn_str if c.isdigit())
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return None


def clean_phone(phone):
    """Clean phone number"""
    if not phone:
        return ""
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return ""  # Return empty if invalid


def clean_state(state):
    """Validate and clean state code"""
    if not state:
        return ""
    state = state.strip().upper()
    valid_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC']
    if state in valid_states:
        return state
    return ""  # Return empty if invalid


def clean_zip(zip_code):
    """Validate and clean ZIP code"""
    if not zip_code:
        return ""
    # Extract just digits
    digits = ''.join(c for c in str(zip_code) if c.isdigit())
    if len(digits) == 5:
        return digits
    elif len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    return ""  # Return empty if invalid


def read_csv_contacts(filepath):
    """Read and parse contacts from CSV"""
    contacts = []

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            type_val = row.get('type', '').strip()
            if type_val not in ['C', 'L', 'X', 'I', 'O', '']:
                continue

            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()

            if not first_name and not last_name:
                continue

            contact = {
                "first_name": first_name,
                "last_name": last_name,
                "email": row.get('email', '').strip(),
                "phone": clean_phone(row.get('phone', '')),
                "mobile": clean_phone(row.get('mobile', '')),
                "address_street": row.get('address', '').strip(),
                "address_city": row.get('city', '').strip(),
                "address_state": clean_state(row.get('state', '')),
                "address_zip": clean_zip(row.get('postal_code', '')),
                "client_type": type_val if type_val else "L",
                "stage": TYPE_MAP.get(type_val, "lead"),
                "cr_provider": row.get('cr_provider', '').strip(),
                "cr_username": row.get('cr_username', '').strip(),
                "cr_password": row.get('cr_password', '').strip(),
                "external_id": row.get('contact_id', '').strip(),
                "ssn_full": clean_ssn(row.get('social_security', '')),
                "ssn_last_four": extract_ssn_last4(row.get('social_security', '')),
                "date_of_birth": parse_dob(row.get('dob', '')),
            }
            contacts.append(contact)

    return contacts


def main():
    print("=" * 60)
    print("FCRA Client Import Script")
    print("=" * 60)

    # Step 1: Get current clients
    print("\n[1/4] Getting current clients...")
    current_clients = get_all_clients()
    print(f"  Found {len(current_clients)} existing clients")

    # Step 2: Delete all test clients
    print("\n[2/4] Deleting all test clients...")
    deleted = 0
    for client in current_clients:
        client_id = client.get('id')
        if delete_client(client_id):
            deleted += 1
            print(f"  Deleted: {client.get('name', 'Unknown')}")
    print(f"  Total deleted: {deleted}")

    # Step 3: Read and import contacts from CSV
    print("\n[3/4] Importing contacts from contacts.csv...")
    contacts = read_csv_contacts("contacts.csv")
    print(f"  Read {len(contacts)} contacts from CSV")

    imported = 0
    failed = 0
    addresses_corrected = 0

    for contact in contacts:
        # Optionally validate and correct address
        addr_status = ""
        address_street = contact["address_street"]
        address_city = contact["address_city"]
        address_state = contact["address_state"]
        address_zip = contact["address_zip"]

        if VALIDATE_ADDRESSES and address_street and address_city and address_state:
            validated = validate_address(address_street, address_city, address_state, address_zip)
            if validated:
                address_street = validated["street"]
                address_city = validated["city"]
                address_state = validated["state"]
                address_zip = validated["zip"]
                if validated["was_corrected"]:
                    addresses_corrected += 1
                    addr_status = " [addr corrected]"

        client_data = {
            "first_name": contact["first_name"],
            "last_name": contact["last_name"],
            "email": contact["email"],
            "phone": contact["phone"] or contact["mobile"],
            "mobile": contact["mobile"],  # Send mobile separately
            "address_street": address_street,
            "address_city": address_city,
            "address_state": address_state,
            "address_zip": address_zip,
            "client_type": contact["client_type"],
            "stage": contact["stage"],
            "ssn_encrypted": contact.get("ssn_full"),  # Full SSN
            "ssn_last_four": contact.get("ssn_last_four"),
            "date_of_birth": contact.get("date_of_birth"),
        }

        success, result = create_client(client_data)
        if success:
            imported += 1
            client_id = result.get("client_id")
            cred_status = ""

            # Create credit monitoring credential if we have the info
            if contact.get("cr_provider") and contact.get("cr_username") and contact.get("cr_password"):
                if create_credential(client_id, contact["cr_provider"], contact["cr_username"], contact["cr_password"]):
                    cred_status = " [+creds]"
                else:
                    cred_status = " [creds failed]"

            print(f"  + {contact['first_name']} {contact['last_name']} ({contact['client_type']}){cred_status}{addr_status}")
        else:
            failed += 1
            print(f"  FAILED: {contact['first_name']} {contact['last_name']} - {result.get('error', 'Unknown')}")

    print(f"\n  Imported: {imported}, Failed: {failed}")
    if VALIDATE_ADDRESSES:
        print(f"  Addresses corrected by USPS: {addresses_corrected}")

    # Step 4: Create 3 demo clients for SOP
    print("\n[4/4] Creating 3 demo clients for SOP purposes...")

    demo_clients = [
        {
            "first_name": "Demo",
            "last_name": "Client",
            "email": "demo.client@example.com",
            "phone": "(555) 100-0001",
            "address_street": "123 Demo Street",
            "address_city": "New York",
            "address_state": "NY",
            "address_zip": "10001",
            "client_type": "C",
            "stage": "active",
        },
        {
            "first_name": "Test",
            "last_name": "Lead",
            "email": "test.lead@example.com",
            "phone": "(555) 100-0002",
            "address_street": "456 Test Avenue",
            "address_city": "Los Angeles",
            "address_state": "CA",
            "address_zip": "90001",
            "client_type": "L",
            "stage": "lead",
        },
        {
            "first_name": "Sample",
            "last_name": "Onboarding",
            "email": "sample.onboarding@example.com",
            "phone": "(555) 100-0003",
            "address_street": "789 Sample Blvd",
            "address_city": "Chicago",
            "address_state": "IL",
            "address_zip": "60601",
            "client_type": "C",
            "stage": "onboarding",
        },
    ]

    for demo in demo_clients:
        success, result = create_client(demo)
        if success:
            print(f"  + Created demo: {demo['first_name']} {demo['last_name']}")
        else:
            print(f"  FAILED: {demo['first_name']} {demo['last_name']}")

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)

    # Final count
    final_clients = get_all_clients()
    print(f"\nFinal client count: {len(final_clients)}")


if __name__ == "__main__":
    main()
