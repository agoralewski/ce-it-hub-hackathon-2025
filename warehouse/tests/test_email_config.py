from django.core.management.base import BaseCommand
import smtplib
from email.mime.text import MIMEText
from django.conf import settings
from ksp.env import get_env_variable


class Command(BaseCommand):
    help = 'Sends a test email to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--receiver',
            type=str,
            help='Email address to send the test email to (defaults to EXPIRY_NOTIFICATION_EMAIL or EMAIL_HOST_USER)',
        )

    def handle(self, *args, **options):
        receiver_email = options.get('receiver')
        if not receiver_email:
            # Use the expiry notification email or fall back to the host email
            receiver_email = get_env_variable(
                'EXPIRY_NOTIFICATION_EMAIL',
                settings.EMAIL_HOST_USER
            )
        
        # Get email settings
        host_email = settings.EMAIL_HOST_USER
        host_password = settings.EMAIL_HOST_PASSWORD
        
        if not host_email or not host_password:
            self.stdout.write(
                self.style.ERROR(
                    'Email settings are not configured properly. '
                    'Make sure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set in your .env file.'
                )
            )
            return
        
        # Prepare the test email
        subject = "Test Email from KSP Warehouse App"
        body = (
            "This is a test email from the KSP Warehouse application.\n\n"
            "If you are receiving this email, your email configuration is working correctly.\n\n"
            "You can now receive automatic notifications for items that are about to expire."
        )
        
        # Create the message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = host_email
        msg['To'] = receiver_email
        
        # Determine which connection method to use based on settings
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', True)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        port = getattr(settings, 'EMAIL_PORT', 465 if use_ssl else 587)
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        
        # Send the email
        try:
            if use_ssl:
                # Connect to the SMTP server using SSL
                with smtplib.SMTP_SSL(host, port) as server:
                    server.login(host_email, host_password)
                    server.send_message(msg)
            else:
                # Connect to the SMTP server using TLS if specified
                with smtplib.SMTP(host, port) as server:
                    if use_tls:
                        server.starttls()
                    server.login(host_email, host_password)
                    server.send_message(msg)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Test email sent successfully to {receiver_email}!'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error sending test email: {e}\n\n'
                    'Common issues:\n'
                    '- Check if your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct\n'
                    '- For Gmail, make sure you have created an app password\n'
                    '- Ensure your account has less secure apps access enabled\n'
                    '- Check your internet connection'
                )
            )
