#!/bin/bash
# Script to run the expiry notification check manually

echo "Running expiry notification check..."

# Check if we're in a Docker environment
if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    echo "Docker Compose detected, running with Docker..."
    docker compose exec web uv run manage.py send_expiry_notifications
else
    uv run manage.py send_expiry_notifications
    if [ $? -ne 0 ]; then
        echo "Error: Failed to run expiry notification check."
        exit 1
    else
        echo "Expiry notification check completed successfully."
    fi
fi