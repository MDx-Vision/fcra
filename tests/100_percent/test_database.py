#!/usr/bin/env python3
"""Database integrity testing for PostgreSQL"""

import psycopg2
import json
from datetime import datetime

DATABASE_URL = "postgresql://localhost/fcra"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_database():
    """Test database integrity"""

    issues = []
    checks_passed = 0

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        log("Connected to database")

        # Test 1: Check for plain text passwords
        log("Checking for plain text passwords...")
        cursor.execute("SELECT id FROM staff WHERE password_hash NOT LIKE 'scrypt:%' AND password_hash IS NOT NULL AND password_hash != ''")
        plain_passwords = cursor.fetchall()
        if plain_passwords:
            issues.append(f"Plain text passwords found: {len(plain_passwords)} records")
        else:
            checks_passed += 1
            log("  PASS: All passwords are hashed")

        # Test 2: Check for XSS in stored data
        log("Checking for XSS in client data...")
        cursor.execute("SELECT id, first_name FROM clients WHERE first_name LIKE '%<script%' OR first_name LIKE '%<img%' OR first_name LIKE '%onerror%'")
        xss_data = cursor.fetchall()
        if xss_data:
            issues.append(f"XSS data found in clients: {xss_data}")
        else:
            checks_passed += 1
            log("  PASS: No XSS in client first names")

        cursor.execute("SELECT id, last_name FROM clients WHERE last_name LIKE '%<script%' OR last_name LIKE '%<img%' OR last_name LIKE '%onerror%'")
        xss_data = cursor.fetchall()
        if xss_data:
            issues.append(f"XSS data found in last names: {xss_data}")
        else:
            checks_passed += 1
            log("  PASS: No XSS in client last names")

        # Test 3: Check email format
        log("Checking email formats...")
        cursor.execute("SELECT id, email FROM clients WHERE email NOT LIKE '%@%.%' AND email IS NOT NULL AND email != ''")
        invalid_emails = cursor.fetchall()
        if invalid_emails:
            issues.append(f"Invalid emails found: {len(invalid_emails)} records - {invalid_emails[:5]}")
        else:
            checks_passed += 1
            log("  PASS: All emails have valid format")

        # Test 4: Check for orphaned records
        log("Checking for orphaned cases...")
        cursor.execute("""
            SELECT c.id FROM cases c
            LEFT JOIN clients cl ON c.client_id = cl.id
            WHERE cl.id IS NULL AND c.client_id IS NOT NULL
        """)
        orphaned_cases = cursor.fetchall()
        if orphaned_cases:
            issues.append(f"Orphaned cases found: {len(orphaned_cases)}")
        else:
            checks_passed += 1
            log("  PASS: No orphaned cases")

        # Test 5: Check for duplicate emails
        log("Checking for duplicate emails...")
        cursor.execute("""
            SELECT email, COUNT(*) as cnt FROM clients
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email HAVING COUNT(*) > 1
        """)
        dup_emails = cursor.fetchall()
        if dup_emails:
            issues.append(f"Duplicate emails found: {dup_emails}")
        else:
            checks_passed += 1
            log("  PASS: No duplicate emails")

        # Test 6: Check required fields not null
        log("Checking required fields...")
        cursor.execute("SELECT id FROM clients WHERE first_name IS NULL OR first_name = ''")
        null_names = cursor.fetchall()
        if null_names:
            issues.append(f"Clients with null first_name: {len(null_names)}")
        else:
            checks_passed += 1
            log("  PASS: All clients have first names")

        # Test 7: Count records
        log("Counting records...")
        cursor.execute("SELECT COUNT(*) FROM clients")
        client_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM staff")
        staff_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM settlements")
        settlement_count = cursor.fetchone()[0]

        log(f"  Clients: {client_count}")
        log(f"  Cases: {case_count}")
        log(f"  Staff: {staff_count}")
        log(f"  Settlements: {settlement_count}")
        checks_passed += 1

        conn.close()

    except Exception as e:
        issues.append(f"Database connection error: {str(e)}")

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks_passed": checks_passed,
        "issues_found": issues
    }

    with open("tests/100_percent/database_results.json", "w") as f:
        json.dump(results, f, indent=2)

    log("\n" + "=" * 40)
    log("DATABASE INTEGRITY RESULTS")
    log("=" * 40)
    log(f"Checks Passed: {checks_passed}")
    log(f"Issues Found: {len(issues)}")

    if issues:
        log("\nIssues:")
        for issue in issues:
            log(f"  - {issue}")

    return results

if __name__ == "__main__":
    test_database()
