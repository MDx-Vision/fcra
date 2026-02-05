# SINGLE TASK: FIX 2 CRITICAL BUGS

---

## ⚠️ THESE MUST BE FIXED BEFORE LAUNCH ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   BUG 1: Client Signup Wizard - Step 2 not advancing             ║
║   BUG 2: White-Label Page - HTTP 500 error                       ║
║                                                                  ║
║   BOTH MUST BE FIXED. DO NOT STOP UNTIL BOTH WORK.               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## BUG 1: CLIENT SIGNUP WIZARD

### The Problem
- Location: `/signup`
- Step 1 fills all fields correctly
- Step 2 radio button selection and "Next" button don't advance to Step 3
- This blocks new client signups

### Step 1: Find the signup wizard code

```bash
cat templates/client_signup.html | head -200
```

### Step 2: Look for the step navigation JavaScript

```bash
grep -n "step\|next\|wizard\|goToStep\|nextStep" templates/client_signup.html
```

### Step 3: Debug the issue

Common causes:
1. JavaScript error preventing navigation
2. Form validation blocking advancement
3. Missing onclick handler on Next button
4. Step 2 radio buttons not properly wired

### Step 4: Test manually in browser

```bash
# Start the app if not running
CI=true python app.py &
sleep 3

# Open in browser and check console for JS errors
echo "Open http://localhost:5001/signup in browser"
echo "Fill Step 1, click Next, check browser console for errors"
```

### Step 5: Fix the issue

Look for code like this:
```javascript
function nextStep(currentStep) {
    // Validate current step
    if (!validateStep(currentStep)) return;  // <-- Is this failing?

    // Hide current, show next
    document.getElementById('step' + currentStep).style.display = 'none';
    document.getElementById('step' + (currentStep + 1)).style.display = 'block';
}
```

Common fixes:
- Add missing validation for Step 2 inputs
- Fix radio button name/value attributes
- Add onclick handler if missing
- Check if form elements have correct IDs

### Step 6: Verify the fix

```python
# Quick test script
import asyncio
from playwright.async_api import async_playwright

async def test_signup_wizard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # See what happens
        page = await browser.new_page()

        await page.goto("http://localhost:5001/signup")

        # Step 1 - Fill personal info
        await page.fill("#firstName", "Test")
        await page.fill("#lastName", "User")
        await page.fill("#email", "test@example.com")
        await page.fill("#phone", "5551234567")

        # Click Next
        next_btn = await page.query_selector("button:has-text('Next')")
        await next_btn.click()
        await page.wait_for_timeout(1000)

        # Verify Step 2 is showing
        step2 = await page.query_selector("#step2, [data-step='2'], .step-2")
        if step2 and await step2.is_visible():
            print("✅ Step 2 visible")
        else:
            print("❌ Step 2 NOT visible")

        # Step 2 - Select plan (radio button)
        plan_radio = await page.query_selector("input[type='radio'][name='plan']")
        if plan_radio:
            await plan_radio.click()
            print("✅ Plan selected")

        # Click Next again
        next_btn2 = await page.query_selector("button:has-text('Next'):visible")
        if next_btn2:
            await next_btn2.click()
            await page.wait_for_timeout(1000)

        # Verify Step 3 is showing
        step3 = await page.query_selector("#step3, [data-step='3'], .step-3")
        if step3 and await step3.is_visible():
            print("✅ Step 3 visible - WIZARD WORKS!")
        else:
            print("❌ Step 3 NOT visible - STILL BROKEN")

        await browser.close()

asyncio.run(test_signup_wizard())
```

---

## BUG 2: WHITE-LABEL PAGE HTTP 500 ERROR

### The Problem
- Location: `/dashboard/white-label`
- Page returns HTTP 500 (server error)
- This blocks the entire white-label feature

### Step 1: Check the server logs

```bash
# Look at recent errors
tail -100 /tmp/app.log 2>/dev/null || echo "Check server output for errors"
```

### Step 2: Find the route handler

```bash
grep -n "white-label\|white_label\|whitelabel" app.py | head -20
```

