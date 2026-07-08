# Vehicle Cost Tracker — TypeScript типи

Файл: `src/types/index.ts`

---

## Довідники

```typescript
// ── Категорії товарів ──────────────────────────────────────
export interface ProductCategory {
  idCategory: number;
  nameCategory: string;
}

// ── Товар ─────────────────────────────────────────────────
export interface Product {
  idProduct: string;
  nameProduct: string;
  idCategory: number | null;
  isActive: boolean;
  category?: ProductCategory;
  logistics?: ProductLogistics;
}

// ── Логістичні дані товару ────────────────────────────────
export interface ProductLogistics {
  idProduct: string;
  unitWeightKg?: number;
  unitLengthCm?: number;
  unitWidthCm?: number;
  unitHeightCm?: number;
  unitsPerBox?: number;
  boxWeightKg?: number;
  boxLengthCm?: number;
  boxWidthCm?: number;
  boxHeightCm?: number;
  unitVolumeCbm?: number;   // розрахунковий
  boxVolumeCbm?: number;    // розрахунковий
}

// ── Клієнт ────────────────────────────────────────────────
export interface Customer {
  idCustomer: string;
  nameCustomer: string;
  networkCustomer?: string;
  isActive: boolean;
}

// ── Магазин / торгова точка ───────────────────────────────
export interface Store {
  idStore: string;
  idCustomer: string;
  nameStore: string;
  storeAddress?: string;
  isActive: boolean;
  customer?: Customer;
  deliveryAddresses?: StoreDeliveryAddress[];
}

export interface StoreDeliveryAddress {
  id: number;
  idStore: string;
  deliveryAddress: string;
  isPrimary: boolean;
  notes?: string;
}

// ── Авто власного автопарку ───────────────────────────────
export type TrackingMode = "daily" | "full";
export type CarStatus = "active" | "repair" | "inactive";

export interface Car {
  idCar: number;
  nameCar: string;
  numberCar: string;
  amountCar: number;            // амортизація грн/міс
  defaultTrackingMode: TrackingMode;
  statusCar: CarStatus;
  isActive: boolean;
}

// ── Водій ─────────────────────────────────────────────────
export interface Driver {
  idDriver: number;
  nameDriver: string;
  phone?: string;
  idCar: number | null;
  isActive: boolean;
  car?: Car;
}

// ── Юридична особа ────────────────────────────────────────
export type LegalEntity = "ESP" | "OPT" | "Rubin";

// ── Канал доставки ────────────────────────────────────────
export type DeliveryChannel = "own" | "hired" | "carrier";
```

---

## Реєстр накладних

```typescript
// ── Рядок накладної із 1С ─────────────────────────────────
export interface WaybillRecord {
  id: number;
  legalEntity: LegalEntity;
  waybillNumber: string;
  waybillDate: string;
  linePosition: number;
  customerId: string;
  customerName: string;
  storeId?: string;             // нове поле
  productId: string;
  productName: string;
  quantity: number;             // + відвантаження, − повернення
  priceUah: number;
  totalUah: number;
  comment?: string;
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  volumetricWeightKg?: number;
  deliveryChannel?: DeliveryChannel | null;  // null = ще не призначено
  importedAt: string;
  importBatchId?: string;
}

export type WaybillLineType = "shipment" | "return";

// ── Агрегована накладна ───────────────────────────────────
export interface WaybillSummary {
  legalEntity: LegalEntity;
  waybillNumber: string;
  waybillDate: string;
  customerId: string;
  customerName: string;
  storeId?: string;
  linesCount: number;
  totalUah: number;
  returnsUah: number;
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  deliveryChannel?: DeliveryChannel | null;
  // деталі каналу (залежно від deliveryChannel)
  carId?: number;               // own
  carNumber?: string;           // own
  tripId?: number;              // hired
  tripRouteName?: string;       // hired
  shipmentId?: number;          // carrier
  carrierName?: string;         // carrier
  status: WaybillStatus;
}

export type WaybillStatus =
  | "pending"     // не призначено до каналу
  | "scanned"     // відскановано
  | "delivered"
  | "cancelled";
```

---

## Трекінг — власний автопарк

