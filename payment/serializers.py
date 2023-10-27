from rest_framework import serializers

from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.select_related("borrowing__book", "borrowing__user")
    )

    """Serializer for the Payment model."""
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("status", "type", "session_url", "session_id")


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for the Payment model for listing purposes."""
    class Meta:
        model = Payment
        fields = ("id", "status", "type", "money_to_pay")
