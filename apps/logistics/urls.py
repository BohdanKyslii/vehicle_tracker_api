from rest_framework.routers import DefaultRouter

from .views import CarrierCostViewSet, CarrierShipmentViewSet, HiredTransportTripViewSet

router = DefaultRouter()
router.register(r"hired-transport-trips", HiredTransportTripViewSet, basename="hired-transport-trips")
router.register(r"carrier-shipments", CarrierShipmentViewSet, basename="carrier-shipments")
router.register(r"carrier-costs", CarrierCostViewSet, basename="carrier-costs")

urlpatterns = router.urls
