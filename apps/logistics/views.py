from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsLogistOrAbove, IsManagerOrHead
from apps.waybills.models import WaybillRecord
from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)
from .serializers import (
    CarrierCostSerializer,
    CarrierShipmentSerializer,
    HiredTransportTripSerializer,
)

WRITE_ACTIONS = ["create", "update", "partial_update", "destroy"]

class HiredTransportTripViewSet(viewsets.ModelViewSet):
    """
        CRUD для рейсів найманого транспорту (§5.3).
        Додатковий endpoint: /api/hired-transport-trips/{id}/attach_waybill/
        """

    queryset = HiredTransportTrip.objects.prefetch_related("waybills").all()
    serializer_class = HiredTransportTripSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["car_number", "route_name"]
    ordering_fields = ["trip_date", "cost_uah"]
    ordering = ["-trip_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки logist/manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsLogistOrAbove()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsLogistOrAbove])
    def attach_waybill(self, request, pk=None):
        """
                POST /api/hired-transport-trips/{id}/attach_waybill/ — {"waybill_number": "..."}
                Прив'язує накладну до рейсу й виставляє WaybillRecord.delivery_channel="hired".
                Ексклюзивність каналів — та сама вимога, що й у Кроці 8.5 (assign_channel).
                """
        trip = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response({
                "error": "waybill_number обов'язковий"},
                status=400,
            )

        if HiredTripWaybill.objects.filter(waybill_number=waybill_number).exists():
            return Response(
                {
                    "error": "Накладна вже прив'язана до рейсу найманого транспорту"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        already_other_channel = records.exclude(
            delivery_channel__in=[None, WaybillRecord.DeliveryChannel.HIRED]
        ).exists()
        if already_other_channel:
            return Response(
                {
                    "error": "Накладна вже призначена іншому каналу доставки"},
                status=400,
            )

        HiredTripWaybill.objects.create(trip=trip, waybill_number=waybill_number)
        records.update(delivery_channel=WaybillRecord.DeliveryChannel.HIRED)

        return Response(HiredTransportTripSerializer(trip).data)

class CarrierShipmentViewSet(viewsets.ModelViewSet):
    """
        CRUD для відправлень служб доставки (§5.4).
        Додатковий endpoint: /api/carrier-shipments/{id}/attach_waybill/
        """
    queryset = CarrierShipment.objects.prefetch_related("waybills", "costs").all()
    serializer_class = CarrierShipmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ttn"]
    ordering_fields = ["shipment_date"]
    ordering = ["-shipment_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"],
            permission_classes=[IsAuthenticated, IsManagerOrHead])
    def attach_waybill(self, request, pk=None):
        """
                POST /api/carrier-shipments/{id}/attach_waybill/ — {"waybill_number": "..."}
                Аналог attach_waybill у HiredTransportTripViewSet, тільки канал "carrier".
                """
        shipment = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response(
                {
                    "error": "waybill_number обов'язковий"},
                            status=400,
            )

        if CarrierShipmentWaybill.objects.filter(
                waybill_number=waybill_number).exists():
            return Response(
                {
                    "error": "Накладна вже прив'язана до відправлення служби доставки"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        already_other_channel = records.exclude(
            delivery_channel__in=[None, WaybillRecord.DeliveryChannel.CARRIER]
        ).exists()
        if already_other_channel:
            return Response(
                {
                    "error": "Накладна вже призначена іншому каналу доставки"},
                status=400,
            )

        CarrierShipmentWaybill.objects.create(shipment=shipment,
                                              waybill_number=waybill_number)
        records.update(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)

        return Response(CarrierShipmentSerializer(shipment).data)

class CarrierCostViewSet(viewsets.ModelViewSet):
    """Реєстр витрат від служб доставки (щотижневий імпорт, матчинг по ТТН)."""

    queryset = CarrierCost.objects.select_related("shipment").all()
    serializer_class = CarrierCostSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["cost_date"]
    ordering = ["-cost_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Матчинг по ТТН — якщо відправлення вже зареєстроване, лінкуємо автоматично."""
        ttn = serializer.validated_data.get("ttn")
        shipment = CarrierShipment.objects.filter(ttn=ttn).first()
        serializer.save(shipment=shipment)
