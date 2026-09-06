from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass
class ParsedRow:
    """
        Один рядок накладної, уже приведений до спільного вигляду —
        незалежно від того, з якого файлу (РУБІН CSV чи ЄСП/ОПТ XLS) він
        прийшов. customer_id заповнений лише для РУБІН (там є реальний
        1С-ID клієнта); для ЄСП/ОПТ = None — там клієнта як такого немає
        (Q2), клієнтом/магазином виступає сама точка (store_name).
        """

    legal_entity: str
    waybill_number: str
    waybill_date: date
    line_position: int
    customer_id: Optional[int]
    customer_name: str
    store_name: str
    product_articl: int
    product_name: str
    quantity: Decimal
    price_uah: Decimal
    total_uah: Decimal
    comment: str = ""

@dataclass
class RowError:
    """Рядок, який не вдалось розпізнати — не зупиняє весь імпорт."""

    row: int
    field: str
    message: str


class HeaderMismatchError(Exception):
    """
    Заголовок файлу не збігається з очікуваним — рішення 2/11 плану:
    краще гучно впасти з точним переліком розбіжності, ніж тихо
    змапити не ту колонку не туди.
    """

    def __init__(self, expected: list[str], actual: list[str]):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Очікувані колонки: {expected}. Отримані: {actual}")
