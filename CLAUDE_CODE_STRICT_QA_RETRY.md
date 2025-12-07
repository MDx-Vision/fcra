# STRICT QA - HIT EXACT TARGETS OR EXPLAIN WHY

---

## ⚠️ PREVIOUS RUN FAILED - YOU MUST DO BETTER ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   LAST RUN RESULTS (UNACCEPTABLE):                               ║
║                                                                  ║
║   Task 1: Target 50 forms → Only tested 33 (FAILED)              ║
║   Task 2: Target 1,584 buttons → Only clicked 66 (FAILED)        ║
║   Task 5: Target 323 links → Only tested 107 (FAILED)            ║
║                                                                  ║
║   THIS TIME YOU MUST:                                            ║
║   - Hit the EXACT targets                                        ║
║   - If target impossible, explain EXACTLY why                    ║
║   - No "skipping" buttons - click them ALL                       ║
║   - No "found 0 modals" - FIND them or prove none exist          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## TASK 1: TEST ALL 50 FORMS (YOU ONLY DID 33)

**Target: 50 forms**
**You tested: 33 forms**
**Missing: 17 forms**

### Step 1: Find ALL 50 forms

The inventory file shows 50 forms. Find them:

```bash
cat tests/exhaustive/all_forms.txt | head -60
```

### Step 2: List every form you're testing

Before testing, output the full list:

```bash
echo "=== ALL 50 FORMS TO TEST ===" > tests/mandatory/FORMS_CHECKLIST.txt
grep -rn "<form" templates/ >> tests/mandatory/FORMS_CHECKLIST.txt
cat tests/mandatory/FORMS_CHECKLIST.txt | wc -l
```

### Step 3: For each form, you MUST:

1. Navigate to the page containing it
2. If form is in a modal, CLICK the button to open the modal FIRST
3. Find ALL input fields in that form
4. Test each field with ALL 37 edge cases
5. Log: "Form X: Y fields, Z edge cases tested"

### Step 4: If a form is unreachable, document WHY:

```
Form: #addClientModal
Location: /dashboard/clients
Status: UNREACHABLE
Reason: Modal trigger button not found
Attempted: Searched for [data-bs-toggle], [data-target], onclick
```

### Step 5: Final count MUST be 50 or explain each missing form

---

## TASK 2: CLICK ALL 1,584 BUTTONS (YOU ONLY DID 66)

**Target: 1,584 buttons**
**You clicked: 66 buttons**
**You skipped: 95 as "dangerous"**
**Missing: 1,423 buttons**

### THE PROBLEM:

You found 867 buttons but only clicked 66. That's 7.6%. UNACCEPTABLE.

### NEW RULES:

1. **DO NOT skip "dangerous" buttons** - click them in a SAFE way:
   - For "delete" buttons: Click, then click "Cancel" in confirmation dialog
   - For "logout" buttons: Click, then log back in
   - For "remove" buttons: Same as delete

2. **If page navigates away, GO BACK and continue**

3. **Count EVERY click** - log each one

### Step 1: Get accurate button count

```bash
cat tests/exhaustive/all_buttons.txt | wc -l
```

If this shows 1,584 buttons, you must click 1,584 buttons.

### Step 2: Updated button click script

```python
# DO NOT SKIP ANY BUTTONS
# Click "dangerous" buttons but handle the confirmation

async def click_button_safely(page, button, button_text):
    """Click any button, handle confirmations"""
    
    await button.click()
    await page.wait_for_timeout(300)
    
    # Check for confirmation dialog
    confirm_dialog = await page.query_selector(
        ".modal.show, "
        "[role='dialog'], "
        ".confirm, "
        ".swal2-popup, "
        "[class*='confirm']"
    )
    
    if confirm_dialog:
        # Click Cancel/No/Close to abort the action
        cancel = await confirm_dialog.query_selector(
            "button:has-text('Cancel'), "
            "button:has-text('No'), "
            "button:has-text('Close'), "
            ".btn-secondary, "
            "[data-dismiss], "
            "[data-bs-dismiss]"
        )
        if cancel:
            await cancel.click()
            await page.wait_for_timeout(200)
        else:
            # Press Escape to close
            await page.keyboard.press("Escape")
    
    # Check if page navigated
    # If so, go back
    
    return True  # Button was clicked
```

### Step 3: Verify final count

Your report MUST show:
```
Buttons Found: 1,584
Buttons Clicked: 1,584
Buttons Skipped: 0
```

Or explain EXACTLY why each unclicked button couldn't be clicked.

---

## TASK 3: FIND THE MODALS (YOU SAID 0 EXIST)

**You claimed: 0 modals found**
**Reality check needed**

### Step 1: Search for modals in templates

```bash
grep -rn "modal" templates/ | wc -l
grep -rn "Modal" templates/ | wc -l
grep -rn "data-bs-toggle" templates/ | wc -l
grep -rn "data-toggle" templates/ | wc -l
```

### Step 2: If truly 0 modals, PROVE IT

Create a file listing every search you did:

