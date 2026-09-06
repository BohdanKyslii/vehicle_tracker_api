from datetime import datetime
from decimal import Decimal, InvalidOperation

import xlrd

from .base import HeaderMismatchError, ParsedRow, RowError

# Оригінальні 13 колонок (IMPORT_1C_SPEC.md, §3) + "АЗС" — новий
# стовпець, який ІТ додали за домовленістю (Q2), бо "Магазин" — це
# склад-відправник, а не отримувач. Перевірено 2026-08-30 напряму
# xlrd-читанням оновленого файлу (`documents/file_1C/Переміщення зі
# складів на АЗС.xls`, фронтенд-репо, з'явився того ж дня): колонка
# називається саме "АЗС" (значення на кшталт "АЗС Киев Богатирская"),
# НЕ "name_store", як спершу назвали в IMPORT_1C_SPEC.md Q2 (там був
# лише опис по суті, не буквальний заголовок стовпця) — 5-та позиція
# підтвердилась.
EXPECTED_HEADER = [
    "№", "Магазин", "ДатаДок", "Докум", "АЗС", "Категория",
    "Код", "Товар", "Количество", "ЦенаВх", "СуммаВх", "СуммаР",
    "КоличВупак", "Вес",
]


def _doc_number(raw: str) -> str:
    """
    'ПеремМежМагазРасх 0000401034' -> '0000401034' — хвостовий числовий
    токен, провідні нулі ЗБЕРІГАЮТЬСЯ (на відміну від РУБІН). Звірено з
    src/utils/parseQR.ts: '0000391877:06.07.26' — водій сканує саме з
    нулями для цього каналу.
    """
    return raw.strip().split()[-1]


def _to_decimal(value) -> Decimal:
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    return Decimal(str(value).strip().replace(",", "."))


def parse_esp_opt_xls(file_obj, legal_entity: str) -> tuple[list[ParsedRow], list[RowError]]:
    """
    file_obj — бінарний файловий об'єкт. xlrd читає весь файл у
    пам'ять одразу (`file_contents=...`) — прийнятно для очікуваних
    2000-4000 рядків/тиждень (Q12), про фонову задачу можна подумати
    пізніше, якщо обсяг суттєво зросте.
    """
    book = xlrd.open_workbook(file_contents=file_obj.read())
    sheet = book.sheet_by_index(0)

    # Рядок 0 — службовий ("Печать таблицы значений"), рядок 1 — заголовок
    header = [str(c).strip() for c in sheet.row_values(1)]
    col = {name: idx for idx, name in enumerate(header)}
    missing = [name for name in EXPECTED_HEADER if name not in col]
    if missing:
        raise HeaderMismatchError(EXPECTED_HEADER, header)

    rows: list[ParsedRow] = []
    errors: list[RowError] = []

    for i in range(2, sheet.nrows):
        values = sheet.row_values(i)

        # Службові рядки (наприклад "ИТОГО:") детектимо НЕ по тексту,
        # а по тому, що обов'язкові числові колонки не парсяться —
        # ловить будь-який подібний рядок, не тільки цей один (Q5).
        try:
            articl = int(_to_decimal(values[col["Код"]]))
            quantity = _to_decimal(values[col["Количество"]])
        except (InvalidOperation, ValueError, IndexError):
            continue

        try:
            waybill_date = datetime.strptime(
                str(values[col["ДатаДок"]]).strip(), "%d.%m.%y"
            ).date()  # Q6: '26' завжди означає 2026, без винятків

            store_name = str(values[col["АЗС"]]).strip()

            rows.append(ParsedRow(
                legal_entity=legal_entity,
                waybill_number=_doc_number(str(values[col["Докум"]])),
                waybill_date=waybill_date,
                line_position=i,  # унікальний в межах файлу — досить для unique_together
                customer_id=None,  # немає окремого клієнта в цьому каналі (Q2)
                customer_name=store_name,
                store_name=store_name,
                product_articl=articl,
                product_name=str(values[col["Товар"]]).strip(),
                quantity=quantity,
                # total_uah = СуммаВх (собівартість), НЕ СуммаР (роздрібна) — Q4.
                # Побічний ефект: аналітика "% від суми продажу" для цього
                # каналу фактично рахуватиме "% від собівартості" — не
                # виправляємо тут, зафіксовано в IMPORT_1C_SPEC.md/плані.
                price_uah=_to_decimal(values[col["ЦенаВх"]]),
                total_uah=_to_decimal(values[col["СуммаВх"]]),
            ))
        except (ValueError, InvalidOperation, IndexError) as exc:
            errors.append(RowError(i + 1, "-", f"Не вдалось розпарсити рядок: {exc}"))

    return rows, errors
