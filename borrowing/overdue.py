from datetime import date, timedelta

import asyncio

from .models import Borrowing
from .telegram_helper import send_notification


def check_borrowing_overdue():
    borrowings = Borrowing.objects.filter(
        expected_return_date__lte=date.today() + timedelta(days=1),
        actual_return_date__isnull=True
    ).select_related("book", "user")
    chat_id = -4035854950

    if borrowings:
        for borrowing in borrowings:
            message = (f"Borrowing #{borrowing.id} is overdue.\n"
                       f"Book: {borrowing.book.title} (id: {borrowing.book.id})\n"
                       f"User: {borrowing.user.email} (id: {borrowing.user.id})\n"
                       f"Today: {date.today()}\n"
                       f"Expected return date: {borrowing.expected_return_date}")
            asyncio.run(send_notification(message, chat_id=chat_id))
    else:
        message = "No borrowings overdue today!"
        asyncio.run(send_notification(message, chat_id=chat_id))
