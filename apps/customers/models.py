# apps/customers/models.py
from django.db import models


class Customer(models.Model):
    """
    Customer (company) from 1C accounting system.
    id_customer is the 1C identifier.
    """

    id_customer = models.IntegerField(
        primary_key=True,
        verbose_name="ID клієнта (1С)",
    )
    name_customer = models.CharField(
        max_length=255,
        verbose_name="Назва клієнта",
    )
    # Напрямок діяльності: Роздріб, Мережа, HoReCa
    network_customer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Напрямок діяльності",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        verbose_name = "Клієнт"
        verbose_name_plural = "Клієнти"
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
        verbose_name="ID магазину (1С)",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.RESTRICT,     # не можна видалити клієнта якщо є магазини
        related_name="stores",
        verbose_name="Клієнт",
    )
    name_store = models.CharField(
        max_length=255,
        verbose_name="Назва магазину",
    )
    store_address = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Адреса магазину",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        verbose_name = "Магазин"
        verbose_name_plural = "Магазини"
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
        verbose_name="Магазин",
    )
    delivery_address = models.CharField(
        max_length=500,
        verbose_name="Адреса доставки",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Основна адреса",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Примітки",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_delivery_addresses"
        verbose_name = "Адреса доставки"
        verbose_name_plural = "Адреси доставки"

    def __str__(self):
        return f"{self.store.name_store}: {self.delivery_address}"
