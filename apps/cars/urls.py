from rest_framework.routers import DefaultRouter

from .views import CarViewSet, DriverViewSet, MonthlyCostsViewSet, RouteEventViewSet

# Router автоматично генерує всі URL для ViewSet
router = DefaultRouter()
router.register(r"cars", CarViewSet, basename="cars")
router.register(r"drivers", DriverViewSet, basename="drivers")
router.register(r"route-events", RouteEventViewSet, basename="route-events")
router.register(r"monthly-costs", MonthlyCostsViewSet, basename="monthly-costs")

urlpatterns = router.urls
