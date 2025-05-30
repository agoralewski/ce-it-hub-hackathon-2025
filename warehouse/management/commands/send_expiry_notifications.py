import datetime
import smtplib
import os
from email.mime.text import MIMEText
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from warehouse.models import Item, ItemShelfAssignment
from ksp.env import get_env_variable


class Command(BaseCommand):
    help = 'Sends email notifications for items that will expire within a week'

    def handle(self, *args, **options):
        # Calculate the date range for items expiring in one week or less
        today = timezone.now().date()
        one_week_from_now = today + datetime.timedelta(days=7)
        
        # Find items that will expire in one week or less
        expiring_items = Item.objects.filter(
            expiration_date__gte=today, 
            expiration_date__lte=one_week_from_now
        )
        
        if not expiring_items.exists():
            self.stdout.write(self.style.SUCCESS('No items expiring in the next week.'))
            return
        
        # Prepare email content
        subject = "Przedmioty z bliskim terminem waznosci"
        body = self.build_email_body(expiring_items)
        
        # Send the email
        try:
            self.send_email(subject, body)
            self.stdout.write(self.style.SUCCESS('Expiration notification email sent successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {e}'))

    def build_email_body(self, expiring_items):
        """Build the email body with the list of expiring items and their locations, grouped by item attributes"""
        lines = ["Te przedmioty maja bliski termin waznosci:\n\n"]
        
        # Dictionary to group items by name, expiration date, and location
        grouped_items = {}
        
        for item in expiring_items:
            # Get active assignments (items currently on shelves)
            active_assignments = ItemShelfAssignment.objects.filter(
                item=item, 
                remove_date__isnull=True
            )
            
            locations = []
            for assignment in active_assignments:
                locations.append(assignment.shelf.full_location)
            
            # Sort locations for consistent grouping
            locations.sort()
            
            # Format the expiration date
            expiration_date = item.expiration_date.strftime('%Y-%m-%d')
            
            # Create a unique key for grouping: name + expiry date + location + manufacturer
            group_key = (
                item.name, 
                expiration_date, 
                ','.join(locations) if locations else 'unassigned',
                item.manufacturer or ''
            )
            
            # Add to the grouping dictionary with any notes
            if group_key in grouped_items:
                grouped_items[group_key]['count'] += 1
                # Append unique notes if they exist
                if item.note and item.note not in grouped_items[group_key]['notes']:
                    grouped_items[group_key]['notes'].append(item.note)
            else:
                grouped_items[group_key] = {
                    'count': 1,
                    'notes': [item.note] if item.note else []
                }
        
        # Generate the email content from the grouped items
        for group_key, group_data in grouped_items.items():
            name, expiration_date, location_str, manufacturer = group_key
            count = group_data['count']
            notes = group_data['notes']
            
            # Format the item entry
            item_entry = f"Przedmiot: {name}"
            
            if manufacturer:
                item_entry += f" (Manufacturer: {manufacturer})"
            
            # Add count information
            item_entry += f" - {count} szt."
                
            item_entry += f"\nData waznosci: {expiration_date}"
            
            if location_str != 'unassigned':
                # Replace commas with comma+space for better readability
                formatted_locations = location_str.replace(',', ', ')
                item_entry += f"\nLokalizacja: {formatted_locations}"
            else:
                item_entry += "\nNie przypisano do zadnej polki."
            
            # Add notes if they exist
            if notes:
                item_entry += "\nNotatki:"
                for i, note in enumerate(notes, 1):
                    if len(notes) > 1:
                        item_entry += f"\n  {i}. {note}"
                    else:
                        item_entry += f"\n  {note}"
            
            lines.append(item_entry)
            lines.append("-" * 40)
            
        return "\n".join(lines)
    
    def send_email(self, subject, body):
        """Send the email using SMTP"""
        # Get email settings from Django settings or environment variables
        host_email = settings.EMAIL_HOST_USER
        host_password = settings.EMAIL_HOST_PASSWORD
        
        # Get receiver emails from environment (comma-separated list)
        # Default to host_email if no recipients are specified
        recipients_str = get_env_variable('EXPIRY_NOTIFICATION_EMAILS', host_email)
        recipient_list = [email.strip() for email in recipients_str.split(',')]
        
        # Ensure the host email is always included in the recipients
        if host_email not in recipient_list:
            recipient_list.append(host_email)
        
        # Create the message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = host_email
        msg['To'] = ', '.join(recipient_list)  # Join all recipients for display
        
        # Determine which connection method to use based on settings
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', True)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        port = getattr(settings, 'EMAIL_PORT', 465 if use_ssl else 587)
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        
        try:
            if use_ssl:
                # Connect to the SMTP server using SSL
                with smtplib.SMTP_SSL(host, port) as server:
                    server.login(host_email, host_password)
                    server.send_message(msg)
                    self.stdout.write(f"Email sent to: {', '.join(recipient_list)}")
            else:
                # Connect to the SMTP server using TLS if specified
                with smtplib.SMTP(host, port) as server:
                    if use_tls:
                        server.starttls()
                    server.login(host_email, host_password)
                    server.send_message(msg)
                    self.stdout.write(f"Email sent to: {', '.join(recipient_list)}")
        except Exception as e:
            # Re-raise the exception to be caught by the calling function
            raise Exception(f"Failed to send email: {e}")
