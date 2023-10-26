from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.utils import json

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingListSerializer

BORROWING_URL = reverse("borrowing:borrowing-list")


def return_url(borrowing_id):
    return reverse("borrowing:borrowing-return-book", args=[borrowing_id])


def sample_book(**params):
    defaults = {
        "title": "Test Title",
        "author": "Test Author",
        "cover": "hard",
        "inventory": 20,
        "daily_fee": "12.2",
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_borrowing(book, user, **params):
    defaults = {
        "expected_return_date": "2000-10-05",
        "book": book,
        "user": user,
    }
    defaults.update(params)

    return Borrowing.objects.create(**defaults)


class PublicBorrowingsApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="newtest@test.com",
            password="testpass",
            is_staff=False,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_only_users_borrowings(self):
        book = sample_book()
        user_borrowing = sample_borrowing(book, self.user)

        other_user = create_user(email="cool@test.com", password="testpass")
        other_user_borrowing = sample_borrowing(book, other_user)

        res = self.client.get(BORROWING_URL)

        serializer1 = BorrowingListSerializer(user_borrowing)
        serializer2 = BorrowingListSerializer(other_user_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_post_borrowing(self):
        book = sample_book()

        payload = {"expected_return_date": "2000-10-05", "book": book.id}

        response = self.client.post(BORROWING_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        updated_book = Book.objects.get(pk=book.id)

        self.assertEqual(updated_book.inventory, book.inventory - 1)

    def test_post_borrowing_book_has_0_inventory(self):
        book = sample_book(inventory=0)

        payload = {"expected_return_date": "2000-10-05", "book": book.id}

        response = self.client.post(BORROWING_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="admintest@test.com", password="testpass", is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_filtering_is_active(self):
        book = sample_book()
        borrowing_active = sample_borrowing(book, self.user)
        borrowing_non_active = sample_borrowing(
            book, self.user, actual_return_date="2000-10-06"
        )

        res = self.client.get(BORROWING_URL, {"is_active": True})

        serializer1 = BorrowingListSerializer(borrowing_active)
        serializer2 = BorrowingListSerializer(borrowing_non_active)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtering_by_user_id(self):
        book = sample_book()
        first_user = create_user(
            email="cooluser@test.com", password="testpass"
        )

        first_borrowing = sample_borrowing(book, first_user)

        second_user = create_user(
            email="bestuser@test.com", password="testpass"
        )
        second_borrowing = sample_borrowing(book, second_user)

        res = self.client.get(BORROWING_URL, {"user_id": f"{first_user.id}"})

        serializer1 = BorrowingListSerializer(first_borrowing)
        serializer2 = BorrowingListSerializer(second_borrowing)

        actual_data = json.loads(res.content.decode())[0]

        self.assertEqual(serializer1.data, actual_data)
        self.assertNotEqual(serializer2.data, actual_data)


class ReturnActionTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="testemail@test.com", password="testpass"
        )
        self.client.force_authenticate(self.user)

    def test_if_book_already_returned(self):
        book = sample_book()
        borrowing = sample_borrowing(
            book, self.user, actual_return_date="2000-10-05"
        )
        url_for_return = return_url(borrowing.id)
        res = self.client.post(url_for_return, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_inventory_incremented(self):
        book = sample_book()
        borrowing = sample_borrowing(
            book,
            self.user,
        )
        url_for_return = return_url(borrowing.id)

        res = self.client.post(url_for_return, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        get_after_transaction = Book.objects.get(id=book.id)

        self.assertEqual(get_after_transaction.inventory, book.inventory + 1)
