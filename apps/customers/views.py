from rest_framework import viewsets, filters

from .models import Customer, Store, StoreDeliveryAddress
from .serializers import CustomerSerializer, StoreSerializer, StoreDeliveryAddressSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.prefetch_related("store").all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "name_customer",
        "network_customer",
    ]
    ordering_fields = [
        "name_customer",
        "network_customer",
    ]
    ordering = [
        "name_customer",
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.select_related("customer").prefetch_related("delivery_address").all()
    serializer_class = StoreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "name_store",
        "store_address"
    ]

    def get_queryset(self):
        """?customer_id=... — магазини конкретного клієнта."""
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs

class StoreDeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = StoreDeliveryAddress.objects.select_related("store").all()
    serializer_class = StoreDeliveryAddressSerializer

    def get_queryset(self):
        """?store_id=... — адреси конкретного магазину."""
        qs = super().get_queryset()
        store_id = self.request.query_params.get("store_id")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs
