# MyFreeScoreNow Selector Fix - CSRF Token Issue

## Problem Identified

**Error:** `"waiting for locator("input") to be visible - 35 × locator resolved to 5 elements. Proceeding with the first one: <input name="_csrf" type="hidden"..."`

**Root Cause:** The login method was using a generic `'input'` selector which matched hidden CSRF tokens before visible login fields.

---

## Changes Made

### 1. Fixed Generic Input Selector (Line 240-246)

**Before:**
```python
await self.page.wait_for_selector('input', timeout=15000)
```

**After:**
```python
# Wait for visible input fields (not hidden CSRF tokens)
try:
    await self.page.wait_for_selector('input[type="email"]:visible, input[type="password"]:visible, input[name="email"]:visible, input[name="username"]:visible', timeout=15000)
except:
    # Fallback to any visible input
    await self.page.wait_for_selector('input:visible', timeout=15000)
```

**Why This Works:**
- `:visible` pseudo-selector excludes hidden inputs like CSRF tokens
- Multiple specific selectors try common login field types
- Fallback ensures compatibility with different page structures

### 2. Updated MyFreeScoreNow Selectors with :visible (Lines 44-53)

**Before:**
```python
'username_selector': 'input[name="email"], #email, input[type="email"]',
'password_selector': 'input[name="password"], #password, input[type="password"]',
'ssn_last4_selector': 'input[name="ssn"], #ssn_last4, #ssn, input[placeholder*="SSN"]',
'login_button_selector': 'button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")',
```

**After:**
```python
'username_selector': 'input[type="email"]:visible, input[name="email"]:visible, #email',
'password_selector': 'input[type="password"]:visible, input[name="password"]:visible, #password',
'ssn_last4_selector': 'input[name="ssn"]:visible, #ssn_last4, #ssn, input[placeholder*="SSN"]:visible',
'login_button_selector': 'button[type="submit"]:visible, button:has-text("Sign In"), button:has-text("Log In")',
```

**Improvements:**
- ✅ `:visible` added to exclude hidden fields
- ✅ Most specific selectors first (type-based)
- ✅ Fallback to ID-based selectors
- ✅ Progressive specificity strategy

---

## Selector Strategy

### Priority Order:
1. **Type + Visible** - Most specific, excludes hidden fields
   - `input[type="email"]:visible`
   - `input[type="password"]:visible`

2. **Name + Visible** - Common form field naming
   - `input[name="email"]:visible`
   - `input[name="password"]:visible`

3. **ID-based** - Traditional selectors (no :visible needed as IDs are unique)
   - `#email`
   - `#password`

4. **Placeholder** - Last resort for SSN fields
   - `input[placeholder*="SSN"]:visible`

---

## How :visible Works in Playwright

Playwright's `:visible` pseudo-selector filters for elements that are:
- ✅ Not `display: none`
- ✅ Not `visibility: hidden`
- ✅ Not `opacity: 0`
- ✅ Not `type="hidden"`
- ✅ Have non-zero dimensions
- ✅ Not covered by other elements

This ensures we only interact with fields the user can actually see.

---

## Testing the Fix

### Run on Replit:
```bash
python3 test_client_125.py
```

### Expected Behavior:

**Before Fix:**
```
❌ waiting for locator("input") to be visible
❌ 5 elements found, using first: <input name="_csrf" type="hidden"...
❌ Login fails because it's trying to type into hidden field
```

**After Fix:**
```
✅ waiting for locator("input[type="email"]:visible, ...")
✅ Finds visible email input field
✅ Fills username successfully
✅ Fills password successfully
✅ Login succeeds
```

---

## Debugging

If login still fails, check:

### 1. Page Structure
View debug screenshot to see actual page:
```bash
ls -lt uploads/credit_reports/login_debug_*.png | head -1
```

### 2. Actual Selectors on Page
Run in browser console:
```javascript
// Check visible inputs
document.querySelectorAll('input:visible')

// Check email input
document.querySelector('input[type="email"]')
document.querySelector('input[name="email"]')

// Check hidden inputs
document.querySelectorAll('input[type="hidden"]')
```

### 3. Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Common Login Page Patterns

MyFreeScoreNow likely uses one of these patterns:

### Pattern 1: Modern React/Vue
```html
<form>
  <input type="hidden" name="_csrf" value="...">
  <input type="email" name="email" placeholder="Email">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Sign In</button>
</form>
```

### Pattern 2: ID-based (Legacy)
```html
<form>
  <input type="hidden" name="_csrf" value="...">
  <input type="text" id="email" name="email">
  <input type="password" id="password" name="password">
  <button type="submit">Log In</button>
</form>
```

### Pattern 3: Name-based
```html
<form>
  <input type="hidden" name="_csrf" value="...">
  <input name="email" type="email">
  <input name="password" type="password">
  <button>Sign In</button>
</form>
```

Our updated selectors handle all three patterns!

---

## Files Modified

1. **`services/credit_import_automation.py`**
   - Line 240-246: Fixed generic input selector
   - Lines 46-49: Updated MyFreeScoreNow config with :visible

---

## Verification

Test the changes locally:

```python
from services.credit_import_automation import SERVICE_CONFIGS

config = SERVICE_CONFIGS['MyFreeScoreNow.com']

print("Username selector:", config['username_selector'])
print("Password selector:", config['password_selector'])
print()

# Verify :visible is in selectors
for key, value in config.items():
    if '_selector' in key and ':visible' in value:
        print(f"✅ {key} has :visible pseudo-selector")
```

Expected output:
```
Username selector: input[type="email"]:visible, input[name="email"]:visible, #email
Password selector: input[type="password"]:visible, input[name="password"]:visible, #password

✅ username_selector has :visible pseudo-selector
✅ password_selector has :visible pseudo-selector
✅ ssn_last4_selector has :visible pseudo-selector
✅ login_button_selector has :visible pseudo-selector
```

---

## Next Steps

1. ✅ Changes committed
2. 🔄 Pull on Replit: `git pull origin main`
3. 🧪 Test: `python3 test_client_125.py`
4. ✅ Should now successfully login and extract report
5. 🚀 Retry other 6 failed clients if successful

---

## Success Criteria

After this fix, the test should:
- ✅ Find visible email input (not CSRF token)
- ✅ Successfully fill username
- ✅ Successfully fill password
- ✅ Click login button
- ✅ Navigate to credit report page
- ✅ Extract scores and accounts
- ✅ Save HTML report

**Status:** Ready for Replit testing
**Confidence Level:** High - This directly addresses the CSRF token issue
