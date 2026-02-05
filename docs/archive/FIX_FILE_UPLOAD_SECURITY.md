# SINGLE TASK: FIX FILE UPLOAD SECURITY

---

## ⚠️ CRITICAL SECURITY VULNERABILITY ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   THE PROBLEM:                                                   ║
║                                                                  ║
║   Your app currently ACCEPTS these dangerous files:              ║
║   - .exe (executables)                                           ║
║   - .php (server scripts)                                        ║
║                                                                  ║
║   This was found on:                                             ║
║   - /dashboard/import                                            ║
║   - /dashboard/documents                                         ║
║                                                                  ║
║   THIS IS A CRITICAL SECURITY HOLE.                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## YOUR ONE TASK

**Fix server-side file upload validation to BLOCK dangerous file types.**

---

## STEP 1: Find the upload handlers

```bash
grep -rn "upload\|file\|save.*file\|request.files" app.py | head -50
```

Look for routes that handle file uploads.

---

## STEP 2: Check if ALLOWED_EXTENSIONS exists

```bash
grep -n "ALLOWED_EXTENSIONS\|allowed_file\|BLOCKED_EXTENSIONS" app.py
```

If it exists, check if it's actually being USED in the upload handlers.

---

## STEP 3: Add or fix the validation

### If ALLOWED_EXTENSIONS exists but isn't enforced:

Find each upload handler and add the check:

```python
def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# In EVERY upload route:
@app.route('/some-upload', methods=['POST'])
def handle_upload():
    file = request.files.get('file')
    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        # ... rest of upload logic
```

### If ALLOWED_EXTENSIONS doesn't exist:

Add at the top of app.py (near other config):

```python
# File upload security
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt', 'csv', 'xlsx'}

def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS
```

Then add the check to EVERY upload handler.

---

## STEP 4: Find ALL upload handlers

```bash
grep -n "request.files" app.py
```

For EACH one, ensure `allowed_file()` is called BEFORE saving.

---

## STEP 5: Test the fix

Create a test script:

```python
# tests/mandatory/test_upload_security.py
import requests

BASE = "http://localhost:5001"

# These MUST be rejected
DANGEROUS_FILES = [
    ('test.exe', b'MZ\x90\x00', 'Executable'),
    ('test.php', b'<?php echo "hack"; ?>', 'PHP script'),
    ('test.sh', b'#!/bin/bash\nrm -rf /', 'Shell script'),
    ('test.bat', b'@echo off\ndel *.*', 'Batch file'),
    ('test.js', b'alert("xss")', 'JavaScript'),
    ('test.py', b'import os; os.system("rm -rf /")', 'Python'),
    ('test.html', b'<script>alert("xss")</script>', 'HTML with script'),
]

# These MUST be accepted
SAFE_FILES = [
    ('test.pdf', b'%PDF-1.4', 'PDF'),
    ('test.txt', b'Hello world', 'Text'),
    ('test.csv', b'a,b,c\n1,2,3', 'CSV'),
    ('test.png', b'\x89PNG\r\n\x1a\n', 'PNG image'),
    ('test.jpg', b'\xff\xd8\xff\xe0', 'JPEG image'),
]

def test_upload_endpoint(endpoint):
    print(f"\n=== Testing {endpoint} ===")

    results = {"blocked": 0, "allowed": 0, "errors": []}

    # Test dangerous files - should ALL be rejected
    for filename, content, description in DANGEROUS_FILES:
        try:
            files = {'file': (filename, content)}
            r = requests.post(f"{BASE}{endpoint}", files=files, timeout=10)

            if r.status_code in [400, 403, 415]:
                print(f"  ✅ BLOCKED: {filename} ({description})")
                results["blocked"] += 1
            else:
                print(f"  ❌ ACCEPTED: {filename} ({description}) - STATUS {r.status_code}")
                results["errors"].append(f"{filename} was accepted!")
        except Exception as e:
            print(f"  ⚠️ ERROR testing {filename}: {e}")

    # Test safe files - should ALL be accepted
    for filename, content, description in SAFE_FILES:
        try:
            files = {'file': (filename, content)}
            r = requests.post(f"{BASE}{endpoint}", files=files, timeout=10)

            if r.status_code in [200, 201]:
                print(f"  ✅ ACCEPTED: {filename} ({description})")
                results["allowed"] += 1
            elif r.status_code in [400, 403, 415]:
                print(f"  ⚠️ REJECTED: {filename} ({description}) - may be too strict")
            else:
                print(f"  ⚠️ UNEXPECTED: {filename} - STATUS {r.status_code}")
        except Exception as e:
            print(f"  ⚠️ ERROR testing {filename}: {e}")

    return results

# Test both endpoints
endpoints = [
    '/api/import/file',  # or whatever the actual endpoint is
    '/api/documents/upload',  # or whatever the actual endpoint is
]

# First, find the actual endpoints
print("Finding upload endpoints...")
import subprocess
result = subprocess.run(['grep', '-n', 'request.files', 'app.py'], capture_output=True, text=True)
print(result.stdout)

print("\n" + "="*50)
print("MANUAL TEST REQUIRED")
print("="*50)
print("\nRun these curl commands to test:")
print("""
# Test .exe upload (should be BLOCKED):
curl -X POST -F "file=@test.exe" http://localhost:5001/your-upload-endpoint

# Test .php upload (should be BLOCKED):
curl -X POST -F "file=@test.php" http://localhost:5001/your-upload-endpoint

# Test .pdf upload (should be ALLOWED):
curl -X POST -F "file=@test.pdf" http://localhost:5001/your-upload-endpoint
""")
```

