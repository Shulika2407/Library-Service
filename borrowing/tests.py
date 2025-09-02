from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from book.models import Book
from borrowing.models import Borrowing


class BorrowingTests(APITestCase):
    """
    A compact set of tests for BorrowingViews and BorrowingReturnView.
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

        # Active loan
        self.borrowing_active = Borrowing.objects.create(
            book=self.book1,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=None,
        )
        # Loan returned
        self.borrowing_returned = Borrowing.objects.create(
            book=self.book2,
            user=self.user,
            expected_return_date=date.today() - timedelta(days=7),
            actual_return_date=date.today(),
        )

    def test_list_and_filter_borrowings(self):
        """
        We test that users see only their loans, admins see everything, and that filtering works.
        """
        list_url = reverse("borrowing:borrowing-list")

        # A regular user only sees their loans
        self.client.force_authenticate(user=self.user)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data), 2)

        # Admin sees all loans
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data), 2)

        # Filter for active loans
        response = self.client.get(list_url, {"is_active": "True"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_active.id)

        # Filter for returned loans
        response = self.client.get(list_url, {"is_active": "False"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_returned.id)

    def test_create_borrowing(self):
        """
        We are testing the creation of a new loan by an authorized user.
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
        We are testing the successful return of the book.
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
        We are testing that it is not possible to return a book that has already been returned.
        """
        # Mark the book as returned
        self.borrowing_active.actual_return_date = date.today()
        self.borrowing_active.save()

        self.client.force_authenticate(user=self.user)
        return_url = reverse("borrowing:return_book", args=[self.borrowing_active.id])
        response = self.client.post(return_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("The book has already been returned.", response.data["error"])
