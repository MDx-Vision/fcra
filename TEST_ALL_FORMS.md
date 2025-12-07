# SINGLE TASK: TEST ALL FORMS WITH ALL EDGE CASES

---

## ⚠️ PREVIOUS RUN FAILED ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   LAST RUN: Found 33 forms but tested most with 0 edge cases     ║
║                                                                  ║
║   THIS IS NOT ACCEPTABLE.                                        ║
║                                                                  ║
║   THIS TIME:                                                     ║
║   - Find ALL forms                                               ║
║   - Test EVERY field with ALL 37 edge cases                      ║
║   - If a field gets 0 edge cases, that's a FAILURE               ║
║   - Log every single test                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## YOUR ONE TASK

Test every form field with all 37 edge cases. No shortcuts.

---

## STEP 1: Find all forms in templates

```bash
grep -rn "<form" templates/ > /tmp/all_forms.txt
cat /tmp/all_forms.txt | wc -l
cat /tmp/all_forms.txt
```

Write down the count. This is your target.

---

## STEP 2: The 37 edge cases (MUST test ALL on EVERY text field)

```python
EDGE_CASES = [
    # Empty/Whitespace (5)
    "",                                          # 1. Empty
    " ",                                         # 2. Single space
    "     ",                                     # 3. Only whitespace
    "\t",                                        # 4. Tab only
    "\n",                                        # 5. Newline only
    
    # Length tests (4)
    "a",                                         # 6. Single char
    "ab",                                        # 7. Two chars
    "a" * 100,                                   # 8. 100 chars
    "a" * 1000,                                  # 9. 1000 chars
    
    # XSS attacks (6)
    "<script>alert('xss')</script>",             # 10. Script tag
    "<img src=x onerror=alert('xss')>",          # 11. Img onerror
    "<svg onload=alert('xss')>",                 # 12. SVG onload
    "javascript:alert('xss')",                   # 13. Javascript protocol
    "<iframe src='evil.com'>",                   # 14. Iframe
    "'\"><script>alert('xss')</script>",         # 15. Quote escape + script
    
    # SQL injection (5)
    "'; DROP TABLE users; --",                   # 16. Drop table
    "' OR '1'='1",                               # 17. Always true
    "1; SELECT * FROM users",                    # 18. Select injection
    "' UNION SELECT * FROM staff --",            # 19. Union injection
    "1' AND '1'='1",                             # 20. AND injection
    
    # Template injection (3)
    "{{7*7}}",                                   # 21. Jinja2
    "${7*7}",                                    # 22. Other template
    "#{7*7}",                                    # 23. Ruby style
    
    # Path traversal (2)
    "../../../etc/passwd",                       # 24. Unix path
    "..\\..\\..\\windows\\system32",             # 25. Windows path
    
    # Special encodings (4)
    "%00",                                       # 26. Null byte
    "%0A%0D",                                    # 27. CRLF
    "&#60;script&#62;",                          # 28. HTML entities
    "\x00\x01\x02",                              # 29. Binary chars
    
    # Unicode (3)
    "こんにちは",                                  # 30. Japanese
    "مرحبا",                                      # 31. Arabic
    "🎉🚀💯",                                     # 32. Emojis
    
    # Special characters (5)
    "O'Brien",                                   # 33. Apostrophe
    'Test "Quotes"',                             # 34. Double quotes
    "Test & Ampersand",                          # 35. Ampersand
    "Test < Less > Greater",                     # 36. Angle brackets
    "Test\nNew\tLine",                           # 37. Mixed whitespace
]
```

---

## STEP 3: Create the test script

Create `tests/mandatory/test_forms_thorough.py`:

