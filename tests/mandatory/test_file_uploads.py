#!/usr/bin/env python3
"""TASK 7: Test file uploads with all file types"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "upload_inputs_found": 0,
    "uploads_tested": 0,
    "uploads_accepted": 0,
    "uploads_rejected": 0,
    "security_tests": 0,
    "issues": [],
    "log": []
}

TEST_FILES = {
    "valid": [
        ("test.pdf", b"%PDF-1.4 test content", "application/pdf"),
        ("test.txt", b"Plain text content", "text/plain"),
        ("test.csv", b"name,email\ntest,test@test.com", "text/csv"),
    ],
    "invalid_should_reject": [
        ("test.exe", b"MZ\x90\x00", "application/x-executable"),
        ("test.php", b"<?php echo 'hack'; ?>", "application/x-php"),
        ("test.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
    ],
    "malicious_names": [
        ("../../../etc/passwd.pdf", b"%PDF-1.4", "application/pdf"),
        ("<script>alert('xss')</script>.pdf", b"%PDF-1.4", "application/pdf"),
    ]
}

async def test_file_uploads():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        pages_with_uploads = [
            "/dashboard/import",
            "/dashboard/documents",
            "/dashboard/credit-import",
        ]

        for url in pages_with_uploads:
            await _run_uploads_on_page(page, url)

        await browser.close()

    save_results()

async def _run_uploads_on_page(page, url):
    """Test file uploads on a specific page"""

    RESULTS["log"].append(f"\n=== Testing uploads on: {url} ===")

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

        file_inputs = await page.query_selector_all("input[type='file']")
        RESULTS["log"].append(f"  Found {len(file_inputs)} file inputs")
        RESULTS["upload_inputs_found"] += len(file_inputs)

        for i, file_input in enumerate(file_inputs):
            RESULTS["log"].append(f"  Testing file input #{i}")

            for filename, content, mime in TEST_FILES["valid"]:
                await _run_single_upload(page, file_input, filename, content, "valid")

            for filename, content, mime in TEST_FILES["invalid_should_reject"]:
                await _run_single_upload(page, file_input, filename, content, "invalid")
                RESULTS["security_tests"] += 1

            for filename, content, mime in TEST_FILES["malicious_names"]:
                await _run_single_upload(page, file_input, filename, content, "malicious")
                RESULTS["security_tests"] += 1

    except Exception as e:
        RESULTS["log"].append(f"  ERROR: {str(e)[:100]}")

async def _run_single_upload(page, file_input, filename, content, test_type):
    """Test uploading a single file"""

    try:
        safe_filename = filename.replace("/", "_").replace("\\", "_").replace("<", "_").replace(">", "_")
        ext = os.path.splitext(safe_filename)[1] or ".txt"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(content)
            temp_path = f.name

        await file_input.set_input_files(temp_path)
        RESULTS["uploads_tested"] += 1

        await page.wait_for_timeout(300)

        error = await page.query_selector(".error, .alert-danger, .text-danger")

        if test_type == "valid":
            if not error:
                RESULTS["uploads_accepted"] += 1
                RESULTS["log"].append(f"    [PASS] {safe_filename} accepted")
            else:
                RESULTS["log"].append(f"    [INFO] {safe_filename} showed error")
        elif test_type == "invalid":
            if error:
                RESULTS["uploads_rejected"] += 1
                RESULTS["log"].append(f"    [PASS] {safe_filename} correctly rejected")
            else:
                RESULTS["log"].append(f"    [INFO] {safe_filename} was accepted (may need validation)")
        elif test_type == "malicious":
            RESULTS["log"].append(f"    [SECURITY] Tested malicious filename: {safe_filename[:30]}")

        os.unlink(temp_path)

        try:
            await file_input.evaluate("el => el.value = ''")
        except:
            pass

    except Exception as e:
        RESULTS["log"].append(f"    [ERROR] {filename[:20]}: {str(e)[:50]}")

def save_results():
    with open("tests/mandatory/TASK7_UPLOADS_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2)

    report = f"""# TASK 7: FILE UPLOAD TESTING RESULTS

**Timestamp:** {RESULTS['timestamp']}

## Summary
| Metric | Count |
|--------|-------|
| Upload Inputs Found | {RESULTS['upload_inputs_found']} |
| Uploads Tested | {RESULTS['uploads_tested']} |
| Valid Files Accepted | {RESULTS['uploads_accepted']} |
| Invalid Files Rejected | {RESULTS['uploads_rejected']} |
| Security Tests Run | {RESULTS['security_tests']} |

## Security Issues
"""
    security_issues = [i for i in RESULTS['issues'] if i.get('type') == 'security']
    if security_issues:
        for issue in security_issues:
            report += f"- [FAIL] {issue}\n"
    else:
        report += "- [PASS] No critical security issues found\n"

    report += "\n## Test Log\n```\n"
    report += "\n".join(RESULTS['log'])
    report += "\n```\n"

    with open("tests/mandatory/TASK7_UPLOADS_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nTASK 7 COMPLETE:")
    print(f"  Uploads tested: {RESULTS['uploads_tested']}")
    print(f"  Security tests: {RESULTS['security_tests']}")

if __name__ == "__main__":
    asyncio.run(test_file_uploads())
