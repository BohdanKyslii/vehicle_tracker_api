# apps/waybills/models.py
from django.db import models
from apps.customers.models import Customer, Store
from apps.products.models import Product


class WaybillRecord(models.Model):
    """
    Single line from a 1C waybill import.
    quantity > 0 = shipment, quantity < 0 = return.
    Unique key: waybill_number + line_position.
    """

    class LegalEntity(models.TextChoices):
        ESP = "ESP", "ESP"
        OPT = "OPT", "OPT"
        RUBIN = "Rubin", "Rubin"

    class DeliveryChannel(models.TextChoices):
        OWN = "own", "Власне авто"
        HIRED = "hired", "Найманий транспорт"
        CARRIER = "carrier", "Служба доставки"

    legal_entity = models.CharField(
        max_length=10,
        choices=LegalEntity.choices,
        verbose_name="Юридична особа",
    )
    waybill_number = models.CharField(
        max_length=50,
        verbose_name="Номер накладної",
    )
    waybill_date = models.DateField(
        verbose_name="Дата накладної",
    )
    line_position = models.SmallIntegerField(
        verbose_name="Позиція в накладній",
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Клієнт",
    )
    # Копія назви на момент імпорту (клієнт може змінити назву)
    customer_name = models.CharField(max_length=255, verbose_name="Клієнт (копія)")
    store = models.ForeignKey(
        Store,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Магазин",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Товар",
    )
    product_name = models.CharField(max_length=255, verbose_name="Товар (копія)")
    # quantity: + відвантаження, - повернення
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість",
    )
    price_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Ціна (грн)",
    )
    total_uah = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Сума (грн)",
    )
    comment = models.TextField(
        blank=True,
        default="",
        verbose_name="Коментар",
    )
    # Логістика (розраховується при імпорті)
    total_weight_kg = models.DecimalField(
        max_digits=12, decimal_places=3,
        null=True, blank=True,
        verbose_name="Загальна вага (кг)",
    )
    total_volume_cbm = models.DecimalField(
        max_digits=12, decimal_places=6,
        null=True, blank=True,
        verbose_name="Об'єм (м³)",
    )
    volumetric_weight_kg = models.DecimalField(
        max_digits=12, decimal_places=3,
        null=True, blank=True,
        verbose_name="Об'ємна вага (кг)",
    )
    # Канал доставки: null = ще не призначено
    delivery_channel = models.CharField(
        max_length=10,
        choices=DeliveryChannel.choices,
        null=True,
        blank=True,
        verbose_name="Канал доставки",
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    import_batch_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="ID імпорту",
    )

    class Meta:
        db_table = "waybill_records"
        verbose_name = "Рядок накладної"
        verbose_name_plural = "Реєстр накладних"
        # Унікальний ключ: накладна + позиція
        unique_together = [["waybill_number", "line_position"]]
        ordering = ["-waybill_date", "waybill_number"]
        indexes = [
            models.Index(fields=["waybill_date"]),
            models.Index(fields=["waybill_number"]),
            models.Index(fields=["delivery_channel"]),
        ]

    def __str__(self):
        return f"{self.waybill_number} / поз.{self.line_position}"

    @property
    def is_return(self) -> bool:
        """Returns True if this line is a product return."""
        return self.quantity < 0
