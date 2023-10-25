from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from payment.models import Payment
from payment.serializers import PaymentSerializer, PaymentListSerializer


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
        if self.action == 'list':
            return PaymentListSerializer

        return self.serializer_class
