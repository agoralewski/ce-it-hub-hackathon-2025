#!/bin/sh

set -e

# Wait for database to be ready
if [ -n "$DB_HOST" ]; then
    echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
        sleep 2
    done
    echo "PostgreSQL is ready!"
fi

# Apply database migrations
echo "Applying database migrations..."
uv run manage.py migrate

# Start server
echo "Starting server..."
exec uv run manage.py runserver 0.0.0.0:8000
exec uv run manage.py migrate
