from rest_framework import serializers

from .models import WaybillRecord


class WaybillRecordSerializer(serializers.ModelSerializer):
    # Property з моделі (quantity < 0) — треба задекларувати явно,
    # ModelSerializer сам бачить тільки поля БД, не @property.
    is_return = serializers.BooleanField(read_only=True)
    assigned_car_number = serializers.CharField(
        source="assigned_car.number_car", read_only=True, default=None
    )

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
            "assigned_car",
            "assigned_car_number",
            "hired_car_number",
            "carrier_ttn",
            "is_return",
            "imported_at",
            "import_batch_id",
        ]
        read_only_fields = ["imported_at"]
