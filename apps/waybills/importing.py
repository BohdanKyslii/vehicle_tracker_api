from django.db import transaction
from django.utils import timezone

from apps.cars.models import RouteEvent

from .importers.base import ParsedRow
from .matching import MatchingCache
from .models import WaybillRecord


def link_own_channel_from_scans(waybill_numbers: set[str], legal_entity: str) -> int:
    """
    Автопризначення каналу "own" за вже наявними сканами водіїв.

    Порядок подій у цьому бізнесі ЗВОРОТНИЙ до того, що можна було б
    очікувати: водій сканує накладну щодня одразу як забирає товар
    (створюючи RouteEvent із waybill_number), а WaybillRecord
    з'являється в БД лише коли менеджер довантажить реєстр із 1С —
    раз на 2-4 тижні. Тобто на момент скану WaybillRecord ще не існує
    (призначити канал одразу неможливо), а на момент імпорту скан уже
    ДАВНО існує. Тому лінкування робимо тут — одразу після імпорту,
    зіставляючи щойно створені WaybillRecord з уже наявними сканами.

    Не займає накладні, яким канал уже призначено (ручний assign-channel
    або попередній лінк) — той самий принцип ексклюзивності, що й
    скрізь у apps.waybills/apps.logistics.
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

    linked = 0
    for number, car_id in car_by_number.items():
        linked += WaybillRecord.objects.filter(
            legal_entity=legal_entity,
            waybill_number=number,
            delivery_channel__isnull=True,
        ).update(
            delivery_channel=WaybillRecord.DeliveryChannel.OWN, assigned_car_id=car_id
        )

    return linked


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

        linked = link_own_channel_from_scans(
            {row.waybill_number for row in rows},
            legal_entity,
        )

    return {
        "batch_id": batch_id,
        "imported": len(records),
        "deleted": deleted,
        "dates": [d.isoformat() for d in dates],
        "linked_to_own_channel": linked,
    }
