#!/usr/bin/env bash
# Script to fix translations for 'krwinkowy system prezentowy'

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Run the fix_translation.py script inside the Docker container
echo "Fixing translations to preserve 'krwinkowy system prezentowy'..."
docker compose exec web python scripts/fix_translation.py

# Compile messages
echo "Compiling translation messages..."
docker compose exec web uv run manage.py compilemessages

echo "Translation fix completed."
echo "The phrase 'krwinkowy system prezentowy' will now be preserved in all translations."
