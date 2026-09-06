import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .base import HeaderMismatchError, ParsedRow, RowError

# Порядок і назви колонок — з розбору файлу (IMPORT_1C_SPEC.md, §2)
REQUIRED_COLUMNS = [
    "customer_id", "customer_name", "date", "invoice_number", "line_number",
    "store_address", "product_id", "product_articl", "product_name",
    "quantity", "price_invoice", "line_total", "comment", "contract_name",
    "doc_type",
]


def _invoice_number_digits(raw: str) -> str:
    """
    'РБН00008425' -> '8425' — тільки цифри, провідні нулі ЗНИКАЮТЬ.
    Не довільний вибір: звірено з src/utils/parseQR.ts фронтенду, який
    парсить QR, що сканує водій ('7908:03.08.26' — без нулів). Якщо
    тут лишити нулі — RouteEvent.waybill_number (водій) і
    WaybillRecord.waybill_number (імпорт) ніколи не зматчаться.
    """
    digits = "".join(ch for ch in raw if ch.isdigit())
    return str(int(digits)) if digits else ""


def parse_rubin_csv(file_obj) -> tuple[list[ParsedRow], list[RowError]]:
    """
    file_obj — бінарний файловий об'єкт (наприклад, upload.file із
    Django UploadedFile). Кодування cp1251 — обгортаємо в текстовий
    режим тут, а не просимо виклик передавати вже декодований текст.
    """
    text_stream = io.TextIOWrapper(file_obj, encoding="cp1251", newline="")
    reader = csv.DictReader(text_stream, delimiter=";")

    header = reader.fieldnames or []
    if header != REQUIRED_COLUMNS:
        raise HeaderMismatchError(REQUIRED_COLUMNS, header)

    rows: list[ParsedRow] = []
    errors: list[RowError] = []

    for i, raw in enumerate(reader, start=2):  # рядок 1 — заголовок
        try:
            waybill_number = _invoice_number_digits(raw["invoice_number"])
            if not waybill_number:
                errors.append(RowError(i, "invoice_number", "Не знайдено номера накладної"))
                continue

            rows.append(ParsedRow(
                legal_entity="Rubin",
                waybill_number=waybill_number,
                waybill_date=datetime.strptime(raw["date"].strip(), "%Y-%m-%d").date(),
                line_position=int(float(raw["line_number"])),
                customer_id=int(raw["customer_id"]),
                customer_name=raw["customer_name"].strip(),
                store_name=raw["store_address"].strip(),
                product_articl=int(raw["product_articl"]),
                product_name=raw["product_name"].strip(),
                # quantity: + відвантаження, - повернення (Q7 — можливе саме тут)
                quantity=Decimal(raw["quantity"]),
                price_uah=Decimal(raw["price_invoice"]),
                total_uah=Decimal(raw["line_total"]),
                comment=(raw.get("comment") or "").strip(),
            ))
        except (ValueError, InvalidOperation, KeyError) as exc:
            errors.append(RowError(i, "-", f"Не вдалось розпарсити рядок: {exc}"))

    return rows, errors
