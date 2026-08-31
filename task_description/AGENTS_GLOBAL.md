# AGENTS_GLOBAL.md — Глобальні правила проекту Vehicle Cost Tracker (v4)

Цей документ містить правила, стандарти та архітектурні рішення для проекту **Vehicle Cost Tracker**.
Обов'язковий до ознайомлення перед будь-яким завданням.

> **Оновлено 2026-08-24 (v3 → v4).** Попередня версія описувала проєкт
> як React-SPA на mock-даних із бекендом "у майбутньому". Це вже не
> так: Django+DRF бекенд написаний і живе в проді. Деталі — нижче та в
> `task_description/transport/*.md` (звірено з реальним кодом),
> `STATE.md` (поточний прогрес).

---

## 1. Огляд проекту

**Vehicle Cost Tracker** — система автоматизації обліку, аналізу та управління транспортними витратами.

**Два репозиторії, спільний деплой** (Raspberry Pi, `warehouse.mom`):
- `vehicle_tracker_api` — Django + DRF backend (цей репозиторій).
- `vehicle_cost_tracker` — React + TypeScript + Vite frontend.

**Основні модулі:**
- **Driver UI (PWA)** — мобільний інтерфейс для водіїв власного автопарку. Реалізовано (Фаза 13 `CODING_GUIDE.md`), включно з логіном через Telegram Mini App.
- **Fleet / Logistics (Desktop)** — керування автопарком, найманим транспортом та службами доставки. Бекенд готовий (`apps.cars`, `apps.logistics`); фронтенд-сторінки ще не набрані (Фаза 16, Крок 12-13 "Що далі" `CODING_GUIDE.md`).
- **Analytics** — розрахунок собівартості доставки та порівняння каналів. Свідомо відкладено — ні бекенд (`apps.analytics`), ні фронтенд ще не написані, чекають накопичення реальних даних.

---

## 2. Tech Stack

### Frontend

| Компонент    | Технологія                                   |
|--------------|----------------------------------------------|
| Framework    | React 18 + TypeScript + Vite                 |
| Styling      | Tailwind CSS                                 |
| State (Data) | TanStack Query v5                            |
| Routing      | React Router v6                              |
| Charts       | Recharts (ще не використано — аналітика не написана) |
| PWA          | vite-plugin-pwa                              |
| Utilities    | date-fns, papaparse, html5-qrcode            |
| Auth         | Django session + CSRF cookie (не JWT, не окремий токен) |

### Backend

| Компонент    | Технологія                                   |
|--------------|----------------------------------------------|
| Framework    | Django + Django REST Framework               |
| Database     | PostgreSQL                                   |
| Auth         | Django session + CSRF (`DEFAULT_AUTHENTICATION_CLASSES` — стандартні Session + Basic) |
| Bot          | `aiogram` (Telegram) — реєстрація водіїв, підтвердження ролі |
| Containerization | Docker + Docker Compose, `network_mode: host` |
| CI/CD        | GitHub Actions → SSH через Cloudflare Tunnel → на Pi |

> ⚠️ DRF тут завжди віддає `403`, не `401`, без авторизації —
> `SessionAuthentication` (перший автентифікатор за замовчуванням) не
> має `WWW-Authenticate`-заголовка, тому DRF занижує `401 → 403`. Це
> для всього API, не помилка конкретного ендпоінту.

---

## 3. Архітектурні принципи

### 3.1 Ексклюзивність каналів доставки
Кожна накладна належить **тільки одному** каналу: `own` (власний автопарк), `hired` (найманий), або `carrier` (служби доставки).
- Реалізовано на рівні **app-логіки** (DRF views), не БД-constraint:
  `unique=True` на `waybill_number` у таблицях-прив'язках
  (`hired_trip_waybills`, `carrier_shipment_waybills`) + явна перевірка
  `delivery_channel` перед призначенням каналу.

### 3.2 Режими трекінгу водія
- `daily` — мінімальний звіт (ранок + вечір).
- `full` — детальний звіт з відмітками на кожній точці вивантаження.

### 3.3 Облік палет
Палети фіксуються:
- В режимі `daily`: сумарно при виїзді зі складу.
- В режимі `full`: на кожній точці вивантаження.

---

## 4. Структура проєкту

### Frontend (`vehicle_cost_tracker/src/`)

```
src/
├── types/          # TypeScript інтерфейси (Single Source of Truth)
├── mocks/          # ЛИШЕ 4 файли: cars, drivers, route-events, waybills (не 15, як планувалось)
├── api/            # Запити до реального Django API (+ mock-режим через VITE_USE_MOCK)
├── hocks/          # ⚠️ так, "hocks" не "hooks" — реальна назва папки в коді
├── utils/          # Чисті функції для розрахунків (calcTransportCost...)
├── components/     # UI компоненти (ui/, layouts/, driver/, waybills/, fleet/⏳, hired/⏳, carriers/⏳)
└── pages/          # Сторінки (driver/, waybills — частково; fleet/hired/carriers/analystics/admin ⏳)
```

