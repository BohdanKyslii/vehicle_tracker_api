from django.db import transaction
from django.utils import timezone

from .importers.base import ParsedRow
from .matching import MatchingCache
from .models import WaybillRecord


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
                customer = cache.get_or_create_rubin_customer(row.customer_id, row.customer_name)
                store = cache.get_or_create_rubin_store(customer, row.store_name)
            else:
                customer, store = cache.get_or_create_esp_opt_point(legal_entity, row.store_name)

            records.append(WaybillRecord(
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
            ))

        WaybillRecord.objects.bulk_create(records)

    return {
        "batch_id": batch_id,
        "imported": len(records),
        "deleted": deleted,
        "dates": [d.isoformat() for d in dates],
    }
