from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.serializers import BookSerializer
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serializers import PaymentSerializer
from user.models import User
from user.serializers import UserSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    """Serializer for the Borrowing model."""
    def validate(self, attrs):
        user = self.context["request"].user
        user_instance = User.objects.get(email=user)
        user_borrowings = Borrowing.objects.filter(user=user_instance).all()

        data = super(BorrowingSerializer, self).validate(attrs=attrs)
        Borrowing.validate_borrowing(
            attrs["book"],
            user_borrowings,
            attrs["expected_return_date"],
            error_to_raise=ValidationError
        )
        attrs["book"].save()
        return data

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = ("actual_return_date", "user")


class BorrowingListSerializer(serializers.ModelSerializer):
    """Serializer for a list of borrowings."""
    book_title = serializers.CharField(source="book.title", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "user_email",
            "payments"
        )


class BorrowingDetailSerializer(BorrowingSerializer):
    """Detailed serializer for the Borrowing model."""
    book = BookSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payments"
        )


class BorrowingReturnSerializer(serializers.ModelSerializer):
    """Serializer for returning a borrowing."""
    book = BookSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = (
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