### Step 3: Test the route directly

```bash
curl -v http://localhost:5001/dashboard/white-label 2>&1 | head -50
```

### Step 4: Common causes of 500 errors

1. **Database query error** - Table doesn't exist or wrong column name
2. **Missing import** - Python module not imported
3. **Null reference** - Accessing property of None
4. **Template error** - Variable not passed to template

### Step 5: Add error handling to find the issue

Find the route in app.py and add try/except:

```python
@app.route('/dashboard/white-label')
def white_label_dashboard():
    try:
        # existing code...
        tenants = Tenant.query.all()  # <-- might fail here
        return render_template('white_label_dashboard.html', tenants=tenants)
    except Exception as e:
        print(f"WHITE-LABEL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {e}", 500
```

### Step 6: Check if database table exists

```bash
# Connect to database and check
psql $DATABASE_URL -c "\dt" | grep -i tenant
psql $DATABASE_URL -c "\dt" | grep -i white
```

### Step 7: Common fixes

**If table missing:**
```python
# Add to app.py or run in flask shell
db.create_all()
```

**If column missing:**
```python
# Check model matches database
class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    # ... check all columns exist in DB
```

**If template variable missing:**
```python
# Make sure all variables are passed
return render_template('white_label_dashboard.html',
    tenants=tenants,
    current_user=current_user,  # <-- might be missing
    stats=stats  # <-- might be missing
)
```

### Step 8: Verify the fix

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/dashboard/white-label
# Should return 200, not 500
```

---

## VERIFICATION

After fixing both bugs, run these tests:

### Test 1: Signup Wizard

```bash
python3 << 'EOF'
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://localhost:5001/signup")

        # Fill Step 1
        await page.fill("#firstName", "Test")
        await page.fill("#lastName", "User")
        await page.fill("#email", "test123@example.com")
        await page.fill("#phone", "5551234567")
        await page.fill("#addressStreet", "123 Test St")
        await page.fill("#addressCity", "Test City")
        await page.fill("#addressZip", "90210")

        # Click Next
        await page.click("button:has-text('Next')")
        await page.wait_for_timeout(500)

        # Check if we advanced
        url = page.url
        content = await page.content()

        if "step2" in content.lower() or "step 2" in content.lower() or "plan" in content.lower():
            print("✅ BUG 1 FIXED: Signup wizard advances to Step 2")
        else:
            print("❌ BUG 1 NOT FIXED: Still stuck on Step 1")

        await browser.close()

asyncio.run(test())
EOF
```

### Test 2: White-Label Page

```bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/dashboard/white-label)
if [ "$STATUS" = "200" ]; then
    echo "✅ BUG 2 FIXED: White-label page returns 200"
else
    echo "❌ BUG 2 NOT FIXED: White-label page returns $STATUS"
fi
```

---

## FINAL REPORT

After fixing, create `tests/mandatory/CRITICAL_BUGS_FIXED.md`:

```markdown
# Critical Bugs - Fix Report

**Date:** [date]

## Bug 1: Client Signup Wizard

**Problem:** Step 2 navigation not advancing
**Root Cause:** [describe what you found]
**Fix:** [describe what you changed]
**File(s) Modified:** [list files]
**Status:** ✅ FIXED / ❌ NOT FIXED

## Bug 2: White-Label Page 500 Error

**Problem:** HTTP 500 error on page load
**Root Cause:** [describe what you found]
**Fix:** [describe what you changed]
**File(s) Modified:** [list files]
**Status:** ✅ FIXED / ❌ NOT FIXED

## Verification

- Signup wizard test: PASS / FAIL
- White-label page test: PASS / FAIL

## Ready for Launch: YES / NO
```

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Fix BUG 1 (signup wizard) completely                        ║
║   2. Fix BUG 2 (white-label 500) completely                      ║
║   3. Run verification tests                                      ║
║   4. Create the fix report                                       ║
║   5. DO NOT STOP until both bugs are fixed                       ║
║                                                                  ║
║   THESE ARE LAUNCH BLOCKERS.                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**FIX BOTH CRITICAL BUGS NOW.**
