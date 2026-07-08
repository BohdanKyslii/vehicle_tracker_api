# Vehicle Cost Tracker — Mock дані (v3)

---

## `cars.json`

```json
[
  {
    "idCar": 1, "nameCar": "Mercedes Sprinter 315 CDI",
    "numberCar": "АА1234ВВ", "amountCar": 8333,
    "defaultTrackingMode": "full", "statusCar": "active", "isActive": true
  },
  {
    "idCar": 2, "nameCar": "Volkswagen Crafter 35",
    "numberCar": "АА5678СС", "amountCar": 10417,
    "defaultTrackingMode": "daily", "statusCar": "active", "isActive": true
  },
  {
    "idCar": 3, "nameCar": "Ford Transit 350",
    "numberCar": "АА9012КК", "amountCar": 6806,
    "defaultTrackingMode": "daily", "statusCar": "repair", "isActive": true
  }
]
```

---

## `drivers.json`

```json
[
  { "idDriver": 1, "nameDriver": "Коваленко Іван Петрович",     "phone": "+380501234567", "idCar": 1, "isActive": true },
  { "idDriver": 2, "nameDriver": "Мельник Сергій Олексійович",  "phone": "+380677654321", "idCar": 2, "isActive": true },
  { "idDriver": 3, "nameDriver": "Бондаренко Олег Миколайович", "phone": "+380639876543", "idCar": 3, "isActive": true }
]
```

---

## `customers.json`

```json
[
  { "idCustomer": "C001", "nameCustomer": "ТОВ Сонячна торгівля",   "networkCustomer": "Роздріб", "isActive": true },
  { "idCustomer": "C002", "nameCustomer": "ФОП Петренко В.М.",       "networkCustomer": "Роздріб", "isActive": true },
  { "idCustomer": "C003", "nameCustomer": "Мережа Зоряний",          "networkCustomer": "Мережа",  "isActive": true },
  { "idCustomer": "C004", "nameCustomer": "ТОВ Смак України",        "networkCustomer": "HoReCa",  "isActive": true },
  { "idCustomer": "C005", "nameCustomer": "Супермаркет АТБ №312",    "networkCustomer": "Мережа",  "isActive": true }
]
```

---

## `stores.json`

```json
[
  { "idStore": "S001", "idCustomer": "C001", "nameStore": "Магазин Сонячний на Хрещатику",   "storeAddress": "вул. Хрещатик, 10, Київ", "isActive": true },
  { "idStore": "S002", "idCustomer": "C001", "nameStore": "Магазин Сонячний на Льва Толстого", "storeAddress": "вул. Льва Толстого, 5, Київ", "isActive": true },
  { "idStore": "S003", "idCustomer": "C003", "nameStore": "Зоряний Полтава",                   "storeAddress": "вул. Соборності, 12, Полтава", "isActive": true },
  { "idStore": "S004", "idCustomer": "C003", "nameStore": "Зоряний Харків",                    "storeAddress": "пр. Науки, 45, Харків", "isActive": true },
  { "idStore": "S005", "idCustomer": "C005", "nameStore": "АТБ Пирятин",                       "storeAddress": "вул. Центральна, 1, Пирятин", "isActive": true }
]
```

---

## `store-delivery-addresses.json`

```json
[
  { "id": 1, "idStore": "S001", "deliveryAddress": "вул. Хрещатик, 10, вхід з боку двору", "isPrimary": true,  "notes": null },
  { "id": 2, "idStore": "S001", "deliveryAddress": "вул. Хрещатик, 10, склад (підвал)",    "isPrimary": false, "notes": "Тільки до 10:00" },
  { "id": 3, "idStore": "S003", "deliveryAddress": "вул. Соборності, 12, вантажний в'їзд", "isPrimary": true,  "notes": null }
]
```

---

## `route-events.json` (скорочено)

