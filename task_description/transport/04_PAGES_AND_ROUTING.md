# Vehicle Cost Tracker — Сторінки та маршрутизація

---

## Структура маршрутів (React Router v6)

```tsx
<BrowserRouter>
  <Routes>
    {/* ── Водій (мобільний PWA) ─────────────────────── */}
    <Route path="/driver" element={<DriverLayout />}>
      <Route index element={<DriverDashboard />} />
      <Route path="event/new" element={<EventForm />} />
      <Route path="scan" element={<QRScanner />} />
      <Route path="history" element={<DriverHistory />} />
    </Route>

    {/* ── Автопарк ──────────────────────────────────── */}
    <Route path="/fleet" element={<MainLayout />}>
      <Route index element={<FleetList />} />
      <Route path=":carId" element={<CarDetail />} />
      <Route path=":carId/month/:month" element={<CarMonth />} />
    </Route>

    {/* ── Накладні ──────────────────────────────────── */}
    <Route path="/waybills" element={<MainLayout />}>
      <Route index element={<WaybillList />} />
      <Route path=":waybillNumber" element={<WaybillDetail />} />
      <Route path="import" element={<WaybillImport />} />
      <Route path="returns" element={<ReturnMatchingList />} />
      <Route path="unassigned" element={<UnassignedWaybills />} />
    </Route>

    {/* ── Найманий транспорт ─────────────────────────── */}
    <Route path="/hired" element={<MainLayout />}>
      <Route index element={<HiredTripList />} />
      <Route path="new" element={<HiredTripForm />} />
      <Route path=":tripId" element={<HiredTripDetail />} />
    </Route>

    {/* ── Служби доставки ────────────────────────────── */}
    <Route path="/carriers" element={<MainLayout />}>
      <Route index element={<CarrierShipmentList />} />
      <Route path="new" element={<CarrierShipmentForm />} />
      <Route path=":shipmentId" element={<CarrierShipmentDetail />} />
      <Route path="import-costs" element={<CarrierCostsImport />} />
    </Route>

    {/* ── Аналітика ─────────────────────────────────── */}
    <Route path="/analytics" element={<MainLayout />}>
      <Route index element={<AnalyticsDashboard />} />
      <Route path="transport-costs" element={<TransportCosts />} />
      <Route path="customers" element={<CustomerAnalytics />} />
      <Route path="channels" element={<ChannelComparison />} />
      <Route path="car/:carId" element={<CarAnalytics />} />
    </Route>

    {/* ── Адміністрування ───────────────────────────── */}
    <Route path="/admin" element={<MainLayout />}>
      <Route index element={<AdminDashboard />} />
      <Route path="cars" element={<CarAdmin />} />
      <Route path="drivers" element={<DriverAdmin />} />
      <Route path="products" element={<ProductAdmin />} />
      <Route path="customers" element={<CustomerAdmin />} />
      <Route path="stores" element={<StoreAdmin />} />
      <Route path="monthly-costs" element={<MonthlyCostsAdmin />} />
    </Route>

    <Route path="/" element={<Navigate to="/driver" replace />} />
    <Route path="*" element={<NotFound />} />
  </Routes>
</BrowserRouter>
```

---

## Сторінки детально

---

### `/driver` — DriverDashboard

**Що відображає:**
- Ім'я водія, авто (номер + назва), поточна дата
- `DayModeSwitch` — перемикач daily/full з дефолтом від логіста
- Поточний одометр
- Кнопки дій за режимом
- Timeline подій поточного дня (з іконками палет де є)
- FAB «Сканувати QR»

---

### `/driver/event/new` — EventForm

**Query param:** `?type=depot_start|delivery|refuel|...`

**Поля за типом події:**

