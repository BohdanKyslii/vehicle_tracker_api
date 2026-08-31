# Vehicle Cost Tracker — TypeScript типи

Файл: `vehicle_cost_tracker/src/types/index.ts`

> **Оновлено 2026-08-24.** Це дзеркало реального файлу на момент
> оновлення, не первинний план — реальний файл уже суттєво розійшовся
> з планом (нові поля `CarSpecs`/`Trailer`/`CarStatusLog`,
> `fuelCardNumber`, `driversLicense`, `idProduct: number` замість
> `string`). **Якщо потрібна стовідсоткова точність — звіряй з живим
> файлом**, цей документ може відстати знову. Відома розбіжність у
> самому живому файлі (не виправлено навмисно, лишень фіксую): у
> `WaybillRecord`/`WaybillSummary` поля `customerId`/`storeId` типізовані
> як `string`, хоча відповідні `Customer.idCustomer`/`Store.idStore` —
> `number`.

---

## Довідники

```typescript
// Категорія товару
export interface ProductCategory {
  idCategory: number;
  nameCategory: string;
  parentID: number | null;
  description: string;
  createdAt: Date;
  updatedAt: Date;
}

// Константи для зручності в коді
export const CATEGORY_DEFAULTS = {
  ROOT_OTHER: 3,
  CHILD_OTHER: 15,
};

// Товар із системи обліку 1С
export interface Product {
  idProduct: number;         // артикул 1С — ЧИСЛО, не рядок
  nameProduct: string;
  idCategory: number;        // default: 15 ("Інше" → "Аксесуари")
  isActive: boolean;
  description?: string;
  createdAt: string;
  updatedAt: string;
  // Опційні вкладені об'єкти (підвантажуються окремим запитом)
  category?: ProductCategory;
  logistics?: ProductLogistics;
}

export const PRODUCT_DEFAULTS: Partial<Product> = {
  idCategory: CATEGORY_DEFAULTS.CHILD_OTHER,
  isActive: true,
};

// Логістичні дані товару — окрема таблиця в БД
export interface ProductLogistics {
  idProduct: number;
  unitWeightKg?: number;
  unitLengthCm?: number;
  unitWidthCm?: number;
  unitHeightCm?: number;
  unitsPerBox?: number;
  boxLengthCm?: number;
  boxWidthCm?: number;
  boxHeightCm?: number;
  // Примітка: на відміну від первинного плану, unitVolumeCbm/
  // boxVolumeCbm тут НЕ описані як поля типу — рахуються з інших полів
  // на боці, що їх споживає (backend @property, не окремий JSON-ключ).
}

// Клієнт (компанія-покупець)
export interface Customer {
  idCustomer: number;
  nameCustomer: string;
  networkCustomer?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Магазин / торгова точка клієнта
export interface Store {
  idStore: number;
  idCustomer: number;
  nameStore: string;
  storeAddress?: string;
  isActive: boolean;
  customer?: Customer;
  deliveryAddress?: StoreDeliveryAddress[];
}

// Додаткова адреса доставки магазину
export interface StoreDeliveryAddress {
  id: number;
  idStore: number;
  deliveryAddress: string;
  isPrimary: boolean;
  notes?: string;
}
```

---

## Автопарк

```typescript
// Режим трекінгу водія на авто
export type TrackingMode = "daily" | "full";

// Статус авто
export type CarStatus = "active" | "repair" | "inactive";

// Авто власного автопарку
export interface Car {
  idCar: number;
  nameCar: string;
  numberCar: string;
  fuelCardNumber?: number;        // немає в первинному плані
  amountCar: number;              // амортизація грн/міс — фіксована
  defaultTrackingMode?: TrackingMode;
  statusCar: CarStatus;
  isActive: boolean;
  specs?: CarSpecs;
  trailer?: Trailer;
}

// Технічні характеристики авто — немає в первинному плані
export interface CarSpecs {
  idCar: number;
  vinCode?: string;
  yearManufactured?: number;
  weightKg?: number;
  payloadKg?: number;
  lengthCm?: number;
  widthCm?: number;
  heightCm?: number;
  hasTailLift: boolean;   // гідроборт, default: false
  hasTrailer: boolean;    // default: false
  trailer?: Trailer;
}

// Причіп — немає в первинному плані
export interface Trailer {
  idTrailer: number;
  vinCode?: string;
  yearManufactured?: number;
  nameTrailer: string;
  idCar: number;
  model: string;
  numberTrailer: string;
  isActive: boolean;
}

// Журнал зміни статусу авто — немає в первинному плані
export interface CarStatusLog {
  id: number;
  idCar: number;
  status: CarStatus;
  reason?: string;
  changedAt: string;
  changedBy?: number;
}

// Водій
export interface Driver {
  idDriver: number;
  nameDriver: string;
  phoneDriver?: string;
  driversLicense?: string;   // немає в первинному плані
  idCar: number | null;
  isActive: boolean;
  car?: Car;
}
```

