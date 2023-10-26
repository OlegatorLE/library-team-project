from celery import shared_task
import telebot

from django.conf import settings

from borrowing.overdue import check_borrowing_overdue

bot = telebot.TeleBot(settings.TELEGRAM_API_KEY)


@shared_task
def run_task():
    return check_borrowing_overdue()