---

## STEP 6: Verify the fix works

After adding validation, test manually:

```bash
# Create test files
echo "MZ" > /tmp/test.exe
echo "<?php echo 'hack'; ?>" > /tmp/test.php
echo "%PDF-1.4 test" > /tmp/test.pdf

# Test uploads (replace with actual endpoint)
curl -X POST -F "file=@/tmp/test.exe" http://localhost:5001/api/upload
# Expected: 400 error "File type not allowed"

curl -X POST -F "file=@/tmp/test.php" http://localhost:5001/api/upload
# Expected: 400 error "File type not allowed"

curl -X POST -F "file=@/tmp/test.pdf" http://localhost:5001/api/upload
# Expected: 200 OK
```

---

## STEP 7: Report results

Create `tests/mandatory/FILE_UPLOAD_SECURITY_FIX.md`:

```markdown
# File Upload Security Fix

**Date:** [date]
**Status:** FIXED

## Changes Made

### File: app.py

Line [X]: Added ALLOWED_EXTENSIONS
Line [Y]: Added allowed_file() function
Line [Z]: Added validation to /upload/endpoint1
Line [W]: Added validation to /upload/endpoint2

## Test Results

| File Type | Before Fix | After Fix |
|-----------|------------|-----------|
| .exe | ❌ Accepted | ✅ Blocked |
| .php | ❌ Accepted | ✅ Blocked |
| .sh | ❌ Accepted | ✅ Blocked |
| .pdf | ✅ Accepted | ✅ Accepted |
| .txt | ✅ Accepted | ✅ Accepted |

## Verification

[Paste curl command outputs here]
```

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. DO NOT move to anything else until this is FIXED            ║
║   2. FIND every upload handler in app.py                         ║
║   3. ADD validation to EVERY one                                 ║
║   4. TEST that .exe and .php are now BLOCKED                     ║
║   5. VERIFY .pdf and .txt still work                             ║
║   6. CREATE the report showing before/after                      ║
║                                                                  ║
║   THIS IS YOUR ONLY TASK. DO NOT STOP UNTIL VERIFIED.            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**FIX THIS SECURITY HOLE NOW.**
