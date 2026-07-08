# Vehicle Cost Tracker — Компоненти, Hooks, Utils

---

## `api/` — шар отримання даних

```typescript
// api/config.ts
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

// api/cars.ts
export async function fetchCars(): Promise<Car[]>
export async function fetchCar(id: number): Promise<Car>
export async function updateCar(id: number, data: Partial<Car>): Promise<Car>

// api/drivers.ts
export async function fetchCurrentDriver(): Promise<Driver>
export async function fetchDrivers(): Promise<Driver[]>

// api/routeEvents.ts
export async function fetchTodayEvents(carId: number): Promise<RouteEvent[]>
export async function fetchEventsByDate(carId: number, date: string): Promise<RouteEvent[]>
export async function fetchEventsByRange(carId: number, from: string, to: string): Promise<RouteEvent[]>
export async function createRouteEvent(data: RouteEventCreate): Promise<RouteEvent>
export async function fetchLastOdometer(carId: number): Promise<number | null>

// api/waybills.ts
export async function fetchWaybills(
  filters: WaybillFilters,
  sort: SortParams,
  pagination: PaginationParams,
): Promise<PaginatedResponse<WaybillSummary>>
export async function fetchWaybillDetail(number: string): Promise<WaybillRecord[]>
export async function importWaybillsCsv(rows: Partial<WaybillRecord>[]): Promise<ImportResult>
export async function checkWaybillChannel(number: string): Promise<{
  waybillNumber: string;
  deliveryChannel: DeliveryChannel | null;
}>
export async function fetchUnassignedWaybills(filters: {
  dateFrom?: string; dateTo?: string; customerId?: string;
}): Promise<WaybillSummary[]>
export async function fetchReturnsPending(): Promise<RouteEvent[]>

// api/stores.ts
export async function fetchStores(): Promise<Store[]>
export async function fetchStore(id: string): Promise<Store>
export async function fetchStoresByCustomer(customerId: string): Promise<Store[]>

// api/hiredTransport.ts
export async function fetchHiredTrips(filters: {
  dateFrom?: string; dateTo?: string; carNumber?: string;
}): Promise<HiredTransportTrip[]>
export async function fetchHiredTrip(id: number): Promise<HiredTransportTrip>
export async function createHiredTrip(data: HiredTransportTripCreate & {
  waybillNumbers: string[];
}): Promise<HiredTransportTrip>

// api/carriers.ts
export async function fetchCarrierShipments(filters: {
  carrierName?: string; dateFrom?: string; dateTo?: string;
}): Promise<CarrierShipment[]>
export async function createCarrierShipment(data: CarrierShipmentCreate & {
  waybillNumbers: string[];
}): Promise<CarrierShipment>
export async function importCarrierCosts(
  carrierName: string,
  rows: Partial<CarrierCost>[],
): Promise<ImportResult>

// api/monthlyCosts.ts
export async function fetchMonthlyCosts(carId: number, month: string): Promise<MonthlyCosts | null>
export async function saveMonthlyCosts(data: MonthlyCostsForm): Promise<MonthlyCosts>

// api/analytics.ts
export async function fetchTransportCosts(params: {
  carId?: number; month?: string; legalEntity?: LegalEntity;
}): Promise<TransportCostPerWaybill[]>
export async function fetchCustomerAnalytics(params: {
  month?: string; legalEntity?: LegalEntity;
}): Promise<TransportCostPerCustomer[]>
export async function fetchChannelComparison(months: number): Promise<ChannelComparison[]>
export async function fetchCarMonthlySummary(carId: number, month: string): Promise<CarMonthlySummary>
```

---

## `hooks/` — React Query хуки

