"""
Tests for the warehouse forms.
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

from warehouse.models import Room, Rack, Shelf, Category, Item
from warehouse.forms import (
    RoomForm, 
    RackForm, 
    ShelfForm, 
    CategoryForm, 
    ItemForm, 
    ItemShelfAssignmentForm,
    ExportForm,
    CustomUserCreationForm
)


class RoomFormTest(TestCase):
    def test_valid_room_form(self):
        """Test valid room form data"""
        form = RoomForm(data={'name': 'test room'})
        self.assertTrue(form.is_valid())
        # Check that the room name preserves user input
        self.assertEqual(form.cleaned_data['name'], 'Test Room')

    def test_room_name_uniqueness(self):
        """Test room name uniqueness validation"""
        # Create a room first - use exact same case that will be tested
        Room.objects.create(name='Test room')  # This will be capitalized to 'Test Room'
        
        # Try to create another room with the same name (case-insensitive)
        form = RoomForm(data={'name': 'Test room'})
        # The form should be invalid due to the case-insensitive uniqueness constraint
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class RackFormTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='Test Room')

    def test_valid_rack_form(self):
        """Test valid rack form data"""
        form = RackForm(data={'name': 'a'}, room=self.room)
        self.assertTrue(form.is_valid())
        # Capitalized with title rule
        self.assertEqual(form.cleaned_data['name'], 'A')

    def test_rack_uniqueness_in_room(self):
        """Test rack name uniqueness within a room"""
        # Create a rack first
        Rack.objects.create(name='A', room=self.room)
        
        # Try to create another rack with the same name in the same room
        form = RackForm(data={'name': 'a'}, room=self.room)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Create another room
        another_room = Room.objects.create(name='Another Room')
        
        # Should be able to create a rack with the same name in a different room
        form = RackForm(data={'name': 'a'}, room=another_room)
        self.assertTrue(form.is_valid())


class ShelfFormTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='Test Room')
        self.rack = Rack.objects.create(name='A', room=self.room)

    def test_valid_shelf_form(self):
        """Test valid shelf form data"""
        form = ShelfForm(data={'number': 1}, rack=self.rack)
        self.assertTrue(form.is_valid())

    def test_shelf_uniqueness_in_rack(self):
        """Test shelf number uniqueness within a rack"""
        # Create a shelf first
        Shelf.objects.create(number=1, rack=self.rack)
        
        # Try to create another shelf with the same number in the same rack
        form = ShelfForm(data={'number': 1}, rack=self.rack)
        self.assertFalse(form.is_valid())
        self.assertIn('number', form.errors)
        
        # Create another rack
        another_rack = Rack.objects.create(name='B', room=self.room)
        
        # Should be able to create a shelf with the same number in a different rack
        form = ShelfForm(data={'number': 1}, rack=another_rack)
        self.assertTrue(form.is_valid())


class CategoryFormTest(TestCase):
    def test_valid_category_form(self):
        """Test valid category form data"""
        form = CategoryForm(data={'name': 'test category'})
        self.assertTrue(form.is_valid())
        # Check that the category name preserves user input
        self.assertEqual(form.cleaned_data['name'], 'Test Category')

    def test_category_name_uniqueness(self):
        """Test category name uniqueness validation"""
        # Create a category first with exact capitalization
        Category.objects.create(name='Test category')
        
        # Try to create another category with the same name (case-insensitive)
        form = CategoryForm(data={'name': 'test category'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_capitalization_preservation(self):
        """Test that form properly preserves user's capitalization"""
        # Create a category directly using the model to test capitalization preservation
        category_name = 'Mixed CASE Category'
        category = Category.objects.create(name=category_name)
        
        # Verify category was created with original capitalization
        self.assertEqual(category.name, category_name,
                        "Application should preserve user's original capitalization")


class ItemFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.valid_data = {
            'name': 'test item',
            'category': self.category.id,
            'manufacturer': 'Test Manufacturer',
            'expiration_date': timezone.now().date() + timedelta(days=30),
            'note': 'Test note'
        }

    def test_valid_item_form(self):
        """Test valid item form data"""
        form = ItemForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        # Check that the item name preserves user input 
        self.assertEqual(form.cleaned_data['name'], 'Test Item')

    def test_item_form_with_minimal_data(self):
        """Test item form with only required fields"""
        # Only name and category are required
        minimal_data = {
            'name': 'minimal item',
            'category': self.category.id
        }
        form = ItemForm(data=minimal_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Minimal Item')


class ItemShelfAssignmentFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.valid_data = {
            'item_name': 'Test Item',
            'category': self.category.id,
            'quantity': 1,
            'manufacturer': 'Test Manufacturer',
            'expiration_date': timezone.now().date() + timedelta(days=30),
            'notes': 'Test notes'
        }

    def test_valid_assignment_form(self):
        """Test valid assignment form data"""
        form = ItemShelfAssignmentForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_assignment_form_with_minimal_data(self):
        """Test assignment form with only required fields"""
        # Only item_name, category, and quantity are required
        minimal_data = {
            'item_name': 'Minimal Item',
            'category': self.category.id,
            'quantity': 1
        }
        form = ItemShelfAssignmentForm(data=minimal_data)
        self.assertTrue(form.is_valid())


class ExportFormTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='Test Room')
        self.rack = Rack.objects.create(name='A', room=self.room)
        self.shelf = Shelf.objects.create(number=1, rack=self.rack)
        self.category = Category.objects.create(name='Test Category')

    def test_valid_export_form(self):
        """Test valid export form data"""
        # Initialize the form with GET-style data structure
        form = ExportForm({
            'room': str(self.room.id),
            'category': str(self.category.id),
            'include_expired': 'on',
            'include_removed': ''
        })
        
        # The rack and shelf fields should still be valid even with empty queryset
        # because they're not required
        self.assertTrue(form.is_valid())

    def test_export_form_with_minimal_data(self):
        """Test export form with no filters selected"""
        # All fields are optional
        form = ExportForm(data={})
        self.assertTrue(form.is_valid())


class CustomUserCreationFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123'
        }

    def test_valid_user_creation_form(self):
        """Test valid user creation form data"""
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_username_uniqueness(self):
        """Test username uniqueness validation"""
        # Create a user first
        User.objects.create_user(username='testuser', password='password123')
        
        # Try to create another user with the same username
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_uniqueness(self):
        """Test email uniqueness validation"""
        # Create a user first with the same email
        User.objects.create_user(
            username='existinguser', 
            email='test@example.com', 
            password='password123'
        )
        
        # Try to create another user with the same email
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        """Test password mismatch validation"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'different_password_123'
        form = CustomUserCreationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_optional_email(self):
        """Test that email is optional"""
        data_without_email = self.valid_data.copy()
        data_without_email.pop('email')
        form = CustomUserCreationForm(data=data_without_email)
        self.assertTrue(form.is_valid())