```python
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

EDGE_CASES = [
    "",
    " ",
    "     ",
    "\t",
    "\n",
    "a",
    "ab",
    "a" * 100,
    "a" * 1000,
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert('xss')>",
    "<svg onload=alert('xss')>",
    "javascript:alert('xss')",
    "<iframe src='evil.com'>",
    "'\"><script>alert('xss')</script>",
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "1; SELECT * FROM users",
    "' UNION SELECT * FROM staff --",
    "1' AND '1'='1",
    "{{7*7}}",
    "${7*7}",
    "#{7*7}",
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32",
    "%00",
    "%0A%0D",
    "&#60;script&#62;",
    "\x00\x01\x02",
    "こんにちは",
    "مرحبا",
    "🎉🚀💯",
    "O'Brien",
    'Test "Quotes"',
    "Test & Ampersand",
    "Test < Less > Greater",
    "Test\nNew\tLine",
]

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "forms_found": 0,
    "forms_tested": 0,
    "fields_found": 0,
    "fields_tested": 0,
    "edge_cases_run": 0,
    "edge_cases_target": 0,
    "issues": [],
    "forms": []
}

async def test_all_forms():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # List of pages known to have forms
        pages_with_forms = [
            "/signup",
            "/staff/login",
            "/portal/login",
            "/dashboard",
            "/dashboard/clients",
            "/dashboard/staff",
            "/dashboard/import",
            "/dashboard/documents",
            "/dashboard/settings",
            "/dashboard/integrations",
            "/dashboard/billing",
            "/dashboard/tasks",
            "/dashboard/workflows",
            "/dashboard/ml-insights",
            "/dashboard/white-label",
            "/dashboard/franchise",
            "/dashboard/affiliates",
            "/dashboard/case-law",
            "/dashboard/knowledge-base",
            "/dashboard/sops",
            "/dashboard/chexsystems",
            "/dashboard/specialty-bureaus",
            "/dashboard/patterns",
            "/dashboard/frivolousness",
            "/dashboard/credit-import",
            "/dashboard/performance",
            "/dashboard/contacts",
            "/dashboard/calendar",
            "/dashboard/settlements",
        ]
        
        for url in pages_with_forms:
            await test_forms_on_page(page, url)
        
        await browser.close()
    
    calculate_totals()
    save_results()

async def test_forms_on_page(page, url):
    """Find all forms on a page and test each one"""
    
    print(f"\n{'='*60}")
    print(f"TESTING PAGE: {url}")
    print(f"{'='*60}")
    
    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)
    except Exception as e:
        print(f"  ERROR loading page: {e}")
        return
    
    # Find all forms
    forms = await page.query_selector_all("form")
    print(f"  Found {len(forms)} forms")
    
    for form_index, form in enumerate(forms):
        form_id = await form.get_attribute("id") or f"form_{form_index}"
        print(f"\n  --- Form: #{form_id} ---")
        
        form_result = {
            "page": url,
            "form_id": form_id,
            "fields": [],
            "total_edge_cases": 0
        }
        
        # Find all input fields in this form
        inputs = await form.query_selector_all(
            "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio']):not([type='file']), "
            "textarea"
        )
        
        print(f"      Found {len(inputs)} testable fields")
        RESULTS["fields_found"] += len(inputs)
        
        for input_index, input_el in enumerate(inputs):
            input_type = await input_el.get_attribute("type") or "text"
            input_name = await input_el.get_attribute("name") or await input_el.get_attribute("id") or f"field_{input_index}"
            
            print(f"      Testing field: {input_name} ({input_type})")
            
            field_result = {
                "name": input_name,
                "type": input_type,
                "edge_cases_tested": 0,
                "errors": []
            }
            
            # Test each edge case
            for case_index, edge_case in enumerate(EDGE_CASES):
                try:
                    # Check if field is still visible and enabled
                    is_visible = await input_el.is_visible()
                    is_enabled = await input_el.is_enabled()
                    
                    if not is_visible or not is_enabled:
                        continue
                    
                    # Clear and fill
                    await input_el.fill("")
                    await input_el.fill(str(edge_case))
                    
                    field_result["edge_cases_tested"] += 1
                    RESULTS["edge_cases_run"] += 1
                    
                except Exception as e:
                    field_result["errors"].append({
                        "case_index": case_index,
                        "error": str(e)[:100]
                    })
            
            print(f"        -> {field_result['edge_cases_tested']}/37 edge cases")
            
            if field_result["edge_cases_tested"] == 0:
                RESULTS["issues"].append({
                    "page": url,
                    "form": form_id,
                    "field": input_name,
                    "issue": "0 edge cases tested - FAILURE"
                })
            
            RESULTS["fields_tested"] += 1
            form_result["fields"].append(field_result)
            form_result["total_edge_cases"] += field_result["edge_cases_tested"]
        
        RESULTS["forms_tested"] += 1
        RESULTS["forms"].append(form_result)
    
    RESULTS["forms_found"] += len(forms)

def calculate_totals():
    RESULTS["edge_cases_target"] = RESULTS["fields_found"] * 37

def save_results():
    # Save JSON
    with open("tests/mandatory/FORMS_THOROUGH_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    
    # Calculate pass/fail
    pass_rate = (RESULTS["edge_cases_run"] / RESULTS["edge_cases_target"] * 100) if RESULTS["edge_cases_target"] > 0 else 0
    
    # Save report
    report = f"""# THOROUGH FORM TESTING RESULTS

**Date:** {RESULTS['timestamp']}
**Status:** {'PASS' if pass_rate >= 90 else 'NEEDS WORK'}

## Summary

| Metric | Count |
|--------|-------|
| Forms Found | {RESULTS['forms_found']} |
| Forms Tested | {RESULTS['forms_tested']} |
| Fields Found | {RESULTS['fields_found']} |
| Fields Tested | {RESULTS['fields_tested']} |
| Edge Cases Target | {RESULTS['edge_cases_target']} |
| Edge Cases Run | {RESULTS['edge_cases_run']} |
| **Pass Rate** | **{pass_rate:.1f}%** |

## Target vs Actual

- Target: {RESULTS['fields_found']} fields × 37 edge cases = {RESULTS['edge_cases_target']}
- Actual: {RESULTS['edge_cases_run']}
- Gap: {RESULTS['edge_cases_target'] - RESULTS['edge_cases_run']}

## Forms Tested

"""
    
    for form in RESULTS['forms']:
        report += f"\n### {form['page']} #{form['form_id']}\n"
        report += f"Edge cases: {form['total_edge_cases']}\n\n"
        report += "| Field | Type | Edge Cases |\n"
        report += "|-------|------|------------|\n"
        for field in form['fields']:
            status = "✅" if field['edge_cases_tested'] >= 30 else "❌"
            report += f"| {field['name']} | {field['type']} | {status} {field['edge_cases_tested']}/37 |\n"
    
    if RESULTS['issues']:
        report += "\n## Issues (Fields with 0 edge cases)\n\n"
        for issue in RESULTS['issues']:
            report += f"- ❌ {issue['page']} #{issue['form']} - {issue['field']}\n"
    
    report += f"""

## Conclusion

{'✅ PASS - All forms thoroughly tested' if pass_rate >= 90 else '❌ NEEDS WORK - Some fields not fully tested'}

Pass rate: {pass_rate:.1f}%
"""
    
    with open("tests/mandatory/FORMS_THOROUGH_REPORT.md", "w") as f:
        f.write(report)
    
    print(f"\n{'='*60}")
    print("FORM TESTING COMPLETE")
    print(f"{'='*60}")
    print(f"Forms: {RESULTS['forms_tested']}/{RESULTS['forms_found']}")
    print(f"Fields: {RESULTS['fields_tested']}/{RESULTS['fields_found']}")
    print(f"Edge Cases: {RESULTS['edge_cases_run']}/{RESULTS['edge_cases_target']} ({pass_rate:.1f}%)")
    print(f"Issues: {len(RESULTS['issues'])}")

if __name__ == "__main__":
    asyncio.run(test_all_forms())
```

