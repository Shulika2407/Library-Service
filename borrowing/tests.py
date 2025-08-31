from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from book.models import Book
from borrowing.models import Borrowing


class BorrowingTests(APITestCase):
    """
    Компактний набір тестів для BorrowingViews та BorrowingReturnView.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com", password="password123"
        )
        self.staff_user = get_user_model().objects.create_user(
            email="staffuser@example.com", password="password123", is_staff=True
        )

        self.book1 = Book.objects.create(
            title="Test Book 1", author="Author 1", inventory=5, daily_fee=1.00
        )
        self.book2 = Book.objects.create(
            title="Test Book 2", author="Author 2", inventory=10, daily_fee=2.00
        )

        # Активна позика
        self.borrowing_active = Borrowing.objects.create(
            book=self.book1,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=None,
        )
        # Повернута позика
        self.borrowing_returned = Borrowing.objects.create(
            book=self.book2,
            user=self.user,
            expected_return_date=date.today() - timedelta(days=7),
            actual_return_date=date.today(),
        )

    def test_list_and_filter_borrowings(self):
        """
        Тестуємо, що користувачі бачать лише свої позики,
        адміни - всі, та що фільтрація працює.
        """
        list_url = reverse("borrowing:borrowing-list")

        # Звичайний користувач бачить тільки свої позики
        self.client.force_authenticate(user=self.user)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data), 2)

        # Адмін бачить всі позики
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data), 2)

        # Фільтр для активних позик
        response = self.client.get(list_url, {"is_active": "True"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_active.id)

        # Фільтр для повернутих позик
        response = self.client.get(list_url, {"is_active": "False"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_returned.id)

    def test_create_borrowing(self):
        """
        Тестуємо створення нової позики авторизованим користувачем.
        """
        self.client.force_authenticate(user=self.user)
        list_url = reverse("borrowing:borrowing-list")
        payload = {
            "book": self.book1.title,
            "expected_return_date": (date.today() + timedelta(days=10)).isoformat(),
        }
        response = self.client.post(list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 3)

    def test_return_borrowing(self):
        """
        Тестуємо успішне повернення книги.
        """
        self.client.force_authenticate(user=self.user)

        return_url = reverse("borrowing:return_book", args=[self.borrowing_active.id])
        initial_inventory = self.book1.inventory
        response = self.client.post(return_url)
        self.borrowing_active.refresh_from_db()
        self.book1.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(self.borrowing_active.actual_return_date)
        self.assertEqual(self.book1.inventory, initial_inventory + 1)

    def test_return_already_returned_book(self):
        """
        Тестуємо, що не можна повернути вже повернуту книгу.
        """
        # Позначаємо книгу як повернуту
        self.borrowing_active.actual_return_date = date.today()
        self.borrowing_active.save()

        self.client.force_authenticate(user=self.user)
        # Оновлено назву URL для відповідності вашому urls.py
        return_url = reverse("borrowing:return_book", args=[self.borrowing_active.id])
        response = self.client.post(return_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("The book has already been returned.", response.data["error"])
