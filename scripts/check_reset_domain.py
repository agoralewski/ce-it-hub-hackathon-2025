#!/usr/bin/env python3
"""
Test script for password reset URL domain configuration.
This script checks if the site domain is properly configured for password reset URLs.
"""
import os
import sys
import django

# Set up Django settings before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksp.settings')
django.setup()

# Now we can import Django models safely
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

def check_reset_url():
    """Check if the password reset URL uses the correct domain"""
    # Get the current site
    try:
        site = Site.objects.get_current()
    except Exception as e:
        print(f"Error: Could not get current site: {e}")
        return False
    
    print(f"Current site domain: {site.domain}")
    print(f"Current site name: {site.name}")
    
    # Get a test user
    User = get_user_model()
    users = User.objects.filter(is_active=True)
    
    if not users.exists():
        print("Error: No active users found in the database.")
        return False
    
    # Use the first active user for testing
    user = users.first()
    
    # Generate a password reset URL for this user
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"http://{site.domain}/accounts/reset/{uid}/{token}/"
    
    print(f"\nPassword reset URL would be:")
    print(reset_url)
    
    # Check if the domain looks valid
    if site.domain == 'example.com':
        print("\nWARNING: Your site domain is still set to the default 'example.com'.")
        print("This should be changed to your actual domain.")
        return False
    elif site.domain == 'localhost' or site.domain.startswith('127.0.0.1'):
        print("\nNote: Your site domain is set to a localhost address.")
        print("This is fine for development but should be changed to your actual domain for production.")
    
    # Check if domain matches SITE_DOMAIN in .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        env_domain = os.environ.get('SITE_DOMAIN')
        
        if env_domain and env_domain != site.domain:
            print(f"\nWARNING: Your SITE_DOMAIN in .env ({env_domain}) doesn't match the current site domain ({site.domain}).")
            print("You may need to run the update_site command to synchronize them.")
            return False
    except ImportError:
        print("\nNote: python-dotenv not installed, skipping .env check.")
    
    print("\nYour site domain appears to be properly configured.")
    return True

if __name__ == "__main__":
    print("Checking password reset URL configuration...")
    success = check_reset_url()
    sys.exit(0 if success else 1)
