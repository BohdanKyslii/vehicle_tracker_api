from rest_framework import serializers

from .models import Customer, Store, StoreDeliveryAddress

class StoreDeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreDeliveryAddress
        fields = [
            "id",
            "store",
            "delivery_address",
            "is_primary",
            "notes",
            "created_at"
        ]
        read_only_fields = ["created_at"]

class StoreSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name_customer",
        read_only=True,
    )

    # related_name="delivery_addresses" на StoreDeliveryAddress.store — DRF сам робить JOIN
    delivery_addresses = StoreDeliveryAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Store
        fields = [
            "id_store",
            "customer_name",
            "delivery_addresses",
            "customer",
            "name_store",
            "store_address",
            "is_active",
            "updated_at",
        ]

class CustomerSerializer(serializers.ModelSerializer):
    # SerializerMethodField — скільки магазинів у клієнта (для списку клієнтів)
    stores_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id_customer",
            "name_customer",
            "network_customer",
            "is_active",
            "stores_count",
            "created_at",
            "updated_at",
        ]

    def get_stores_count(self, obj) -> int:
        return obj.stores.count()
