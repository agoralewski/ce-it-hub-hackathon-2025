#!/bin/bash
# Script to check the site domain configuration for password reset links

echo "Checking site domain configuration for password reset links..."

# Determine if we're running in Docker or locally
if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    echo "Docker Compose detected, running with Docker..."
    docker compose exec web uv run manage.py shell -c "
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import os

# Get the current site
site = Site.objects.get_current()
print(f'Current site domain: {site.domain}')
print(f'Current site name: {site.name}')

# Get a test user
User = get_user_model()
users = User.objects.filter(is_active=True)

if not users.exists():
    print('Error: No active users found in the database.')
    exit(1)

# Use the first active user for testing
user = users.first()

# Generate a password reset URL for this user
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = default_token_generator.make_token(user)
reset_url = f'http://{site.domain}/accounts/reset/{uid}/{token}/'

print(f'\nPassword reset URL would be:')
print(reset_url)

# Check if the domain looks valid
if site.domain == 'example.com':
    print('\nWARNING: Your site domain is still set to the default \"example.com\".')
    print('This should be changed to your actual domain.')
    exit(1)
elif site.domain == 'localhost' or site.domain.startswith('127.0.0.1'):
    print('\nNote: Your site domain is set to a localhost address.')
    print('This is fine for development but should be changed to your actual domain for production.')

# Check if domain matches SITE_DOMAIN in .env
try:
    env_domain = os.environ.get('SITE_DOMAIN')
    if env_domain and env_domain != site.domain:
        print(f'\nWARNING: Your SITE_DOMAIN in .env ({env_domain}) does not match the current site domain ({site.domain}).')
        print('You may need to run the update_site command to synchronize them.')
        exit(1)
except Exception:
    print('\nNote: Could not check SITE_DOMAIN in environment, skipping .env check.')

print('\nYour site domain appears to be properly configured.')
exit(0)
"
else
    # Running locally
    echo "Running locally..."
    uv run manage.py shell -c "
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import os

# Get the current site
site = Site.objects.get_current()
print(f'Current site domain: {site.domain}')
print(f'Current site name: {site.name}')

# Get a test user
User = get_user_model()
users = User.objects.filter(is_active=True)

if not users.exists():
    print('Error: No active users found in the database.')
    exit(1)

# Use the first active user for testing
user = users.first()

# Generate a password reset URL for this user
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = default_token_generator.make_token(user)
reset_url = f'http://{site.domain}/accounts/reset/{uid}/{token}/'

print(f'\nPassword reset URL would be:')
print(reset_url)

# Check if the domain looks valid
if site.domain == 'example.com':
    print('\nWARNING: Your site domain is still set to the default \"example.com\".')
    print('This should be changed to your actual domain.')
    exit(1)
elif site.domain == 'localhost' or site.domain.startswith('127.0.0.1'):
    print('\nNote: Your site domain is set to a localhost address.')
    print('This is fine for development but should be changed to your actual domain for production.')

# Check if domain matches SITE_DOMAIN in .env
try:
    env_domain = os.environ.get('SITE_DOMAIN')
    if env_domain and env_domain != site.domain:
        print(f'\nWARNING: Your SITE_DOMAIN in .env ({env_domain}) does not match the current site domain ({site.domain}).')
        print('You may need to run the update_site command to synchronize them.')
        exit(1)
except Exception:
    print('\nNote: Could not check SITE_DOMAIN in environment, skipping .env check.')

print('\nYour site domain appears to be properly configured.')
exit(0)
"
fi

# Check if the script found issues
if [ $? -ne 0 ]; then
    echo ""
    echo "Issues were found with your domain configuration."
    echo "You can update your domain using:"
    echo "./scripts/update_site_domain.sh your-domain.com"
else
    echo ""
    echo "Domain configuration check completed successfully."
fi
