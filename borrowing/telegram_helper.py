import telebot

from django.conf import settings

bot = telebot.TeleBot(settings.TELEGRAM_API_KEY)


def send_notification(message_text, chat_id):
    """Send notification to the specified chat ID."""
    bot.send_message(chat_id=chat_id, text=message_text)
