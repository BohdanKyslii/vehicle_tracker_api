import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.bot import run

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Запускає Telegram-бот реєстрації водіїв (long polling)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN не задано в .env")
        try:
            asyncio.run(run())
        except (KeyboardInterrupt, SystemExit):
            pass
