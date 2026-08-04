from rest_framework import serializers

from .models import Product, ProductCategory, ProductLogistics


class ProductCategorySerializer(serializers.ModelSerializer):
    # SerializerMethodField — поле яке рахується методом get_<field>
    is_root = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name_category",
            "parent",
            "is_root",
            "parent_name",
        ]

    def get_is_root(self, obj) -> bool:
        """obj — це екземпляр ProductCategory."""
        return obj.parent is None

    def get_parent_name(self, obj) -> str | None:
        return obj.parent.name_category if obj.parent else None


class ProductLogisticsSerializer(serializers.ModelSerializer):
    # Поля що розраховуються (read_only — тільки для читання)
    unit_volume_cbm = serializers.SerializerMethodField()
    box_volume_cbm = serializers.SerializerMethodField()
    calculated_box_weight = serializers.SerializerMethodField()

    class Meta:
        model = ProductLogistics
        fields = [
            "unit_weight_kg",
            "unit_length_cm",
            "unit_width_cm",
            "unit_height_cm",
            "units_per_box",
            "box_weight_kg",
            "box_length_cm",
            "box_width_cm",
            "box_height_cm",
            "unit_volume_cbm",
            "box_volume_cbm",
            "calculated_box_weight",
        ]

    def get_unit_volume_cbm(self, obj):
        return obj.unit_volume_cbm

    def get_box_volume_cbm(self, obj):
        return obj.box_volume_cbm

    def get_calculated_box_weight(self, obj):
        return obj.calculated_box_weight_kg


class ProductSerializer(serializers.ModelSerializer):
    # Вкладений серіалізатор (read_only — тільки для читання)
    category_name = serializers.CharField(
        source="category.name_category",
        read_only=True,
    )
    logistics = ProductLogisticsSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id_product",
            "name_product",
            "category",
            "category_name",
            "description",
            "is_active",
            "logistics",
            "created_at",
            "updated_at",
        ]
