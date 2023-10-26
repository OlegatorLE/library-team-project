from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import asyncio


from .models import Borrowing
from .telegram_helper import send_notification


@receiver(post_save, sender=Borrowing)
def new_borrowing(sender, instance, created, **kwargs):
    if created:
        message = (f"New borrowing created at {instance.borrow_date}.\n"
                   f"ID: {instance.id}\n"
                   f"Book: {instance.book.title}")
        asyncio.run(send_notification(message, chat_id=-4035854950))
