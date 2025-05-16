#!/bin/zsh
# This script removes the obsolete version directive from docker-compose.yaml

echo "Removing obsolete version directive from docker-compose.yaml..."

# Check if the file exists
if [ ! -f "docker-compose.yaml" ]; then
  echo "Error: docker-compose.yaml not found!"
  exit 1
fi

# Create a temporary file
TMP_FILE=$(mktemp)

# Remove the version line and write to temporary file
grep -v "^version:" docker-compose.yaml > "$TMP_FILE"

# Replace the original file
mv "$TMP_FILE" docker-compose.yaml

echo "Done! The 'version' directive has been removed."
echo "This will prevent the warning message when running docker-compose commands."
