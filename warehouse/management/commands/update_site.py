from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from warehouse.views.utils import get_network_ip
import os
from ksp.env import get_env_variable


class Command(BaseCommand):
    help = 'Updates the site domain and name for password reset emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain to use for the site (default: value from SITE_DOMAIN env var or auto-detect)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Name to use for the site (default: KSP - Krwinkowy System Prezentowy)',
        )

    def handle(self, *args, **options):
        # Get or create the default Site object
        site, created = Site.objects.get_or_create(pk=1)
        
        # Set the site name
        site_name = options.get('name') or 'KSP - Krwinkowy System Prezentowy'
        
        # Get the domain
        domain = options.get('domain')
        if not domain:
            # Check if SITE_DOMAIN is set in the environment
            domain = get_env_variable('SITE_DOMAIN')
            
            if domain:
                self.stdout.write(f"Using domain from SITE_DOMAIN: {domain}")
            else:
                # Try to auto-detect the domain
                ip = get_network_ip()
                if ip:
                    domain = f"{ip}"
                    # Add port 80 if not running on standard HTTP port
                    if 'DJANGO_SETTINGS_MODULE' in os.environ and os.environ.get('DJANGO_SETTINGS_MODULE') == 'ksp.settings.development':
                        domain = f"{ip}:8000"
                else:
                    domain = 'localhost'
                    self.stdout.write(self.style.WARNING('Could not detect network IP, using localhost as domain'))
        
        # Update the site
        site.domain = domain
        site.name = site_name
        site.save()
        
        self.stdout.write(self.style.SUCCESS(f'Site updated: domain="{domain}", name="{site_name}"'))
