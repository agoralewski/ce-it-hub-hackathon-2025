"""
Pytest configuration file for the warehouse application.
"""
import os
import django
from django.conf import settings

# Configure Django settings before running tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksp.settings')
django.setup()