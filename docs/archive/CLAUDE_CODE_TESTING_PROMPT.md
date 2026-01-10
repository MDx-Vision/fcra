# Claude Code Exhaustive Testing Prompt

## Your Mission
You are a senior QA engineer. Your job is to exhaustively test every page, button, field, and edge case in this FCRA Litigation Platform, then fix any bugs you find.

## Step 1: Scan the Codebase

First, identify all testable modules by scanning:

```bash
# Find all routes
grep -n "@app.route" app.py | head -100

# Find all templates
ls -la templates/

# Find all API endpoints
grep -n "def api_" app.py | head -50
```

## Step 2: Create Test Checklists

Create a `tests/manual/` directory with one file per module:

```
tests/manual/
├── 00_smoke.md           # Basic app health
├── 01_auth.md            # Login/logout flows
├── 02_dashboard.md       # Main dashboard
├── 03_clients.md         # Client management
├── 04_cases.md           # Case management
├── 05_settlements.md     # Settlement tracking
├── 06_staff.md           # Staff management
├── 07_analytics.md       # Analytics page
├── 08_credit_viewer.md   # Credit report viewer
├── 09_client_portal.md   # Client-facing portal
├── 10_settings.md        # App settings
├── 11_signup.md          # Public signup flow
├── 12_api_endpoints.md   # API endpoint testing
└── RESULTS.md            # Summary of all findings
```

## Step 3: Test Checklist Format

Each test file should follow this format:

```markdown
# [Module Name] - Exhaustive Test Checklist

## Page: [URL]
**Template:** [template_file.html]
**Route:** [Flask route function]

### Load Tests
- [ ] Page loads without errors (HTTP 200)
- [ ] No JavaScript console errors
- [ ] All CSS loads correctly
- [ ] Page renders in < 3 seconds

### UI Elements
- [ ] Header displays correctly
- [ ] Navigation works
- [ ] [Element 1] visible
- [ ] [Element 2] visible
- [ ] [etc...]

### Functionality
- [ ] [Button 1] works - expected: [what should happen]
- [ ] [Form field 1] accepts valid input
- [ ] [Form field 1] rejects invalid input
- [ ] [etc...]

### Edge Cases
- [ ] Empty state displays correctly
- [ ] Handles 100+ records
- [ ] Special characters in input
- [ ] SQL injection attempt blocked
- [ ] XSS attempt blocked

### Mobile Responsive
- [ ] Displays correctly at 375px width
- [ ] Displays correctly at 768px width
- [ ] Touch targets are 44px minimum

### Accessibility
- [ ] All images have alt text
- [ ] Form labels linked to inputs
- [ ] Keyboard navigation works
- [ ] Color contrast passes WCAG AA

## Issues Found
| # | Severity | Description | Status |
|---|----------|-------------|--------|
| 1 | Critical | [description] | Fixed/Open |
```

## Step 4: How to Test

For each checklist item:

1. **Start the app** (if not running):
   ```bash
   python app.py
   ```

2. **Test in browser** - Use the webview or describe what you're checking

3. **Check server logs** - Look for errors in terminal

4. **Check database** - Verify data is saved/retrieved correctly:
   ```bash
   sqlite3 instance/fcra.db "SELECT * FROM [table] LIMIT 5;"
   ```

5. **Test API endpoints** with curl:
   ```bash
   curl -X GET http://localhost:5000/api/[endpoint]
   curl -X POST http://localhost:5000/api/[endpoint] -H "Content-Type: application/json" -d '{"key":"value"}'
   ```

## Step 5: Fix Issues

When you find a bug:

1. Document it in the checklist with severity:
   - **Critical**: App crashes, data loss, security issue
   - **Major**: Feature broken, bad UX
   - **Minor**: Cosmetic, edge case

2. Fix it immediately if possible

3. Mark the fix in the checklist

4. Re-test to confirm fix works

## Step 6: Report Results

After testing all modules, create `tests/manual/RESULTS.md`:

```markdown
# QA Testing Results

**Date:** [date]
**Tester:** Claude Code
**App Version:** [git commit hash]

## Summary
- Total Tests: [X]
- Passed: [X]
- Failed: [X]
- Fixed: [X]
- Remaining Issues: [X]

## Critical Issues
[List any unresolved critical issues]

## Recommendations
[List suggested improvements]

## Module Status
| Module | Tests | Pass | Fail | Status |
|--------|-------|------|------|--------|
| Auth | 25 | 24 | 1 | ⚠️ |
| Dashboard | 40 | 40 | 0 | ✅ |
| [etc...] |

## Ready for Launch?
[ ] Yes - all critical issues resolved
[ ] No - [X] critical issues remaining
```

## Important Notes

1. **Test with real data** - Don't just check if pages load. Create test clients, cases, settlements.

2. **Test as different users** - Admin, attorney, paralegal, client (portal)

3. **Test error handling** - What happens with bad input? Network errors?

4. **Check the database** - Is data actually being saved correctly?

5. **Security checks**:
   - Can you access pages without login?
   - Can you access other users' data?
   - Are passwords hashed?
   - Is sensitive data encrypted?

## Start Command

Begin by creating the test directory and scanning routes:

```bash
mkdir -p tests/manual
grep -n "@app.route" app.py > tests/manual/routes_list.txt
ls templates/ > tests/manual/templates_list.txt
echo "Routes and templates identified. Ready to generate checklists."
```

Then generate the first checklist file and start testing systematically.

---

## Quick Reference: Test Credentials

```
Staff Login: /staff/login
- Email: admin@brightpath.com (or check your database)
- Password: [check with user]

Client Portal: /portal/login
- Use a test client's email
```

## Quick Reference: Key URLs to Test

```
/ - Home page
/staff/login - Staff login
/dashboard - Main dashboard
/dashboard/clients - Client list
/dashboard/clients/[id] - Client detail
/dashboard/cases - Case list
/dashboard/cases/[id] - Case detail
/dashboard/settlements - Settlements
/dashboard/staff - Staff management
/dashboard/analytics - Analytics
/dashboard/credit-imports - Credit report viewer
/settings - Settings
/signup - Public signup
/portal/login - Client portal login
/portal - Client portal dashboard
```
