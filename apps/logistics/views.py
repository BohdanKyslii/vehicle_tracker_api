from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

# Ліміт на один запит bulk_import — фронт шле реєстр пачками
BULK_IMPORT_MAX = 500
CHANNEL_CONFLICT_ERROR = "Накладна вже призначена іншому каналу доставки"


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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsLogistOrAbove],
    )
    def attach_waybill(self, request, pk=None):
        """
        POST /api/hired-transport-trips/{id}/attach_waybill/ — {"waybill_number": "..."}
        Прив'язує накладну до рейсу й виставляє WaybillRecord.delivery_channel="hired".
        Ексклюзивність каналів — та сама вимога, що й у Кроці 8.5 (assign_channel).
        """
        trip = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response(
                {"error": "waybill_number обов'язковий"},
                status=400,
            )

        if HiredTripWaybill.objects.filter(waybill_number=waybill_number).exists():
            return Response(
                {"error": "Накладна вже прив'язана до рейсу найманого транспорту"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        # не exclude(delivery_channel__in=[None, ...]) — Django викидає None
        # з IN, і накладна без каналу хибно вважалась "іншим каналом"
        already_other_channel = (
            records.filter(delivery_channel__isnull=False)
            .exclude(delivery_channel=WaybillRecord.DeliveryChannel.HIRED)
            .exists()
        )
        if already_other_channel:
            return Response(
                {"error": "Накладна вже призначена іншому каналу доставки"},
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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsManagerOrHead],
    )
    def attach_waybill(self, request, pk=None):
        """
        POST /api/carrier-shipments/{id}/attach_waybill/ — {"waybill_number": "..."}
        Аналог attach_waybill у HiredTransportTripViewSet, тільки канал "carrier".
        """
        shipment = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response(
                {"error": "waybill_number обов'язковий"},
                status=400,
            )

        # Одна накладна може бути в кількох ТТН (посилка + зворотна доставка
        # документів) — забороняємо лише дубль у межах цього ж відправлення
        if shipment.waybills.filter(waybill_number=waybill_number).exists():
            return Response(
                {"error": "Накладна вже прив'язана до цього відправлення"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        # не exclude(delivery_channel__in=[None, ...]) — Django викидає None
        # з IN, і накладна без каналу хибно вважалась "іншим каналом"
        already_other_channel = (
            records.filter(delivery_channel__isnull=False)
            .exclude(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)
            .exists()
        )
        if already_other_channel:
            return Response(
                {"error": "Накладна вже призначена іншому каналу доставки"},
                status=400,
            )

        CarrierShipmentWaybill.objects.create(
            shipment=shipment, waybill_number=waybill_number
        )
        records.update(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)

        return Response(CarrierShipmentSerializer(shipment).data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsManagerOrHead],
    )
    def bulk_import(self, request):
        """
        POST /api/carrier-shipments/bulk_import/ — імпорт реєстру служби доставки:
        {"carrier": "nova_poshta",
         "shipments": [{"ttn": "...", "shipment_date": "YYYY-MM-DD",
                        "waybills": ["7770", ...]}, ...]}

        Ідемпотентний: існуюча ТТН не дублюється (до неї лише доприв'язуються
        відсутні накладні), вже прив'язана накладна пропускається — той самий
        реєстр можна залити повторно. Кожна ТТН — окрема транзакція, тож
        помилка в одному рядку не зупиняє решту. Ексклюзивність каналів — та
        сама, що в attach_waybill.
        """
        carrier = request.data.get("carrier")
        items = request.data.get("shipments")
        if carrier not in CarrierShipment.Carrier.values:
            return Response({"error": "Невідома служба доставки"}, status=400)
        if not isinstance(items, list) or not items:
            return Response(
                {"error": "shipments має бути непорожнім списком"}, status=400
            )
        if len(items) > BULK_IMPORT_MAX:
            return Response(
                {"error": f"Не більше {BULK_IMPORT_MAX} відправлень за один запит"},
                status=400,
            )

        result = {
            "created_shipments": 0,
            "existing_shipments": 0,
            "attached_waybills": 0,
            "skipped_waybills": 0,
            "errors": [],
        }
        for item in items:
            ttn = str(item.get("ttn") or "").strip()
            try:
                shipment_date = parse_date(str(item.get("shipment_date") or ""))
            except ValueError:  # формат вірний, але дата неіснуюча (2026-02-30)
                shipment_date = None
            waybills = [
                str(w).strip() for w in item.get("waybills") or [] if str(w).strip()
            ]
            if not ttn or not shipment_date:
                result["errors"].append(
                    {"ttn": ttn, "message": "Порожня ТТН або некоректна дата"}
                )
                continue

            with transaction.atomic():
                shipment, created = CarrierShipment.objects.get_or_create(
                    ttn=ttn,
                    defaults={"carrier": carrier, "shipment_date": shipment_date},
                )
                result["created_shipments" if created else "existing_shipments"] += 1

                attached = set(shipment.waybills.values_list("waybill_number", flat=True))
                for number in dict.fromkeys(waybills):
                    if number in attached:
                        result["skipped_waybills"] += 1
                        continue
                    records = WaybillRecord.objects.filter(waybill_number=number)
                    if (
                        records.filter(delivery_channel__isnull=False)
                        .exclude(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)
                        .exists()
                    ):
                        result["errors"].append(
                            {
                                "ttn": ttn,
                                "waybill_number": number,
                                "message": CHANNEL_CONFLICT_ERROR,
                            }
                        )
                        continue
                    CarrierShipmentWaybill.objects.create(
                        shipment=shipment, waybill_number=number
                    )
                    records.update(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)
                    result["attached_waybills"] += 1

        return Response(result)


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