---

## Канал доставки

```typescript
export type LegalEntity = "ESP" | "OPT" | "Rubin";

// Канал доставки — кожна накладна належить ТІЛЬКИ одному каналу
// own     = власне авто (водій сканує QR)
// hired   = найманий транспорт (логіст вносить)
// carrier = служба доставки (НП, Міст Експрес)
export type DeliveryChannel = "own" | "hired" | "carrier";
```

---

## Реєстр накладних (із 1С)

```typescript
// Один рядок накладної із 1С
// quantity > 0 = відвантаження
// quantity < 0 = повернення
export interface WaybillRecord {
  id: number;
  legalEntity: LegalEntity;
  waybillNumber: string;
  waybillDate: string;
  linePosition: number;
  customerId: string;         // ⚠️ string, хоча Customer.idCustomer — number
  customerName: string;
  storeId?: string;           // ⚠️ те саме для Store.idStore
  productId: number;
  productName: string;
  quantity: number;
  priceUah: number;
  totalUah: number;
  comment?: string;
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  volumetricWeightKg?: number;
  deliveryChannel?: DeliveryChannel | null;
  status?: WaybillStatus;
  importedAt: string;
  importBatchId?: string;
}

// Агрегована накладна (всі рядки одної накладної → один рядок у таблиці UI)
export interface WaybillSummary {
  legalEntity: LegalEntity;
  waybillNumber: string;
  waybillDate: string;
  customerId: string;
  customerName: string;
  storeId?: string;
  storeName?: string;
  linesCount: number;
  totalUah: number;       // сума відвантажень
  returnsUah: number;     // сума повернень (від'ємна)
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  deliveryChannel?: DeliveryChannel | null;
  // Деталі каналу
  carId?: number;
  carNumber?: string;
  tripId?: number;
  tripRouteName?: string;
  shipmentId?: number;
  carrierName?: string;
  status: WaybillStatus;
}

export type WaybillStatus = "pending" | "scanned" | "delivered" | "cancelled";
```

---

## Трекінг маршруту (власний автопарк)

```typescript
export type RouteEventType =
  | "depot_start"   // ранок, склад
  | "delivery"      // вивантаження у клієнта
  | "parking_end"   // кінець дня
  | "depot_return"  // повернення на склад
  | "refuel"        // заправка
  | "other_cost"    // інші витрати
  | "return_goods"  // повернення товару
  | "extra_cargo";  // додатковий вантаж

// Відмова від прийому товару
export interface DeliveryRejection {
  isFull: boolean;
  productId?: number;
  quantity?: number;
  comment?: string;
}

// Одна подія маршруту
export interface RouteEvent {
  id: number;
  carId: number;
  driverId: number;
  trackingMode?: TrackingMode;
  eventType: RouteEventType;
  eventTs: string;              // ISO 8601
  odometerKm?: number;
  palletsCount?: number;

  // Для delivery
  waybillNumber?: string;
  waybillDate?: string;
  customerName?: string;
  rejection?: DeliveryRejection;

  // Для refuel
  fuelLiters?: number;
  fuelCostUah?: number;
  adBlueLiters?: number;
  adBlueCostUah?: number;

  // Для other_cost
  otherCostUah?: number;
  otherCostComment?: string;

  // Для return_goods
  returnClientWaybill?: string;

  // Для extra_cargo
  extraFrom?: string;
  extraTo?: string;
  extraWeightKg?: number;
  extraWaybill?: string;
  extraComment?: string;

  notes?: string;
  createdAt: string;
}

export type RouteEventCreate = Omit<RouteEvent, "id" | "createdAt">;

// Відрізок маршруту між двома подіями (тільки full режим)
export interface RouteSegment {
  fromEvent: RouteEventType;
  toEvent: RouteEventType;
  waybillNumber?: string;
  customerName?: string;
  distanceKm: number;
  durationMin: number;
}

// Підсумок дня — розраховується з масиву RouteEvent
export interface DailySummary {
  carId: number;
  driverId: number;
  trackingMode: TrackingMode;
  date: string;
  totalMileageKm: number;
  loadedMileageKm: number | null;   // null для daily режиму
  emptyMileageKm: number | null;    // null для daily режиму
  palletsCount: number | null;
  fuelLiters: number;
  fuelCostUah: number;
  adBlueLiters: number;
  adBlueCostUah: number;
  otherCostUah: number;
  deliveriesCount: number;
  returnCount: number;
  extraCargoCount: number;
  waybillNumbers: string[];
  segments: RouteSegment[];   // [] для daily режиму
}
```

---

## Місячні витрати (від логіста)

