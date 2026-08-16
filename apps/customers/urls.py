from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, StoreDeliveryAddressViewSet, StoreViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"stores", StoreViewSet, basename="stores")
router.register(
    r"store-delivery-addresses", StoreDeliveryAddressViewSet, basename="store-delivery-addresses"
)

urlpatterns = router.urls
