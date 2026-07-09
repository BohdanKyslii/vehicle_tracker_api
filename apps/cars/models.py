# apps/cars/models.py
from django.db import models


class Car(models.Model):
    """
    Vehicle from the company fleet.
    Includes fuel card and default tracking mode for the driver.
    """

    # Статус авто — choices обмежує значення поля
    class Status(models.TextChoices):
        ACTIVE = "active", "Активне"
        REPAIR = "repair", "Ремонт"
        INACTIVE = "inactive", "Неактивне"

    # Режим трекінгу водія
    class TrackingMode(models.TextChoices):
        DAILY = "daily", "Щоденний (одометр)"
        FULL = "full", "Повний (кожна точка)"

    name_car = models.CharField(
        max_length=100,
        verbose_name="Назва авто",
    )
    number_car = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Держ. номер",
    )
    fuel_card_number = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Номер паливної карти",
    )
    # Амортизація грн/міс — стала величина для розрахунків
    amount_car = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Амортизація (грн/міс)",
    )
    default_tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        default=TrackingMode.DAILY,
        verbose_name="Режим трекінгу (дефолт)",
    )
    status_car = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активне")
    created_at = models.DateTimeField(auto_now_add=True)

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
        verbose_name="Авто",
    )
    status = models.CharField(
        max_length=20,
        choices=Car.Status.choices,
        verbose_name="Статус",
    )
    reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Причина / коментар",
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата зміни",
    )
    # Хто змінив — посилання на User (майбутня авторизація)
    changed_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Змінив",
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
        verbose_name="Авто",
    )
    vin_code = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name="VIN код",
    )
    year_manufactured = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Рік випуску",
    )
    weight_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Маса авто (кг)",
    )
    payload_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Вантажопідйомність (кг)",
    )
    length_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Довжина (см)",
    )
    width_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Ширина (см)",
    )
    height_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Висота (см)",
    )
    # Гідроборт — за замовчуванням немає
    has_tail_lift = models.BooleanField(
        default=False,
        verbose_name="Гідроборт",
    )
    # Причіп — за замовчуванням немає
    has_trailer = models.BooleanField(
        default=False,
        verbose_name="Причіп",
    )

    class Meta:
        db_table = "car_specs"
        verbose_name = "Характеристики авто"
        verbose_name_plural = "Характеристики авто"

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
        verbose_name="Авто",
    )
    name_trailer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Назва причепа",
    )
    vin_code = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name="VIN код",
    )
    model = models.CharField(
        max_length=100,
        verbose_name="Модель причепа",
    )
    number_trailer = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номерний знак",
    )
    year_manufactured = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Рік випуску",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        db_table = "trailers"
        verbose_name = "Причіп"
        verbose_name_plural = "Причепи"

    def __str__(self):
        return f"{self.number_trailer} — {self.model}"


class Driver(models.Model):
    """
    Driver assigned to a vehicle.
    telegram_id is optional — for future bot notifications.
    """

    name_driver = models.CharField(
        max_length=150,
        verbose_name="ПІБ водія",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Телефон",
    )
    drivers_license = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Посвідчення водія",
    )
    # Telegram ID для майбутнього бота (розсилки, звіти)
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram ID",
    )
    car = models.OneToOneField(
        Car,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="driver",
        verbose_name="Закріплене авто",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drivers"
        verbose_name = "Водій"
        verbose_name_plural = "Водії"
        ordering = ["name_driver"]

    def __str__(self):
        return self.name_driver


class RouteEvent(models.Model):
    """
    Single event in a driver's route.
    All tracking data is stored here — daily and full mode.
    """

    class EventType(models.TextChoices):
        DEPOT_START = "depot_start", "Старт зі складу"
        DELIVERY = "delivery", "Вивантаження"
        PARKING_END = "parking_end", "Кінець маршруту"
        DEPOT_RETURN = "depot_return", "Повернення на склад"
        REFUEL = "refuel", "Заправка"
        OTHER_COST = "other_cost", "Інші витрати"
        RETURN_GOODS = "return_goods", "Повернення товару"
        EXTRA_CARGO = "extra_cargo", "Додатковий вантаж"

    class TrackingMode(models.TextChoices):
        DAILY = "daily", "Щоденний"
        FULL = "full", "Повний"

    car = models.ForeignKey(
        Car,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name="Авто",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name="Водій",
    )
    tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        verbose_name="Режим трекінгу",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name="Тип події",
    )
    event_ts = models.DateTimeField(
        verbose_name="Час події",
    )
    odometer_km = models.IntegerField(
        null=True, blank=True,
        verbose_name="Одометр (км)",
    )
    pallets_count = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Кількість палет",
    )

    # Для delivery
    waybill_number = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Номер накладної",
    )
    waybill_date = models.DateField(
        null=True, blank=True,
        verbose_name="Дата накладної",
    )
    customer_name = models.CharField(
        max_length=255, blank=True, default="",
        verbose_name="Клієнт",
    )

    # Відмова від поставки (delivery)
    rejection_full = models.BooleanField(
        null=True, blank=True,
        verbose_name="Повна відмова",
    )
    rejection_product_id = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Артикул (відмова)",
    )
    rejection_qty = models.DecimalField(
        max_digits=10, decimal_places=3,
        null=True, blank=True,
        verbose_name="Кількість (відмова)",
    )
    rejection_comment = models.TextField(blank=True, default="")

    # Для refuel
    fuel_liters = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Паливо (л)",
    )
    fuel_cost_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Паливо (грн)",
    )
    ad_blue_liters = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="AdBlue (л)",
    )
    ad_blue_cost_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="AdBlue (грн)",
    )

    # Для other_cost
    other_costs_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Інші витрати (грн)",
    )
    other_costs_comment = models.TextField(blank=True, default="")

    # Для return_goods
    return_client_waybill = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Накладна клієнта (повернення)",
    )

    # Для extra_cargo
    extra_from = models.CharField(max_length=255, blank=True, default="")
    extra_to = models.CharField(max_length=255, blank=True, default="")
    extra_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=3,
        null=True, blank=True,
    )
    extra_waybill = models.CharField(max_length=50, blank=True, default="")
    extra_comment = models.TextField(blank=True, default="")

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "route_events"
        verbose_name = "Подія маршруту"
        verbose_name_plural = "Події маршруту"
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
        verbose_name="Авто",
    )
    # Зберігаємо як перший день місяця: 2026-06-01
    month = models.DateField(verbose_name="Місяць")
    salary_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="ЗП водія (грн)",
    )
    taxes_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Податки із ЗП (грн)",
    )
    depreciation_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Амортизація (грн)",
    )
    # Якщо заповнено — пріоритет над розрахунковим
    repair_actual_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Ремонт фактичний (грн)",
    )
    repair_rate_uah_km = models.DecimalField(
        max_digits=6, decimal_places=2, default=2.00,
        verbose_name="Ставка ремонту (грн/км)",
    )
    other_costs_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Інші витрати (грн)",
    )
    other_costs_comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_costs"
        verbose_name = "Місячні витрати"
        verbose_name_plural = "Місячні витрати"
        # Один запис на авто на місяць
        unique_together = [["car", "month"]]
        ordering = ["-month"]

    def __str__(self):
        return f"{self.car.number_car} — {self.month.strftime('%m.%Y')}"
