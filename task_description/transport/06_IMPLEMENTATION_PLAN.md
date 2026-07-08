# Vehicle Cost Tracker — Покроковий план реалізації

---

## Загальний таймлайн

```
Тиждень 1 — Foundation (типи, моки, утиліти)
Тиждень 2 — Driver UI (мобільний, власний автопарк)
Тиждень 3 — WaybillList + FleetList (оцінюваний функціонал)
Тиждень 4 — Найманий транспорт + Служби доставки
Тиждень 5 — Аналітика + PWA + polish
```

---

## ТИЖДЕНЬ 1 — Foundation

### Крок 1.1 — Ініціалізація

```bash
npm create vite@latest vehicle-tracker -- --template react-ts
cd vehicle-tracker
npm install react-router-dom @tanstack/react-query
npm install tailwindcss @tailwindcss/vite
npm install recharts html5-qrcode papaparse date-fns
npm install -D @types/papaparse @tanstack/react-query-devtools vite-plugin-pwa
```

### Крок 1.2 — Типи (`src/types/index.ts`)

Ключові нові типи (порівняно з v2):
- `DeliveryChannel` = `"own" | "hired" | "carrier"`
- `CarStatus` = `"active" | "repair" | "inactive"`
- `Store`, `StoreDeliveryAddress`
- `Car` (замість `Vehicle`)
- `HiredTransportTrip`, `HiredTripWaybill`
- `CarrierShipment`, `CarrierWaybill`, `CarrierCost`
- `WaybillRecord.deliveryChannel` (нове поле)
- `WaybillRecord.storeId` (нове поле)
- `RouteEvent.palletsCount` (нове поле)

### Крок 1.3 — Mock JSON файли

```
src/mocks/
├── cars.json                  3 авто (1 full, 2 daily; різні statusCar)
├── drivers.json               3 водії, прив'язані до cars
├── product-categories.json    5 категорій
├── products.json              20 товарів
├── product-logistics.json     20 записів
├── customers.json             10 клієнтів
├── stores.json                20 магазинів (2 на клієнта)
├── store-delivery-addresses.json  40 адрес (2 на магазин)
├── route-events.json          5 днів × 2 авто (з palletsCount)
├── waybills.json              80 рядків із 20 накладних
│   (deliveryChannel: 'own'×10, 'hired'×5, 'carrier'×3, null×2)
├── monthly-costs.json         2 місяці × 3 авто
├── hired-trips.json           5 рейсів
├── hired-trip-waybills.json   прив'язані накладні
├── carrier-shipments.json     6 відправлень (НП + Міст Експрес)
├── carrier-waybills.json      прив'язані накладні
└── carrier-costs.json         6 рядків реєстру витрат
```

### Крок 1.4 — Utils

1. `formatters.ts` — додати `channelLabel()`
2. `eventHelpers.ts` — додати `requiresPallets(type, mode)`
3. `calcSummary.ts` — `buildDailySummary` + `calcTotalPallets`
4. `calcProduct.ts`
5. `calcTransportCost.ts` — додати `allocateHiredTripCost()`
6. `parseQR.ts`
7. `parseCsv.ts` — додати `parseCsvToCarrierCosts()`
8. `clientFilter.ts` — `filterWaybills` з `deliveryChannel` і `storeId`

### Крок 1.5 — API + React Query setup

Патерн перевірки ексклюзивності в `api/waybills.ts`:
```typescript
export async function checkWaybillChannel(number: string) {
  if (USE_MOCK) {
    const waybills = mockWaybills as WaybillRecord[];
    const found = waybills.find(w => w.waybillNumber === number);
    return { waybillNumber: number, deliveryChannel: found?.deliveryChannel ?? null };
  }
  const res = await fetch(`${API_BASE}/waybills/${number}/channel/`);
  return res.json();
}
```

---

## ТИЖДЕНЬ 2 — Driver UI

### Крок 2.1 — Layouts + UI компоненти

**Нові компоненти порівняно з v2:**
- `ChannelBadge.tsx` — кольоровий badge каналу
- `CarStatusBadge.tsx`
- `PalletsInput.tsx` — великі кнопки +/− для телефону

### Крок 2.2 — DriverDashboard

```tsx
// Зміна: vehicle → car, vehicleId → carId
const { data: driver }      = useCurrentDriver();
const { data: car }         = useCar(driver?.idCar);
const { data: todayEvents } = useTodayEvents(car?.idCar);
const { dayMode, setDayMode, isOverridden } = useDayMode(
  car?.defaultTrackingMode ?? "daily"
);
```

