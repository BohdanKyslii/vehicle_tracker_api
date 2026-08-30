from django.db import models
from django.utils.translation import gettext_lazy as _


class Car(models.Model):
    """
    Vehicle from the company fleet.
    Includes fuel card and default tracking mode for the driver.
    """

    # Статус авто — choices обмежує значення поля
    class Status(models.TextChoices):
        ACTIVE = "active", _("Активне")
        REPAIR = "repair", _("Ремонт")
        INACTIVE = "inactive", _("Неактивне")
        # Вимушений простій через регуляцію часу праці водія/авто (тахограф/чіп)
        PAUSE = "pause", _("Пауза")
        # Загальний простій через відсутність водія (лікарняний, відпустка,
        # вихідний за сімейними обставинами тощо) — без деталізації причини
        # тут, вона фіксується окремо через change_status(reason=...)
        DRIVER_DOWNTIME = "driver_downtime", _("Простій (водій)")

    # Режим трекінгу водія
    class TrackingMode(models.TextChoices):
        DAILY = "daily", _("Щоденний (одометр)")
        FULL = "full", _("Повний (кожна точка)")

    name_car = models.CharField(
        max_length=100,
        verbose_name=_("Назва авто"),
        help_text=_("Назва авто"),
    )

    number_car = models.CharField(
        max_length=17,
        unique=True,
        verbose_name=_("Держ. номер"),
        help_text=_("Держ. номер"),
    )

    fuel_card_number = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Номер паливної карти"),
        help_text=_("Номер паливної карти"),
    )

    # Амортизація грн/міс — стала величина для розрахунків
    amount_car = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Амортизація (грн/міс)"),
        help_text=_("Амортизація (грн/міс)"),
    )

    default_tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        default=TrackingMode.DAILY,
        verbose_name=_("Режим трекінгу (дефолт)"),
        help_text=_("Режим трекінгу (дефолт)"),
    )

    status_car = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_("Статус"),
        help_text=_("Статус"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активне"),
        help_text=_("Активне"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Дата створення"),
    )

    class Meta:
        db_table = "cars"
        verbose_name = "Авто"
        verbose_name_plural = "Автопарк"
        ordering = ["number_car"]

    def __str__(self):
        return f"{self.number_car} — {self.name_car}"


class CarStatusLog(models.Model):
    """
    History of car status changes.
    Used to calculate days in repair per month.
    """

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name=_("Авто"),
        help_text=_("Авто"),
    )

    status = models.CharField(
        max_length=20,
        choices=Car.Status.choices,
        verbose_name=_("Статус"),
        help_text=_("Статус"),
    )

    reason = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Причина / коментар"),
        help_text=_("Причина / коментар"),
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Дата зміни"),
    )

    # Хто змінив — посилання на User (майбутня авторизація)
    changed_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Змінив"),
        help_text=_("Користувач, що змінив статус"),
    )

    class Meta:
        db_table = "car_status_logs"
        verbose_name = "Журнал статусів авто"
        verbose_name_plural = "Журнал статусів авто"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.car.number_car}: {self.status} ({self.changed_at.date()})"


class CarSpecs(models.Model):
    """
    Technical specifications of a vehicle.
    Stored separately to keep Car model clean.
    """

    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name="specs",
        verbose_name=_("Авто"),
        help_text=_("Авто"),
    )

    vin_code = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name=_("VIN код"),
        help_text=_("VIN код"),
    )

    year_manufactured = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Рік випуску"),
        help_text=_("Рік випуску"),
    )

    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Маса авто (кг)"),
        help_text=_("Маса авто (кг)"),
    )

    payload_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Вантажопідйомність (кг)"),
        help_text=_("Вантажопідйомність (кг)"),
    )

    length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Довжина (см)"),
        help_text=_("Довжина (см)"),
    )

    width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ширина (см)"),
        help_text=_("Ширина (см)"),
    )

    height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Висота (см)"),
        help_text=_("Висота (см)"),
    )

    # Гідроборт — за замовчуванням немає
    has_tail_lift = models.BooleanField(
        default=False,
        verbose_name=_("Гідроборт"),
        help_text=_("Гідроборт"),
    )

    # Причіп — за замовчуванням немає
    has_trailer = models.BooleanField(
        default=False,
        verbose_name=_("Причіп"),
        help_text=_("Причіп"),
    )

    class Meta:
        db_table = "car_specs"
        verbose_name = _("Характеристики авто")
        verbose_name_plural = _("Характеристики авто")

    def __str__(self):
        return f"Характеристики: {self.car.number_car}"


