# AI_AGENT_CONTEXT.md — Технічний контекст проекту Vehicle Cost Tracker (v3)

Технічний контекст для AI-агентів. Читати після `AGENTS_GLOBAL.md`.

---

## Проект

**Назва:** Vehicle Cost Tracker
**Тип:** React PWA (MVP на Mock-даних)
**Технології:** React 18, TypeScript, Vite, TanStack Query v5, Tailwind CSS.

---

## Ключові сутності (Types)

### `Car`
```typescript
interface Car {
  idCar: number;
  nameCar: string;
  numberCar: string;
  amountCar: number;          // Амортизація грн/міс
  defaultTrackingMode: 'daily' | 'full';
  statusCar: 'active' | 'repair' | 'inactive';
  isActive: boolean;
}
```

### `WaybillRecord`
```typescript
interface WaybillRecord {
  waybillNumber: string;
  waybillDate: string;
  legalEntity: 'ESP' | 'OPT' | 'Rubin';
  storeId: string;
  deliveryChannel: 'own' | 'hired' | 'carrier' | null;
  // ... поля товарів
}
```

### `RouteEvent`
```typescript
interface RouteEvent {
  id: number;
  carId: number;
  type: 'depot_start' | 'delivery' | 'fuel' | 'depot_finish' | ...;
  palletsCount?: number;      // Обов'язково для depot_start (daily) та delivery (full)
  // ...
}
```

---

## Структура Mock-даних (`src/mocks/`)

Дані зберігаються у форматі JSON і використовуються для імітації API.
- `cars.json` — довідник авто.
- `waybills.json` — реєстр усіх накладних з прив'язкою до каналів.
- `route-events.json` — події маршрутів водіїв.
- `hired-trips.json` — рейси найманого транспорту.

---

## Бізнес-логіка

### 1. Розрахунок собівартості (Allocation)
- **Власний автопарк:** Місячні витрати (`MonthlyCosts`) розподіляються між усіма накладними авто за цей місяць пропорційно до обраної метрики (вага/палети/сума).
- **Найманий транспорт:** Вартість рейсу (`costUah`) розподіляється між накладними, що були відскановані для цього рейсу.
- **Служби доставки:** Вартість береться прямо з реєстру витрат служби (`CarrierCost`) по номеру ТТН.

### 2. Ексклюзивність каналів (Channel Guard)
Перед додаванням накладної до рейсу (будь-якого каналу) система має викликати `checkWaybillChannel(number)`.
- Якщо `deliveryChannel` вже встановлено і він не збігається з поточним — виводити помилку.

### 3. Режими водія (Day Mode)
- Зберігається в `localStorage` з ключем `dayMode:{carId}:{date}`.
- Якщо режим `daily`, то `palletsCount` запитується один раз при старті (`depot_start`).
- Якщо режим `full`, то `palletsCount` запитується при кожній доставці (`delivery`).

---

## UI Компоненти та Патерни

### Базові компоненти (`src/components/ui/`)
- `ChannelBadge` — відображає канал доставки з відповідним кольором.
- `PalletsInput` — спеціальний інпут з великими кнопками +/- для водіїв.
- `StoreConfirmModal` — підтвердження магазину при скануванні першої накладної в `daily` режимі.

### Хуки (`src/hooks/`)
- `useWaybillChannelGuard` — інкапсулює логіку перевірки ексклюзивності.
- `useDayMode` — керування поточним режимі водія.

---

## Типові помилки та як їх уникнути

| Ситуація | Правильно |
|----------|-----------|
| Додавання накладної | Завжди викликати `checkWaybillChannel` перед записом |
| Робота з ID авто | Використовувати `idCar`, а не `vehicleId` (v3 update) |
| Дати | Використовувати формат `YYYY-MM-DD` |
| Числа | Обробляти через `parseFloat` або `Number` (mock дані приходять як string/number) |
| Мобільний UI | Забезпечувати `min-height: 44px` для кнопок |
