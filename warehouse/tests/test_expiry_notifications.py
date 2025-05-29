import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from warehouse.models import Item, Category, Room, Rack, Shelf, ItemShelfAssignment
from django.contrib.auth.models import User
from django.core.management import call_command


class ExpiryNotificationCommandTest(TestCase):
    def setUp(self):
        # Create test data
        self.category = Category.objects.create(name="Test Category")
        
        # Create items with different expiration dates
        today = timezone.now().date()
        
        # Item expiring today
        self.item1 = Item.objects.create(
            name="Item Expiring Today",
            category=self.category,
            expiration_date=today
        )
        
        # Item expiring in 3 days
        self.item2 = Item.objects.create(
            name="Item Expiring Soon",
            category=self.category,
            expiration_date=today + datetime.timedelta(days=3)
        )
        
        # Item expiring in 10 days (outside the notification window)
        self.item3 = Item.objects.create(
            name="Item Expiring Later",
            category=self.category,
            expiration_date=today + datetime.timedelta(days=10)
        )
        
        # Create a shelf structure for testing
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="password")
        
        # Assign the expiring items to shelves
        self.assignment1 = ItemShelfAssignment.objects.create(
            item=self.item1,
            shelf=self.shelf,
            added_by=self.user
        )
        
        self.assignment2 = ItemShelfAssignment.objects.create(
            item=self.item2,
            shelf=self.shelf,
            added_by=self.user
        )

    @patch('warehouse.management.commands.send_expiry_notifications.Command.send_email')
    def test_command_sends_email_for_expiring_items(self, mock_send_email):
        # Run the command
        call_command('send_expiry_notifications')
        
        # Check that send_email was called
        mock_send_email.assert_called_once()
        
        # Get the email body from the call arguments
        email_body = mock_send_email.call_args[0][1]
        
        # Verify both expiring items are in the email
        self.assertIn("Item Expiring Today", email_body)
        self.assertIn("Item Expiring Soon", email_body)
        
        # Verify the non-expiring item is not in the email
        self.assertNotIn("Item Expiring Later", email_body)
        
        # Verify the shelf location is included
        self.assertIn(self.shelf.full_location, email_body)

    @patch('smtplib.SMTP_SSL')
    def test_email_sending(self, mock_smtp):
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Run the command with the real send_email method
        with patch('warehouse.management.commands.send_expiry_notifications.settings') as mock_settings:
            # Configure mock settings
            mock_settings.EMAIL_HOST_USER = 'test@example.com'
            mock_settings.EMAIL_HOST_PASSWORD = 'password'
            
            # Run the command
            call_command('send_expiry_notifications')
            
            # Verify SMTP calls
            mock_smtp.assert_called_once_with("smtp.gmail.com", 465)
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
