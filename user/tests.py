# user/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
# No specific model imports needed here as we use get_user_model()

User = get_user_model()

class UserModelTests(TestCase):

    def test_create_user(self):
        """Test creating a user with the custom manager."""
        user = User.objects.create_user(
            phone_number='1234567890',
            name='Test User',
            password='password123'
        )
        self.assertEqual(user.phone_number, '1234567890')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, 'customer') # Default role (assuming model default is fixed)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = User.objects.create_superuser(
            phone_number='9876543210',
            name='Admin User',
            password='adminpassword'
        )
        self.assertEqual(admin_user.phone_number, '9876543210')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, 'admin') # Role set for superuser (assuming model manager is fixed)

    def test_create_user_missing_phone(self):
        """Test error when creating user without phone number."""
        with self.assertRaises(ValueError):
            User.objects.create_user(phone_number='', name='Test', password='pw')

    def test_create_user_missing_name(self):
        """Test error when creating user without name."""
        with self.assertRaises(ValueError): # Assuming model manager validation is fixed
            User.objects.create_user(phone_number='111222333', name='', password='pw')

    def test_user_str_representation(self):
        """Test the __str__ method."""
        user = User.objects.create_user(phone_number='5555555555', name='String Test', password='pw')
        self.assertEqual(str(user), 'String Test (5555555555)') # Assuming model __str__ is fixed

# Add tests for UserCreationForm if you have custom validation logic beyond the model


class UserAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone_number='111', name='API User', password='pw')
        self.admin_user = User.objects.create_superuser(phone_number='999', name='API Admin', password='pw')
        self.list_url = reverse('user-list') # Basename 'user' from api_urls.py

    def test_list_users_unauthenticated(self):
        response = self.client.get(self.list_url)
        # Default permission is IsAuthenticatedOrReadOnly, so list might be allowed if GET is safe
        # However, UserViewSet explicitly sets IsAdminUser, so it should be forbidden.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # UserViewSet requires IsAdminUser

    def test_list_users_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response data might be paginated by default
        # Check count if pagination is used, or length if not.
        # Assuming no pagination for simplicity here:
        self.assertEqual(len(response.data), 2) # user and admin_user
        # Check if data structure matches UserSerializer
        # Use list comprehension to check if phone numbers are present
        phone_numbers_in_response = [item['phone_number'] for item in response.data]
        self.assertIn(self.user.phone_number, phone_numbers_in_response)
        self.assertIn(self.admin_user.phone_number, phone_numbers_in_response)

    def test_retrieve_user_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.user.phone_number)

    def test_cannot_create_user_via_api(self):
        """UserViewSet is ReadOnly, POST should fail."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.list_url, {'phone_number': '555', 'name': 'Fail', 'password': 'pw'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_update_user_via_api(self):
        """UserViewSet is ReadOnly, PUT/PATCH should fail."""
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.put(detail_url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
