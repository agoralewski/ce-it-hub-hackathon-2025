#!/usr/bin/env bash
# Script to run Django DB migration and create a superuser interactively

# Cross-platform check
OS=$(uname)
if [[ "$OS" == MINGW* || "$OS" == MSYS* || "$OS" == CYGWIN* || "$OS" == "Windows_NT" ]]; then
    echo "[WARNING] This script is intended for Bash-compatible shells. On Windows, use WSL or Git Bash."
fi
docker compose exec web uv run manage.py migrate
docker compose exec web uv run manage.py update_site --domain=$SITE_DOMAIN

# Add fix_translations option
if [ "$1" = "fix_translations" ]; then
    echo "Fixing translations to preserve 'krwinkowy system prezentowy'..."
    ./scripts/fix_ksp_translation.sh
    exit 0
fi

echo "Would you like to create a new superuser now? (y/n)"
read dbsetup
if [ "$dbsetup" = "y" ] || [ "$dbsetup" = "Y" ]; then
    echo "Running database migration and superuser creation..."
    docker compose exec web uv run manage.py createsuperuser
    docker compose exec web uv run manage.py send_expiry_notifications
    echo "Database migration and superuser creation complete."
else
    echo "You can run migrations and create a superuser later with:"
    echo "docker compose exec web uv run manage.py migrate"
    echo "docker compose exec web uv run manage.py createsuperuser"
    echo ""
    echo "To fix translations and prevent 'krwinkowy system prezentowy' from being translated:"
    echo "./scripts/manage_django.sh fix_translations"
fi
