from django.utils import timezone

import stripe.error
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer,
)
from payment.models import Payment
from payment.views import create_checkout_session


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """ViewSet for handling borrowings."""
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """Get the queryset for borrowings."""
        queryset = self.queryset.select_related("book", "user").prefetch_related("payments")

        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user_id")
            is_active = self.request.query_params.get("is_active")

            if user_id:
                queryset = queryset.filter(user_id=int(user_id))

            if is_active:
                is_active = is_active.lower()
                if is_active == "false":
                    queryset = queryset.filter(
                        actual_return_date__isnull=False
                    )

                if is_active == "true":
                    queryset = queryset.filter(actual_return_date__isnull=True)
            return queryset
        return queryset.filter(user_id=self.request.user)

    def get_serializer_class(self):
        """Get the appropriate serializer class for the action."""
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "return_book":
            return BorrowingReturnSerializer

        return self.serializer_class

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
    )
    def return_book(self, request, pk=None):
        """Endpoint for returning book to library"""
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing)

        if borrowing.actual_return_date:
            return Response(
                {"detail": "The book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (payment_obj := borrowing.payments.filter(status=0)).exists():
            return HttpResponseRedirect(payment_obj.first().session_url)

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            book = borrowing.book
            book.inventory += 1

            book.save()
            borrowing.save()

        if borrowing.actual_return_date > borrowing.expected_return_date:
            self.create_payment_for_borrowing(self.request, borrowing, borrowing.overdue, 1)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        """Perform creation with transaction handling."""
        try:
            with transaction.atomic():
                borrowing = serializer.save(user=self.request.user)

                book = borrowing.book
                book.inventory -= 1
                book.save()

                self.create_payment_for_borrowing(self.request, borrowing, borrowing.price, 0)

        except stripe.error.APIError:
            borrowing.delete()

    @staticmethod
    def create_payment_for_borrowing(request, borrowing: Borrowing, money: int, payment_type: int):
        """Create payment for the borrowing."""

        payment = Payment.objects.create(
            status=0,
            type=payment_type,
            borrowing=borrowing,
            money_to_pay=money,
        )

        base_url = request.build_absolute_uri(
            reverse("payment:payment-detail", kwargs={"pk": payment.id})
        )

        money_to_pay = int(money * 100)

        session_data = create_checkout_session(money_to_pay, base_url)

        if session_data.get("error", None):
            raise stripe.error.APIError

        payment.session_url = session_data["session_url"]
        payment.session_id = session_data["session_id"]
        payment.save()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="Filter borrowings by user ID. (ex. ?user_id=1)",
                type={"type": "number"},
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter borrowings by active status. (ex. ?is_active=true)",
                type={"type": "boolean"},
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List all the borrowings."""
        return super().list(request, *args, **kwargs)
