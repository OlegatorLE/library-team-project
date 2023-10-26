import stripe
from django.urls import reverse
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

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

    @action(methods=["GET"], detail=True, url_path="success")
    def success(self, request, pk=None):
        session_id = self.get_object().session_id
        payment = Payment.objects.get(session_id=session_id)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        if session["payment_status"] == "paid":
            payment.status = 1
            payment.save()
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    @action(methods=["GET"], detail=True, url_path="cancelled")
    def cancel(self, request, pk=None):
        return Response({"detail": "You can make your pay in next 24 hours"})


def create_checkout_session(money_to_pay: int, domain_url: str):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success/",
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


@api_view(['GET'])
def api_root(request):
    data = {
        "User-API": {
            "user_create": reverse(
                "user:create", request=request
            ),
            "token_obtain_pair": reverse(
                "user:token_obtain_pair", request=request
            ),
            "token_refresh": reverse(
                "user:token_refresh", request=request
            ),
        },
        "Book-API": {
            "book_list": reverse("book:book-list", request=request),
        },
    }

    if request.user.is_authenticated:
        data["Borrowing-API"] = {
            "borrowings": reverse(
                "borrowing:borrowing-list", request=request
            ),
        }
        data["Payment-API"] = {
            "payments": reverse(
                "payment:payment-list", request=request
            ),
        }
        data["User-API"]["manage_user"] = reverse(
            "user:manage", request=request
        )

    return Response(data)
