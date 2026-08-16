from rest_framework.routers import DefaultRouter

from .views import WaybillRecordViewSet

router = DefaultRouter()
router.register(r"waybill-records", WaybillRecordViewSet, basename="waybill-records")

urlpatterns = router.urls
