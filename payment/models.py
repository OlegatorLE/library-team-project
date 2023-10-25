from django.db import models

from borrowing.models import Borrowing


class Payment(models.Model):
    STATUS_CHOICES = (
        (0, "PENDING"),
        (1, "PAID")
    )

    TYPE_CHOICES = (
        (0, "PAYMENT"),
        (1, "FINE")
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES, default=0
    )
    type = models.IntegerField(
        choices=TYPE_CHOICES, default=0
    )

    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )

    session_url = models.CharField(max_length=255)
    session_id = models.CharField(max_length=63)

    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment: {self.id}; Pay: {self.money_to_pay};"
