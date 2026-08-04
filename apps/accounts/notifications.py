from django.conf import settings
from django.core.mail import send_mail


def notify_admin_new_registration(user):
    """Лист адміну про нову заявку — акаунт неактивний, поки його не підтвердять вручну в Django admin."""  # noqa: E501
    if not settings.ADMIN_EMAIL:
        return
    role = user.profile.get_role_display()
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