```typescript
// hooks/useCars.ts
export function useCars()
export function useCar(id: number)

// hooks/useCurrentDriver.ts
export function useCurrentDriver()

// hooks/useRouteEvents.ts
export function useTodayEvents(carId: number)
export function useEventsByDate(carId: number, date: string)
export function useLastOdometer(carId: number)
export function useCreateRouteEvent()
// Інвалідує: ["route-events", carId], ["last-odometer", carId], ["daily-summary", carId, date]

// hooks/useDayMode.ts
// Зберігає вибір режиму водія в localStorage (ключ: "dayMode:{carId}:{date}")
export function useDayMode(carDefaultMode: TrackingMode): {
  dayMode: TrackingMode;
  setDayMode: (mode: TrackingMode) => void;
  isOverridden: boolean;
}

// hooks/useWaybills.ts
export function useWaybills(filters, sort, pagination)
export function useWaybillDetail(waybillNumber: string)
export function useCheckWaybillChannel(waybillNumber: string)
export function useUnassignedWaybills(filters)
export function useImportWaybills()
export function useReturnsPending()

// hooks/useWaybillFilters.ts
// Стан фільтрів у URL search params — включає deliveryChannel, storeId
export function useWaybillFilters()

// hooks/useDailySummary.ts
export function useDailySummary(carId: number, date: string): DailySummary | null

// hooks/useHiredTransport.ts
export function useHiredTrips(filters)
export function useHiredTrip(id: number)
export function useCreateHiredTrip()

// hooks/useCarriers.ts
export function useCarrierShipments(filters)
export function useCarrierShipment(id: number)
export function useCreateCarrierShipment()
export function useImportCarrierCosts()

// hooks/useMonthlyCosts.ts
export function useMonthlyCosts(carId: number, month: string)
export function useSaveMonthlyCosts()

// hooks/useWaybillChannelGuard.ts
// Утилітний хук — перевірка ексклюзивності перед додаванням накладної
export function useWaybillChannelGuard() {
  return async (waybillNumber: string): Promise<boolean> => {
    const result = await checkWaybillChannel(waybillNumber);
    if (result.deliveryChannel !== null) {
      toast.error(`Накладна ${waybillNumber} вже в каналі: ${channelLabel(result.deliveryChannel)}`);
      return false;
    }
    return true;
  };
}
```

---

## `utils/` — Бізнес-логіка

```typescript
// utils/calcSummary.ts
// daily: mileage = depot_start сьогодні − depot_start вчора.
// full: mileage = сума відрізків; порожній пробіг = parking_end − остання delivery.
// palletsCount береться з depot_start (daily) або SUM по delivery (full).

export function buildDailySummary(
  events: RouteEvent[],
  prevDayLastOdometer: number | null,
): DailySummary

export function buildRouteSegments(events: RouteEvent[]): RouteSegment[]
export function calcEmptyMileage(events: RouteEvent[]): number | null
export function calcTotalPallets(events: RouteEvent[], mode: TrackingMode): number

// utils/calcProduct.ts
export function calcLineWeight(logistics: ProductLogistics, quantity: number): number
export function calcLineVolume(logistics: ProductLogistics, quantity: number): number
export function calcVolumetricWeight(volumeCbm: number): number

// utils/calcTransportCost.ts
// Власний автопарк: пропорція від місячних витрат.
// Найманий: cost_per_waybill = trip.cost_uah / trip.waybills_count.
// Служби: cost = carrier_costs.cost_uah для конкретного ТТН.

export function allocateMonthlyCosts(
  waybills: WaybillSummary[],
  costs: MonthlyCostsSummary,
): TransportCostPerWaybill[]

export function allocateHiredTripCost(
  trip: HiredTransportTrip,
): { waybillNumber: string; costUah: number }[]

export function aggregateByCustomer(
  perWaybill: TransportCostPerWaybill[],
  customers: Customer[],
): TransportCostPerCustomer[]

export function calcRepairCost(costs: MonthlyCosts, totalKm: number): number
export function calcTotalMonthlyCost(costs: MonthlyCosts, totalKm: number): number

// utils/parseQR.ts
export function parseQRCode(raw: string): QRResult | null

// utils/parseCsv.ts
// Для реєстру 1С (waybill_records) і реєстру служб доставки (carrier_costs).
export function parseCsvToWaybills(csvText, columnMap): { rows; errors }
export function parseCsvToCarrierCosts(csvText, carrierName): { rows: Partial<CarrierCost>[]; errors }

// utils/formatters.ts
export function formatUah(v: number): string
export function formatKm(v: number): string
export function formatLiters(v: number): string
export function formatKg(v: number): string
export function formatCbm(v: number): string
export function formatDate(iso: string): string
export function formatDateTime(iso: string): string
export function formatMonth(iso: string): string
export function formatPct(v: number): string
export function formatLegalEntity(e: LegalEntity): string
export function channelLabel(ch: DeliveryChannel): string  // «Власне авто» / «Найманий» / «Служба»

// utils/eventHelpers.ts
export function getAvailableEventTypes(mode: TrackingMode): RouteEventType[]
export function requiresOdometer(type: RouteEventType): boolean
export function requiresWaybill(type: RouteEventType): boolean
export function requiresPallets(type: RouteEventType, mode: TrackingMode): boolean
export function eventTypeLabel(type: RouteEventType): string
export function eventTypeIcon(type: RouteEventType): string

// utils/clientFilter.ts
export function filterWaybills(items: WaybillSummary[], filters: WaybillFilters): WaybillSummary[]
export function sortItems<T>(items: T[], sort: SortParams): T[]
export function paginate<T>(items: T[], pagination: PaginationParams): PaginatedResponse<T>
```

