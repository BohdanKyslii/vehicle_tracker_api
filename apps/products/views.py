import calendar
from datetime import date

from django.db.models import Count, Q
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrHead

from .models import Product, ProductCategory
from .serializers import ProductCategorySerializer, ProductSerializer

WRITE_ACTIONS = ["create", "update", "partial_update", "destroy"]


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """CRUD для категорій товарів (з ієрархією parent/children)."""

    queryset = ProductCategory.objects.select_related("parent").all()
    serializer_class = ProductCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name_category"]
    ordering_fields = ["name_category"]
    ordering = ["name_category"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("root") == "true":
            qs = qs.filter(parent_isnull=True)
        return qs

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — довідникові дані, /panel (head)."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD для товарів, разом із вкладеною логістикою (вага/габарити)."""

    queryset = Product.objects.select_related("category", "logistics").all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["id_product", "name_product"]
    ordering_fields = ["name_product", "id_product"]
    ordering = ["name_product"]

    def get_queryset(self):
        """Фільтрація по категорії і активності."""
        qs = super().get_queryset()
        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — довідникові дані, /panel (head)."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def delivered_in_month(self, request):
        """
        GET /api/products/delivered_in_month/?month=2026-08 — унікальні
        товари з накладних ЗА ЦЕЙ МІСЯЦЬ, яким уже призначено канал
        доставки (будь-який — own/hired/carrier, не лише own), разом із
        поточним станом їхньої логістики (вага/габарити) — щоб на
        сторінці "Доставлені товари" (Адміністрування) можна було
        звірити й дозаповнювати каталог поступово, а не всі товари одразу.
        Сортування — від найчастіше відвантажуваних (lines_count), щоб
        спершу заповнювались товари з найбільшим впливом на аналітику.
        """
        month = request.query_params.get("month")
        if not month:
            return Response(
                {"error": "Параметр 'month' обов'язковий (напр. 2026-08)"}, status=400
            )
        try:
            year, mon = (int(part) for part in month.split("-"))
            date_from = date(year, mon, 1)
            date_to = date(year, mon, calendar.monthrange(year, mon)[1])
        except (ValueError, TypeError):
            return Response(
                {"error": "Невірний формат 'month', очікується YYYY-MM"}, status=400
            )

        match = Q(
            waybill_records__delivery_channel__isnull=False,
            waybill_records__waybill_date__gte=date_from,
            waybill_records__waybill_date__lte=date_to,
        )
        products = (
            Product.objects.filter(match)
            .select_related("category", "logistics")
            .annotate(lines_count=Count("waybill_records", filter=match))
            .distinct()
            .order_by("-lines_count", "name_product")
        )

        data = []
        for p in products:
            # Reverse OneToOne (Product -> ProductLogistics) кидає
            # RelatedObjectDoesNotExist при доступі, якщо рядка нема —
            # getattr із дефолтом ловить це (той самий гачок, що вже
            # був у видаленому missing_logistics_for_own).
            logistics = getattr(p, "logistics", None)
            data.append(
                {
                    "id_product": p.id_product,
                    "name_product": p.name_product,
                    "category_name": p.category.name_category if p.category else "",
                    "lines_count": p.lines_count,
                    "unit_weight_kg": logistics.unit_weight_kg if logistics else None,
                    "unit_length_cm": logistics.unit_length_cm if logistics else None,
                    "unit_width_cm": logistics.unit_width_cm if logistics else None,
                    "unit_height_cm": logistics.unit_height_cm if logistics else None,
                    "units_per_box": logistics.units_per_box if logistics else None,
                }
            )
        return Response({"count": len(data), "products": data})