### Крок 2.3 — EventForm з `palletsCount`

```typescript
// Відображення поля палет
const showPallets = requiresPallets(eventType, dayMode);
// true для: depot_start (daily), delivery (full)

// Логіка QR для daily depot_start
const handleFirstScan = (result: QRResult) => {
  const waybill = waybillsCache.find(w => w.waybillNumber === result.waybillNumber);
  if (waybill?.storeId) {
    setConfirmStore({
      storeName: waybill.storeName,
      storeId: waybill.storeId,
    });
    setShowStoreConfirm(true); // модальне вікно підтвердження
  } else {
    addScanned(result);
  }
};
```

### Крок 2.4 — Channel guard при скануванні

```typescript
const channelGuard = useWaybillChannelGuard();

const handleQRScan = async (decoded: string) => {
  const result = parseQRCode(decoded);
  if (!result) return;
  const allowed = await channelGuard(result.waybillNumber);
  if (!allowed) return; // toast вже показано
  addScanned(result);
};
```

---

## ТИЖДЕНЬ 3 — WaybillList + FleetList

### Крок 3.1 — WaybillList (пріоритет!)

**Нові фільтри порівняно з v2:**
```typescript
// WaybillFiltersBar — додаткові контролі:
<Select
  label="Канал доставки"
  options={[
    { value: "all", label: "Всі" },
    { value: "own", label: "Власне авто" },
    { value: "hired", label: "Найманий транспорт" },
    { value: "carrier", label: "Служба доставки" },
    { value: "unassigned", label: "⚠️ Не призначено" },
  ]}
/>
<Select label="Магазин" options={storesOptions} />
```

### Крок 3.2 — UnassignedWaybills

```tsx
export function UnassignedWaybills() {
  const { data, isLoading, isError } = useUnassignedWaybills(filters);

  return (
    <>
      <Banner type="warning" text={`${data?.length ?? 0} накладних без каналу доставки`} />
      <table>
        {data?.map(w => (
          <UnassignedRow
            key={w.waybillNumber}
            waybill={w}
            onAssign={(channel) => handleAssign(w.waybillNumber, channel)}
          />
        ))}
      </table>
    </>
  );
}
```

### Крок 3.3 — FleetList

**Зміна:** `vehicle` → `car`, додана колонка «Палет/міс», «Статус» з `CarStatusBadge`.

---

## ТИЖДЕНЬ 4 — Найманий транспорт + Служби доставки

### Крок 4.1 — HiredTripForm

```tsx
export function HiredTripForm() {
  const [form, setForm] = useState<HiredTripFormState>({
    carNumber: "", routeName: "", tripDate: today,
    palletsCount: "", costUah: "", comment: "", scannedWaybills: [],
  });
  const channelGuard = useWaybillChannelGuard();
  const mutation = useCreateHiredTrip();

  const handleAddWaybill = async (raw: string) => {
    const qr = parseQRCode(raw) ?? { waybillNumber: raw, waybillDate: today };
    const allowed = await channelGuard(qr.waybillNumber);
    if (!allowed) return;
    setForm(f => ({
      ...f,
      scannedWaybills: [...f.scannedWaybills, { ...qr, scannedAt: now() }],
    }));
  };

  const handleSubmit = () => {
    mutation.mutate({
      ...form,
      waybillNumbers: form.scannedWaybills.map(w => w.waybillNumber),
    }, {
      onSuccess: () => navigate("/hired"),
      onError: (e) => toast.error(e.message),
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-4">
      <h1 className="text-xl font-semibold">Новий рейс найманого транспорту</h1>
      <Input label="Номер авто" value={form.carNumber} onChange={...} />
      <Input label="Назва маршруту" value={form.routeName}
             placeholder="Пирятин, Полтава, Харків" onChange={...} />
      <DatePicker label="Дата рейсу" value={form.tripDate} onChange={...} />
      <PalletsInput label="Кількість палет" value={form.palletsCount} onChange={...} />
      <Input label="Вартість доставки (грн)" type="number" value={form.costUah} onChange={...} />
      <Textarea label="Коментар" value={form.comment} onChange={...} />

      <ScannedWaybillList
        waybills={form.scannedWaybills}
        onRemove={(n) => setForm(f => ({
          ...f,
          scannedWaybills: f.scannedWaybills.filter(w => w.waybillNumber !== n),
        }))}
      />
      <Button onClick={() => navigate("/hired/scan?mode=hired")}>
        Сканувати накладну
      </Button>
      <Button variant="primary" onClick={handleSubmit}>
        Зберегти рейс
      </Button>
      <Button variant="ghost" onClick={() => navigate("/hired")}>← Назад</Button>
    </div>
  );
}
```

