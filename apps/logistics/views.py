from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Max, Min, Sum
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


def link_orphan_costs(shipment):
    """Прив'язує до відправлення витрати з його ТТН, що прийшли раніше за нього."""
    CarrierCost.objects.filter(ttn=shipment.ttn, shipment__isnull=True).update(
        shipment=shipment
    )


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

    def perform_create(self, serializer):
        """Вартість могла прийти раніше за відправлення — підхоплюємо її по ТТН."""
        link_orphan_costs(serializer.save())

    def perform_update(self, serializer):
        """Змінили ТТН — підхоплюємо вартість, що прийшла раніше під новим номером."""
        link_orphan_costs(serializer.save())

    def perform_destroy(self, instance):
        """
        Прив'язки накладних видаляються каскадом — знімаємо канал "carrier"
        з накладних, які після цього не лишились у жодній ТТН (як detach_waybill).
        """
        numbers = list(instance.waybills.values_list("waybill_number", flat=True))
        with transaction.atomic():
            instance.delete()
            still_linked = set(
                CarrierShipmentWaybill.objects.filter(
                    waybill_number__in=numbers
                ).values_list("waybill_number", flat=True)
            )
            WaybillRecord.objects.filter(
                waybill_number__in=set(numbers) - still_linked,
                delivery_channel=WaybillRecord.DeliveryChannel.CARRIER,
            ).update(delivery_channel=None)

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
                if created:
                    link_orphan_costs(shipment)
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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsManagerOrHead],
    )
    def detach_waybill(self, request, pk=None):
        """
        POST /api/carrier-shipments/{id}/detach_waybill/ — {"waybill_number": "..."}
        Відкріплює накладну від ТТН. Якщо накладна більше не входить у жодне
        відправлення служби доставки — знімає з неї канал "carrier", щоб її
        можна було призначити іншому каналу.
        """
        shipment = self.get_object()
        waybill_number = request.data.get("waybill_number")
        link = shipment.waybills.filter(waybill_number=waybill_number).first()
        if not link:
            return Response(
                {"error": "Накладна не прив'язана до цього відправлення"},
                status=404,
            )
        with transaction.atomic():
            link.delete()
            if not CarrierShipmentWaybill.objects.filter(
                waybill_number=waybill_number
            ).exists():
                WaybillRecord.objects.filter(
                    waybill_number=waybill_number,
                    delivery_channel=WaybillRecord.DeliveryChannel.CARRIER,
                ).update(delivery_channel=None)
        return Response(CarrierShipmentSerializer(shipment).data)

    @action(detail=False, methods=["get"])
    def review(self, request):
        """
        GET /api/carrier-shipments/review/?carrier=&date_from=&date_to=
        Звірка відправлень служби доставки (/analytics/carriers): кожна ТТН
        з вартістю (CarrierCost) і накладними, збагаченими даними з 1С
        (WaybillRecord) та списком інших ТТН з тією ж накладною. Кілька
        запитів на весь період замість N+1 на кожне відправлення.
        """
        shipments = CarrierShipment.objects.all()
        carrier = request.query_params.get("carrier")
        if carrier:
            shipments = shipments.filter(carrier=carrier)
        for param, lookup in (("date_from", "gte"), ("date_to", "lte")):
            value = request.query_params.get(param)
            if value:
                try:
                    parsed = parse_date(value)
                except ValueError:
                    parsed = None
                if not parsed:
                    return Response({"error": f"Некоректна дата {param}"}, status=400)
                shipments = shipments.filter(**{f"shipment_date__{lookup}": parsed})
        shipments = (
            shipments.annotate(
                cost_uah=Sum("costs__cost_uah"),
                cost_weight_kg=Sum("costs__weight_kg"),
                costs_count=Count("costs"),
            )
            .prefetch_related("waybills")
            .order_by("shipment_date", "ttn")
        )
        shipments = list(shipments)
        numbers = {w.waybill_number for s in shipments for w in s.waybills.all()}

        records = {}
        rows = (
            WaybillRecord.objects.filter(waybill_number__in=numbers)
            .values("waybill_number", "legal_entity")
            .annotate(
                total_uah=Sum("total_uah"),
                waybill_date=Min("waybill_date"),
                customer_name=Max("customer_name"),
                delivery_channel=Max("delivery_channel"),
                car_number=Max("assigned_car__number_car"),
            )
        )
        for row in rows:
            records.setdefault(row["waybill_number"], []).append(row)

        ttns_by_number = {}
        links = CarrierShipmentWaybill.objects.filter(
            waybill_number__in=numbers
        ).values_list("waybill_number", "shipment_id", "shipment__ttn")
        for number, shipment_id, ttn in links:
            ttns_by_number.setdefault(number, []).append((shipment_id, ttn))

        def waybill_data(shipment, link):
            matches = records.get(link.waybill_number, [])
            first = matches[0] if matches else {}
            return {
                "id": link.id,
                "waybill_number": link.waybill_number,
                "found": bool(matches),
                "legal_entities": [m["legal_entity"] for m in matches],
                "customer_name": first.get("customer_name"),
                "waybill_date": first.get("waybill_date"),
                "total_uah": sum((m["total_uah"] or 0) for m in matches),
                "delivery_channel": first.get("delivery_channel"),
                "car_number": first.get("car_number"),
                "other_ttns": [
                    ttn
                    for sid, ttn in ttns_by_number.get(link.waybill_number, [])
                    if sid != shipment.id
                ],
            }

        return Response(
            [
                {
                    "id": s.id,
                    "carrier": s.carrier,
                    "ttn": s.ttn,
                    "shipment_date": s.shipment_date,
                    "cost_uah": s.cost_uah,
                    "cost_weight_kg": s.cost_weight_kg,
                    "costs_count": s.costs_count,
                    "waybills": [waybill_data(s, w) for w in s.waybills.all()],
                }
                for s in shipments
            ]
        )


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

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsManagerOrHead],
    )
    def bulk_import(self, request):
        """
        POST /api/carrier-costs/bulk_import/ — вартість з реєстру служби доставки:
        {"costs": [{"ttn": "...", "cost_date": "YYYY-MM-DD",
                    "cost_uah": "110.50", "weight_kg": "0.50"}, ...]}

        Ідемпотентний: ТТН, для якої вартість уже є, пропускається — той
        самий звіт можна залити повторно (на відміну від create, який
        завжди додає). Відправлення з такою ТТН лінкується одразу; якщо
        його ще нема — підхопиться при створенні (link_orphan_costs).
        """
        items = request.data.get("costs")
        if not isinstance(items, list) or not items:
            return Response({"error": "costs має бути непорожнім списком"}, status=400)
        if len(items) > BULK_IMPORT_MAX:
            return Response(
                {"error": f"Не більше {BULK_IMPORT_MAX} рядків за один запит"},
                status=400,
            )

        ttns = {str(i.get("ttn") or "").strip() for i in items}
        existing = set(
            CarrierCost.objects.filter(ttn__in=ttns).values_list("ttn", flat=True)
        )
        shipments = dict(
            CarrierShipment.objects.filter(ttn__in=ttns).values_list("ttn", "id")
        )
        result = {"created": 0, "linked": 0, "skipped_existing": 0, "errors": []}
        new_costs = []
        for item in items:
            ttn = str(item.get("ttn") or "").strip()
            if ttn in existing:
                result["skipped_existing"] += 1
                continue
            try:
                cost_date = parse_date(str(item.get("cost_date") or ""))
                cost_uah = Decimal(str(item.get("cost_uah")))
                weight_kg = Decimal(str(item.get("weight_kg")))
            except (ValueError, InvalidOperation):
                cost_date = None
            if (
                not ttn
                or not cost_date
                or not cost_uah.is_finite()
                or not weight_kg.is_finite()
            ):
                result["errors"].append(
                    {"ttn": ttn, "message": "Некоректні ТТН, дата, вартість чи вага"}
                )
                continue
            existing.add(ttn)  # дубль ТТН у самому файлі — беремо перший рядок
            new_costs.append(
                CarrierCost(
                    ttn=ttn,
                    cost_date=cost_date,
                    cost_uah=cost_uah,
                    weight_kg=weight_kg,
                    shipment_id=shipments.get(ttn),
                )
            )
        CarrierCost.objects.bulk_create(new_costs)
        result["created"] = len(new_costs)
        result["linked"] = sum(1 for c in new_costs if c.shipment_id)
        return Response(result)
