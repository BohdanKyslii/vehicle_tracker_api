from django.db import transaction
from django.utils import timezone

from apps.cars.models import RouteEvent

from .importers.base import ParsedRow
from .matching import MatchingCache
from .models import WaybillRecord


def link_waybill_to_own_channel(waybill_number: str, car_id: int) -> int:
    """
    Bulk-виставляє delivery_channel="own"+assigned_car на всі рядки
    цієї накладної, ЯКЩО їй ще не призначено канал (та сама
    ексклюзивність, що й скрізь у apps.waybills/apps.logistics). Не
    матчить по legal_entity — формати номерів (з нулями/без) уже й так
    розрізняють джерела, колізія між ними по суті неможлива.

    Спільна для ОБОХ напрямків гонитви скан↔імпорт (див.
    `link_own_channel_from_scans` і `apps.cars.views.RouteEventViewSet`):
    порядок подій у цьому бізнесі може бути будь-яким — здебільшого
    водій сканує ЩОДНЯ, а менеджер довантажує реєстр із 1С раз на
    2-4 тижні (скан раніше за WaybillRecord), але буває й навпаки
    (накладна вже імпортована, а скан водія прилітає пізніше/його
    правлять вручну в EventDetail/EventAdminForm).
    """
    if not waybill_number:
        return 0
    return WaybillRecord.objects.filter(
        waybill_number=waybill_number,
        delivery_channel__isnull=True,
    ).update(delivery_channel=WaybillRecord.DeliveryChannel.OWN, assigned_car_id=car_id)


def link_own_channel_from_scans(waybill_numbers: set[str]) -> int:
    """
    Автопризначення каналу "own" за вже наявними сканами водіїв —
    напрямок "скан був раніше за імпорт" (типовий випадок, викликається
    з `import_waybills` одразу після вставки нових рядків).
    """
    if not waybill_numbers:
        return 0

    scans = (
        RouteEvent.objects.filter(
            event_type=RouteEvent.EventType.DELIVERY,
            waybill_number__in=waybill_numbers,
        )
        .exclude(waybill_number="")
        .order_by("event_ts")
        .values_list("waybill_number", "car_id")
    )
    # Якщо номер сканували кілька разів (напр. кілька позицій в одну
    # зупинку) — беремо перше авто, з яким він зустрівся; на практиці
    # це те саме авто, бо один водій/авто веде один маршрут.
    car_by_number: dict[str, int] = {}
    for number, car_id in scans:
        car_by_number.setdefault(number, car_id)

    return sum(
        link_waybill_to_own_channel(number, car_id)
        for number, car_id in car_by_number.items()
    )


def import_waybills(legal_entity: str, rows: list[ParsedRow]) -> dict:
    """
    Перезаливка за датами з файлу (Q9): видаляє старі WaybillRecord
    ЦІЄЇ юрособи за ВСІ дати, що зустрічаються у rows, вставляє нові —
    одна транзакція. Решту історії (інші дати, інші юрособи) не чіпає.
    """
    batch_id = f"{legal_entity}_{timezone.now():%Y%m%d%H%M%S}"
    dates = sorted({row.waybill_date for row in rows})
    cache = MatchingCache()

    with transaction.atomic():
        deleted, _ = WaybillRecord.objects.filter(
            legal_entity=legal_entity,
            waybill_date__in=dates,
        ).delete()

        records = []
        for row in rows:
            product = cache.get_or_create_product(row.product_articl, row.product_name)

            if row.customer_id is not None:
                customer = cache.get_or_create_rubin_customer(
                    row.customer_id, row.customer_name
                )
                store = cache.get_or_create_rubin_store(customer, row.store_name)
            else:
                customer, store = cache.get_or_create_esp_opt_point(
                    legal_entity, row.store_name
                )

            records.append(
                WaybillRecord(
                    legal_entity=row.legal_entity,
                    waybill_number=row.waybill_number,
                    waybill_date=row.waybill_date,
                    line_position=row.line_position,
                    customer=customer,
                    customer_name=row.customer_name,
                    store=store,
                    product=product,
                    product_name=row.product_name,
                    quantity=row.quantity,
                    price_uah=row.price_uah,
                    total_uah=row.total_uah,
                    comment=row.comment,
                    import_batch_id=batch_id,
                    # total_weight_kg/total_volume_cbm/volumetric_weight_kg
                    # лишаються null — нема усталеної формули об'єм→вага в
                    # жодному з репо, не вигадуємо коефіцієнт (рішення 8).
                )
            )

        WaybillRecord.objects.bulk_create(records)

        linked = link_own_channel_from_scans({row.waybill_number for row in rows})

    return {
        "batch_id": batch_id,
        "imported": len(records),
        "deleted": deleted,
        "dates": [d.isoformat() for d in dates],
        "linked_to_own_channel": linked,
    }