```
tests/mandatory/MODAL_PROOF.md

# Modal Search Results

## Search 1: "modal" in templates
Command: grep -rn "modal" templates/
Results: [paste output]

## Search 2: data-bs-toggle
Command: grep -rn "data-bs-toggle" templates/
Results: [paste output]

## Search 3: Bootstrap modal classes
Command: grep -rn "class.*modal" templates/
Results: [paste output]

## Conclusion
The application uses [inline forms / other pattern] instead of modals.
Evidence: [specific file and line numbers]
```

---

## TASK 4: FIX THE FAILED FLOW (5/6 IS NOT 6/6)

**Staff Login flow failed with timeout**

### Step 1: Debug the issue

```python
# Add explicit waits and retries
async def test_staff_login(page):
    await page.goto(f"{BASE_URL}/staff/login", wait_until="networkidle")
    
    # Wait for form to be visible
    await page.wait_for_selector("form", state="visible", timeout=10000)
    
    # Try multiple selectors for email field
    email_selectors = [
        "#email",
        "[name='email']",
        "input[type='email']",
        "input[type='text']",
        "form input:first-of-type"
    ]
    
    email_field = None
    for selector in email_selectors:
        try:
            email_field = await page.wait_for_selector(selector, state="visible", timeout=3000)
            if email_field:
                break
        except:
            continue
    
    if not email_field:
        # Take screenshot to debug
        await page.screenshot(path="tests/mandatory/staff_login_debug.png")
        raise Exception("Could not find email field")
    
    await email_field.fill("admin@test.com")
    # ... continue
```

### Step 2: Re-run until 6/6 passes

---

## TASK 5: TEST ALL 323 LINKS (YOU ONLY DID 107)

**Target: 323 links**
**You tested: 107 links**
**Missing: 216 links**

### THE PROBLEM:

The inventory shows 323 links. You only tested 107.

### Step 1: Verify the actual count

```bash
cat tests/exhaustive/all_links.txt | wc -l
```

### Step 2: Test EVERY link, not just unique ones

Your script deduplicated links. DON'T DO THAT for the count - test every occurrence.

### Step 3: Visit EVERY page and test EVERY link on it

```python
# Test every link on every page, including duplicates
all_links_tested = 0

for url in ALL_PAGES:
    await page.goto(url)
    links = await page.query_selector_all("a[href]")
    
    for link in links:
        href = await link.get_attribute("href")
        # Test it
        all_links_tested += 1
        # Log it

print(f"Total links tested: {all_links_tested}")
# This MUST equal or exceed 323
```

---

## TASK 7: FIX FILE UPLOAD SECURITY

**Issue found: Server accepts .exe, .php files**

### Step 1: Add server-side validation

Find the upload handler in app.py and add:

```python
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt', 'csv'}
BLOCKED_EXTENSIONS = {'exe', 'php', 'sh', 'bat', 'cmd', 'ps1', 'js', 'vbs', 'py'}

def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in BLOCKED_EXTENSIONS:
        return False
    return ext in ALLOWED_EXTENSIONS
```

### Step 2: Re-test uploads

After fixing, re-run upload tests to verify .exe and .php are rejected.

---

## FIX BROKEN LINK

**Issue: /login returns 404**

### Step 1: Find where /login is linked

```bash
grep -rn '"/login"' templates/
grep -rn "'/login'" templates/
```

### Step 2: Either:
- Create the /login route (redirect to /staff/login)
- OR change the link to point to /staff/login

---

## FINAL REQUIREMENTS

Your MANDATORY_FINAL_REPORT.md must show:

```
| Task | Target | Actual | Status |
|------|--------|--------|--------|
| 1. Forms | 50 | 50 | PASS |
| 2. Buttons | 1,584 | 1,584 | PASS |
| 3. Modals | All | [X or N/A with proof] | PASS |
| 4. Flows | 6/6 | 6/6 | PASS |
| 5. Links | 323 | 323 | PASS |
| 6. Credit | 5/5 | 5/5 | PASS |
| 7. Uploads | Secure | Secure (fixed) | PASS |
| 8. Browsers | 3/3 | 3/3 | PASS |
```

If ANY target is not met, you must include:
- Exact reason why
- What you tried
- Evidence (screenshots, logs, search results)

---

## ⚠️ EXECUTION RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. DO NOT SKIP BUTTONS - click them all, handle confirmations  ║
║   2. DO NOT DEDUPLICATE - test every occurrence                  ║
║   3. DO NOT GIVE UP - retry with different selectors             ║
║   4. DO NOT ACCEPT PARTIAL - 100% or explain why impossible      ║
║   5. FIX ISSUES AS YOU FIND THEM                                 ║
║   6. TAKE SCREENSHOTS when things fail                           ║
║   7. PROVE modals don't exist if claiming 0                      ║
║                                                                  ║
║   NO QUESTIONS. NO EXCUSES. HIT THE TARGETS.                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**THIS IS YOUR SECOND CHANCE. DO NOT FAIL AGAIN.**

**START NOW. HIT EVERY TARGET. REPORT WHEN 100% COMPLETE.**
