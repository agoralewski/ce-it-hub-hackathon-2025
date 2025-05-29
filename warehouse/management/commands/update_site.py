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
            # Always use SITE_DOMAIN from the environment, do not auto-detect
            domain = get_env_variable('SITE_DOMAIN')
            if not domain or domain.startswith('localhost') or domain.startswith('127.0.0.1'):
                self.stdout.write(self.style.ERROR('SITE_DOMAIN environment variable is not set or resolves to localhost/127.0.0.1. Please set it in your .env file to a valid public domain or IP.'))
                return
            self.stdout.write(f"Using domain from SITE_DOMAIN: {domain}")
        
        # Update the site
        site.domain = domain
        site.name = site_name
        site.save()
        self.stdout.write(self.style.SUCCESS(f'Site updated: domain="{domain}", name="{site_name}"'))
