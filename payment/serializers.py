from rest_framework import serializers

from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    status = serializers.IntegerField(read_only=True)
    type = serializers.IntegerField(read_only=True)
    session_url = serializers.CharField(read_only=True)
    session_id = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentListSerializer(PaymentSerializer):
    class Meta:
        model = Payment
        fields = ("id", "status", "type", "money_to_pay")
