from rest_framework import serializers
from .models import WaybillRecord

class WaybillRecordSerializer(serializers.ModelSerializer):
    # Property з моделі (quantity < 0) — треба задекларувати явно,
    # ModelSerializer сам бачить тільки поля БД, не @property.
    is_return = serializers.BooleanField(read_only=True)

    class Meta:
        model = WaybillRecord
        fields = [
            "id",
            "legal_entity",
            "waybill_number",
            "waybill_date",
            "line_position",
            "customer",
            "customer_name",
            "store",
            "product",
            "product_name",
            "quantity",
            "price_uah",
            "total_uah",
            "comment",
            "total_weight_kg",
            "total_volume_cbm",
            "volumetric_weight_kg",
            "delivery_channel",
            "is_return",
            "imported_at",
            "import_batch_id"
        ]
        read_only_fields = ["imported_at"]
