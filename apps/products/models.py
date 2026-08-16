from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.Model):
    """
    Product category with support for parent-child hierarchy.
    Root categories: Вино, Китай, Сопутка (parent=None)
    Child categories reference their parent.
    """

    name_category = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Назва категорії"),
        help_text=_("Назва категорії товару"),
    )

    # null=True, blank=True — поле може бути порожнім (коренева категорія)
    # on_delete=SET_NULL — якщо батьківська видалена, дочірня стає коренева
    # related_name — як звертатись до дочірніх: category.children.all()
    parent = models.ForeignKey(
        "self",                      # посилання на ту саму модель
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name=_("Батьківська категорія"),
        help_text=_("Батьківська категорія товару"),
    )

    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Опис"),
        help_text=_("Опис категорії товару"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Створено"),
        help_text=_("Дата створення категорії товару"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Оновлено"),
        help_text=_("Дата оновлення категорії товару"),
    )

    class Meta:
        db_table = "product_categories"        # назва таблиці у БД
        verbose_name = _("Категорія товару")
        verbose_name_plural = _("Категорії товарів")
        ordering = ["name_category"]

    def __str__(self):
        # __str__ — що показує Django Admin у списку
        if self.parent:
            return f"{self.parent.name_category} → {self.name_category}"
        return self.name_category

    @property
    def is_root(self) -> bool:
        """Returns True if this is a root category (no parent)."""
        return self.parent is None


class Product(models.Model):
    """
    Product from the 1C accounting system.
    id_product is the 1C article code (not auto-generated).
    """

    # primary_key=True — цей рядок є первинним ключем замість auto id
    id_product = models.IntegerField(
        primary_key=True,
        verbose_name=_("Артикул (1С)"),
        help_text=_("Артикул товару з 1С"),
    )
    name_product = models.CharField(
        max_length=255,
        verbose_name=_("Назва товару"),
        help_text=_("Назва товару"),
    )

    # ForeignKey — зовнішній ключ до ProductCategory
    # default=15 — категорія "Інше" за замовчуванням
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=15,
        related_name="products",
        verbose_name=_("Категорія"),
        help_text=_("Категорія товару"),
    )

    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Опис"),
        help_text=_("Опис товару"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активний"),
        help_text=_("Активний товар"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,   # автоматично при створенні
        verbose_name=_("Створено"),
        help_text=_("Дата створення товару"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,       # автоматично при кожному збереженні
        verbose_name=_("Оновлено"),
        help_text=_("Дата оновлення товару"),
    )

    class Meta:
        db_table = "products"
        verbose_name = _("Товар")
        verbose_name_plural = _("Товари")
        ordering = ["name_product"]

    def __str__(self):
        return f"{self.id_product} — {self.name_product}"


class ProductLogistics(models.Model):
    """
    Logistics data for a product: dimensions and weight.
    Calculated fields (volume) are computed in utils, not stored.
    """

    # OneToOneField — один товар має одну логістику
    # Відрізняється від ForeignKey: унікальне з'єднання 1-до-1
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,      # видалили товар → видалили логістику
        related_name="logistics",
        verbose_name=_("Товар"),
        help_text=_("Товар, для якого вказані логістичні дані"),
    )

    # Одиниця товару
    # max_digits=8 — максимум 8 цифр; decimal_places=3 — 3 після коми
    unit_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Вага одиниці (кг)"),
        help_text=_("Вага однієї одиниці товару"),
    )

    unit_length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Довжина одиниці (см)"),
        help_text=_("Довжина однієї одиниці товару"),
    )

    unit_width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ширина одиниці (см)"),
        help_text=_("Ширина однієї одиниці товару"),
    )

    unit_height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Висота одиниці (см)"),
        help_text=_("Висота однієї одиниці товару"),
    )

    # Ящик
    units_per_box = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Одиниць у ящику"),
        help_text=_("Кількість одиниць товару у ящику"),
    )

    box_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Вага ящика (кг)"),
        help_text=_("Вага ящика товару"),
    )

    box_length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Довжина ящика (см)"),
        help_text=_("Довжина ящика товару"),
    )

    box_width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ширина ящика (см)"),
        help_text=_("Ширина ящика товару"),
    )

    box_height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Висота ящика (см)"),
        help_text=_("Висота ящика товару"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Дата останнього оновлення логістики товару"),
    )

    class Meta:
        db_table = "product_logistics"
        verbose_name = _("Логістика товару")
        verbose_name_plural = _("Логістика товарів")

    def __str__(self):
        return f"Логістика: {self.product.name_product}"

    # Property — обчислюване поле, не зберігається у БД
    # Викликається як атрибут: logistics.unit_volume_cbm
    @property
    def unit_volume_cbm(self):
        """Unit volume in cubic meters."""
        if self.unit_length_cm and self.unit_width_cm and self.unit_height_cm:
            return float(self.unit_length_cm * self.unit_width_cm * self.unit_height_cm) / 1_000_000
        return None

    @property
    def box_volume_cbm(self):
        """Box volume in cubic meters."""
        if self.box_length_cm and self.box_width_cm and self.box_height_cm:
            return float(self.box_length_cm * self.box_width_cm * self.box_height_cm) / 1_000_000
        return None

    @property
    def calculated_box_weight_kg(self):
        """Calculated box weight = unit weight × units per box."""
        if self.unit_weight_kg and self.units_per_box:
            return float(self.unit_weight_kg) * self.units_per_box
        return None
