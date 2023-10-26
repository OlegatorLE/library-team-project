import stripe
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from payment.models import Payment
from payment.serializers import PaymentSerializer, PaymentListSerializer
from django.conf import settings


class PaymentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Payment.objects.select_related("borrowing")
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset

        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        return self.serializer_class


def create_checkout_session(money_to_pay: int):
    domain_url = "http://localhost:8000/"
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancelled/",
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": money_to_pay,
                    "product_data": {
                        "name": "Book",
                        "description": "Book borrowing",
                    },
                },
                "quantity": 1,
            }],
        )
        return {"session_id": checkout_session["id"], "session_url": checkout_session["url"]}
    except Exception as e:
        return {"error": str(e)}
