from django.db import models
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    """
    Customer (company) from 1C accounting system.
    id_customer is the 1C identifier.
    """

    id_customer = models.IntegerField(
        primary_key=True,
        verbose_name=_("ID клієнта (1С)"),
        help_text=_("ID клієнта (1С)"),
    )

    name_customer = models.CharField(
        max_length=255,
        verbose_name=_("Назва клієнта"),
        help_text=_("Назва клієнта"),
    )

    # Напрямок діяльності: Роздріб, Мережа, HoReCa
    network_customer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Напрямок діяльності"),
        help_text=_("Напрямок діяльності"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активний"),
        help_text=_("Активний"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата створення"),
        help_text=_("Дата створення"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата оновлення"),
        help_text=_("Дата оновлення"),
    )

    class Meta:
        db_table = "customers"
        verbose_name = _("Клієнт")
        verbose_name_plural = _("Клієнти")
        ordering = ["name_customer"]

    def __str__(self):
        return self.name_customer


class Store(models.Model):
    """
    Store / retail point belonging to a customer.
    One customer can have multiple stores.
    """

    id_store = models.IntegerField(
        primary_key=True,
        verbose_name=_("ID магазину (1С)"),
        help_text=_("ID магазину в системі 1С"),
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.RESTRICT,     # не можна видалити клієнта якщо є магазини
        related_name="stores",
        verbose_name=_("Клієнт"),
        help_text=_("Клієнт, до якого належить магазин"),
    )

    name_store = models.CharField(
        max_length=255,
        verbose_name=_("Назва магазину"),
        help_text=_("Назва магазину"),
    )

    store_address = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name=_("Адреса магазину"),
        help_text=_("Адреса магазину"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активний"),
        help_text=_("Статус активності магазину"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата оновлення"),
        help_text=_("Дата останнього оновлення магазину"),
    )

    class Meta:
        db_table = "stores"
        verbose_name = _("Магазин")
        verbose_name_plural = _("Магазини")
        ordering = ["name_store"]

    def __str__(self):
        return f"{self.name_store} ({self.customer.name_customer})"


class StoreDeliveryAddress(models.Model):
    """
    Additional delivery addresses for a store.
    One store can have multiple delivery addresses.
    """

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="delivery_addresses",
        verbose_name=_("Магазин"),
        help_text=_("Магазин, для якого встановлена адреса доставки"),
    )

    delivery_address = models.CharField(
        max_length=500,
        verbose_name=_("Адреса доставки"),
        help_text=_("Адреса доставки для магазину"),
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Основна адреса"),
        help_text=_("Якщо встановлено, ця адреса буде використовуватися для доставки товарів"),
    )

    notes = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Примітки"),
        help_text=_("Додаткові примітки до адреси доставки"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Дата створення адреси доставки"),
    )

    class Meta:
        db_table = "store_delivery_addresses"
        verbose_name = _("Адреса доставки")
        verbose_name_plural = _("Адреси доставки")

    def __str__(self):
        return f"{self.store.name_store}: {self.delivery_address}"
