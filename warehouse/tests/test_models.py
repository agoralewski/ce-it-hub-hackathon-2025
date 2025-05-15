"""
Tests for the warehouse models.
"""
import uuid
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.utils import IntegrityError

from warehouse.models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment


class RoomModelTest(TestCase):
    def test_room_creation(self):
        """Test creating a room instance"""
        room = Room.objects.create(name="Test Room")
        self.assertEqual(room.name, "Test Room")
        self.assertIsNotNone(room.qr_code_uuid)
        self.assertIsInstance(room.qr_code_uuid, uuid.UUID)

    def test_room_str_representation(self):
        """Test string representation of a room"""
        room = Room.objects.create(name="Test Room")
        self.assertEqual(str(room), "Test Room")

    def test_room_name_uniqueness(self):
        """Test that room names must be unique"""
        Room.objects.create(name="Unique Room")
        with self.assertRaises(IntegrityError):
            Room.objects.create(name="Unique Room")


class RackModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name="Test Room")

    def test_rack_creation(self):
        """Test creating a rack instance"""
        rack = Rack.objects.create(name="A", room=self.room)
        self.assertEqual(rack.name, "A")
        self.assertEqual(rack.room, self.room)
        self.assertIsNotNone(rack.qr_code_uuid)
        self.assertIsInstance(rack.qr_code_uuid, uuid.UUID)

    def test_rack_str_representation(self):
        """Test string representation of a rack"""
        rack = Rack.objects.create(name="A", room=self.room)
        self.assertEqual(str(rack), "Test Room.A")

    def test_rack_unique_together_constraint(self):
        """Test that name and room combination must be unique"""
        Rack.objects.create(name="A", room=self.room)
        with self.assertRaises(IntegrityError):
            Rack.objects.create(name="A", room=self.room)


class ShelfModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)

    def test_shelf_creation(self):
        """Test creating a shelf instance"""
        shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.assertEqual(shelf.number, 1)
        self.assertEqual(shelf.rack, self.rack)
        self.assertIsNotNone(shelf.qr_code_uuid)
        self.assertIsInstance(shelf.qr_code_uuid, uuid.UUID)

    def test_shelf_str_representation(self):
        """Test string representation of a shelf"""
        shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.assertEqual(str(shelf), "Test Room.A.1")

    def test_shelf_full_location_property(self):
        """Test the full_location property of a shelf"""
        shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.assertEqual(shelf.full_location, "Test Room.A.1")

    def test_shelf_unique_together_constraint(self):
        """Test that number and rack combination must be unique"""
        Shelf.objects.create(number=1, rack=self.rack)
        with self.assertRaises(IntegrityError):
            Shelf.objects.create(number=1, rack=self.rack)


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        """Test creating a category instance"""
        category = Category.objects.create(name="Test Category")
        self.assertEqual(category.name, "Test Category")

    def test_category_str_representation(self):
        """Test string representation of a category"""
        category = Category.objects.create(name="Test Category")
        self.assertEqual(str(category), "Test Category")

    def test_category_name_uniqueness(self):
        """Test that category names must be unique"""
        Category.objects.create(name="Unique Category")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Unique Category")


class ItemModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")

    def test_item_creation(self):
        """Test creating an item instance"""
        item = Item.objects.create(
            name="Test Item",
            category=self.category,
            manufacturer="Test Manufacturer",
            expiration_date=timezone.now().date() + timedelta(days=30),
            note="Test note",
            is_gifted=True
        )
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.category, self.category)
        self.assertEqual(item.manufacturer, "Test Manufacturer")
        self.assertEqual(item.expiration_date, timezone.now().date() + timedelta(days=30))
        self.assertEqual(item.note, "Test note")
        self.assertTrue(item.is_gifted)

    def test_item_str_representation(self):
        """Test string representation of an item"""
        item = Item.objects.create(name="Test Item", category=self.category)
        self.assertEqual(str(item), "Test Item")

    def test_item_optional_fields(self):
        """Test that some fields are optional"""
        item = Item.objects.create(name="Minimal Item", category=self.category)
        self.assertIsNone(item.manufacturer)
        self.assertIsNone(item.expiration_date)
        self.assertIsNone(item.note)
        self.assertFalse(item.is_gifted)


class ItemShelfAssignmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.room = Room.objects.create(name="Test Room")
        self.rack = Rack.objects.create(name="A", room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name="Test Category")
        self.item = Item.objects.create(name="Test Item", category=self.category)

    def test_assignment_creation(self):
        """Test creating an item-shelf assignment"""
        assignment = ItemShelfAssignment.objects.create(
            item=self.item,
            shelf=self.shelf,
            added_by=self.user
        )
        self.assertEqual(assignment.item, self.item)
        self.assertEqual(assignment.shelf, self.shelf)
        self.assertEqual(assignment.added_by, self.user)
        self.assertIsNone(assignment.removed_by)
        self.assertIsNone(assignment.remove_date)
        self.assertTrue(assignment.is_active)

    def test_assignment_str_representation(self):
        """Test string representation of an assignment"""
        assignment = ItemShelfAssignment.objects.create(
            item=self.item,
            shelf=self.shelf,
            added_by=self.user
        )
        self.assertEqual(str(assignment), f"Test Item on Test Room.A.1 - Active")

    def test_is_active_property(self):
        """Test the is_active property"""
        assignment = ItemShelfAssignment.objects.create(
            item=self.item,
            shelf=self.shelf,
            added_by=self.user
        )
        self.assertTrue(assignment.is_active)
        
        # Mark as removed
        assignment.removed_by = self.user
        assignment.remove_date = timezone.now()
        assignment.save()
        
        self.assertFalse(assignment.is_active)
        self.assertEqual(str(assignment), f"Test Item on Test Room.A.1 - Removed")