Детальний реальний інвентар (що вже існує, а що ще ⏳) —
`task_description/transport/05_COMPONENTS_HOOKS_UTILS.md`.

### Backend (`vehicle_tracker_api/apps/`)

```
apps/
├── accounts/     # Profile (ролі), Telegram-бот, авторизація
├── cars/          # Car, Driver, RouteEvent, MonthlyCosts (Фаза 6-7, задеплоєно)
├── products/      # Product, ProductCategory, ProductLogistics
├── customers/     # Customer, Store, StoreDeliveryAddress
├── waybills/      # WaybillRecord (реєстр накладних із 1С)
├── logistics/     # HiredTransportTrip, CarrierShipment/CarrierCost (Фаза 11, готово)
└── analytics/     # ⏳ порожньо, свідомо
```

---

## 5. Стиль коду та патерни

### 5.1 React Компоненти
- Використовувати **Функціональні компоненти (FC)**.
- Пропси мають бути типізовані через `interface` або `type`.
- Логіку виносити в кастомні хуки (`src/hocks/`).

### 5.2 TypeScript
- Суворий режим типізації. Уникати `any`.
- Всі сутності мають відповідати типам з `src/types/index.ts`.

### 5.3 Стилізація
- Виключно **Tailwind CSS**.
- Для мобільних інтерфейсів використовувати `Safe Area` та забезпечувати зручність кліку (мін. 44px).

### 5.4 Django / DRF
- ViewSets (`viewsets.ModelViewSet`) + `DefaultRouter`, не function-based views.
- `get_permissions()` для рольового розмежування читання/запису
  (`IsAuthenticated`, `IsManagerOrHead`, `IsLogistOrAbove` —
  `apps/accounts/permissions.py`).
- `verbose_name`/`help_text` українською на кожному полі моделі.
- `db_table` — явний `snake_case`, не покладатись на Django-дефолт.

---

## 6. Робота з даними

Фронтенд працює через **TanStack Query**, реальний DRF API — за
замовчуванням (`VITE_USE_MOCK=false` у проді). Mock-режим
(`VITE_USE_MOCK=true`, локальний dev) лишається паралельно в кожному
`api/*.ts` файлі як `if (USE_MOCK) {...}` гілка — не окремий шар, який
"перемкнеться на DRF колись у майбутньому": DRF вже є, mock — просто
альтернативний шлях у тому самому коді для розробки без бекенду під
рукою.

```typescript
// Приклад виклику в компоненті
const { data, isLoading } = useWaybills(filters, sort, pagination);
```

---

## 7. Git Workflow

**Коміти:** проєкт історично НЕ дотримується суворо Conventional
Commits (реальні повідомлення — суміш `faza_8: ...`, `Fixed bot
functionality...`, `docs: ...`) — орієнтуйся на стислий, змістовний
опис "чому", а не жорсткий формат.

**Перед кожним комітом:**
- Код має бути відформатований.
- Типи мають сходитись (`npx tsc -b` для фронтенду, `python manage.py check` для бекенду).
- Переконатися, що бізнес-логіка не порушує ексклюзивність каналів.
- Міграції створені й накочені (`makemigrations`/`migrate`), якщо змінювались моделі.

---

## 8. Джерела істини (де шукати актуальний стан)

| Питання | Де дивитись |
|---|---|
| Бізнес-логіка, ролі, БД-схема, TS-типи | `task_description/transport/01-08_*.md` (звірено з кодом 2026-08-24) |
| Покроковий процес розробки бекенду | `DJANGO_CODING_GUIDE.md` (Фаза 1-11) |
| Покроковий процес розробки фронтенду | `vehicle_cost_tracker/CODING_GUIDE.md` (Фаза 1-16) |
| Поточний прогрес, живі інциденти | `task_description/STATE.md` |
| Формат імпорту з 1С (Крок 11, у роботі) | `task_description/IMPORT_1C_SPEC.md` |
| Telegram-бот, деплой | `TELEGRAM_BOT_SETUP.md` |

> Обидва `*_CODING_GUIDE.md` — сценарії для ручного набору коду
> ("пиши руками"), **не changelog**: перевіряй, що файл справді існує,
> перш ніж вважати кроку виконаним — вже траплялись неправдиві
> позначки "виконано" в обох гайдах.

> ⚠️ `task_description/warehouse/` — **не цей проєкт**. Окремий,
> непов'язаний Django-застосунок (облік складських витрат), запланований
> на майбутнє, коду якого в цьому репозиторії немає.