### Крок 4.2 — CarrierShipmentForm

Аналогічна структура до HiredTripForm, але без `carNumber`, `palletsCount`, `costUah`.
Замість них: `carrierName` (select: НП / Міст Експрес), `ttn`.

### Крок 4.3 — CarrierCostsImport

```typescript
// utils/parseCsv.ts — парсер реєстру Нової Пошти
export function parseCsvToCarrierCosts(
  csvText: string,
  carrierName: string,
): { rows: Partial<CarrierCost>[]; errors: ImportError[] } {
  const { data } = Papa.parse(csvText, { header: true, skipEmptyLines: true });
  const rows: Partial<CarrierCost>[] = [];
  const errors: ImportError[] = [];

  data.forEach((raw: any, i) => {
    const ttn = raw["ТТН"] ?? raw["ttn"];
    const costUah = parseFloat(raw["Вартість"] ?? raw["cost_uah"] ?? "0");
    const weightKg = parseFloat(raw["Вага"] ?? raw["weight_kg"] ?? "0");
    const costDate = raw["Дата"] ?? raw["date"];

    if (!ttn) { errors.push({ row: i + 2, field: "ttn", message: "Відсутній ТТН" }); return; }
    rows.push({ carrierName, ttn, costUah, weightKg, costDate });
  });

  return { rows, errors };
}
```

---

## ТИЖДЕНЬ 5 — Аналітика + PWA

### Крок 5.1 — MonthlyCostsAdmin

**Зміна:** поле `carId` замість `vehicleId`.
Значення амортизації підставляється автоматично з `cars.amount_car`:
```typescript
// При виборі авто — підставляємо амортизацію
const handleCarChange = (carId: number) => {
  const car = cars.find(c => c.idCar === carId);
  setForm(f => ({ ...f, carId, depreciationUah: car?.amountCar ?? 0 }));
};
```

### Крок 5.2 — ChannelComparison

```tsx
export function ChannelComparison() {
  const { data } = useChannelComparison(6); // 6 місяців

  return (
    <>
      <h1>Порівняння каналів доставки</h1>
      <ChannelComparisonChart data={data} />
      <table>
        <thead>
          <tr>
            <th>Місяць</th>
            <th>Власне авто — накл.</th><th>грн</th><th>грн/палета</th>
            <th>Найманий — накл.</th><th>грн</th><th>грн/палета</th>
            <th>Служби — накл.</th><th>грн</th>
          </tr>
        </thead>
        <tbody>
          {data?.map(row => <ChannelComparisonRow key={row.month} row={row} />)}
        </tbody>
      </table>
    </>
  );
}
```

### Крок 5.3 — PWA + мобільний polish

```css
/* index.css */
input, select, textarea { font-size: 16px; }
.bottom-nav { padding-bottom: env(safe-area-inset-bottom); }
button, a[role="button"] { min-height: 44px; touch-action: manipulation; }
```

---

## Чеклист перед demo

```
Foundation
  ✅ types: DeliveryChannel, Car, Store, HiredTransportTrip, CarrierShipment
  ✅ mocks: cars, stores, hired-trips, carrier-shipments, carrier-costs
  ✅ utils: channelLabel, requiresPallets, allocateHiredTripCost, parseCsvToCarrierCosts

Driver UI
  ✅ DayModeSwitch
  ✅ PalletsInput на depot_start (daily) і delivery (full)
  ✅ Підтвердження магазину при першому QR скані (daily)
  ✅ Channel guard при кожному скані
  ✅ Всі 8 типів подій

WaybillList (оцінка!)
  ✅ Фільтр по deliveryChannel (own/hired/carrier/unassigned/all)
  ✅ Фільтр по storeId
  ✅ ChannelBadge у таблиці
  ✅ Сортування, пагінація, стани

FleetList (оцінка!)
  ✅ CarStatusBadge
  ✅ Колонка палет/міс

Найманий транспорт
  ✅ HiredTripList з фільтрами
  ✅ HiredTripForm з channel guard
  ✅ HiredTripDetail

Служби доставки
  ✅ CarrierShipmentList
  ✅ CarrierShipmentForm з channel guard
  ✅ CarrierCostsImport (CSV парсинг)

Аналітика
  ✅ ChannelComparison (3 канали по місяцях)
  ✅ CustomerAnalytics з розбивкою по каналах
  ✅ MonthlyCosts — auto-fill з cars.amount_car

PWA
  ✅ Installable на телефон
  ✅ font-size 16px на inputs
```
