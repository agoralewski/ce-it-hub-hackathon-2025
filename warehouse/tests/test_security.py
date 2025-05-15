"""
Tests for security features of the warehouse application.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from warehouse.models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment

class CSRFProtectionTest(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )
        self.client = Client(enforce_csrf_checks=True)
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name="Test Category")
        self.item = Item.objects.create(
            name="Test Item",
            category=self.category
        )
        self.assignment = ItemShelfAssignment.objects.create(
            item=self.item,
            shelf=self.shelf,
            added_by=self.user
        )

    def test_csrf_protection_on_forms(self):
        """Test CSRF protection on important forms"""
        # Login
        self.client.login(username="admin", password="admin123")
        
        # First get the form and extract the CSRF token
        response = self.client.get(reverse('warehouse:category_create'))
        self.assertEqual(response.status_code, 200)
        
        # Try to submit without a CSRF token (should fail)
        response = self.client.post(
            reverse('warehouse:category_create'),
            {'name': 'CSRF Test Category'}
        )
        # Without CSRF token, this should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Same test for item removal (a potentially destructive action)
        response = self.client.post(
            reverse('warehouse:remove_item_from_shelf', kwargs={'pk': self.assignment.pk})
        )
        self.assertEqual(response.status_code, 403)
        
        # Check that the item was not actually removed
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.remove_date)