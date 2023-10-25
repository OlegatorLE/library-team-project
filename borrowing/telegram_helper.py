import telegram
import asyncio
from django.conf import settings


async def send_notification(message_text, chat_id):
    bot = telegram.Bot(token=settings.TELEGRAM_API_KEY)
    async with bot:
        await bot.send_message(chat_id=chat_id, text=message_text)
