from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Tests the password reset email functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send the password reset test to',
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # Check if a user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'No user found with email {email}. '
                    'Please provide a valid email address associated with a user account.'
                )
            )
            return
        
        # Get the current domain
        current_site = Site.objects.get_current()
        site_name = current_site.name
        domain = current_site.domain
        
        # Create the password reset form and save it to send the email
        form = PasswordResetForm({'email': email})
        
        if form.is_valid():
            self.stdout.write(self.style.WARNING('Sending password reset email...'))
            
            # Use Django's built-in password reset functionality
            form.save(
                domain_override=domain,
                subject_template_name='registration/password_reset_subject.txt',
                email_template_name='registration/password_reset_email.html',
                use_https=False,  # Set to True for production
                from_email=settings.DEFAULT_FROM_EMAIL,
                request=None,
            )
            
            # Also display what the reset URL would look like (for debugging)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"http://{domain}/accounts/reset/{uid}/{token}/"
            
            self.stdout.write(self.style.SUCCESS(f'Password reset email sent to {email}!'))
            self.stdout.write(f"Debug info - Reset URL would be: {reset_url}")
            
            # Show the email settings being used
            self.stdout.write("\nEmail settings:")
            self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            self.stdout.write(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
            self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            # Display email configuration test results
            try:
                # Try a simple direct email send as a test
                send_mail(
                    'Test Email Connection',
                    'This is a test email to verify your SMTP settings are working.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS('Direct email test successful!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Direct email test failed: {e}'))
        else:
            self.stdout.write(self.style.ERROR(f'Form validation failed: {form.errors}'))
