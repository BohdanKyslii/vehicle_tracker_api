from django.contrib import admin

from .models import Car, CarSpecs, CarStatusLog, Driver, MonthlyCosts, RouteEvent, Trailer


class CarSpecsInline(admin.StackedInline):
    model = CarSpecs
    extra = 0


class TrailerInline(admin.StackedInline):
    model = Trailer
    extra = 0


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        "number_car",
        "name_car",
        "status_car",
        "default_tracking_mode",
        "is_active",
    ]
    list_filter = ["status_car", "default_tracking_mode", "is_active"]
    search_fields = ["name_car", "number_car", "fuel_card_number"]
    inlines = [CarSpecsInline, TrailerInline]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["name_driver", "car", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name_driver", "phone"]


@admin.register(CarStatusLog)
class CarStatusLogAdmin(admin.ModelAdmin):
    list_filter = ["car", "status", "changed_at", "changed_by"]
    readonly_fields = ["changed_at"]


@admin.register(RouteEvent)
class RouteEventAdmin(admin.ModelAdmin):
    list_display = ["car", "driver", "event_type", "event_ts", "odometer_km"]
    list_filter = ["event_type", "tracking_mode"]
    search_fields = ["car__number_car", "waybill_number"]
    date_hierarchy = "event_ts"


@admin.register(MonthlyCosts)
class MonthlyCostsAdmin(admin.ModelAdmin):
    list_display = ["car", "month", "salary_uah", "depreciation_uah", "repair_actual_uah"]
    list_filter = ["month"]
