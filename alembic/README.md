# Database Migrations

This directory contains Alembic database migrations for the FCRA platform.

## Common Commands

```bash
# Create a new migration (auto-detect changes)
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --indicate-current
```

## Initial Setup

For a new database, apply all migrations:

```bash
alembic upgrade head
```

## Creating Migrations

1. Make changes to models in `database.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add new column to users"
   ```
3. Review the generated migration in `alembic/versions/`
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

## CI/CD Integration

Migrations are applied automatically in CI/CD pipelines via:
```bash
alembic upgrade head
```

## Rollback

If a migration fails:
```bash
# Rollback the last migration
alembic downgrade -1

# Fix the issue and re-apply
alembic upgrade head
```

## Best Practices

1. Always review auto-generated migrations before applying
2. Test migrations on a copy of production data
3. Keep migrations small and focused
4. Never edit a migration that has been applied to production
5. Use meaningful migration names