```json
[
  // Авто 1 (full), 2026-06-27 — з palletsCount ──────────────────
  {
    "id": 1, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "depot_start", "eventTs": "2026-06-27T07:45:00+03:00",
    "odometerKm": 87450, "palletsCount": null
  },
  {
    "id": 2, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "delivery", "eventTs": "2026-06-27T09:30:00+03:00",
    "odometerKm": 87523, "palletsCount": 3,
    "waybillNumber": "НН-000101", "waybillDate": "2026-06-27",
    "customerName": "ТОВ Сонячна торгівля", "rejectionFull": false
  },
  {
    "id": 3, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "delivery", "eventTs": "2026-06-27T11:15:00+03:00",
    "odometerKm": 87561, "palletsCount": 2,
    "waybillNumber": "НН-000102", "waybillDate": "2026-06-27",
    "customerName": "ФОП Петренко В.М.",
    "rejectionFull": false,
    "rejectionProductId": "P004", "rejectionQty": 24,
    "rejectionComment": "Відмовились від пива"
  },
  {
    "id": 4, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "refuel", "eventTs": "2026-06-27T12:00:00+03:00",
    "fuelLiters": 55.4, "fuelCostUah": 3158.0,
    "adBlueLiters": 2.0, "adBlueCostUah": 90.0
  },
  {
    "id": 5, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "return_goods", "eventTs": "2026-06-27T13:00:00+03:00",
    "returnClientWaybill": "НН-000098"
  },
  {
    "id": 6, "carId": 1, "driverId": 1, "trackingMode": "full",
    "eventType": "parking_end", "eventTs": "2026-06-27T17:30:00+03:00",
    "odometerKm": 87648
  },

  // Авто 2 (daily, вніс палети), 2026-06-28 ──────────────────────
  {
    "id": 7, "carId": 2, "driverId": 2, "trackingMode": "daily",
    "eventType": "depot_start", "eventTs": "2026-06-28T08:00:00+03:00",
    "odometerKm": 54478, "palletsCount": 6,
    "notes": "НН-000204, НН-000205, НН-000206 — на різні магазини"
  }
]
```

---

## `waybills.json` (скорочено — різні канали)

```json
[
  // own — відскановано водієм авто 1 ─────────────────────────────
  {
    "id": 1, "legalEntity": "Rubin",
    "waybillNumber": "НН-000101", "waybillDate": "2026-06-27", "linePosition": 1,
    "customerId": "C001", "customerName": "ТОВ Сонячна торгівля",
    "storeId": "S001", "productId": "P001", "productName": "Вино Ркацителі 0.75л",
    "quantity": 60, "priceUah": 145.00, "totalUah": 8700.00,
    "totalWeightKg": 90.0, "totalVolumeCbm": 0.072,
    "deliveryChannel": "own", "status": "delivered"
  },

  // hired — прив'язана до рейсу найманого транспорту ──────────────
  {
    "id": 5, "legalEntity": "ESP",
    "waybillNumber": "НН-000201", "waybillDate": "2026-06-27", "linePosition": 1,
    "customerId": "C003", "customerName": "Мережа Зоряний",
    "storeId": "S003", "productId": "P003", "productName": "Горілка Хортиця 0.5л",
    "quantity": 240, "priceUah": 210.00, "totalUah": 50400.00,
    "totalWeightKg": 156.0, "totalVolumeCbm": 0.080,
    "deliveryChannel": "hired", "status": "delivered"
  },

  // carrier — відправлена Новою Поштою ───────────────────────────
  {
    "id": 9, "legalEntity": "OPT",
    "waybillNumber": "НН-000301", "waybillDate": "2026-06-28", "linePosition": 1,
    "customerId": "C002", "customerName": "ФОП Петренко В.М.",
    "storeId": null, "productId": "P005", "productName": "Коньяк Тиса 0.5л",
    "quantity": 12, "priceUah": 385.00, "totalUah": 4620.00,
    "totalWeightKg": 9.0, "totalVolumeCbm": 0.008,
    "deliveryChannel": "carrier", "status": "delivered"
  },

  // unassigned — ще не призначено ────────────────────────────────
  {
    "id": 12, "legalEntity": "Rubin",
    "waybillNumber": "НН-000401", "waybillDate": "2026-06-29", "linePosition": 1,
    "customerId": "C005", "customerName": "Супермаркет АТБ №312",
    "storeId": "S005", "productId": "P004", "productName": "Пиво Чернігівське 0.5л",
    "quantity": 480, "priceUah": 42.00, "totalUah": 20160.00,
    "deliveryChannel": null, "status": "pending"
  },

  // Повернення (quantity < 0) ──────────────────────────────────────
  {
    "id": 15, "legalEntity": "Rubin",
    "waybillNumber": "НН-000098-Р", "waybillDate": "2026-06-27", "linePosition": 1,
    "customerId": "C001", "customerName": "ТОВ Сонячна торгівля",
    "storeId": "S001", "productId": "P002", "productName": "Вино Аліготе 0.75л",
    "quantity": -12, "priceUah": 132.00, "totalUah": -1584.00,
    "comment": "НН-000088", "deliveryChannel": "own", "status": "delivered"
  }
]
```

