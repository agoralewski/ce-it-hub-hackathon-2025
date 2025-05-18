#!/bin/bash
# Script to run Django DB migration and create a superuser interactively

echo "Would you like to perform database migration and create a superuser now? (y/n)"
read dbsetup
if [[ "$dbsetup" =~ ^[Yy]$ ]]; then
    echo "Running database migration and superuser creation..."
    docker compose exec web uv run manage.py migrate
    docker compose exec web uv run manage.py createsuperuser
    echo "Database migration and superuser creation complete."
else
    echo "You can run migrations and create a superuser later with:"
    echo "docker compose exec web uv run manage.py migrate"
    echo "docker compose exec web uv run manage.py createsuperuser"
fi
