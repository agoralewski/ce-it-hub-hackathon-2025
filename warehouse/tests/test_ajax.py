"""
Tests for AJAX functionality in the warehouse application.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from warehouse.models import Room, Rack, Shelf, Category, Item


class AjaxViewsTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test data
        self.room = Room.objects.create(name="Test Room")
        self.rack1 = Rack.objects.create(name="A", room=self.room)
        self.rack2 = Rack.objects.create(name="B", room=self.room)
        self.shelf1 = Shelf.objects.create(number=1, rack=self.rack1)
        self.shelf2 = Shelf.objects.create(number=2, rack=self.rack1)
        
        # Create categories
        self.category1 = Category.objects.create(name="Category 1")
        self.category2 = Category.objects.create(name="Category 2")
        
        # Create items
        self.item1 = Item.objects.create(
            name="Test Item 1",
            category=self.category1,
            manufacturer="Manufacturer 1"
        )
        self.item2 = Item.objects.create(
            name="Test Item 2",
            category=self.category1,
            manufacturer="Manufacturer 2"
        )
        self.item3 = Item.objects.create(
            name="Another Item",
            category=self.category2,
            manufacturer="Manufacturer 1"
        )

    def test_get_racks_ajax(self):
        """Test AJAX endpoint for getting racks based on room"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Check if we get at least one rack when making a request
        response = self.client.get(reverse('warehouse:get_racks'))
        self.assertEqual(response.status_code, 200)
        
        # Test with room_id
        response = self.client.get(
            f"{reverse('warehouse:get_racks')}?room_id={self.room.id}"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Verify we get the racks for this specific room
        rack_ids = [rack['id'] for rack in data]
        self.assertIn(self.rack1.id, rack_ids)
        self.assertIn(self.rack2.id, rack_ids)

    def test_get_shelves_ajax(self):
        """Test AJAX endpoint for getting shelves based on rack"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test with rack_id
        response = self.client.get(
            f"{reverse('warehouse:get_shelves')}?rack_id={self.rack1.id}"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify shelf data is present
        self.assertGreaterEqual(len(data), 2)
        
        # Get IDs of shelves that should be returned
        shelf_ids = [self.shelf1.id, self.shelf2.id]
        
        # Check that our shelves are in the results
        result_ids = [shelf['id'] for shelf in data]
        for shelf_id in shelf_ids:
            self.assertIn(shelf_id, result_ids)

    def test_autocomplete_categories_ajax(self):
        """Test AJAX endpoint for category autocomplete"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test without query - make sure it returns valid data
        response = self.client.get(reverse('warehouse:autocomplete_categories'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # The response includes a 'results' key with the data
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        
        # Create fresh categories to ensure they exist in the database
        category1 = Category.objects.get_or_create(name="Category 1")[0]
        category2 = Category.objects.get_or_create(name="Category 2")[0]
        
        # Test with specific query to find our category - using 'term' parameter as expected by the view
        response = self.client.get(
            f"{reverse('warehouse:autocomplete_categories')}?term=Category 1"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        
        # Check if category appears in results
        found = False
        for item in data['results']:
            if 'text' in item and "Category 1" in item['text']:
                found = True
                break
        self.assertTrue(found, "Category 1 not found in autocomplete results")

    def test_autocomplete_items_ajax(self):
        """Test AJAX endpoint for item autocomplete"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test without query
        response = self.client.get(reverse('warehouse:autocomplete_items'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # The response includes a 'results' key with the data
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        
        # Create specific items to search for
        item1 = Item.objects.get_or_create(
            name="Test Item 1",
            category=self.category1,
            manufacturer="Manufacturer 1"
        )[0]
        
        # Test with specific query - using 'term' parameter as expected by the view
        response = self.client.get(
            f"{reverse('warehouse:autocomplete_items')}?term=Test Item 1"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        
        # Check if item appears in results
        found = False
        for item in data['results']:
            if 'text' in item and "Test Item 1" in item['text']:
                found = True
                break
        self.assertTrue(found, "Test Item 1 not found in autocomplete results")
        
        # Test with category filter
        response = self.client.get(
            f"{reverse('warehouse:autocomplete_items')}?category_id={self.category1.id}"
        )
        self.assertEqual(response.status_code, 200)

    def test_autocomplete_manufacturers_ajax(self):
        """Test AJAX endpoint for manufacturer autocomplete"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test without query
        response = self.client.get(reverse('warehouse:autocomplete_manufacturers'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # The response includes a 'results' key with the data
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        
        # Create items with specific manufacturers
        Item.objects.get_or_create(
            name="Test Item M1",
            category=self.category1,
            manufacturer="Manufacturer 1"
        )
        Item.objects.get_or_create(
            name="Test Item M2",
            category=self.category1,
            manufacturer="Manufacturer 2"
        )
        
        # Test with specific query - using 'term' parameter as expected by the view
        response = self.client.get(
            f"{reverse('warehouse:autocomplete_manufacturers')}?term=Manufacturer 2"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        
        # Check for manufacturer in results
        found = False
        for item in data['results']:
            if 'text' in item and "Manufacturer 2" in item['text']:
                found = True
                break
        self.assertTrue(found, "Manufacturer 2 not found in autocomplete results")