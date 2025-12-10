# Autonomous Test Generation System

## Overview

This system automatically generates Cypress tests for Flask routes using Claude API.

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `detect-new-routes.js` | Find routes without tests | `npm run detect-routes` |
| `generate-test.js` | Generate test for one route | `npm run generate-test /dashboard/feature` |
| `auto-fix-tests.js` | Fix failing tests with AI | `npm run auto-fix cypress/e2e/file.cy.js` |
| `generate-all-missing.js` | Generate all missing tests | `npm run generate-all` |

## How It Works

1. **Detection**: Scans `app.py` for `@app.route` decorators
2. **Comparison**: Checks which routes have Cypress tests
3. **Generation**: Creates test files using Claude API
4. **Auto-fix**: If tests fail, Claude analyzes and fixes them
5. **PR Creation**: GitHub Action creates PR for review

## Auth Handling

| Route Pattern | Auth Type | Login Method |
|---------------|-----------|--------------|
| `/dashboard/*` | Staff | cy.login() with staff credentials |
| `/portal/*` | Client | Client portal login flow |
| Everything else | Public | None |

## Environment Variables

- `CLAUDE_API_KEY` - Required for test generation and auto-fix

Set it up:
```bash
export CLAUDE_API_KEY="your-api-key-here"
```

Or add to your shell profile (~/.zshrc or ~/.bashrc):
```bash
echo 'export CLAUDE_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

## Manual Usage

### Check Test Coverage
```bash
npm run detect-routes
```

Output shows:
- Total HTML routes
- Routes with tests
- Routes missing tests (grouped by auth type)

### Generate Test for Specific Route
```bash
npm run generate-test /dashboard/new-feature

# Override auth type if needed
npm run generate-test /dashboard/feature --auth staff
```

### Generate All Missing Tests (Limited)
```bash
# Dry run to see what would be generated
node scripts/generate-all-missing.js --dry-run

# Generate tests for first 5 routes
node scripts/generate-all-missing.js --limit 5

# Generate all (use with caution!)
npm run generate-all
```

### Fix a Failing Test
```bash
npm run auto-fix cypress/e2e/my_test.cy.js

# Custom max attempts
node scripts/auto-fix-tests.js cypress/e2e/my_test.cy.js --max-attempts 3
```

## GitHub Action

**Automatic Trigger**: Runs when `app.py` changes on main branch

**Manual Trigger**:
1. Go to Actions → Auto Test Generation
2. Click "Run workflow"
3. Optionally specify a route to generate test for
4. Action creates a PR with generated tests

## Test Generation Process

### 1. Detection Phase
```
🔍 Detecting routes without test coverage...

📊 Summary:
   Total HTML routes: 75
   Routes with tests: 8
   Routes missing tests: 67
```

### 2. Generation Phase
For each route:
1. Analyzes route pattern (`/dashboard/clients`, `/portal/dashboard`, etc.)
2. Determines auth requirements
3. Creates base test template with:
   - Page load tests
   - UI element tests
   - Responsive design tests
4. Calls Claude API to generate feature-specific tests based on route context
5. Runs generated test to verify it works

### 3. Auto-Fix Phase (if needed)
If tests fail:
1. Extracts failure messages
2. Sends test code + errors to Claude API
3. Claude analyzes and fixes issues
4. Writes fixed test
5. Re-runs test (up to 5 attempts)

## Generated Test Structure

```javascript
// Auto-generated test for /dashboard/feature
// Generated: 2025-12-10T...
// Auth: staff

describe('Feature - Full QA Suite', () => {
  beforeEach(() => {
    // Auth setup (staff/client/public)
    cy.login('test@example.com', 'password123');
  });

  describe('Page Load', () => {
    it('should load /dashboard/feature successfully', () => { ... });
    it('should not display errors', () => { ... });
  });

  describe('UI Elements', () => {
    it('should have navigation', () => { ... });
    it('should have main content', () => { ... });
  });

  describe('Responsive Design', () => {
    it('should display on desktop', () => { ... });
    it('should display on tablet', () => { ... });
    it('should display on mobile', () => { ... });
  });

  // CLAUDE_GENERATED_TESTS_START
  describe('Feature-Specific Tests', () => {
    // Claude generates these based on route context
    it('should display client table', () => { ... });
    it('should filter clients', () => { ... });
    // ...
  });
  // CLAUDE_GENERATED_TESTS_END
});
```

## Common Issues

### CLAUDE_API_KEY not set
```
❌ CLAUDE_API_KEY environment variable not set
```
**Fix**: Set the API key in your environment (see Environment Variables section)

### Test Generation Fails
```
⚠️  Some tests failed - you can use auto-fix-tests.js to fix them
```
**Fix**: Run `npm run auto-fix cypress/e2e/generated_test.cy.js`

### Route Already Has Test
If detection shows a route is "missing" but you know it's tested:
- Add `// Tests: /dashboard/route` comment to existing test file
- Or ensure test file has `cy.visit('/dashboard/route')`

### Generated Test Too Generic
Claude generates based on route patterns. For complex features:
1. Let it generate the base structure
2. Manually add specific test cases
3. Commit both generated + manual tests

## Best Practices

1. **Review Generated Tests**: Always review PRs from the GitHub Action before merging
2. **Start Small**: Use `--limit 5` when generating multiple tests
3. **Iterative Approach**: Generate tests for one feature area at a time
4. **Manual Enhancement**: Use generated tests as starting point, enhance manually
5. **Keep API Key Secure**: Never commit CLAUDE_API_KEY to git

## File Output

Generated test files are named using this pattern:
```
/dashboard/credit-tracker  →  credit_tracker_autogen.cy.js
/portal/messages           →  messages_autogen.cy.js
/signup/success            →  success_autogen.cy.js
```

## Maintenance

### Update Route Detection
Edit `scripts/detect-new-routes.js`:
- `ignorePatterns`: Add routes to ignore
- `authPatterns`: Adjust auth detection rules

### Update Test Templates
Edit `scripts/generate-test.js`:
- `generateBaseTemplate()`: Modify base test structure
- `analyzePageAndGenerateTests()`: Update Claude prompt

### Update Auto-Fix Logic
Edit `scripts/auto-fix-tests.js`:
- `fixTest()`: Modify Claude prompt for fixing
- `maxAttempts`: Change default retry limit

## Statistics

As of December 10, 2025:
- **Total Routes**: 570 in app.py
- **HTML Routes**: 75 (after filtering APIs, webhooks, etc.)
- **Current Coverage**: 8 routes tested
- **Missing Tests**: 67 routes

Run `npm run detect-routes` for current stats.

## Support

For issues or questions:
1. Check this README
2. Review generated test output and errors
3. Try auto-fix: `npm run auto-fix <test-file>`
4. Check Claude API status
5. Review journal.txt for similar past issues

## Future Enhancements

Potential improvements:
- [ ] Visual regression testing integration
- [ ] Automatic test naming based on feature description
- [ ] Test coverage reports with gaps highlighted
- [ ] Integration with E2E test results to prioritize untested critical paths
- [ ] Smart test grouping to avoid duplicate coverage
