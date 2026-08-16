from django.db import models
from django.utils.translation import gettext_lazy as _

class HiredTransportTrip(models.Model):
    """
        Single trip by hired (non-fleet) transport (§5.3 01_PROJECT_OVERVIEW.md).
        Entered by the logist, one row per trip — cost is actual, from the carrier.
        """

    car_number = models.CharField(
        max_length=20,
        verbose_name=_("Номер авто (найманий)"),
        help_text=_("Номер авто, який використовувався на рейсі"),
    )

    route_name = models.CharField(
        max_length=255,
        verbose_name=_("Назва маршруту"),
        help_text=_("Назва маршруту, який був використаний на рейсі"),
    )

    trip_date = models.DateField(
        verbose_name=_("Дата рейсу"),
        help_text=_("Дата, на яку був виконаний рейс"),
    )

    cost_uah=models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Вартість доставки (грн)"),
        help_text=_("Вартість доставки, вказана в гривнях"),
    )

    pallets_count = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Кількість палет"),
        help_text=_("Кількість палет, які були використані на рейсі"),
    )

    comment = models.TextField(
        default="",
        blank=True,
        verbose_name=_("Коментар"),
        help_text=_("Додатковий коментар до рейсу"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата створення"),
        help_text=_("Дата створення запису"),
    )

    class Meta:
        db_table = "hired_transport_trips"
        verbose_name = _("Рейс найманого транспорту")
        verbose_name_plural = _("Рейси найманим транспортом")
        ordering = ["-trip_date"]

    def __str__(self):
        return f"{self.car_number} - {self.route_name} ({self.trip_date})"

class HiredTripWaybill(models.Model):
    """
        Waybill attached to a hired-transport trip.
        waybill_number is unique — a waybill can belong to only one channel/trip.
        """

    trip = models.ForeignKey(
        HiredTransportTrip,
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name=_("Рейс"),
        help_text=_("Рейс, до якого прикріплено відправлення"),
    )

    waybill_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Номер накладної"),
        help_text=_("Номер накладної, який приєднано до рейсу"),
    )

    class Meta:
        db_table = "hired_trip_waybills"
        verbose_name = _("Накладна найманого транспорту")
        verbose_name_plural = _("Накладні найманим транспортом")

    def __str__(self):
        return f"{self.trip} - {self.waybill_number}"

class CarrierShipment(models.Model):
    """
    Shipment handed off to a delivery service (§5.4 01_PROJECT_OVERVIEW.md).
    Entered by the manager when assigning waybills to НП / Міст Експрес / etc.
    """

    class Carrier(models.TextChoices):
        NOVA_POSHTA = "nova_poshta", _("Нова Пошта")
        MIST_EXPRESS = "mist_express", _("Міст Експрес")
        OTHER = "other", _("Інша служба")

    carrier = models.CharField(
        max_length=20,
        choices=Carrier.choices,
        verbose_name=_("Служба доставки"),
        help_text=_("Служба доставки, яка прийняла відправлення"),
    )

    ttn = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Номер ТТН"),
        help_text=_("Номер ТТН, який прийняла відправлення служба доставки"),
    )

    shipment_date = models.DateField(
        verbose_name=_("Дата передачі відправлення"),
        help_text=_("Дата, на яку було передано відправлення службі доставки"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата створення"),
        help_text=_("Дата створення запису"),
    )

    class Meta:
        db_table = "carrier_shipments"
        verbose_name = _("Відправлення служби доставки")
        verbose_name_plural = _("Відправлення службам доставки")
        ordering = ["-shipment_date"]

    def __str__(self):
        return f"{self.ttn} ({self.get_carrier_display()})"

class CarrierShipmentWaybill(models.Model):
    """
        Waybill included in a carrier shipment. One ТТН can cover several waybills.
        """

    shipment = models.ForeignKey(
        CarrierShipment,
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name=_("Відправлення"),
        help_text=_("Відправлення, до якого належить відправлення"),
    )

    waybill_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Номер відправлення"),
        help_text=_("Номер відправлення"),
    )

    class Meta:
        db_table = "carrier_shipment_waybills"
        verbose_name = _("Накладна відправлення")
        verbose_name_plural = _("Накладні відправлення")

    def __str__(self):
        return f"{self.shipment.ttn} ({self.waybill_number})"

class CarrierCost(models.Model):
    """
    Row from the weekly carrier cost registry import, matched to a
    CarrierShipment by ttn (§5.4). shipment stays null until a matching
    CarrierShipment.ttn is found — registries can arrive before or after
    the shipment is registered.
    """

    shipment = models.ForeignKey(
        CarrierShipment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="costs",
        verbose_name=_("Відправлення"),
        help_text=_("Відправлення, до якого належить відправлення"),
    )

    ttn = models.CharField(
        max_length=50,
        verbose_name=_("Номер ТТН"),
        help_text=_("Номер ТТН"),
    )

    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Вага в кілограмах"),
        help_text=_("Вага відправлення в кілограмах"),
    )

    cost_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Вартість в гривнях"),
        help_text=_("Вартість відправлення в гривнях"),
    )

    cost_date = models.DateField(
        verbose_name=_("Дата відправлення"),
        help_text=_("Дата відправлення"),
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата і час імпорту"),
        help_text=_("Дата і час імпорту"),
    )

    class Meta:
        db_table = "carrier_costs"
        verbose_name = _("Витрата служби доставки")
        verbose_name_plural = _("Витрати служб доставки")
        ordering = ["-cost_date"]
        indexes = [models.Index(fields=["ttn"])]

    def __str__(self):
        return f"{self.ttn} — {self.cost_uah} грн"
