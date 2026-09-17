from django.db.models import Case, Count, DecimalField, Q, Sum, Value, When
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsLogistOrAbove, IsManagerOrHeadOnly
from apps.cars.models import Car

from .importers.base import HeaderMismatchError
from .importers.esp_opt_xls import parse_esp_opt_xls
from .importers.rubin_csv import parse_rubin_csv
from .importing import import_waybills
from .models import WaybillRecord
from .serializers import WaybillRecordSerializer

WRITE_ACTIONS = ["create", "update", "partial_update", "destroy"]

# Суми відвантажень і повернень (quantity зі знаком) — рахуються за
# одним проходом Sum(Case(...)) замість двох окремих .filter().aggregate(),
# щоб .values().annotate() лишався однією GROUP BY-агрегацією.
# Функції, а НЕ модульні константи: Django-вирази мутують свій внутрішній
# стан при resolve_expression() (перше ж використання псує їх для
# наступного запиту — "is an aggregate" на другому виклику) — кожен
# виклик summary() мусить отримати свіжий екземпляр.
_MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)
_QTY_FIELD = DecimalField(max_digits=10, decimal_places=3)


def _shipment_total():
    return Sum(
        Case(
            When(quantity__gt=0, then="total_uah"),
            default=Value(0),
            output_field=_MONEY_FIELD,
        )
    )


def _return_total():
    return Sum(
        Case(
            When(quantity__lt=0, then="total_uah"),
            default=Value(0),
            output_field=_MONEY_FIELD,
        )
    )


def _shipped_qty_total():
    """Сума кількості лише по рядках-відвантаженнях (quantity > 0) — для аналітики."""
    return Sum(
        Case(
            When(quantity__gt=0, then="quantity"),
            default=Value(0),
            output_field=_QTY_FIELD,
        )
    )


ORDER_FIELD_MAP = {
    "date": "waybill_date",
    "-date": "-waybill_date",
    "total": "shipped_uah",
    "-total": "-shipped_uah",
    "customer": "customer_name",
    "-customer": "-customer_name",
    "weight": "weight_kg_sum",
    "-weight": "-weight_kg_sum",
    "waybill_number": "waybill_number",
    "-waybill_number": "-waybill_number",
}


class WaybillRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD для реєстру накладних (рядки, імпортовані з 1С).
    Додатковий endpoint: /api/waybill-records/{id}/assign_channel/
    """

    queryset = WaybillRecord.objects.select_related("customer", "store", "product").all()
    serializer_class = WaybillRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["waybill_number", "customer_name", "product_name"]
    ordering_fields = ["waybill_number", "waybill_date", "total_uah"]
    ordering = ["-waybill_date", "waybill_number"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки manager/head (не logist)."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHeadOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Фільтри: клієнт, товар, юрособа, канал доставки, діапазон дат."""
        qs = super().get_queryset()
        params = self.request.query_params

        customer_id = params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        product_id = params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)

        legal_entity = params.get("legal_entity")
        if legal_entity:
            qs = qs.filter(legal_entity=legal_entity)

        delivery_channel = params.get("delivery_channel")
        if delivery_channel:
            qs = qs.filter(delivery_channel=delivery_channel)

        date_from = params.get("date_from")
        if date_from:
            qs = qs.filter(waybill_date__gte=date_from)

        date_to = params.get("date_to")
        if date_to:
            qs = qs.filter(waybill_date__lte=date_to)

        return qs

    @action(detail=False, methods=["get"])
    def unassigned(self, request):
        """GET /api/waybill-records/unassigned/ — рядки без каналу доставки."""
        qs = self.get_queryset().filter(delivery_channel__isnull=True)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        GET /api/waybill-records/summary/ — реєстр, агрегований по
        НАКЛАДНІЙ (один рядок відповіді = вся накладна, не одна товарна
        позиція, на відміну від list/). Причина, чому це окремий екшн, а
        не /list/: DRF ModelSerializer працює з інстансами моделі,
        .values().annotate() повертає прості dict — простіше не
        намагатись впхнути агрегацію в серіалізатор.

        Фільтри: search (номер накладної/клієнт), legal_entity,
        delivery_channel (+ спецзначення "unassigned"), line_type
        (shipment/return — по агрегованій сумі, не по окремому рядку),
        date_from/date_to, status (pending/scanned — похідне від
        delivery_channel; "delivered"/"cancelled" нема чим підкріпити на
        бекенді зараз, тому ігноруються), ordering (date/total/customer/
        weight, з "-" для спадання).
        """
        qs = WaybillRecord.objects.all()
        params = request.query_params

        legal_entity = params.get("legal_entity")
        if legal_entity:
            qs = qs.filter(legal_entity=legal_entity)

        date_from = params.get("date_from")
        if date_from:
            qs = qs.filter(waybill_date__gte=date_from)

        date_to = params.get("date_to")
        if date_to:
            qs = qs.filter(waybill_date__lte=date_to)

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(waybill_number__icontains=search) | Q(customer_name__icontains=search)
            )

        delivery_channel = params.get("delivery_channel")
        if delivery_channel == "unassigned":
            qs = qs.filter(delivery_channel__isnull=True)
        elif delivery_channel:
            qs = qs.filter(delivery_channel=delivery_channel)

        status_param = params.get("status")
        if status_param == "pending":
            qs = qs.filter(delivery_channel__isnull=True)
        elif status_param == "scanned":
            qs = qs.filter(delivery_channel__isnull=False)

        grouped = qs.values(
            "waybill_number",
            "waybill_date",
            "legal_entity",
            "customer",
            "customer_name",
            "store",
            "delivery_channel",
            "assigned_car",
            "assigned_car__number_car",
            "hired_car_number",
            "carrier_ttn",
        )
        # Аліаси НЕ мають збігатись з реальними іменами полів моделі
        # (total_uah/total_weight_kg вже існують на WaybillRecord) —
        # інакше .annotate() плутає посилання на "своє ж" ім'я всередині
        # Case(then="total_uah") із щойно оголошуваною анотацією і падає
        # з "FieldError: ... is an aggregate".
        grouped = grouped.annotate(
            lines_count=Count("id"),
            shipped_uah=_shipment_total(),
            returned_uah=_return_total(),
            shipped_qty=_shipped_qty_total(),
            weight_kg_sum=Sum("total_weight_kg"),
        )

        line_type = params.get("line_type")
        if line_type == "shipment":
            grouped = grouped.filter(shipped_uah__gt=0)
        elif line_type == "return":
            grouped = grouped.filter(returned_uah__lt=0)

        order_field = ORDER_FIELD_MAP.get(params.get("ordering"), "-waybill_date")
        grouped = grouped.order_by(order_field, "waybill_number")

        page = self.paginate_queryset(grouped)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(list(grouped))

    @action(
        detail=False, methods=["get"], url_path=r"by-number/(?P<waybill_number>[^/]+)"
    )
    def by_number(self, request, waybill_number=None):
        """
        GET /api/waybill-records/by-number/<номер>/ — усі товарні рядки
        цієї накладної. Окремий екшн, а не звичайний detail-retrieve:
        waybill_number НЕ первинний ключ і не унікальний сам по собі
        (унікальний ключ — waybill_number+line_position, кілька рядків
        на одну накладну — це нормальний випадок, не виняток).
        """
        records = (
            WaybillRecord.objects.filter(waybill_number=waybill_number)
            .select_related("customer", "store", "product", "assigned_car")
            .order_by("line_position")
        )
        if not records.exists():
            return Response({"error": "Накладну не знайдено"}, status=404)
        return Response(WaybillRecordSerializer(records, many=True).data)

    @action(
        detail=False,
        methods=["post"],
        url_path=r"by-number/(?P<waybill_number>[^/]+)/assign-channel",
        permission_classes=[IsAuthenticated, IsLogistOrAbove],
    )
    def assign_channel_by_number(self, request, waybill_number=None):
        """
        POST /api/waybill-records/by-number/<номер>/assign-channel/ —
        {"delivery_channel": "own"|"hired"|"carrier",
         "assigned_car"?: <id Car>, "hired_car_number"?: "...",
         "carrier_ttn"?: "..."}.
        Той самий принцип, що attach_waybill у apps.logistics
        (HiredTransportTripViewSet/CarrierShipmentViewSet): виставляє
        канал одразу на ВСІ рядки накладної (bulk update), не на одну
        товарну позицію, як assign_channel(pk) вище. Ексклюзивність —
        та сама вимога: раз призначений канал змінити вже не можна.
        """
        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        if not records.exists():
            return Response({"error": "Накладну не знайдено"}, status=404)
        if records.exclude(delivery_channel__isnull=True).exists():
            return Response({"error": "Канал доставки вже призначений"}, status=400)

        channel = request.data.get("delivery_channel")
        if channel not in [c.value for c in WaybillRecord.DeliveryChannel]:
            return Response({"error": "Невірний канал доставки"}, status=400)

        update_fields = {"delivery_channel": channel}
        if channel == WaybillRecord.DeliveryChannel.OWN:
            car_id = request.data.get("assigned_car")
            if not car_id or not Car.objects.filter(pk=car_id).exists():
                return Response({"error": "Оберіть авто"}, status=400)
            update_fields["assigned_car_id"] = car_id
        elif channel == WaybillRecord.DeliveryChannel.HIRED:
            car_number = (request.data.get("hired_car_number") or "").strip()
            if not car_number:
                return Response({"error": "Вкажіть номер авто"}, status=400)
            update_fields["hired_car_number"] = car_number
        elif channel == WaybillRecord.DeliveryChannel.CARRIER:
            ttn = (request.data.get("carrier_ttn") or "").strip()
            if not ttn:
                return Response({"error": "Вкажіть номер ТТН"}, status=400)
            update_fields["carrier_ttn"] = ttn

        records.update(**update_fields)
        updated = (
            WaybillRecord.objects.filter(waybill_number=waybill_number)
            .select_related("customer", "store", "product", "assigned_car")
            .order_by("line_position")
        )
        return Response(WaybillRecordSerializer(updated, many=True).data)

    @action(detail=True, methods=["post"])
    def assign_channel(self, request, pk=None):
        """
        POST /api/waybill-records/{id}/assign_channel/ — {"delivery_channel": "own"}
        Канал можна призначити лише один раз — ексклюзивність каналів
        це критична бізнес-вимога (див. task_description/STATE.md).
        """
        record = self.get_object()
        channel = request.data.get("delivery_channel")

        if channel not in [c.value for c in WaybillRecord.DeliveryChannel]:
            return Response({"error": "Невірний канал доставки"}, status=400)
        if record.delivery_channel:
            return Response({"error": "Канал доставки вже призначений"}, status=400)

        record.delivery_channel = channel
        record.save()
        return Response(WaybillRecordSerializer(record).data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsManagerOrHeadOnly],
        parser_classes=[MultiPartParser, FormParser],
    )
    def import_file(self, request):
        """
        POST /api/waybill-records/import_file/ — multipart/form-data:
        {legal_entity: "Rubin"|"ESP"|"OPT", file: <.csv|.xls>}.
        Юрособу завжди обирає менеджер явно (Q8) — бекенд не вгадує її
        з вмісту файлу.
        """
        legal_entity = request.data.get("legal_entity")
        upload = request.FILES.get("file")

        if legal_entity not in [c.value for c in WaybillRecord.LegalEntity]:
            return Response({"error": "Невірна юридична особа"}, status=400)
        if not upload:
            return Response({"error": "Файл обов'язковий"}, status=400)

        try:
            if legal_entity == WaybillRecord.LegalEntity.RUBIN:
                rows, errors = parse_rubin_csv(upload.file)
            else:
                rows, errors = parse_esp_opt_xls(upload, legal_entity)
        except HeaderMismatchError as exc:
            return Response(
                {
                    "error": "Формат файлу не відповідає очікуваному",
                    "expected": exc.expected,
                    "actual": exc.actual,
                },
                status=400,
            )

        if not rows:
            return Response(
                {
                    "error": "Жодного рядка не вдалось розпізнати",
                    "errors": [
                        {"row": e.row, "field": e.field, "message": e.message}
                        for e in errors
                    ],
                },
                status=400,
            )

        result = import_waybills(legal_entity, rows)
        result["errors"] = [
            {"row": e.row, "field": e.field, "message": e.message} for e in errors
        ]
        return Response(result, status=201)
