# Vehicle Cost Tracker — Mock дані

> **Оновлено 2026-08-24.** Первинний план описував 15 mock-файлів
> (окремо customers/stores/products/monthly-costs/hired-trips/
> carrier-shipments/carrier-costs...). У реальному
> `vehicle_cost_tracker/src/mocks/` існує лише **4 файли**:
> `cars.json`, `drivers.json`, `route-events.json`, `waybills.json` —
> рівно ті сутності, чиї сторінки вже реально написані (Фаза 11 і 13
> `CODING_GUIDE.md`). Решту не створювали, бо відповідних сторінок ще
> нема — мокати дані під ненаписаний UI сенсу не було.

---

## `cars.json` (реальний вміст)

```json
[
  { "idCar": 1, "nameCar": "Citroen Jumpy",     "numberCar": "KA0458MХ", "amountCar": 24987, "defaultTrackingMode": "full",  "statusCar": "active", "isActive": true },
  { "idCar": 2, "nameCar": "Renault Trafic",    "numberCar": "АІ8822СІ", "amountCar": 15000, "defaultTrackingMode": "full",  "statusCar": "active", "isActive": true },
  { "idCar": 3, "nameCar": "DAF XF 460",        "numberCar": "КА2579НС", "amountCar": 29400, "defaultTrackingMode": "daily", "statusCar": "active", "isActive": true },
  { "idCar": 4, "nameCar": "MAN TGL 12.220",    "numberCar": "KA8634MO", "amountCar": 40600, "defaultTrackingMode": "daily", "statusCar": "active", "isActive": true }
]
```

> Без `fuelCardNumber`/`specs`/`trailer` — ці поля реальний `Car`-тип
> має (`03_TYPESCRIPT_TYPES.md`), але mock їх не заповнює (усі —
> опційні, `mapCar()` в `api/cars.ts` коректно обробляє відсутність).

## `drivers.json` (реальний вміст)

```json
[
  { "idDriver": 1, "nameDriver": "Акулов Олександр",              "phoneDriver": "+380980122469", "idCar": 1, "isActive": true },
  { "idDriver": 2, "nameDriver": "Піндюр Валентин",                "phoneDriver": "+380963990001", "idCar": 2, "isActive": true },
  { "idDriver": 3, "nameDriver": "Стужнєв Ігор Вікторович",        "phoneDriver": "+380676206282", "idCar": 3, "isActive": true },
  { "idDriver": 4, "nameDriver": "Гусєв Андрій Анатолійович",      "phoneDriver": "+380675071743", "idCar": 4, "isActive": true }
]
```

Поле в типі — `phoneDriver` (не `phone`, як був первинний план) і
`driversLicense` (опційне, у mock не заповнено).

## `route-events.json`, `waybills.json`

Реально існують, структура відповідає поточним `RouteEvent`/
`WaybillRecord`/`WaybillSummary` з `03_TYPESCRIPT_TYPES.md` — не
дублюю вміст тут (файли достатньо великі й змінюються частіше за цей
документ; дивись безпосередньо `src/mocks/*.json`, якщо потрібні
приклади).

---

## Чого немає (первинний план очікував, не створено)

`product-categories.json`, `products.json`, `product-logistics.json`,
`customers.json`, `stores.json`, `store-delivery-addresses.json`,
`monthly-costs.json`, `hired-trips.json`, `hired-trip-waybills.json`,
`carrier-shipments.json`, `carrier-waybills.json`, `carrier-costs.json`.

Створювати варто безпосередньо перед сторінкою, яка їх реально
споживатиме (Фаза 16, Крок 12-14 "Що далі" в `CODING_GUIDE.md`) — не
наперед, за первинним планом.

---

## Маппінг колонок CSV 1С → система

> **Замінено реальним дослідженням** — первинний план описував
> єдиний, простий формат (`юридична особа`, `дата`, `номер`, ...), що
> виявилось невірним: РУБІН, ЄСП і ОПТ мають **різні** формати
> вивантаження (CSV vs XLS, різні назви колонок, різна структура).
> Повний, перевірений на реальних файлах маппінг — тепер тільки в
> `task_description/IMPORT_1C_SPEC.md` (не дублюється тут, щоб не
> розходитись у двох місцях одночасно — той файл ще й активно
> оновлюється відповідями користувача).

## Маппінг реєстру НП / Міст Експрес → `carrier_costs`

Ще не досліджено на реальних файлах (на відміну від реєстру
накладних) — first-cut з первинного плану лишається орієнтиром, поки
не з'являться реальні зразки файлів:

| CSV | Поле |
|-----|------|
| `ТТН` або `№ відправлення` | `ttn` |
| `Дата` | `costDate` |
| `Вага` | `weightKg` |
| `Вартість` | `costUah` |
