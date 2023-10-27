import json
from unittest.mock import patch
import stripe
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from payment.tests.samples import create_user, sample_payment
from borrowing.tests.samples import sample_borrowing, sample_book
from payment.models import Payment
from payment.serializers import PaymentListSerializer, PaymentSerializer
from payment.views import create_checkout_session


stripe.api_key = "sk_test_26PHem9AhJZvU623DfE1x4sd"

PAYMENTS_URL = reverse("payment:payment-list")
BORROWING_URL = reverse("borrowing:borrowing-list")


def success_url(payment_id):
    return reverse("payment:payment-success", args=[payment_id])


class PublicPaymentsApi(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePaymentsApi(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="newtest@test.com",
            password="testpass",
            is_staff=False,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("borrowing.signals.send_notification", create=True)
    def test_get_only_users_payments(self, mock_send_notification):
        book = sample_book()
        borrowing_user = sample_borrowing(book, self.user)

        another_user = create_user(email="another@test.com")
        borrowing_other = sample_borrowing(book, another_user)

        payment_our_user = sample_payment(borrowing_user)
        payment_other_user = sample_payment(borrowing_other)

        res = self.client.get(PAYMENTS_URL)

        serializer1 = PaymentListSerializer(payment_our_user)
        serializer2 = PaymentListSerializer(payment_other_user)

        self.assertEqual(serializer1.data, json.loads(res.content.decode())[0])
        self.assertNotEqual(serializer2.data, json.loads(res.content.decode())[0])

    @patch("stripe.checkout.Session.create")
    def test_create_session_book_quantity_is_1(self, mock_create_session):
        mock_create_session.return_value = {
            "id": "test_session_id",
            "url": "https://test_url.com",
        }

        money_to_pay = 1000
        domain_url = "http://127.0.0.1:8000/"
        session_data = create_checkout_session(money_to_pay, domain_url)

        self.assertEqual(
            session_data,
            {"session_id": "test_session_id", "session_url": "https://test_url.com"},
        )

        mock_create_session.assert_called_once_with(
            success_url=domain_url + "success/",
            cancel_url=domain_url + "cancelled/",
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": money_to_pay,
                        "product_data": {
                            "name": "Book",
                            "description": "Book borrowing",
                        },
                    },
                    "quantity": 1,
                }
            ],
        )

    @patch("borrowing.views.BorrowingViewSet.create_payment_for_borrowing")
    @patch("borrowing.signals.send_notification")
    def test_check_if_create_payment_called_after_borrowing(
        self, mock_send_notification, mock_create_payment_for_borrowing
    ):
        book = sample_book()
        payload = {"expected_return_date": "2000-10-05", "book": book.id}

        self.client.post(BORROWING_URL, payload)
        mock_create_payment_for_borrowing.assert_called_once()


class AdminPaymentApiTest(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="admintest@test.com", password="testpass", is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


class TestSuccessEndpoint(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="testemail@test.com", password="testpass")
        self.client.force_authenticate(self.user)

    @patch("stripe.checkout.Session.retrieve")
    @patch("borrowing.signals.send_notification", create=True)
    def test_success_endpoint(self, mock_send_notifications, mock_session_retrieve):
        book = sample_book()
        borrowing = sample_borrowing(book, self.user)
        payment = sample_payment(borrowing)

        mock_session_retrieve.return_value = {
            "id": payment.session_id,
            "payment_status": "paid",
        }

        response = self.client.get(success_url(payment.id))

        updated_payment = Payment.objects.get(pk=payment.pk)
        self.assertEqual(updated_payment.status, 1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PaymentSerializer(updated_payment)
        self.assertEqual(response.data, serializer.data)
