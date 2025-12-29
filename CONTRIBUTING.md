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

- **Unit Tests** - 167+ pytest tests
- **Cypress E2E Tests** - 88 end-to-end tests
- **Lint** - flake8 code style check

## Running Tests Locally

```bash
# Unit tests
python -m pytest tests/ -v --tb=short

# Cypress tests
npm test

# Lint
flake8 app.py services/ --max-line-length=150
```

## Code Review

- All PRs should be reviewed before merging
- Address review comments before merging
- Keep PRs focused and reasonably sized
