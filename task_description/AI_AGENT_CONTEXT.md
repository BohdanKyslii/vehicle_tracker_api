# AI_AGENT_CONTEXT.md — Технічний контекст проекту Vehicle Cost Tracker (v4)

Технічний контекст для AI-агентів. Читати після `AGENTS_GLOBAL.md`.

> **Оновлено 2026-08-24.** Попередня версія (v3) описувала проєкт як
> "React PWA, MVP на Mock-даних" і містила кілька фактичних помилок
> незалежно від застарілості (неправильна назва поля `RouteEvent.type`
> замість реального `eventType`, вигадані значення enum, компоненти й
> хуки, яких у реальному коді немає). Нижче — звірено з реальним кодом.
> Повний і детальний контракт типів — `task_description/transport/03_TYPESCRIPT_TYPES.md`
> (дзеркало `src/types/index.ts`), тут — лише найважливіше й
> найчастіше плутане.

---

## Проект

**Назва:** Vehicle Cost Tracker
**Тип:** Django + DRF backend (живий, задеплоєний) + React PWA frontend
**Backend:** Django, DRF, PostgreSQL, сесійна авторизація.
**Frontend:** React 18, TypeScript, Vite, TanStack Query v5, Tailwind CSS.

`VITE_USE_MOCK` перемикає фронтенд між mock JSON (лише для локальної
розробки без піднятого бекенду) і реальним DRF API — у проді завжди
`false`.

---

## Ключові сутності (Types)

### `Car`
```typescript
interface Car {
  idCar: number;
  nameCar: string;
  numberCar: string;
  fuelCardNumber?: number;    // не було в v3
  amountCar: number;          // Амортизація грн/міс
  defaultTrackingMode?: 'daily' | 'full';
  statusCar: 'active' | 'repair' | 'inactive';
  isActive: boolean;
  specs?: CarSpecs;            // не було в v3 — VIN, габарити, гідроборт
  trailer?: Trailer;           // не було в v3
}
```

### `WaybillRecord`
```typescript
interface WaybillRecord {
  id: number;
  legalEntity: 'ESP' | 'OPT' | 'Rubin';
  waybillNumber: string;
  waybillDate: string;
  linePosition: number;
  customerId: string;         // ⚠️ типізовано як string, хоча Customer.idCustomer — number (жива непослідовність, не виправлено)
  customerName: string;
  storeId?: string;
  productId: number;          // число, не string — артикул з 1С зберігається як IntegerField на бекенді
  productName: string;
  quantity: number;           // + відвантаження, − повернення
  priceUah: number;
  totalUah: number;
  deliveryChannel?: 'own' | 'hired' | 'carrier' | null;
  // ... повний список полів — 03_TYPESCRIPT_TYPES.md
}
```

### `RouteEvent`
```typescript
interface RouteEvent {
  id: number;
  carId: number;
  driverId: number;
  eventType: RouteEventType;   // ⚠️ поле називається eventType, НЕ type
  eventTs: string;
  palletsCount?: number;       // Обов'язково для depot_start (daily) та delivery (full)
  // ...
}

// Реальні значення enum (8, не 4 вигаданих):
type RouteEventType =
  | 'depot_start' | 'delivery' | 'parking_end' | 'depot_return'
  | 'refuel' | 'other_cost' | 'return_goods' | 'extra_cargo';
// 'fuel' і 'depot_finish' НЕ існують — це були вигадані назви в v3.
```

---

## Структура Mock-даних (`src/mocks/`)

**Реально існує лише 4 файли** (не 15, як планувалось спочатку, і не
той список, що був у v3):
- `cars.json`
- `drivers.json`
- `route-events.json`
- `waybills.json`

`hired-trips.json`, `customers.json`, `stores.json`, `products.json`
тощо — **не існують**, бо відповідних сторінок ще не написано (Фаза 16,
Крок 12-14 "Що далі" `CODING_GUIDE.md`). Не посилайся на них, поки не
створюєш сторінку, яка їх реально споживає.

---

## Бізнес-логіка

