from rest_framework import viewsets, filters
from unicodedata import category

from .models import Product, ProductCategory
from .serializers import ProductSerializer, ProductCategorySerializer

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

class ProductViewSet(viewsets.ModelViewSet):
    """CRUD для товарів. Логістика — вкладено (read_only) через ProductSerializer."""

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
