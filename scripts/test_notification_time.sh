#!/bin/bash
# Script to test the configured notification time

echo "Testing expiry notification time configuration..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please run this script from the project root directory."
    exit 1
fi

# Get configured notification time from .env
NOTIFICATION_HOUR=$(grep NOTIFICATION_HOUR .env | cut -d'=' -f2)
NOTIFICATION_MINUTE=$(grep NOTIFICATION_MINUTE .env | cut -d'=' -f2)

# Use default values if not set
if [ -z "$NOTIFICATION_HOUR" ]; then
    NOTIFICATION_HOUR=8
fi

if [ -z "$NOTIFICATION_MINUTE" ]; then
    NOTIFICATION_MINUTE=0
fi

echo "Current notification schedule:"
echo "Time: ${NOTIFICATION_HOUR}:${NOTIFICATION_MINUTE}"

# Check if we're in a Docker environment
if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    echo "Docker Compose detected, running with Docker..."
    docker compose exec web python -c "from django.conf import settings; from ksp.env import get_env_variable; hour = get_env_variable('NOTIFICATION_HOUR', '8'); minute = get_env_variable('NOTIFICATION_MINUTE', '0'); print(f'Django settings confirmed notification time: {hour}:{minute}')"
    # Also run a test expiry check
    docker compose exec web uv run manage.py send_expiry_notifications
else
    python -c "from django.conf import settings; from ksp.env import get_env_variable; hour = get_env_variable('NOTIFICATION_HOUR', '8'); minute = get_env_variable('NOTIFICATION_MINUTE', '0'); print(f'Django settings confirmed notification time: {hour}:{minute}')"
    # Also run a test expiry check
    uv run manage.py send_expiry_notifications
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to run test notification check."
        exit 1
    fi
fi

echo "To change the notification time, modify NOTIFICATION_HOUR and NOTIFICATION_MINUTE in your .env file."
echo "For example, to set notifications to run at 2:30 PM:"
echo "NOTIFICATION_HOUR=14"
echo "NOTIFICATION_MINUTE=30"
