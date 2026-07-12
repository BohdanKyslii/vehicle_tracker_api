from django.contrib.auth.models import User
from django.db import models

from apps.cars.models import Driver


class Profile(models.Model):
    class Role(models.TextChoices):
        DRIVER = "driver", "Водій"
        LOGIST = "logist", "Логіст"
        MANAGER = "manager", "Менеджер"
        HEAD = "head", "Керівник"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile",
        verbose_name="Користувач",
    )
    role = models.CharField(max_length=20, choices=Role.choices,
                            verbose_name="Роль")
    phone = models.CharField(max_length=17, blank=True, default="",
                             verbose_name="Телефон")
    telegram_id = models.BigIntegerField(null=True, blank=True,
                                         verbose_name="Telegram ID")

    # тільки для role=DRIVER — зв'язок з існуючою доменною моделлю Driver
    driver = models.OneToOneField(
        Driver, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="profile", verbose_name="Картка водія",
    )

    class Meta:
        db_table = "profiles"
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
