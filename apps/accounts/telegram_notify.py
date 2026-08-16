"""
Synchronous, dependency-free calls to the Telegram Bot API HTTP interface.
Separate from apps.accounts.bot (aiogram, async, long polling) — this is for
firing a one-off notification from plain sync Django code (views/notifications),
where spinning up an event loop just to send one message would be overkill.
"""

import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/{method}"


def _call(bot_token: str, method: str, payload: dict) -> None:
    """Best-effort call — a notification failing (bot blocked, network hiccup)
    must never break the registration request itself."""
    req = urllib.request.Request(
        API_URL.format(token=bot_token, method=method),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Telegram API call %s failed: %s", method, exc)


def send_message(
    bot_token: str, chat_id: int, text: str, reply_markup: dict | None = None
) -> None:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    _call(bot_token, "sendMessage", payload)


def approval_keyboard(user_id: int) -> dict:
    """
    Одна кнопка на роль — адмін одразу підтверджує з правильною роллю,
    а не просто "Так/Ні" (роль, обрана користувачем при реєстрації, може
    бути неточною або незаданою — бот завжди реєструє водіїв як DRIVER).
    HEAD тут доступний (на відміну від `RegisterSerializer` для веб-
    реєстрації, де він свідомо виключений) — ці кнопки й так бачать лише
    ID зі списку `TELEGRAM_ADMIN_IDS`, тобто вже довірені підтверджувати
    БУДЬ-яку роль; ховати саме HEAD від них не додавало жодного захисту.
    """
    from .models import Profile

    role_buttons = [
        {"text": f"✅ {label}", "callback_data": f"approve:{value}:{user_id}"}
        for value, label in Profile.Role.choices
    ]
    return {
        "inline_keyboard": [
            role_buttons,
            [{"text": "❌ Відхилити", "callback_data": f"reject:{user_id}"}],
        ]
    }
