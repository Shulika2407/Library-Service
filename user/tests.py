from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from user.serializers import UserSerializer, AuthTokenSerializer
from user.models import Users


# Testing custom user and manager model
class UserModelTest(TestCase):
    def test_create_user(self):
        """Verifying the creation of a regular user"""
        email = "test@example.com"
        user = get_user_model().objects.create_user(
            email=email, password="password123", first_name="John", last_name="Doe"
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Verifying superuser creation"""
        email = "superuser@example.com"
        superuser = get_user_model().objects.create_superuser(
            email=email, password="password123", first_name="Admin", last_name="User"
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


# Testing serializers
class UserSerializerTest(TestCase):
    def test_user_serializer_valid_data(self):
        """Validation check for correct data for UserSerializer"""
        data = {
            "email": "user@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_auth_token_serializer_valid_credentials(self):
        """Verifying AuthTokenSerializer with correct credentials"""
        get_user_model().objects.create_user(
            email="valid@test.com", password="password123"
        )
        data = {"email": "valid@test.com", "password": "password123"}
        serializer = AuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())


# Testing API views
class UserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Use new names for URLs
        self.register_url = reverse("users:create")
        self.manage_url = reverse("users:me")
        self.user_data = {
            "email": "user@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_user_success(self):
        """Checking the successful registration of a new user"""
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Users.objects.filter(email=self.user_data["email"]).exists())

    def test_retrieve_and_update_user_profile(self):
        """Verifying the retrieval and update of profile data for an authenticated user"""
        user = Users.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)

        # Getting data
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_data["email"])

        # Data update
        new_data = {"first_name": "UpdatedName"}
        response = self.client.patch(self.manage_url, new_data, format="json")
        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.first_name, new_data["first_name"])