---

## `hired-trips.json`

```json
[
  {
    "id": 1,
    "carNumber": "ВВ1111АА",
    "routeName": "Пирятин, Полтава, Харків",
    "tripDate": "2026-06-27",
    "palletsCount": 8,
    "costUah": 4500.00,
    "comment": "Перевізник ТОВ Транслог",
    "createdAt": "2026-06-27T09:00:00+03:00"
  },
  {
    "id": 2,
    "carNumber": "КК2222ВВ",
    "routeName": "Суми, Конотоп",
    "tripDate": "2026-06-28",
    "palletsCount": 5,
    "costUah": 2800.00,
    "comment": null,
    "createdAt": "2026-06-28T10:00:00+03:00"
  }
]
```

---

## `hired-trip-waybills.json`

```json
[
  { "id": 1, "tripId": 1, "waybillNumber": "НН-000201", "scannedAt": "2026-06-27T09:05:00+03:00" },
  { "id": 2, "tripId": 1, "waybillNumber": "НН-000202", "scannedAt": "2026-06-27T09:06:00+03:00" },
  { "id": 3, "tripId": 1, "waybillNumber": "НН-000203", "scannedAt": "2026-06-27T09:07:00+03:00" },
  { "id": 4, "tripId": 2, "waybillNumber": "НН-000204", "scannedAt": "2026-06-28T10:05:00+03:00" }
]
```

---

## `carrier-shipments.json`

```json
[
  {
    "id": 1, "carrierName": "Нова Пошта",
    "ttn": "59001234567890", "shipmentDate": "2026-06-28", "comment": null,
    "createdAt": "2026-06-28T11:00:00+03:00"
  },
  {
    "id": 2, "carrierName": "Міст Експрес",
    "ttn": "МЕ-0012345", "shipmentDate": "2026-06-28", "comment": "Термінова",
    "createdAt": "2026-06-28T12:00:00+03:00"
  }
]
```

---

## `carrier-costs.json`

```json
[
  {
    "id": 1, "shipmentId": 1, "carrierName": "Нова Пошта",
    "ttn": "59001234567890", "costDate": "2026-06-29",
    "weightKg": 9.0, "costUah": 145.00,
    "importBatchId": "np-2026-06-29", "importedAt": "2026-06-29T09:00:00+03:00"
  },
  {
    "id": 2, "shipmentId": 2, "carrierName": "Міст Експрес",
    "ttn": "МЕ-0012345", "costDate": "2026-06-29",
    "weightKg": 5.5, "costUah": 120.00,
    "importBatchId": "me-2026-06-29", "importedAt": "2026-06-29T09:30:00+03:00"
  }
]
```

---

## `monthly-costs.json`

```json
[
  {
    "id": 1, "carId": 1, "month": "2026-06-01",
    "salaryUah": 25000, "taxesUah": 5500,
    "depreciationUah": 8333,
    "repairActualUah": null, "repairRateUahKm": 2.00,
    "otherCostsUah": 1200, "otherCostsComment": "Штраф за паркування"
  },
  {
    "id": 2, "carId": 2, "month": "2026-06-01",
    "salaryUah": 22000, "taxesUah": 4840,
    "depreciationUah": 10417,
    "repairActualUah": 3500, "repairRateUahKm": 2.00,
    "otherCostsUah": 800, "otherCostsComment": "Заміна гальмівних колодок"
  }
]
```

---

## Маппінг колонок CSV 1С → система

| CSV | Поле | Примітка |
|-----|------|---------|
| `юридична особа` | `legalEntity` | ESP / OPT / Rubin |
| `дата` | `waybillDate` | DD.MM.YYYY |
| `номер` | `waybillNumber` | |
| `клієнт id` | `customerId` | |
| `торгова точка id` | `storeId` | новий ключ |
| `артикул` | `productId` | |
| `кількість` | `quantity` | < 0 = повернення |
| `ціна` | `priceUah` | |
| `сума` | `totalUah` | |
| `позиція` | `linePosition` | |
| `коментар` | `comment` | для повернень = накладна клієнта |

## Маппінг реєстру НП / Міст Експрес → `carrier_costs`

| CSV | Поле |
|-----|------|
| `ТТН` або `№ відправлення` | `ttn` |
| `Дата` | `costDate` |
| `Вага` | `weightKg` |
| `Вартість` | `costUah` |