```typescript
export interface MonthlyCosts {
  id: number;
  carId: number;
  month: string;                // "2026-06"
  salaryUah: number;
  taxesUah: number;
  depreciationUah: number;
  repairActualUah?: number;     // якщо є — пріоритет над розрахунковим
  repairRateUahKm: number;      // default: 2.00 грн/км
  otherCostUah: number;
  otherCostComment?: string;
}

export type MonthlyCostsForm = Omit<MonthlyCosts, "id">;

export interface MonthlyCostsSummary extends MonthlyCosts {
  totalKm: number;
  repairCostUah: number;
  totalCostUah: number;
}
```

---

## Найманий транспорт

```typescript
export interface HiredTransportTrip {
  id: number;
  carNumber: string;      // вільний ввід, не з довідника
  routeName: string;
  tripDate: string;
  palletsCount?: number;
  costUah: number;
  comment?: string;
  createdAt: string;
  waybills?: HiredTripWaybill[];
}

export type HiredTransportTripCreate = Omit<
  HiredTransportTrip,
  "id" | "createdAt" | "waybills"
>;

export interface HiredTripWaybill {
  id: number;
  tripId: number;
  waybillNumber: string;
  scannedAt: string;
}
```

---

## Служби доставки (НП, Міст Експрес)

```typescript
export interface CarrierShipment {
  id: number;
  carrierName: string;    // "Нова Пошта" / "Міст Експрес"
  ttn: string;
  shipmentDate: string;
  comment?: string;
  createdAt: string;
  waybills?: CarrierWaybill[];
  cost?: CarrierCost;
}

export type CarrierShipmentCreate = Omit<
  CarrierShipment,
  "id" | "createdAt" | "waybills" | "cost"
>;

export interface CarrierWaybill {
  id: number;
  shipmentId: number;
  waybillNumber: string;
  scannedAt: string;
}

export interface CarrierCost {
  id: number;
  shipmentId?: number;
  carrierName: string;
  ttn: string;
  costDate: string;
  weightKg?: number;
  costUah: number;
  importBatchId?: string;
  importedAt: string;
}
```

---

## Аналітика

> Ці типи вже описані на фронтенді, але **бекенд ще не має жодного
> ендпоінту аналітики** (`apps.analytics` порожній, свідомо відкладено —
> `01_PROJECT_OVERVIEW.md` §10 п.9).

```typescript
export interface TransportCostPerWaybill {
  legalEntity: LegalEntity;
  waybillNumber: string;
  waybillDate: string;
  customerId: string;
  customerName: string;
  storeId?: string;
  carId: number;
  carNumber: string;
  saleUah: number;
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  allocatedCostUah: number;
  costPctOfSale: number;
}

export interface TransportCostPerCustomer {
  customerId: string;
  customerName: string;
  networkCustomer?: string;
  waybillsCount: number;
  saleUah: number;
  totalWeightKg?: number;
  ownCostUah: number;
  hiredCostUah: number;
  carrierCostUah: number;
  totalCostUah: number;
  costPctOfSale: number;
}

export interface CarMonthlySummary {
  carId: number;
  carNumber: string;
  month: string;
  totalKm: number;
  totalPallets: number;
  fuelLiters: number;
  fuelCostUah: number;
  adBlueLiters: number;
  adBlueCostUah: number;
  fuelLitersPer100Km: number;
  totalCostUah: number;
  costPerKmUah: number;
}

export interface ChannelComparison {
  month: string;
  ownWaybillsCount: number;
  ownTotalCostUah: number;
  ownCostPerPallet: number;
  hiredWaybillsCount: number;
  hiredTotalCostUah: number;
  hiredCostPerPallet: number;
  carrierWaybillsCount: number;
  carrierTotalCostUah: number;
}
```

---

## Допоміжні типи (UI)

```typescript
export type LoadingState = "idle" | "loading" | "success" | "error";

export interface PaginationParams {
  page: number;
  pageSize: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface WaybillFilters {
  search?: string;
  status?: WaybillStatus;
  deliveryChannel?: DeliveryChannel | "unassigned" | "all";
  carId?: number;
  legalEntity?: LegalEntity;
  lineType?: "shipment" | "return" | "all";
  storeId?: string;
  dateFrom?: string;
  dateTo?: string;
}

export type SortField = "date" | "total" | "customer" | "vehicle" | "weight";
export type SortDirection = "asc" | "desc";

export interface SortParams {
  field: SortField;
  direction: SortDirection;
}

export interface ImportResult {
  batchId: string;
  imported: number;
  skipped: number;
  errors: ImportError[];
}

export interface ImportError {
  row: number;
  field: string;
  message: string;
}

// Відскана накладна (у формі водія / логіста)
export interface ScannedWaybill {
  waybillNumber: string;
  waybillDate: string;
  scannedAt: string;
  customerName?: string;
  storeName?: string;
  deliveryChannel?: DeliveryChannel;
}
```
