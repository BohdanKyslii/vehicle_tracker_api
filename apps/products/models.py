# apps/products/models.py
from django.db import models


class ProductCategory(models.Model):
    """
    Product category with support for parent-child hierarchy.
    Root categories: Вино, Китай, Сопутка (parent=None)
    Child categories reference their parent.
    """

    name_category = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Назва категорії",
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
        verbose_name="Батьківська категорія",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Опис",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        db_table = "product_categories"        # назва таблиці у БД
        verbose_name = "Категорія товару"
        verbose_name_plural = "Категорії товарів"
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
        verbose_name="Артикул (1С)",
    )
    name_product = models.CharField(
        max_length=255,
        verbose_name="Назва товару",
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
        verbose_name="Категорія",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Опис",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,   # автоматично при створенні
        verbose_name="Створено",
    )
    updated_at = models.DateTimeField(
        auto_now=True,       # автоматично при кожному збереженні
        verbose_name="Оновлено",
    )

    class Meta:
        db_table = "products"
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
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
        verbose_name="Товар",
    )
    # Одиниця товару
    # max_digits=8 — максимум 8 цифр; decimal_places=3 — 3 після коми
    unit_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Вага одиниці (кг)",
    )
    unit_length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Довжина одиниці (см)",
    )
    unit_width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ширина одиниці (см)",
    )
    unit_height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Висота одиниці (см)",
    )
    # Ящик
    units_per_box = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Одиниць у ящику",
    )
    box_weight_kg = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True,
        verbose_name="Вага ящика (кг)",
    )
    box_length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Довжина ящика (см)",
    )
    box_width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ширина ящика (см)",
    )
    box_height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Висота ящика (см)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_logistics"
        verbose_name = "Логістика товару"
        verbose_name_plural = "Логістика товарів"

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
