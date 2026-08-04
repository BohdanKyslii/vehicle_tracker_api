from django.conf import settings
from django.core.mail import send_mail

from .telegram_notify import approval_keyboard, send_message


def notify_admin_new_registration(user):
    """
    Сповіщає адмінів про нову заявку — акаунт неактивний, поки хтось її не
    підтвердить: або вручну в Django Admin, або кнопкою прямо в Telegram
    (якщо налаштовано TELEGRAM_ADMIN_IDS — див. on_approve/on_reject у bot.py).
    Email і Telegram незалежні — відсутність одного не блокує інший.
    """
    role = user.profile.get_role_display()

    if settings.ADMIN_EMAIL:
        send_mail(
            subject=f"Нова заявка на реєстрацію: {user.username}",
            message=(
                f"Користувач {user.username} ({user.email or 'без email'}) "
                f"зареєструвався як «{role}» і очікує підтвердження.\n\n"
                "Підтвердити або відхилити можна в Django Admin → Users "
                "(поставити/зняти галочку Active)."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )

    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_IDS:
        text = (
            f"🆕 Нова заявка на реєстрацію\n\n"
            f"Користувач: <b>{user.username}</b>\n"
            f"Роль при реєстрації: {role}\n"
            f"Email: {user.email or 'без email'}\n\n"
            "Оберіть роль, з якою підтвердити:"
        )
        keyboard = approval_keyboard(user.id)
        for admin_id in settings.TELEGRAM_ADMIN_IDS:
            send_message(settings.TELEGRAM_BOT_TOKEN, admin_id, text, keyboard)
