from django.conf import settings
from django.db import models
from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )

    @property
    def price(self):
        return (
            self.book.daily_fee *
            (self.borrow_date - self.expected_return_date).days
        )

    @property
    def overdue(self):
        if self.actual_return_date:
            return (
                (self.actual_return_date - self.expected_return_date).days *
                self.book.daily_fee
            )
        return 0

    def __str__(self):
        return f"{self.book} ({self.user})"
