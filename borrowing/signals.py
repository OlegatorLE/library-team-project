from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.models import Payment
from borrowing.models import Borrowing
from .telegram_helper import send_notification


@receiver(post_save, sender=Borrowing)
def new_borrowing(sender, instance, created, **kwargs):
    """
    Handle the post-save signal for a new borrowing instance.

    Args:
        sender: The model class.
        instance: The actual instance being saved.
        created: A boolean; True if a new record was created.
        **kwargs: Additional keyword arguments.

    Sends a notification to the specified chat ID about a newly created borrowing instance.
    """
    if created:
        message = (
            f"New borrowing created at {instance.borrow_date}.\n"
            f"ID: {instance.id}\n"
            f"Book: {instance.book.title}"
        )
        send_notification(message, chat_id=settings.TELEGRAM_CHAT_ID)


@receiver(post_save, sender=Payment)
def notify_payment_status(sender, instance, **kwargs):
    if instance.status == 1:
        message = (
            f"Payment for the borrowing ID: {instance.borrowing_id} "
            f"in the amount of {instance.money_to_pay}$ was completed successful"
        )
        send_notification(message, chat_id=settings.TELEGRAM_CHAT_ID)
