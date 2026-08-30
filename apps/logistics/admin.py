from django.contrib import admin

from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)

class HiredTripWaybillInLine(admin.TabularInline):
    model = HiredTripWaybill
    extra = 0

@admin.register(HiredTransportTrip)
class HiredTransportTripAdmin(admin.ModelAdmin):
    list_display = ["car_number", "route_name", "trip_date", "cost_uah"]
    list_filter = ["trip_date"]
    search_fields = ["car_number", "route_name"]
    inlines = [HiredTripWaybillInLine]

class CarrierShipmentWaybillInLine(admin.TabularInline):
    model = CarrierShipmentWaybill
    extra = 0

@admin.register(CarrierShipment)
class CarrierShipmentAdmin(admin.ModelAdmin):
    list_display = ["ttn", "carrier", "shipment_date"]
    list_filter = ["carrier", "shipment_date"]
    search_fields = ["ttn"]
    inlines = [CarrierShipmentWaybillInLine]

@admin.register(CarrierCost)
class CarrierCostAdmin(admin.ModelAdmin):
    list_display = ["ttn", "shipment", "weight_kg", "cost_uah", "cost_date"]
    list_filter = ["cost_date"]
    search_fields = ["ttn"]