| Тип | Режим | Поля |
|-----|-------|------|
| `depot_start` | daily | Одометр*, **Кількість палет***, накладні (QR-список)*, заправка (опц.), AdBlue (опц.), інші витрати (опц.), повернення (опц.), доп. вантаж (опц.) |
| `depot_start` | full | Одометр*, накладні (QR-список)* |
| `delivery` | full | Одометр*, **Кількість палет на точці***, QR накладної*, відмова (опц.) |
| `refuel` | обидва | Літри*, сума*, AdBlue л (опц.), AdBlue грн (опц.) |
| `other_cost` | обидва | Сума*, коментар* |
| `return_goods` | обидва | Номер накладної клієнта* |
| `extra_cargo` | обидва | Звідки*, куди*, вага*, накладна (опц.), коментар |
| `parking_end` | full | Одометр* |

**Логіка QR для `daily` depot_start:**
```
1. Сканування першої накладної
2. Система знаходить store_id → показує «Точка вивантаження: {name_store}»
3. «Це вірна точка? [Так / Ні]»
4. Підтверджено → продовжуємо сканування без запиту
5. Кожна наступна накладна приєднується до тієї ж точки або нової
```

**Перевірка ексклюзивності при скануванні:**
```typescript
// При додаванні накладної до списку
const check = await checkWaybillChannel(waybillNumber);
if (check.deliveryChannel !== null) {
  toast.error(`Накладна ${waybillNumber} вже призначена: ${check.deliveryChannel}`);
  return; // не додаємо
}
```

---

### `/driver/scan` — QRScanner

- Мульти-скан без закриття камери
- Для кожної відсканованої накладної: показати `customerName` + `storeName`
- При duplicate: попередження «Вже відскановано»
- При вже призначеній до іншого каналу: попередження «Зайнята»

---

### `/fleet` — FleetList ⭐

**Фільтри:** `search` (номер/назва), `statusCar`, `trackingMode`, `isActive`

**Колонки:**

| Колонка | Джерело |
|---------|---------|
| Номер + назва | `cars` |
| Статус | badge: active/repair/inactive |
| Режим (дефолт) | `cars.default_tracking_mode` |
| Пробіг / місяць | `daily_summaries` |
| Палет / місяць | `daily_summaries.pallets_count` |
| Паливо л/100км | розрахунок |
| Загальні витрати | `monthly_costs` |
| Остання активність | `route_events` |

---

### `/fleet/:carId` — CarDetail

**Tabs:** `route` (timeline дня) | `month` (графік + таблиця) | `waybills`

---

### `/waybills` — WaybillList ⭐

**Фільтри:**
```typescript
interface WaybillFilters {
  search?: string;              // customer / waybill number
  status?: WaybillStatus;
  deliveryChannel?: DeliveryChannel | "unassigned" | "all";
  carId?: number;
  legalEntity?: LegalEntity;
  lineType?: "shipment" | "return" | "all";
  storeId?: string;
  dateFrom?: string;
  dateTo?: string;
}
```

**Нові колонки порівняно з v2:**

| Колонка | Примітка |
|---------|----------|
| Канал | badge: own/hired/carrier/⚠️ не призначено |
| Магазин | `store.name_store` |

---

### `/waybills/unassigned` — UnassignedWaybills

**Призначення:** Список накладних без каналу доставки (`delivery_channel IS NULL`).

**Що відображає:**
- Накладні, які є в реєстрі 1С, але ще не відскановані жодним каналом
- Дата, номер, клієнт, магазин, сума
- Фільтр по даті / клієнту

**Дії:**
- «Призначити вручну» → модальне вікно: вибір каналу (own/hired/carrier)

---

### `/hired` — HiredTripList

**Призначення:** Список рейсів найманого транспорту.

**Колонки:**

| Колонка | |
|---------|--|
| Дата | |
| Номер авто | |
| Маршрут | «Пирятин, Полтава, Харків» |
| Палет | |
| Накладних | кількість прив'язаних |
| Вартість (грн) | |

**Фільтри:** дата від/до, номер авто (текст), маршрут

---

### `/hired/new` — HiredTripForm

**Призначення:** Форма внесення рейсу найманого транспорту (логіст).

