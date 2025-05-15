"""
Tests for the location management views (rooms, racks, shelves).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from warehouse.models import Room, Rack, Shelf


class RoomViewsTest(TestCase):
    def setUp(self):
        # Create a user with superuser privileges (for admin actions)
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )
        # Create a regular user
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test rooms
        self.room1 = Room.objects.create(name="Room 1")
        self.room2 = Room.objects.create(name="Room 2")

    def test_room_list_view(self):
        """Test room list view requires admin privileges"""
        # Test without login (should redirect)
        response = self.client.get(reverse('warehouse:room_list'))
        self.assertEqual(response.status_code, 302)
        
        # Test with regular user login (should redirect due to admin requirement)
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse('warehouse:room_list'))
        self.assertEqual(response.status_code, 302)  # Redirected because not admin
        
        # Test with admin login (should show rooms)
        self.client.logout()
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('warehouse:room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/room_list.html')
        self.assertIn('rooms', response.context)
        self.assertEqual(len(response.context['rooms']), 2)

    def test_room_create_view(self):
        """Test room creation view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(reverse('warehouse:room_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/room_form.html')
        
        # Test POST request with valid data
        room_name = 'New Room'  # We now preserve original capitalization
        response = self.client.post(
            reverse('warehouse:room_create'),
            {'name': room_name}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify room was created with preserved capitalization
        self.assertTrue(Room.objects.filter(name=room_name).exists())
        
        # Test POST request with invalid data (duplicate name)
        response = self.client.post(
            reverse('warehouse:room_create'),
            {'name': 'Room 1'}  # Already exists
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertFalse(response.context['form'].is_valid())

    def test_room_update_view(self):
        """Test room update view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(
            reverse('warehouse:room_update', kwargs={'pk': self.room1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/room_form.html')
        
        # Test POST request with valid data
        updated_name = 'Updated Room 1'
        response = self.client.post(
            reverse('warehouse:room_update', kwargs={'pk': self.room1.pk}),
            {'name': updated_name}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify room was updated with preserved capitalization
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.name, updated_name)

    def test_room_delete_view(self):
        """Test room delete view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show confirmation page)
        response = self.client.get(
            reverse('warehouse:room_delete', kwargs={'pk': self.room1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/room_delete.html')
        
        # Test POST request to confirm deletion
        response = self.client.post(
            reverse('warehouse:room_delete', kwargs={'pk': self.room1.pk}),
            {'confirm': 'yes'}  # Include the confirm parameter required by the view
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify room was deleted
        self.assertFalse(Room.objects.filter(pk=self.room1.pk).exists())


class RackViewsTest(TestCase):
    def setUp(self):
        # Create a user with superuser privileges (for admin actions)
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )
        self.client = Client()
        
        # Create test room and racks
        self.room = Room.objects.create(name="Test Room")
        self.rack1 = Rack.objects.create(name="A", room=self.room)
        self.rack2 = Rack.objects.create(name="B", room=self.room)

    def test_rack_create_view(self):
        """Test rack creation view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(
            reverse('warehouse:rack_create', kwargs={'room_id': self.room.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/rack_form.html')
        
        # Test POST request with valid data
        response = self.client.post(
            reverse('warehouse:rack_create', kwargs={'room_id': self.room.pk}),
            {'name': 'C'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify rack was created
        self.assertTrue(Rack.objects.filter(name='C', room=self.room).exists())
        
        # Test POST request with invalid data (duplicate name)
        response = self.client.post(
            reverse('warehouse:rack_create', kwargs={'room_id': self.room.pk}),
            {'name': 'A'}  # Already exists
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertFalse(response.context['form'].is_valid())

    def test_rack_update_view(self):
        """Test rack update view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(
            reverse('warehouse:rack_update', kwargs={'pk': self.rack1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/rack_form.html')
        
        # Test POST request with valid data
        response = self.client.post(
            reverse('warehouse:rack_update', kwargs={'pk': self.rack1.pk}),
            {'name': 'D'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify rack was updated
        self.rack1.refresh_from_db()
        self.assertEqual(self.rack1.name, 'D')

    def test_rack_delete_view(self):
        """Test rack delete view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show confirmation page)
        response = self.client.get(
            reverse('warehouse:rack_delete', kwargs={'pk': self.rack1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/rack_delete.html')
        
        # Test POST request to confirm deletion
        response = self.client.post(
            reverse('warehouse:rack_delete', kwargs={'pk': self.rack1.pk}),
            {'confirm': 'yes'}  # Include the confirm parameter
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify rack was deleted
        self.assertFalse(Rack.objects.filter(pk=self.rack1.pk).exists())


class ShelfViewsTest(TestCase):
    def setUp(self):
        # Create a user with superuser privileges (for admin actions)
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client = Client()
        
        # Create test room, rack, and shelves
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf1 = Shelf.objects.create(number=1, rack=self.rack)
        self.shelf2 = Shelf.objects.create(number=2, rack=self.rack)

    def test_shelf_detail_view(self):
        """Test shelf detail view"""
        # Login as user
        self.client.login(username="testuser", password="password123")
        
        # Test GET request
        response = self.client.get(
            reverse('warehouse:shelf_detail', kwargs={'pk': self.shelf1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/shelf_detail.html')
        self.assertEqual(response.context['shelf'], self.shelf1)
        
        # Check that assignments are in context (name might be 'assignments' instead of 'active_assignments')
        self.assertIn('assignments', response.context)

    def test_shelf_create_view(self):
        """Test shelf creation view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(
            reverse('warehouse:shelf_create', kwargs={'rack_id': self.rack.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/shelf_form.html')
        
        # Test POST request with valid data
        response = self.client.post(
            reverse('warehouse:shelf_create', kwargs={'rack_id': self.rack.pk}),
            {'number': 3}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify shelf was created
        self.assertTrue(Shelf.objects.filter(number=3, rack=self.rack).exists())
        
        # Test POST request with invalid data (duplicate number)
        response = self.client.post(
            reverse('warehouse:shelf_create', kwargs={'rack_id': self.rack.pk}),
            {'number': 1}  # Already exists
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertFalse(response.context['form'].is_valid())

    def test_shelf_update_view(self):
        """Test shelf update view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show form)
        response = self.client.get(
            reverse('warehouse:shelf_update', kwargs={'pk': self.shelf1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/shelf_form.html')
        
        # Test POST request with valid data
        response = self.client.post(
            reverse('warehouse:shelf_update', kwargs={'pk': self.shelf1.pk}),
            {'number': 5}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify shelf was updated
        self.shelf1.refresh_from_db()
        self.assertEqual(self.shelf1.number, 5)

    def test_shelf_delete_view(self):
        """Test shelf delete view"""
        # Login as admin
        self.client.login(username="admin", password="admin123")
        
        # Test GET request (should show confirmation page)
        response = self.client.get(
            reverse('warehouse:shelf_delete', kwargs={'pk': self.shelf1.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/shelf_delete.html')
        
        # Test POST request to confirm deletion
        response = self.client.post(
            reverse('warehouse:shelf_delete', kwargs={'pk': self.shelf1.pk}),
            {'confirm': 'yes'}  # Include the confirm parameter
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify shelf was deleted
        self.assertFalse(Shelf.objects.filter(pk=self.shelf1.pk).exists())