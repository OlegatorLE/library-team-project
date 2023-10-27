from django.contrib.auth import get_user_model

from payment.models import Payment


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_payment(borrowing, **params):
    defaults = {
        "status": 0,
        "type": 0,
        "borrowing": borrowing,
        "money_to_pay": "12.5",
        "session_url": "https://checkout.stripe.com/c/pay/",
        "session_id": "test_id",
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)