**Поля:**
```typescript
interface HiredTripFormFields {
  carNumber: string;            // вільний ввід
  routeName: string;            // «Пирятин, Полтава, Харків»
  tripDate: string;
  palletsCount: number;
  costUah: number;
  comment?: string;
  waybills: ScannedWaybill[];  // QR-скан або ручний ввід
}
```

**Логіка:**
- При додаванні накладної → перевірка `delivery_channel IS NULL`
- Якщо вже призначена → показати помилку «Накладна {N} вже у {канал}»
- Submit → зберегти trip + `hired_trip_waybills` + оновити `waybill_records.delivery_channel = 'hired'`

**Кнопка Back** → `/hired`

---

### `/hired/:tripId` — HiredTripDetail

- Деталі рейсу
- Таблиця прив'язаних накладних (з клієнтом, магазином, сумою)
- KPI: загальна сума, к-сть палет, вартість/палета
- Кнопка Back → `/hired`

---

### `/carriers` — CarrierShipmentList

**Призначення:** Список відправлень через служби доставки.

**Колонки:**

| Колонка | |
|---------|--|
| Дата | |
| Служба | НП / Міст Експрес |
| ТТН | |
| Накладних | |
| Вартість (грн) | із реєстру або «Очікується» |

**Фільтри:** служба, дата, ТТН

---

### `/carriers/new` — CarrierShipmentForm

**Призначення:** Прив'язка накладних до відправлення службою.

**Поля:**
```typescript
interface CarrierShipmentFormFields {
  carrierName: string;          // «Нова Пошта» / «Міст Експрес»
  ttn: string;                  // номер ТТН
  shipmentDate: string;
  comment?: string;
  waybills: ScannedWaybill[];  // QR-скан або ручний ввід
}
```

**Логіка:** аналогічна HiredTripForm — перевірка ексклюзивності каналу.

---

### `/carriers/import-costs` — CarrierCostsImport

**Призначення:** Імпорт реєстру витрат від служби доставки.

**Кроки:**
1. Вибір служби (НП / Міст Експрес)
2. Завантаження CSV / Excel реєстру
3. Попередній перегляд (перші 5 рядків)
4. Маппінг колонок → поля `carrier_costs`
5. «Імпортувати» → матч по (carrier_name, ttn) з `carrier_shipments`
6. Підсумок: імпортовано / не знайдено TTN / помилки

**Очікувані колонки реєстру:**
```
TTN, дата, вага (кг), вартість (грн)
```

---

### `/analytics/channels` — ChannelComparison

**Призначення:** Порівняння каналів доставки.

**Що відображає:**
- Таблиця по місяцях: власний / найманий / служби — к-сть накладних, сума, вартість/палета
- BarChart: структура витрат по каналах
- KPI: найдешевший канал для поточного місяця

---

### `/admin/stores` — StoreAdmin

**Що відображає:**
- Список магазинів з клієнтом і адресою
- Форма редагування: назва, основна адреса, додаткові адреси (список з + / -)
- Прив'язка клієнта

---

### `/admin/cars` — CarAdmin

**Що відображає:**
- Список авто: номер, назва, амортизація, режим, статус
- Форма: всі поля + `default_tracking_mode` + `status_car` + `amount_car`

---

### `/admin/monthly-costs` — MonthlyCostsAdmin

**Форма:**
```typescript
interface MonthlyCostsFormFields {
  carId: number;                // select із cars
  month: string;
  salaryUah: number;
  taxesUah: number;
  depreciationUah: number;      // підставляється з cars.amount_car, редагується
  repairActualUah?: number;
  repairRateUahKm: number;      // default 2.00
  otherCostsUah: number;
  otherCostsComment?: string;
}
```

**Підказка по ремонту:**
```
Якщо repairActualUah порожній →
  «Розрахункове: {km} км × {rate} грн/км = {result} грн»
Якщо заповнений →
  Зелений badge «Фактичні витрати»
```
