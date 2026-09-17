from django.db.models import Q
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
    def missing_logistics_for_own(self, request):
        """
        GET /api/products/missing_logistics_for_own/ — товари без ваги
        (ProductLogistics.unit_weight_kg), які фігурують хоча б в одній
        накладній каналу "own" (тобто вже реально возились власним
        авто). Для аналітики "вартість доставки vs вага/об'єм" ці
        товари треба заповнити вручну — нема жодної формули, яка б їх
        вивела (importing.py свідомо не вигадує коефіцієнт об'єм→вага).
        Тимчасовий read-only ендпоінт — прибрати після використання.
        """
        products = (
            Product.objects.filter(waybill_records__delivery_channel="own")
            .filter(Q(logistics__isnull=True) | Q(logistics__unit_weight_kg__isnull=True))
            .select_related("category", "logistics")
            .distinct()
            .order_by("name_product")
        )
        data = [
            {
                "id_product": p.id_product,
                "name_product": p.name_product,
                "category_name": p.category.name_category if p.category else "",
                "unit_weight_kg": p.logistics.unit_weight_kg if p.logistics else None,
                "unit_length_cm": p.logistics.unit_length_cm if p.logistics else None,
                "unit_width_cm": p.logistics.unit_width_cm if p.logistics else None,
                "unit_height_cm": p.logistics.unit_height_cm if p.logistics else None,
                "units_per_box": p.logistics.units_per_box if p.logistics else None,
            }
            for p in products
        ]
        return Response({"count": len(data), "products": data})
