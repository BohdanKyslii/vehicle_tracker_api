from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrHeadOnly
from .importers.base import HeaderMismatchError
from .importers.esp_opt_xls import parse_esp_opt_xls
from .importers.rubin_csv import parse_rubin_csv
from .importing import import_waybills
from .models import WaybillRecord
from .serializers import WaybillRecordSerializer

WRITE_ACTIONS = ["create", "update", "partial_update", "destroy"]

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
        detail=False, methods=["post"],
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
                    "errors": [{"row": e.row, "field": e.field, "message": e.message} for e in errors],
                },
                status=400,
            )

        result = import_waybills(legal_entity, rows)
        result["errors"] = [{"row": e.row, "field": e.field, "message": e.message} for e in errors]
        return Response(result, status=201)
