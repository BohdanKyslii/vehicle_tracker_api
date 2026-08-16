from django.db import models
from apps.customers.models import Customer, Store
from apps.products.models import Product
from django.utils.translation import gettext_lazy as _

class WaybillRecord(models.Model):
    """
    Single line from a 1C waybill import.
    quantity > 0 = shipment, quantity < 0 = return.
    Unique key: waybill_number + line_position.
    """

    class LegalEntity(models.TextChoices):
        ESP = "ESP", _("ESP")
        OPT = "OPT", _("OPT")
        RUBIN = "Rubin", _("Rubin")

    class DeliveryChannel(models.TextChoices):
        OWN = "own", _("Власне авто")
        HIRED = "hired", _("Найманий транспорт")
        CARRIER = "carrier", _("Служба доставки")

    legal_entity = models.CharField(
        max_length=10,
        choices=LegalEntity.choices,
        verbose_name=_("Юридична особа"),
        help_text=_("Юридична особа, яка відправила накладну"),
    )

    waybill_number = models.CharField(
        max_length=50,
        verbose_name=_("Номер накладної"),
        help_text=_("Номер накладної"),
    )

    waybill_date = models.DateField(
        verbose_name=_("Дата накладної"),
        help_text=_("Дата накладної"),
    )

    line_position = models.SmallIntegerField(
        verbose_name=_("Позиція в накладній"),
        help_text=_("Позиція в накладній"),
    )

    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name=_("Клієнт"),
        help_text=_("Клієнт, який отримав накладну"),
    )

    # Копія назви на момент імпорту (клієнт може змінити назву)
    customer_name = models.CharField(
        max_length=255,
        verbose_name=_("Клієнт (копія)"),
        help_text=_("Копія назви клієнта на момент імпорту"),
    )

    store = models.ForeignKey(
        Store,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name=_("Магазин"),
        help_text=_("Магазин, в якому отримав накладну"),
    )

    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name=_("Товар"),
        help_text=_("Товар, який був відвантажений"),
    )

    product_name = models.CharField(
        max_length=255,
        verbose_name=_("Товар (копія)"),
        help_text=_("Копія назви товару на момент імпорту"),
    )

    # quantity: + відвантаження, - повернення
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name=_("Кількість"),
        help_text=_("Кількість товару, яка була відвантажена"),
    )

    price_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Ціна (грн)"),
        help_text=_("Ціна товару, яка була відвантажена"),
    )

    total_uah = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Сума (грн)"),
        help_text=_("Сума товару, яка була відвантажена"),
    )

    comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Коментар"),
        help_text=_("Коментар до відвантаження"),
    )

    # Логістика (розраховується при імпорті)
    total_weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Загальна вага (кг)"),
        help_text=_("Загальна вага товару, яка була відвантажена"),
    )

    total_volume_cbm = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Об'єм (м³)"),
        help_text=_("Об'єм товару, який було відвантажено"),
    )

    volumetric_weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Об'ємна вага (кг)"),
        help_text=_("Об'ємна вага товару, яка була відвантажена"),
    )

    # Канал доставки: null = ще не призначено
    delivery_channel = models.CharField(
        max_length=10,
        choices=DeliveryChannel.choices,
        null=True,
        blank=True,
        verbose_name=_("Канал доставки"),
        help_text=_("Канал доставки товару"),
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Дата і час імпорту данних"),
    )

    import_batch_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("ID імпорту"),
        help_text=_("ID імпорту данних"),
    )

    class Meta:
        db_table = "waybill_records"
        verbose_name = _("Рядок накладної")
        verbose_name_plural = _("Реєстр накладних")
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