class Trailer(models.Model):
    """
    Trailer attached to a vehicle.
    Created only when car.specs.has_trailer = True.
    """

    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name="trailer",
        verbose_name=_("Авто"),
        help_text=_("Авто"),
    )

    name_trailer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Назва причепа"),
        help_text=_("Назва причепа"),
    )

    vin_code = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name=_("VIN код"),
        help_text=_("Модель причепа"),
    )

    number_trailer = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Номерний знак"),
        help_text=_("Номерний знак"),
    )

    year_manufactured = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Рік випуску"),
        help_text=_("Рік випуску"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Активний"))

    class Meta:
        db_table = "trailers"
        verbose_name = _("Причіп")
        verbose_name_plural = _("Причепи")

    def __str__(self):
        return f"{self.number_trailer} — {self.name_trailer}"


class Driver(models.Model):
    """
    Driver assigned to a vehicle.
    Telegram-лінк живе на apps.accounts.Profile.telegram_id (auth), не тут.
    """

    name_driver = models.CharField(
        max_length=150,
        verbose_name=_("ПІБ водія"),
        help_text=_("ПІБ водія"),
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name=_("Телефон"),
        help_text=_("Телефон водія"),
    )

    drivers_license = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Посвідчення водія"),
        help_text=_("Посвідчення водія"),
    )

    car = models.OneToOneField(
        Car,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="driver",
        verbose_name=_("Закріплене авто"),
        help_text=_("Закріплене авто водія"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активний"),
        help_text=_("Активний водій"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата створення"),
        help_text=_("Дата створення водія"),
    )

    class Meta:
        db_table = "drivers"
        verbose_name = _("Водій")
        verbose_name_plural = _("Водії")
        ordering = ["name_driver"]

    def __str__(self):
        return self.name_driver


class RouteEvent(models.Model):
    """
    Single event in a driver's route.
    All tracking data is stored here — daily and full mode.
    """

    class EventType(models.TextChoices):
        DEPOT_START = "depot_start", _("Старт зі складу")
        DELIVERY = "delivery", _("Вивантаження")
        PARKING_END = "parking_end", _("Кінець маршруту")
        DEPOT_RETURN = "depot_return", _("Повернення на склад")
        REFUEL = "refuel", _("Заправка")
        OTHER_COST = "other_cost", _("Інші витрати")
        RETURN_GOODS = "return_goods", _("Повернення товару")
        EXTRA_CARGO = "extra_cargo", _("Додатковий вантаж")

    class TrackingMode(models.TextChoices):
        DAILY = "daily", _("Щоденний")
        FULL = "full", _("Повний")

    car = models.ForeignKey(
        Car,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name=_("Авто"),
        help_text=_("Авто, на якому відбувається маршрут"),
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name=_("Водій"),
        help_text=_("Водій, який веде маршрут"),
    )

    tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        verbose_name=_("Режим трекінгу"),
        help_text=_("Режим трекінгу для маршруту"),
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name=_("Тип події"),
        help_text=_("Тип події, яка відбулася на маршруті"),
    )

    event_ts = models.DateTimeField(
        verbose_name=_("Час події"),
        help_text=_("Час події, яка відбулася на маршруті"),
    )

    odometer_km = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Одометр (км)"),
        help_text=_("Одометр (км)"),
    )

    pallets_count = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Кількість палет"),
        help_text=_("Кількість палет"),
    )

    # Для delivery
    waybill_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Номер накладної"),
        help_text=_("Номер накладної"),
    )

    waybill_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Дата накладної"),
        help_text=_("Дата накладної"),
    )

    customer_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Клієнт"),
        help_text=_("Клієнт"),
    )

    # Відмова від поставки (delivery)
    rejection_full = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("Повна відмова"),
        help_text=_("Повна відмова від поставки"),
    )

    rejection_product_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Артикул (відмова)"),
        help_text=_("Артикул (відмова)"),
    )

    rejection_qty = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Кількість (відмова)"),
        help_text=_("Кількість (відмова)"),
    )

    rejection_comment = models.TextField(
        blank=True,
        default="",
        help_text=_("Коментар до відмови"),
    )

    # Для refuel
    fuel_liters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Паливо (л)"),
        help_text=_("Кількість палива"),
    )

    fuel_cost_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Паливо (грн)"),
        help_text=_("Кількість палива"),
    )

    ad_blue_liters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("AdBlue (л)"),
        help_text=_("Кількість AdBlue"),
    )

    ad_blue_cost_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("AdBlue (грн)"),
        help_text=_("Кількість AdBlue"),
    )

    # Для other_cost
    other_costs_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Інші витрати (грн)"),
        help_text=_("Кількість інших витрат"),
    )

    other_costs_comment = models.TextField(
        blank=True,
        default="",
        help_text=_("Коментар до інших витрат"),
    )

    # Для return_goods
    return_client_waybill = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Накладна клієнта (повернення)"),
        help_text=_("Накладна клієнта (повернення)"),
    )

    # Для extra_cargo
    extra_from = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=_("Місто відправлення"),
    )
    extra_to = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=_("Місто призначення"),
    )

    extra_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_("Вага відправлення"),
    )

    extra_waybill = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Накладна відправлення"),
    )

    extra_comment = models.TextField(
        blank=True,
        default="",
        help_text=_("Коментар до відправлення"),
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Коментар до події"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Дата створення події"),
    )

    class Meta:
        db_table = "route_events"
        verbose_name = _("Подія маршруту")
        verbose_name_plural = _("Події маршруту")
        ordering = ["event_ts"]
        indexes = [
            models.Index(fields=["car", "event_ts"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.car.number_car} | {self.event_type} | {self.event_ts}"


class MonthlyCosts(models.Model):
    """
    Monthly operating costs per vehicle, entered by the logistics manager.
    repair_actual_uah overrides the calculated rate if provided.
    """

    car = models.ForeignKey(
        Car,
        on_delete=models.RESTRICT,
        related_name="monthly_costs",
        verbose_name=_("Авто"),
        help_text=_("Авто"),
    )

    # Зберігаємо як перший день місяця: 2026-06-01
    month = models.DateField(
        verbose_name=_("Місяць"),
        help_text=_("Місяць"),
    )

    salary_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("ЗП водія (грн)"),
        help_text=_("ЗП водія (грн)"),
    )

    taxes_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Податки із ЗП (грн)"),
        help_text=_("Податки із ЗП (грн)"),
    )

    depreciation_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Амортизація (грн)"),
        help_text=_("Амортизація (грн)"),
    )

    # Якщо заповнено — пріоритет над розрахунковим
    repair_actual_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ремонт фактичний (грн)"),
        help_text=_("Ремонт фактичний (грн)"),
    )

    repair_rate_uah_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=2.00,
        verbose_name=_("Ставка ремонту (грн/км)"),
        help_text=_("Ставка ремонту (грн/км)"),
    )

    other_costs_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Інші витрати (грн)"),
        help_text=_("Інші витрати (грн)"),
    )

    other_costs_comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Коментар до інших витрат"),
        help_text=_("Коментар до інших витрат"),
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
        db_table = "monthly_costs"
        verbose_name = _("Місячні витрати")
        verbose_name_plural = _("Місячні витрати")
        # Один запис на авто на місяць
        unique_together = [["car", "month"]]
        ordering = ["-month"]

    def __str__(self):
        return f"{self.car.number_car} — {self.month.strftime('%m.%Y')}"
