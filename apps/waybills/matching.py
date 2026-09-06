from django.db.models import Max

from apps.customers.models import Customer, Store
from apps.products.models import Product

# Синтетичні ID стартують високо, щоб гарантовано не перетнутись із
# реальними 1С-ID (у переглянутих зразках — 3-6-значні).
SYNTHETIC_ID_START = 900_000_000


class MatchingCache:
    """
    Кеш на час одного імпорту (одного HTTP-запиту): уникає повторних
    SELECT для того самого клієнта/магазину/товару в межах тисяч рядків
    одного файлу, і видає синтетичні ID без запиту до БД на кожен рядок
    (лічильник рахується один раз при першому створенні).
    """

    def __init__(self):
        self._customers: dict = {}
        self._stores: dict = {}
        self._products: dict = {}
        self._next_customer_id: int | None = None
        self._next_store_id: int | None = None

    def _alloc_customer_id(self) -> int:
        if self._next_customer_id is None:
            current = Customer.objects.filter(
                id_customer__gte=SYNTHETIC_ID_START
            ).aggregate(m=Max("id_customer"))["m"]
            self._next_customer_id = (current or SYNTHETIC_ID_START - 1) + 1
        value = self._next_customer_id
        self._next_customer_id += 1
        return value

    def _alloc_store_id(self) -> int:
        if self._next_store_id is None:
            current = Store.objects.filter(
                id_store__gte=SYNTHETIC_ID_START
            ).aggregate(m=Max("id_store"))["m"]
            self._next_store_id = (current or SYNTHETIC_ID_START - 1) + 1
        value = self._next_store_id
        self._next_store_id += 1
        return value

    def get_or_create_product(self, articl: int, name: str) -> Product:
        if articl in self._products:
            return self._products[articl]
        product, _ = Product.objects.get_or_create(
            id_product=articl,
            defaults={"name_product": name},
        )
        self._products[articl] = product
        return product

    def get_or_create_rubin_customer(self, customer_id: int, name: str) -> Customer:
        """РУБІН має реальний 1С customer_id — синтетичний тут не треба."""
        if customer_id in self._customers:
            return self._customers[customer_id]
        customer, _ = Customer.objects.get_or_create(
            id_customer=customer_id,
            defaults={"name_customer": name},
        )
        self._customers[customer_id] = customer
        return customer

    def get_or_create_rubin_store(self, customer: Customer, address: str) -> Store:
        """
        store_address — вільний текст без 1С-ID (§2 спеку). Синтетичний
        Store замість store=null+текст у comment (рішення 6 плану) —
        дає фільтрацію по точках ціною можливих дублікатів, якщо адреса
        трохи відрізняється тиждень до тижня (нема fuzzy-дедуплікації).
        """
        key = (customer.pk, address)
        if key in self._stores:
            return self._stores[key]
        store = Store.objects.filter(customer=customer, store_address=address).first()
        if store is None:
            store = Store.objects.create(
                id_store=self._alloc_store_id(),
                customer=customer,
                name_store=address,
                store_address=address,
            )
        self._stores[key] = store
        return store

    def get_or_create_esp_opt_point(self, legal_entity: str, name_store: str) -> tuple[Customer, Store]:
        """
        ЄСП/ОПТ не мають окремого клієнта у файлі (Q2) — точка одночасно
        і "клієнт", і "магазин". Один "парасольковий" Customer на
        юрособу (напр. "Точки ESP"), під ним — Store на кожну унікальну
        точку з файлу.
        """
        umbrella_name = f"Точки {legal_entity}"
        customer = self._customers.get(umbrella_name)
        if customer is None:
            customer = Customer.objects.filter(name_customer=umbrella_name).first()
            if customer is None:
                customer = Customer.objects.create(
                    id_customer=self._alloc_customer_id(),
                    name_customer=umbrella_name,
                )
            self._customers[umbrella_name] = customer

        key = (customer.pk, name_store)
        store = self._stores.get(key)
        if store is None:
            store = Store.objects.filter(customer=customer, name_store=name_store).first()
            if store is None:
                store = Store.objects.create(
                    id_store=self._alloc_store_id(),
                    customer=customer,
                    name_store=name_store,
                )
            self._stores[key] = store
        return customer, store
