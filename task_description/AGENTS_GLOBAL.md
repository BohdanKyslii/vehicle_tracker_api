# AGENTS_GLOBAL.md — Глобальні правила проекту Vehicle Cost Tracker (v3)

Цей документ містить правила, стандарти та архітектурні рішення для проекту **Vehicle Cost Tracker**.
Обов'язковий до ознайомлення перед будь-яким завданням.

---

## 1. Огляд проекту

**Vehicle Cost Tracker** — система автоматизації обліку, аналізу та управління транспортними витратами.

**Основні модулі:**
- **Driver UI (PWA)** — мобільний інтерфейс для водіїв власного автопарку.
- **Logistics (Desktop)** — керування найманим транспортом та службами доставки.
- **Analytics** — розрахунок собівартості доставки та порівняння каналів.

---

## 2. Tech Stack

| Компонент    | Технологія                                   |
|--------------|----------------------------------------------|
| Framework    | React 18 + TypeScript + Vite                 |
| Styling      | Tailwind CSS                                 |
| State (Data) | TanStack Query v5                            |
| Routing      | React Router v6                              |
| Charts       | Recharts                                     |
| PWA          | vite-plugin-pwa                              |
| Utilities    | date-fns, papaparse, html5-qrcode            |
| Mocking      | Local JSON files + Fetch API logic           |

---

## 3. Архітектурні принципи

### 3.1 Ексклюзивність каналів доставки
Кожна накладна належить **тільки одному** каналу: `own` (власний автопарк), `hired` (найманий), або `carrier` (служби доставки).
- Система має блокувати спроби додати накладну в інший канал, якщо вона вже десь закріплена.

### 3.2 Режими трекінгу водія
- `daily` — мінімальний звіт (ранок + вечір).
- `full` — детальний звіт з відмітками на кожній точці вивантаження.

### 3.3 Облік палет
Палети фіксуються:
- В режимі `daily`: сумарно при виїзді зі складу.
- В режимі `full`: на кожній точці вивантаження.

---

## 4. Структура проєкту (v3)

```
src/
├── types/          # TypeScript інтерфейси (Single Source of Truth)
├── mocks/          # JSON файли з даними (cars, waybills, route-events...)
├── api/            # Логіка запитів до даних (навіть якщо це mock)
├── hooks/          # React hooks для бізнес-логіки (useWaybills, useCars...)
├── utils/          # Чисті функції для розрахунків (calcTransportCost...)
├── components/     # UI компоненти (ui/, layouts/, driver/, fleet/...)
└── pages/          # Сторінки (driver/, fleet/, analytics/, admin/...)
```

---

## 5. Стиль коду та патерни

### 5.1 React Компоненти
- Використовувати **Функціональні компоненти (FC)**.
- Пропси мають бути типізовані через `interface` або `type`.
- Логіку виносити в кастомні хуки.

### 5.2 TypeScript
- Суворий режим типізації. Уникати `any`.
- Всі сутності мають відповідати типам з `src/types/index.ts`.

### 5.3 Стилізація
- Виключно **Tailwind CSS**.
- Для мобільних інтерфейсів використовувати `Safe Area` та забезпечувати зручність кліку (мін. 44px).

---

## 6. Робота з даними (Mock API)

В MVP ми використовуємо Mock-дані, але працюємо з ними через **TanStack Query**, імітуючи реальний API.
Це дозволить швидко переключитись на Django DRF у майбутньому.

```typescript
// Приклад виклику в компоненті
const { data, isLoading } = useWaybills(filters);
```

---

## 7. Git Workflow

**Коміти (Conventional Commits):**
```
feat(driver): add pallets input to event form
fix(analytics): correct cost allocation for hired trips
docs: update implementation status in STATE.md
```

**Перед кожним комітом:**
- Код має бути відформатований.
- Типи мають сходитись.
- Переконатися, що бізнес-логіка не порушує ексклюзивність каналів.
