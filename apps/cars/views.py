from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Car, CarStatusLog, Driver, MonthlyCosts, RouteEvent
from .serializers import (
    CarSerializer,
    CarStatusLogSerializer,
    DriverSerializer,
    MonthlyCostsSerializer,
    RouteEventCreateSerializer,
    RouteEventSerializer,
)


class CarViewSet(viewsets.ModelViewSet):
    """
    CRUD для автопарку.
    Додатковий endpoint: /api/cars/{id}/status_logs/
    """

    queryset = Car.objects.select_related("specs", "trailer", "driver").all()
    serializer_class = CarSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number_car", "name_car", "fuel_card_number"]
    ordering_fields = ["number_car", "name_car", "status_car"]
    ordering = ["number_car"]

    def get_queryset(self):
        """Фільтрація по статусу і режиму трекінгу."""
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status_car=status_filter)
        mode = self.request.query_params.get("tracking_mode")
        if mode:
            qs = qs.filter(default_tracking_mode=mode)
        return qs

    # @action — додатковий endpoint на конкретне авто
    @action(detail=True, methods=["get"])
    def status_logs(self, request, pk=None):
        """GET /api/cars/{id}/status_logs/ — журнал статусів."""
        car = self.get_object()
        logs = car.status_logs.all()
        serializer = CarStatusLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """POST /api/cars/{id}/change_status/ — змінити статус."""
        car = self.get_object()
        new_status = request.data.get("status")
        reason = request.data.get("reason", "")

        if new_status not in [s.value for s in Car.Status]:
            return Response(
                {"error": "Невірний статус"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        car.status_car = new_status
        car.save()

        CarStatusLog.objects.create(
            car=car,
            status=new_status,
            reason=reason,
            changed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(CarSerializer(car).data)


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.select_related("car").all()
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["number_car", "phone"]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        GET /api/drivers/me/ — поточний водій.
        Поки повертає першого активного (до авторизації).
        """
        driver = Driver.objects.filter(is_active=True).first()
        if not driver:
            return Response(
                {"error": "Водія не знайдено"},
                status=404,
            )
        return Response(DriverSerializer(driver).data)


class RouteEventViewSet(viewsets.ModelViewSet):
    queryset = RouteEvent.objects.select_related("car", "driver").all()
    filter_backends = [filters.OrderingFilter]
    ordering = ["event_ts"]

    def get_serializer_class(self):
        """Різний серіалізатор для читання і запису."""
        if self.action in ["create", "update", "partial_update"]:
            return RouteEventCreateSerializer
        return RouteEventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        car_id = self.request.query_params.get("car_id")
        date = self.request.query_params.get("date")

        if car_id:
            qs = qs.filter(car__id=car_id)
        if date == "today":
            from django.utils import timezone

            today = timezone.localdate()
            qs = qs.filter(event_ts__date=today)
        elif date:
            qs = qs.filter(event_ts__date=date)

        return qs

    @action(detail=False, methods=["get"])
    def last_odometer(self, request):
        """GET /api/route-events/last_odometer/?car_id=1"""
        car_id = request.query_params.get("car_id")
        if not car_id:
            return Response(
                {"error": "car_id required"},
                status=400,
            )

        last = (
            RouteEvent.objects.filter(car_id=car_id, odometer_km__isnull=False)
            .order_by("-event_ts")
            .first()
        )

        return Response(
            {"odometer_km": last.odometer_km if last is not None else None},
        )


class MonthlyCostsViewSet(viewsets.ModelViewSet):
    queryset = MonthlyCosts.objects.select_related("car").all()
    serializer_class = MonthlyCostsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        car_id = self.request.query_params.get("car_id")
        month = self.request.query_params.get("month")
        if car_id:
            qs = qs.filter(car_id=car_id)
        if month:
            qs = qs.filter(month__startswith=month)
        return qs