### 1. Розрахунок собівартості (Allocation)
- **Власний автопарк:** місячні витрати (`MonthlyCosts`) розподіляються
  між накладними авто за місяць пропорційно до суми продажу (`total_uah`).
  Реалізовано лише як SQL-начерк VIEW в `02_DATABASE_SCHEMA.md`
  (`transport_cost_per_waybill`) — **фактичного ендпоінту/VIEW у БД
  немає**, `apps.analytics` порожній.
- **Найманий транспорт:** вартість рейсу (`cost_uah`) — по задуму
  ділиться між прив'язаними накладними; конкретна формула розподілу
  ще не реалізована (бекенд-модель `HiredTransportTrip` + прив'язка
  накладних є, розрахунок — ні).
- **Служби доставки:** вартість береться з `CarrierCost` по `ttn`,
  матчиться автоматично при імпорті (`perform_create` у
  `CarrierCostViewSet`).

### 2. Ексклюзивність каналів (Channel Guard)
Перед прив'язкою накладної до рейсу/відправлення бекенд перевіряє
`delivery_channel`. **На фронтенді немає окремого `checkWaybillChannel`-
guard хука** (`useWaybillChannelGuard` із v3 не існує) — перевірка
відбувається на бекенді при виклику
`POST /api/hired-transport-trips/{id}/attach_waybill/` /
`POST /api/carrier-shipments/{id}/attach_waybill/` (400, якщо канал уже
зайнятий), фронтенд-форм для цього ще не написано взагалі.

### 3. Режими водія (Day Mode)
- Зберігається в `localStorage`, реальний ключ — `dayMode:{today}`
  (без `carId` у ключі, на відміну від того, що описував v3).
- Якщо режим `daily`, то `palletsCount` запитується один раз при
  старті (`depot_start`).
- Якщо режим `full`, то `palletsCount` запитується при кожній доставці
  (`delivery`).

---

## UI Компоненти та Патерни (реальний інвентар)

### Базові компоненти (`src/components/ui/`)
Реально є: `Badge`, `Button`, `EmptyState`, `ErrorBanner`, `Input`,
`Pagination`, `SortHeader`, `Spinner`.

**Не існують** (були у v3 як вже готові — насправді ще не написані):
`ChannelBadge`, `CarStatusBadge`, `PalletsInput`, `StoreConfirmModal`,
`Modal`, `Select`, `Toast`, `DatePicker`. Повний реальний vs
запланований інвентар — `task_description/transport/05_COMPONENTS_HOOKS_UTILS.md`.

### Хуки (`src/hocks/` — так, не `hooks/`, реальна назва папки в коді)
Реально є: `useAuthModal`, `useCars`, `useCurrentUser`, `useDayMode`,
`useDrivers`, `useRouteEvents`, `useWaybillFilters`, `useWaybills`.

**Не існує** `useWaybillChannelGuard` (був у v3) — жодного хука для
клієнтської перевірки ексклюзивності каналу немає.

---

## Типові помилки та як їх уникнути

| Ситуація | Правильно |
|----------|-----------|
| Поле типу події маршруту | `eventType`, НЕ `type` |
| Шлях до хуків | `src/hocks/`, НЕ `src/hooks/` (реальна назва папки) |
| Артикул товару (`productId`) | `number`, не `string` — 1С-артикул зберігається як `IntegerField` |
| Ексклюзивність каналу | Перевіряється на бекенді при `attach_waybill`, окремого клієнтського guard-хука немає |
| Дати | `YYYY-MM-DD`; для 1С-джерел зустрічаються й інші формати (`DD.MM.YY` в ЄСП/ОПТ) — див. `IMPORT_1C_SPEC.md` |
| Числа з DRF | `DecimalField` бекенду серіалізується в JSON як **рядок**, не число — явний `Number(...)`/`parseFloat` при мапінгу (див. `api/cars.ts`, `mapCar()`) |
| Мобільний UI | Забезпечувати `min-height: 44px` для кнопок |
| Довіра "виконано" в гайдах | Обидва `*_CODING_GUIDE.md` — сценарії для ручного набору коду, не changelog; перевіряй файли перед тим, як вважати крок готовим |