---

## `components/ui/` — Атомарні компоненти

```
Button.tsx            — primary/secondary/ghost/danger; sm/md/lg
Badge.tsx             — статуси накладних
LegalEntityBadge.tsx  — ESP=синій, OPT=зелений, Rubin=червоний
ChannelBadge.tsx      — own=сірий, hired=жовтий, carrier=фіолетовий, null=помаранчевий⚠️
CarStatusBadge.tsx    — active=зелений, repair=жовтий, inactive=сірий
Spinner.tsx
SkeletonRow.tsx
EmptyState.tsx
ErrorBanner.tsx
Pagination.tsx
SortHeader.tsx
Modal.tsx
Input.tsx
Select.tsx
Textarea.tsx
DatePicker.tsx
MonthPicker.tsx
Toast.tsx
```

---

## `components/driver/`

```
DayModeSwitch.tsx       — toggle daily/full + індикатор «відрізняється від дефолту»
RouteTimeline.tsx       — timeline подій + палети на точках
EventTypeButtons.tsx    — кнопки за режимом (8 типів)
ScannedWaybillList.tsx  — чіпи + customerName + storeName + видалення
PalletsInput.tsx        — число палет з +/- кнопками (великий tap target)
RejectionForm.tsx       — повна / часткова відмова
ReturnGoodsForm.tsx     — номер накладної клієнта
ExtraCargoForm.tsx      — звідки, куди, вага, накладна
```

---

## `components/hired/`

```
HiredTripCard.tsx
  Props: { trip: HiredTransportTrip }
  — картка рейсу: номер авто, маршрут, дата, палети, сума

HiredWaybillList.tsx
  Props: { waybills: HiredTripWaybill[]; onRemove? }
  — список прив'язаних накладних + видалення (якщо в режимі редагування)
```

---

## `components/carriers/`

```
CarrierShipmentCard.tsx
  Props: { shipment: CarrierShipment }
  — картка відправлення: служба, ТТН, дата, к-сть накладних, сума

CarrierCostStatus.tsx
  Props: { cost?: CarrierCost }
  — badge «Витрати отримані: X грн» або «Очікується реєстр»
```

---

## `components/fleet/`

```
CarCard.tsx             — мобільна картка авто
CarTable.tsx            — таблиця з CarStatusBadge і TrackingModeBadge
DailyCostsChart.tsx     — recharts BarChart: пробіг + витрати по днях + палети
CostBreakdownPie.tsx    — recharts PieChart: структура місячних витрат
```

---

## `components/waybills/`

```
WaybillFiltersBar.tsx   — search + status + channel + legalEntity + lineType + store + dates
WaybillTable.tsx        — + ChannelBadge + LegalEntityBadge + store column
WaybillLineTable.tsx    — від'ємна кількість = повернення (червоний колір)
CsvPreview.tsx          — preview + маппінг колонок
ReturnMatchRow.tsx      — рядок матчингу повернень
UnassignedRow.tsx       — рядок з кнопкою «Призначити канал»
```

---

## `components/analytics/`

```
KpiCard.tsx
MileageLineChart.tsx
TransportCostTable.tsx     — + ChannelBadge
CustomerCostTable.tsx      — + розбивка по каналах
ChannelComparisonChart.tsx — recharts BarChart: 3 канали по місяцях
```