---

## STEP 4: Run the tests

```bash
# Make sure app is running
CI=true python app.py &
sleep 5

# Run form tests
python tests/mandatory/test_forms_thorough.py
```

---

## STEP 5: Check results

```bash
cat tests/mandatory/FORMS_THOROUGH_REPORT.md
```

**You must see:**
- Edge cases run close to target (fields × 37)
- No fields with "0 edge cases"
- Pass rate above 90%

---

## STEP 6: If any field has 0 edge cases, debug why

For each failed field:
1. Is the field visible?
2. Is the field enabled?
3. Is it inside a modal that needs to be opened first?
4. Does it have a different selector?

Fix and re-run until pass rate is 90%+.

---

## STEP 7: Create final report

After testing complete, create `tests/mandatory/FORMS_FINAL_STATUS.md`:

```markdown
# Form Testing - Final Status

**Date:** [date]
**Pass Rate:** [X]%

## Summary
- Forms tested: X
- Fields tested: X
- Edge cases run: X

## Any fields NOT tested and WHY:
- [field]: [reason - e.g., "inside modal", "dynamically loaded", etc.]
```

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. EVERY field must get 37 edge cases (or document why not)    ║
║   2. "0 edge cases" is a FAILURE, not a pass                     ║
║   3. If a field is in a modal, OPEN the modal first              ║
║   4. Log every test run                                          ║
║   5. Do not stop until pass rate is 90%+                         ║
║                                                                  ║
║   THIS IS YOUR ONLY TASK.                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**TEST ALL FORMS THOROUGHLY. NO SHORTCUTS.**
