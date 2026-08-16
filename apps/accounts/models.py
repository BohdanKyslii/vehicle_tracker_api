from django.contrib.auth.models import User
from django.db import models

from apps.cars.models import Driver
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):

    class Role(models.TextChoices):
        DRIVER = "driver", _("Водій")
        LOGIST = "logist", _("Логіст")
        MANAGER = "manager", _("Менеджер")
        HEAD = "head", _("Керівник")

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("Користувач"),
        help_text=_("Користувач, який пов'язаний з цим профілем"),
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        verbose_name=_("Роль"),
        help_text=_("Роль користувача"),
    )

    phone = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name=_("Телефон"),
        help_text=_("Телефон користувача"),
    )

    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=_("Telegram ID"),
        help_text=_("Telegram ID користувача"),
    )

    # тільки для role=DRIVER — зв'язок з існуючою доменною моделлю Driver
    driver = models.OneToOneField(
        Driver,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profile",
        verbose_name=_("Картка водія"),
        help_text=_("Картка водія, яка пов'язана з цим профілем"),
    )

    class Meta:
        db_table = "profiles"
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
