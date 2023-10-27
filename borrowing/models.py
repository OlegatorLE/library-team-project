from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

from book.models import Book

FINE_MULTIPLIER = 2


class Borrowing(models.Model):
    """Model representing the borrowing of a book by a user."""
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
        related_name="borrowings",
    )

    @property
    def price(self):
        """Calculate the total price for the borrowing."""
        return (
            self.book.daily_fee *
            ((self.expected_return_date - self.borrow_date).days + 1)
        )

    @property
    def overdue(self):
        """Calculate the overdue fine for the borrowing."""
        if self.actual_return_date and self.actual_return_date > self.expected_return_date:
            return (
                self.actual_return_date - self.expected_return_date
            ).days * self.book.daily_fee * FINE_MULTIPLIER
        return 0

    @staticmethod
    def validate_borrowing(book, user_borrowings, expected_return_date, borrow_date, error_to_raise):
        """Validate the borrowing process for a user and a book."""
        if book.inventory == 0:
            raise error_to_raise(
                "Book is out of stock and cannot be borrowed."
            )

        for borrowing in user_borrowings:
            if borrowing.payments.filter(status=0).exists():
                raise error_to_raise("You cannot borrow a new book with pending payments")

        if expected_return_date < borrow_date:
            raise error_to_raise("Expected return date cannot be earlier than today.")

    def clean(self):
        """Perform data validation for the borrowing."""
        user_borrowings = Borrowing.objects.filter(user=self.user).all()

        Borrowing.validate_borrowing(
            self.book,
            user_borrowings,
            self.expected_return_date,
            self.borrow_date,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        """Save the borrowing instance after cleaning data."""
        self.full_clean()
        return super(Borrowing, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{self.book} ({self.user})"
