import datetime
from django.contrib.auth import get_user_model

from book.models import Book
from borrowing.models import Borrowing


def sample_book(**params):
    defaults = {
        "title": "Test Title",
        "author": "Test Author",
        "cover": "hard",
        "inventory": 20,
        "daily_fee": "12.2",
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_borrowing(book, user, **params):
    defaults = {
        "expected_return_date": "2090-10-05",
        "book": book,
        "user": user,
    }
    defaults.update(params)

    return Borrowing.objects.create(**defaults)


def get_current_date():
    return datetime.date.today()
