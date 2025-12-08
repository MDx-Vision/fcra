# FIX CYPRESS TEST SYNTAX ERRORS

---

## THE PROBLEM

9 Cypress test files have syntax errors causing them to fail in GitHub Actions CI:

```
✖  9 of 21 failed (43%)
```

All failures are `SyntaxError: Unexpected token` - extra closing brackets `});`

---

## FILES TO FIX

1. `cypress/e2e/analysis_exhaustive.cy.js` - line 93
2. `cypress/e2e/auth_exhaustive.cy.js` - line 113
3. `cypress/e2e/automation_exhaustive.cy.js` - line 108
4. `cypress/e2e/cases_exhaustive.cy.js` - line 103
5. `cypress/e2e/clients_exhaustive.cy.js` - line 98
6. `cypress/e2e/dashboard_exhaustive.cy.js` - line 188
7. `cypress/e2e/other_exhaustive.cy.js` - line 53 (different issue)
8. `cypress/e2e/settlements_exhaustive.cy.js` - line 98
9. `cypress/e2e/staff_exhaustive.cy.js` - line 98

---

## YOUR TASK

1. Check each file for unbalanced brackets
2. Fix the syntax errors
3. Run eslint to verify
4. Push to git

---

## STEP 1: Check bracket balance in each file

For each file, count opening and closing brackets:

```bash
for file in cypress/e2e/*_exhaustive.cy.js cypress/e2e/other_exhaustive.cy.js; do
  echo "=== $file ==="
  open=$(grep -o '{' "$file" | wc -l)
  close=$(grep -o '}' "$file" | wc -l)
  echo "Opening {: $open, Closing }: $close"
  if [ "$open" -ne "$close" ]; then
    echo "⚠️  UNBALANCED!"
  fi
done
```

---

## STEP 2: Fix each file

### For most files (extra `});` at end):

Look at the last ~10 lines of each file:

```bash
tail -15 cypress/e2e/analysis_exhaustive.cy.js
```

The issue is likely an extra `});` that closes a block that doesn't exist.

**Typical fix:** Remove the extra `});` at the end.

### For other_exhaustive.cy.js (line 53):

This file has a different issue - there's code after `it.skip()`:

```javascript
it.skip('should load /admin/clients - JSON endpoint', () => {});
  cy.url().should('include', 'admin');  // <-- This line is outside the test!
});
```

**Fix:** Either remove the orphan line or move it inside a test.

---

## STEP 3: Verify syntax with eslint

```bash
npx eslint cypress/e2e/analysis_exhaustive.cy.js
npx eslint cypress/e2e/auth_exhaustive.cy.js
npx eslint cypress/e2e/automation_exhaustive.cy.js
npx eslint cypress/e2e/cases_exhaustive.cy.js
npx eslint cypress/e2e/clients_exhaustive.cy.js
npx eslint cypress/e2e/dashboard_exhaustive.cy.js
npx eslint cypress/e2e/other_exhaustive.cy.js
npx eslint cypress/e2e/settlements_exhaustive.cy.js
npx eslint cypress/e2e/staff_exhaustive.cy.js
```

Or all at once:

```bash
npx eslint cypress/e2e/*_exhaustive.cy.js
```

---

## STEP 4: Run Cypress locally to verify

```bash
npx cypress run --spec "cypress/e2e/analysis_exhaustive.cy.js"
```

Or run all:

```bash
npx cypress run
```

---

## STEP 5: Push to git

```bash
git add cypress/e2e/
git commit -m "Fix syntax errors in exhaustive Cypress tests"
git push
```

---

## VERIFICATION

After pushing, GitHub Actions should show:
- All 21 specs passing
- 0 syntax errors

---

## ⚠️ IMPORTANT ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   FIX ALL 9 FILES WITH SYNTAX ERRORS                             ║
║                                                                  ║
║   1. analysis_exhaustive.cy.js                                   ║
║   2. auth_exhaustive.cy.js                                       ║
║   3. automation_exhaustive.cy.js                                 ║
║   4. cases_exhaustive.cy.js                                      ║
║   5. clients_exhaustive.cy.js                                    ║
║   6. dashboard_exhaustive.cy.js                                  ║
║   7. other_exhaustive.cy.js (different issue)                    ║
║   8. settlements_exhaustive.cy.js                                ║
║   9. staff_exhaustive.cy.js                                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**FIX ALL CYPRESS SYNTAX ERRORS AND PUSH TO GIT.**
