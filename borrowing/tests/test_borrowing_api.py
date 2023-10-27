from unittest.mock import patch
from datetime import date
from django.test import TestCase, RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.utils import json

from borrowing.tests.samples import sample_book, sample_borrowing, create_user
from book.models import Book
from borrowing.serializers import BorrowingListSerializer
from payment.models import Payment
from payment.tests.test_payment_api import sample_payment

BORROWING_URL = reverse("borrowing:borrowing-list")
PAYMENTS_URL = reverse("payment:payment-list")


def return_url(borrowing_id):
    return reverse("borrowing:borrowing-return-book", args=[borrowing_id])


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

    @patch("borrowing.signals.send_notification", create=True)
    def test_get_only_users_borrowings(self, mock_send_notification):
        book = sample_book()
        user_borrowing = sample_borrowing(book, self.user)

        other_user = create_user(email="cool@test.com", password="testpass")
        other_user_borrowing = sample_borrowing(book, other_user)
        res = self.client.get(BORROWING_URL)

        serializer1 = BorrowingListSerializer(user_borrowing)
        serializer2 = BorrowingListSerializer(other_user_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    @patch("borrowing.tests.samples.get_current_date")
    @patch("borrowing.signals.send_notification", create=True)
    def test_post_borrowing(self, mock_send_notification, mock_get_current_date):
        mock_get_current_date.return_value = date(2050, 10, 10)
        book = sample_book()

        payload = {"expected_return_date": "2050-10-15", "book": book.id}

        response = self.client.post(BORROWING_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_send_notification.assert_called_once()

        updated_book = Book.objects.get(pk=book.id)
        self.assertEqual(updated_book.inventory, book.inventory - 1)

    def test_post_borrowing_book_has_0_inventory(self):
        book = sample_book(inventory=0)

        payload = {"expected_return_date": "2000-10-05", "book": book.id}

        response = self.client.post(BORROWING_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("borrowing.signals.send_notification")
    def test_cannot_borrow_if_has_unpaid_payment(self, mock_send_notification):
        book = sample_book()
        borrowing = sample_borrowing(book, self.user)
        sample_payment(borrowing)

        payment_obj = Payment.objects.all().first()
        self.assertEqual(payment_obj.status, 0)

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

    @patch("borrowing.signals.send_notification", create=True)
    def test_filtering_is_active(self, mock_send_notification):
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

    @patch("borrowing.signals.send_notification", create=True)
    def test_filtering_by_user_id(self, mock_send_notification):
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

        self.assertEqual(serializer1.data, json.loads(res.content.decode())[0])
        self.assertNotEqual(serializer2.data, json.loads(res.content.decode())[0])


class ReturnActionTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="testemail@test.com", password="testpass"
        )
        self.client.force_authenticate(self.user)
        self.factory = RequestFactory()

    @patch("borrowing.signals.send_notification", create=True)
    def test_cannot_return_borrowing_twice(self, mock_send_notification):
        book = sample_book()
        borrowing = sample_borrowing(
            book, self.user, actual_return_date="2000-10-05"
        )
        url_for_return = return_url(borrowing.id)
        res = self.client.post(url_for_return, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("borrowing.models.timezone")
    @patch("borrowing.views.timezone")
    @patch("borrowing.views.BorrowingViewSet.create_payment_for_borrowing")
    @patch("borrowing.signals.send_notification", create=True)
    def test_expected_return_date_expired_fine(self, mock_send_notification, mock_create_payment_for_borrowing, mock_datetime_view, mock_datetime_model):
        mock_datetime_model.now.return_value.date.return_value = date(2000, 10, 10)
        mock_datetime_view.now.return_value.date.return_value = date(2000, 12, 10)
        book = sample_book()

        borrowing = sample_borrowing(book, self.user, expected_return_date="2000-10-10")
        url_for_return = return_url(borrowing.id)

        self.client.post(url_for_return, {})
        mock_create_payment_for_borrowing.assert_called_once()

    @patch("borrowing.signals.send_notification", create=True)
    def test_book_inventory_incremented(self, mock_send_notification):
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
