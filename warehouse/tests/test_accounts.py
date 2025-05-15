"""
Tests for account-related functionality (login, registration, profile).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class UserAuthenticationTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.client = Client()

    def test_login_view(self):
        """Test login view"""
        # Test GET request
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Test successful login
        response = self.client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'password123'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
        # Verify user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Test login with wrong password
        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'wrongpassword'}
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_email_login(self):
        """Test login with email instead of username"""
        response = self.client.post(
            reverse('login'),
            {'username': 'test@example.com', 'password': 'password123'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        """Test logout view"""
        # Login first
        self.client.login(username="testuser", password="password123")
        
        # Verify user is logged in
        response = self.client.get(reverse('warehouse:index'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Test logout
        response = self.client.get(reverse('warehouse:custom_logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        
        # Verify user is logged out
        response = self.client.get(reverse('warehouse:index'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view(self):
        """Test user registration"""
        # Test GET request
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        
        # Test successful registration
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'complex_password_123',
                'password2': 'complex_password_123'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Test registration with existing username
        response = self.client.post(
            reverse('register'),
            {
                'username': 'testuser',  # Already exists
                'email': 'another@example.com',
                'password1': 'complex_password_123',
                'password2': 'complex_password_123'
            }
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        # Check for error in any language - just check if form has errors
        self.assertFalse(response.context['form'].is_valid())


class UserProfileTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.client = Client()

    def test_profile_view(self):
        """Test profile view"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test GET request
        response = self.client.get(reverse('warehouse:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/profile.html')
        
        # Verify user data is in context
        self.assertEqual(response.context['user'], self.user)

    def test_change_password_view(self):
        """Test password change functionality"""
        # Login
        self.client.login(username="testuser", password="password123")
        
        # Test GET request
        response = self.client.get(reverse('warehouse:change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'warehouse/change_password.html')
        
        # Test successful password change
        response = self.client.post(
            reverse('warehouse:change_password'),
            {
                'old_password': 'password123',
                'new_password1': 'new_password_456',
                'new_password2': 'new_password_456'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after password change
        
        # Verify password was changed by logging in with new password
        self.client.logout()
        login_success = self.client.login(username="testuser", password="new_password_456")
        self.assertTrue(login_success)
        
        # Test password change with incorrect old password
        response = self.client.post(
            reverse('warehouse:change_password'),
            {
                'old_password': 'wrong_old_password',
                'new_password1': 'another_new_password',
                'new_password2': 'another_new_password'
            }
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        # Just check if the form is invalid rather than for a specific error message
        self.assertTrue('old_password' in response.context['form'].errors)
        
        # Test password change with mismatched new passwords
        response = self.client.post(
            reverse('warehouse:change_password'),
            {
                'old_password': 'new_password_456',
                'new_password1': 'password_one',
                'new_password2': 'password_two'  # Different from new_password1
            }
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        # Just check if the form is invalid rather than for a specific error message
        self.assertTrue('new_password2' in response.context['form'].errors)