```typescript
// ── Тип події ─────────────────────────────────────────────
export type RouteEventType =
  | "depot_start"
  | "delivery"
  | "parking_end"
  | "depot_return"
  | "refuel"
  | "other_cost"
  | "return_goods"
  | "extra_cargo";

// ── Відмова від поставки ──────────────────────────────────
export interface DeliveryRejection {
  isFull: boolean;
  productId?: string;
  quantity?: number;
  comment?: string;
}

// ── Подія маршруту ────────────────────────────────────────
export interface RouteEvent {
  id: number;
  carId: number;
  driverId: number;
  trackingMode: TrackingMode;
  eventType: RouteEventType;
  eventTs: string;
  odometerKm?: number;
  palletsCount?: number;        // нове поле

  // delivery
  waybillNumber?: string;
  waybillDate?: string;
  customerName?: string;
  rejection?: DeliveryRejection;

  // refuel
  fuelLiters?: number;
  fuelCostUah?: number;
  adBlueLiters?: number;
  adBlueCostUah?: number;

  // other_cost
  otherCostsUah?: number;
  otherCostsComment?: string;

  // return_goods
  returnClientWaybill?: string;

  // extra_cargo
  extraFrom?: string;
  extraTo?: string;
  extraWeightKg?: number;
  extraWaybill?: string;
  extraComment?: string;

  notes?: string;
  createdAt: string;
}

export type RouteEventCreate = Omit<RouteEvent, "id" | "createdAt">;

// ── Відрізок маршруту ─────────────────────────────────────
export interface RouteSegment {
  fromEvent: RouteEventType;
  toEvent: RouteEventType;
  waybillNumber?: string;
  customerName?: string;
  distanceKm: number;
  durationMin: number;
}

// ── Денний підсумок ───────────────────────────────────────
export interface DailySummary {
  carId: number;
  driverId: number;
  trackingMode: TrackingMode;
  date: string;
  totalMileageKm: number;
  loadedMileageKm: number | null;
  emptyMileageKm: number | null;
  palletsCount: number | null;  // нове поле
  fuelLiters: number;
  fuelCostUah: number;
  adBlueLiters: number;
  adBlueCostUah: number;
  otherCostsUah: number;
  deliveriesCount: number;
  returnsCount: number;
  extraCargoCount: number;
  waybillNumbers: string[];
  segments: RouteSegment[];
}
```

---

## Місячні витрати

```typescript
export interface MonthlyCosts {
  id: number;
  carId: number;
  month: string;
  salaryUah: number;
  taxesUah: number;
  depreciationUah: number;
  repairActualUah?: number;
  repairRateUahKm: number;
  otherCostsUah: number;
  otherCostsComment?: string;
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
// ── Рейс найманого транспорту ─────────────────────────────
export interface HiredTransportTrip {
  id: number;
  carNumber: string;            // вільний ввід
  routeName: string;            // «Пирятин, Полтава, Харків»
  tripDate: string;
  palletsCount?: number;
  costUah: number;
  comment?: string;
  createdAt: string;
  // прив'язані накладні (join)
  waybills?: HiredTripWaybill[];
}

export type HiredTransportTripCreate = Omit<HiredTransportTrip, "id" | "createdAt" | "waybills">;

export interface HiredTripWaybill {
  id: number;
  tripId: number;
  waybillNumber: string;
  scannedAt: string;
}

// ── Форма внесення рейсу (логіст) ────────────────────────
export interface HiredTripFormState {
  carNumber: string;
  routeName: string;
  tripDate: string;
  palletsCount: string;
  costUah: string;
  comment: string;
  scannedWaybills: ScannedWaybill[];
}
```

---

## Служби доставки

```typescript
// ── Відправлення через службу ─────────────────────────────
export interface CarrierShipment {
  id: number;
  carrierName: string;          // «Нова Пошта», «Міст Експрес»
  ttn: string;                  // номер ТТН
  shipmentDate: string;
  comment?: string;
  createdAt: string;
  waybills?: CarrierWaybill[];
  cost?: CarrierCost;           // після імпорту реєстру
}

export type CarrierShipmentCreate = Omit<CarrierShipment, "id" | "createdAt" | "waybills" | "cost">;

export interface CarrierWaybill {
  id: number;
  shipmentId: number;
  waybillNumber: string;
  scannedAt: string;
}

// ── Рядок реєстру витрат від служби ──────────────────────
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

```typescript
// ── Транспортна собівартість по накладній (власний автопарк)
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

// ── Транспортна собівартість по клієнту ──────────────────
export interface TransportCostPerCustomer {
  customerId: string;
  customerName: string;
  networkCustomer?: string;
  waybillsCount: number;
  saleUah: number;
  totalWeightKg?: number;
  totalVolumeCbm?: number;
  // розбивка по каналах
  ownCostUah: number;
  hiredCostUah: number;
  carrierCostUah: number;
  totalCostUah: number;
  costPctOfSale: number;
}

// ── Місячний підсумок по авто ─────────────────────────────
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
  totalWeightKg?: number;
}

// ── Порівняння каналів доставки ───────────────────────────
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

export interface PaginationParams { page: number; pageSize: number; }

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
export interface SortParams { field: SortField; direction: SortDirection; }

export interface ImportResult {
  batchId: string;
  imported: number;
  skipped: number;
  errors: ImportError[];
}

export interface ImportError { row: number; field: string; message: string; }

export interface ScannedWaybill {
  waybillNumber: string;
  waybillDate: string;
  scannedAt: string;
  customerName?: string;
  storeName?: string;
  deliveryChannel?: DeliveryChannel;  // перевірка ексклюзивності при скануванні
}
```
