from django.contrib import admin

from .models import Product, ProductCategory, ProductLogistics


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_category", "parent", "is_root"]
    list_filter = ["parent"]
    search_fields = ["name_category"]


class ProductLogisticsAdmin(admin.StackedInline):
    """
    Inline — редагування логістики прямо на сторінці товару.
    StackedInline = вертикальне розташування полів.
    """

    model = ProductLogistics
    extra = 0  # не показувати порожні форми
    fields = [
        ("unit_weight_kg", "unit_per_box"),
        ("unit_length_cm", "unit_width_cm", "unit_height_cm"),
        ("box_weight_kg"),
        ("box_length_cm", "box_width_cm", "box_height_cm"),
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id_product", "name_product", "category", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["id_product", "name_product"]
    list_editable = ["is_active"]  # редагування прямо у списку
    inlines = [ProductLogisticsAdmin]
