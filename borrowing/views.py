import http
from datetime import datetime

from django.db import transaction
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
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = self.queryset.select_related("book", "user")

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

        with transaction.atomic():
            borrowing.actual_return_date = datetime.today().date()
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        with transaction.atomic():
            borrowing = serializer.save(user=self.request.user)
            self.borrowing_helper(borrowing)

    @staticmethod
    def borrowing_helper(borrowing: Borrowing):
        with transaction.atomic():
            money_to_pay = int(borrowing.price * 100)
            session_data = create_checkout_session(money_to_pay, borrowing.id)

        if session_data.get("error", None):
            return Response(session_data, status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            status=0,
            type=0,
            borrowing=borrowing,
            session_url=session_data["session_url"],
            session_id=session_data["session_id"],
            money_to_pay=money_to_pay,
        )
