from rest_framework import serializers

from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)

class HiredTripWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiredTripWaybill
        fields = ["id", "waybill_number"]

class HiredTransportTripSerializer(serializers.ModelSerializer):
    waybills = HiredTripWaybillSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = HiredTransportTrip
        fields = [
            "id",
            "car_number",
            "route_name",
            "trip_date",
            "pallets_count",
            "cost_uah",
            "comment",
            "waybills",
            "created_at",
        ]
        read_only_fields = ["created_at"]

class CarrierShipmentWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierShipmentWaybill
        fields = ["id", "waybill_number"]

class CarrierShipmentSerializer(serializers.ModelSerializer):
    waybills = CarrierShipmentWaybillSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = CarrierShipment
        fields = [
            "id",
            "carrier",
            "ttn",
            "shipment_date",
            "waybills",
            "created_at",
        ]
        read_only_fields = ["created_at"]

class CarrierCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierCost
        fields = [
            "id",
            "shipment",
            "ttn",
            "weight_kg",
            "cost_uah",
            "cost_date",
            "imported_at",
        ]
        read_only_fields = ["shipment", "imported_at"]
