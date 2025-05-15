"""
Tests for the warehouse views.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from warehouse.models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment


class IndexViewTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name="Test Category")
        self.item = Item.objects.create(name="Test Item", category=self.category)
        self.assignment = ItemShelfAssignment.objects.create(
            item=self.item,
            shelf=self.shelf,
            added_by=self.user
        )

    def test_index_view_with_login(self):
        """Test index view when user is logged in"""
        # Log in the user
        self.client.login(username="testuser", password="password123")
        
        # Get the index page
        response = self.client.get(reverse('warehouse:index'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that our test room is in the context
        self.assertIn('rooms', response.context)
        self.assertIn(self.room, response.context['rooms'])
        
        # Check that the template is correct
        self.assertTemplateUsed(response, 'warehouse/index.html')
        
        # Check that the active items count is correct
        for room in response.context['rooms']:
            if room.id == self.room.id:
                self.assertEqual(room.active_items, 1)
                self.assertEqual(room.rack_count, 1)
                self.assertEqual(room.shelf_count, 1)

    def test_index_view_without_login(self):
        """Test index view redirects when user is not logged in"""
        # Try to get the index page without logging in
        response = self.client.get(reverse('warehouse:index'))
        
        # Check that the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class ItemListViewTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name="Test Category")
        
        # Create an item with an expiration date in the future
        self.future_item = Item.objects.create(
            name="Future Item",
            category=self.category,
            expiration_date=timezone.now().date() + timedelta(days=60)
        )
        
        # Create an item with an expiration date in the next 30 days
        self.expiring_soon_item = Item.objects.create(
            name="Expiring Soon Item",
            category=self.category,
            expiration_date=timezone.now().date() + timedelta(days=15)
        )
        
        # Create an item with an expired date
        self.expired_item = Item.objects.create(
            name="Expired Item",
            category=self.category,
            expiration_date=timezone.now().date() - timedelta(days=5)
        )
        
        # Create an item with a note
        self.noted_item = Item.objects.create(
            name="Noted Item",
            category=self.category,
            note="This is a test note"
        )
        
        # Create assignments for each item
        self.future_assignment = ItemShelfAssignment.objects.create(
            item=self.future_item,
            shelf=self.shelf,
            added_by=self.user
        )
        
        self.expiring_soon_assignment = ItemShelfAssignment.objects.create(
            item=self.expiring_soon_item,
            shelf=self.shelf,
            added_by=self.user
        )
        
        self.expired_assignment = ItemShelfAssignment.objects.create(
            item=self.expired_item,
            shelf=self.shelf,
            added_by=self.user
        )
        
        self.noted_assignment = ItemShelfAssignment.objects.create(
            item=self.noted_item,
            shelf=self.shelf,
            added_by=self.user
        )

    def test_item_list_view_with_login(self):
        """Test item list view when user is logged in"""
        # Log in the user
        self.client.login(username="testuser", password="password123")
        
        # Get the item list page
        response = self.client.get(reverse('warehouse:item_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that our assignments are in the context
        self.assertIn('assignments', response.context)
        self.assertEqual(response.context['total_count'], 4)  # All items are active
        
        # Check that the template is correct
        self.assertTemplateUsed(response, 'warehouse/item_list.html')

    def test_item_list_view_without_login(self):
        """Test item list view redirects when user is not logged in"""
        # Try to get the item list page without logging in
        response = self.client.get(reverse('warehouse:item_list'))
        
        # Check that the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_item_list_view_with_filters(self):
        """Test item list view with various filters"""
        # Log in the user
        self.client.login(username="testuser", password="password123")
        
        # Test room filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?room={self.room.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 4)
        
        # Test search filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?search=Expiring")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        
        # Test category filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?category={self.category.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 4)
        
        # Test has_note filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?has_note=on")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        
        # Test expiring_soon filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?filter=expiring_soon")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        
        # Test expired filter
        response = self.client.get(f"{reverse('warehouse:item_list')}?filter=expired")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        
        # Test combined filters
        response = self.client.get(f"{reverse('warehouse:item_list')}?filter=expired&filter=expiring_soon")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)


class LowStockViewTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        
        # Create a category with less than 10 items (low stock)
        self.low_stock_category = Category.objects.create(name="Low Stock Category")
        self.low_stock_item = Item.objects.create(
            name="Low Stock Item",
            category=self.low_stock_category
        )
        self.low_stock_assignment = ItemShelfAssignment.objects.create(
            item=self.low_stock_item,
            shelf=self.shelf,
            added_by=self.user
        )
        
        # Create a category with more than 10 items (not low stock)
        self.normal_stock_category = Category.objects.create(name="Normal Stock Category")
        for i in range(15):
            item = Item.objects.create(
                name=f"Normal Stock Item {i}",
                category=self.normal_stock_category
            )
            ItemShelfAssignment.objects.create(
                item=item,
                shelf=self.shelf,
                added_by=self.user
            )

    def test_low_stock_view_with_login(self):
        """Test low stock view when user is logged in"""
        # Log in the user
        self.client.login(username="testuser", password="password123")
        
        # Get the low stock page
        response = self.client.get(reverse('warehouse:low_stock'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that our low stock category is in the context
        self.assertIn('low_stock_categories', response.context)
        low_stock_names = [cat['name'] for cat in response.context['low_stock_categories']]
        self.assertIn(self.low_stock_category.name, low_stock_names)
        
        # Check that the normal stock category is not in the context
        self.assertNotIn(self.normal_stock_category.name, low_stock_names)
        
        # Check that the template is correct
        self.assertTemplateUsed(response, 'warehouse/low_stock.html')

    def test_low_stock_view_without_login(self):
        """Test low stock view redirects when user is not logged in"""
        # Try to get the low stock page without logging in
        response = self.client.get(reverse('warehouse:low_stock'))
        
        # Check that the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class ExpirationTest(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name="Test Category")
        
        # Create items with different expiration dates
        self.expired_item = Item.objects.create(
            name="Expired Item",
            category=self.category,
            expiration_date=timezone.now().date() - timedelta(days=10)
        )
        self.soon_expiring_item = Item.objects.create(
            name="Soon Expiring Item",
            category=self.category,
            expiration_date=timezone.now().date() + timedelta(days=5)
        )
        self.valid_item = Item.objects.create(
            name="Valid Item",
            category=self.category,
            expiration_date=timezone.now().date() + timedelta(days=60)
        )
        
        # Add items to shelf
        self.expired_assignment = ItemShelfAssignment.objects.create(
            item=self.expired_item,
            shelf=self.shelf,
            added_by=self.user
        )
        self.soon_expiring_assignment = ItemShelfAssignment.objects.create(
            item=self.soon_expiring_item,
            shelf=self.shelf,
            added_by=self.user
        )
        self.valid_assignment = ItemShelfAssignment.objects.create(
            item=self.valid_item,
            shelf=self.shelf,
            added_by=self.user
        )

    def test_expired_items_warning(self):
        """Test that expired items are properly marked with warnings"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # View shelf detail page
        response = self.client.get(
            reverse('warehouse:shelf_detail', kwargs={'pk': self.shelf.pk})
        )
        self.assertEqual(response.status_code, 200)
        
        # Check that the today_date and thirty_days_from_now are in context
        self.assertIn('today_date', response.context)
        self.assertIn('thirty_days_from_now', response.context)
        
        # Check response HTML for appropriate warning class/indicators for expired items
        response_html = response.content.decode('utf-8')
        
        # A good application should have CSS classes or indicators for expired items
        self.assertIn('expired', response_html.lower(),
                     "Missing visual indicators for expired items")
        
        # For soon expiring items - fix the assertion syntax
        self.assertTrue(
            'expiring-soon' in response_html.lower() or 'warning' in response_html.lower(),
            "Missing visual indicators for soon-expiring items"
        )