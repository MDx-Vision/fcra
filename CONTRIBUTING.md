# Contributing Guidelines

## Branch Strategy

**Main branch (`main`)** is protected. All changes should go through Pull Requests.

## Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

3. **Push your branch**
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch to `main`
   - Wait for CI checks to pass
   - Request review if needed
   - Merge when approved

## Commit Message Format

Use conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `ci:` - CI/CD changes
- `chore:` - Maintenance tasks

## CI Requirements

All PRs must pass:

- **Unit Tests** - 5,936+ pytest tests (98 test files)
- **Cypress E2E Tests** - 88 end-to-end tests
- **Lint** - flake8 code style check

## Running Tests Locally

```bash
# Unit tests (quick summary)
python -m pytest --tb=short -q

# Unit tests (verbose)
python -m pytest tests/ -v --tb=short

# Run specific test file
python -m pytest tests/test_credit_report_parser.py -v

# Cypress tests
CI=true npx cypress run

# Lint
flake8 app.py services/ --max-line-length=150
```

## Bug Fixes: Always Add Regression Tests

**When fixing any bug, you MUST add a test that would have caught the bug.**

### Pattern:

1. **Fix the bug** in the code
2. **Write a test** that reproduces the bug scenario
3. **Verify test passes** with the fix applied
4. **Verify test FAILS** if you revert the fix (proves test is effective)

### Example:

```python
# Bug: soup.find() returned wrong element
# Fix: Iterate through all elements

def test_extract_personal_info_myfreescorenow_format(self):
    """Test that we find Personal Information, not Credit Scores."""
    html = """
    <h2 class="headline">Credit Scores</h2>  <!-- First -->
    <h2 class="headline">Personal Information</h2>  <!-- Second -->
    """
    parser = CreditReportParser(html)
    info = parser._extract_personal_info()

    # This assertion would FAIL if bug returned
    assert info["name"] is not None, "Should find Personal Information section"
```

### Why This Matters:

- **Prevents regressions**: Bug can never silently return
- **Documents behavior**: Future developers understand requirements
- **CI catches issues**: Pipeline fails before deployment

## Code Review

- All PRs should be reviewed before merging
- Address review comments before merging
- Keep PRs focused and reasonably sized
- **Bug fixes MUST include regression tests**
