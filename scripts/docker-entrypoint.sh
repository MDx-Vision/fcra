#!/bin/bash
set -e

echo "=== FCRA Platform Startup ==="

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "from database import engine; engine.connect()" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete!"

# Start the application
echo "Starting application..."
exec "$@"
