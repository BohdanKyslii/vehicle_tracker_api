from django.contrib import admin

from .models import Customer, Store, StoreDeliveryAddress


class StoreDeliveryAddressInLine(admin.TabularInline):
    """TabularInline = горизонтальне (таблиця) розташування."""

    model = StoreDeliveryAddress
    extra = 1


class StoreInline(admin.TabularInline):
    model = Store
    extra = 0
    show_change_link = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id_customer", "name_customer", "network_customer", "is_active")
    list_filter = ("is_active", "network_customer")
    search_fields = ("id_customer", "name_customer")
    inlines = [StoreInline]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id_store", "name_store", "customer", "is_active")
    list_filter = ("is_active", "customer")
    search_fields = ("id_store", "name_store")
    inlines = [StoreDeliveryAddressInLine]
