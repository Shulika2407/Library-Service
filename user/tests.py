from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from user.serializers import UserSerializer, AuthTokenSerializer
from user.models import Users


# Тестування кастомної моделі користувача та менеджера
class UserModelTest(TestCase):
    def test_create_user(self):
        """Перевірка створення звичайного користувача"""
        email = "test@example.com"
        user = get_user_model().objects.create_user(
            email=email, password="password123", first_name="John", last_name="Doe"
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Перевірка створення суперкористувача"""
        email = "superuser@example.com"
        superuser = get_user_model().objects.create_superuser(
            email=email, password="password123", first_name="Admin", last_name="User"
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


# Тестування серіалізаторів
class UserSerializerTest(TestCase):
    def test_user_serializer_valid_data(self):
        """Перевірка валідації коректних даних для UserSerializer"""
        data = {
            "email": "user@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_auth_token_serializer_valid_credentials(self):
        """Перевірка AuthTokenSerializer з коректними обліковими даними"""
        get_user_model().objects.create_user(
            email="valid@test.com", password="password123"
        )
        data = {"email": "valid@test.com", "password": "password123"}
        serializer = AuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())


# Тестування API-представлень
class UserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Використовуємо нові імена для URL-адрес
        self.register_url = reverse("users:create")
        self.manage_url = reverse("users:me")
        self.user_data = {
            "email": "user@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_user_success(self):
        """Перевірка успішної реєстрації нового користувача"""
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Users.objects.filter(email=self.user_data["email"]).exists())

    def test_retrieve_and_update_user_profile(self):
        """Перевірка отримання та оновлення даних профілю для автентифікованого користувача"""
        user = Users.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)

        # Отримання даних
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_data["email"])

        # Оновлення даних
        new_data = {"first_name": "UpdatedName"}
        response = self.client.patch(self.manage_url, new_data, format="json")
        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.first_name, new_data["first_name"])
