from datetime import date, timedelta

from django.conf import settings

from .models import Borrowing
from .telegram_helper import send_notification


def check_borrowing_overdue():
    """
    Check for any overdue borrowings and send notifications if found.

    Queries the database for any borrowings that are overdue and sends a notification to the specified chat ID.
    """
    borrowings = Borrowing.objects.filter(
        expected_return_date__lte=date.today() + timedelta(days=1),
        actual_return_date__isnull=True,
    ).select_related("book", "user")

    if borrowings:
        for borrowing in borrowings:
            message = (
                f"Borrowing #{borrowing.id} is overdue.\n"
                f"Book: {borrowing.book.title} (id: {borrowing.book.id})\n"
                f"User: {borrowing.user.email} (id: {borrowing.user.id})\n"
                f"Today: {date.today()}\n"
                f"Expected return date: {borrowing.expected_return_date}"
            )
            send_notification(message, chat_id=settings.TELEGRAM_CHAT_ID)
    else:
        message = "No borrowings overdue today!"
        send_notification(message, chat_id=settings.TELEGRAM_CHAT_ID)
