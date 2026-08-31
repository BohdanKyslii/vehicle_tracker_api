# Vehicle Cost Tracker — Структура файлів проєкту

> **Оновлено 2026-08-24.** Первинна версія описувала тільки фронтенд
> (`vehicle-tracker/`) як єдиний майбутній React SPA. Реально проєкт —
> **два окремі репозиторії** (`[[project_vehicle_cost_tracker_split]]`
> у пам'яті агента, якщо працюєш через Claude Code):
> `vehicle_tracker_api` (Django backend) і `vehicle_cost_tracker`
> (React frontend), кожен зі своїм деплоєм на той самий Raspberry Pi.
> Нижче — реальне дерево обох, не аспіраційне.

---

## Backend — `vehicle_tracker_api/`

```
vehicle_tracker_api/
│
├── apps/
│   ├── accounts/            # Авторизація, ролі, Telegram-бот
│   │   ├── models.py        # Profile (role/phone/telegram_id/driver)
│   │   ├── views.py         # /api/auth/* (csrf, login, register, logout, telegram)
│   │   ├── permissions.py   # HasRole, IsManagerOrHead, IsLogistOrAbove
│   │   ├── bot.py           # aiogram: реєстрація, підтвердження ролі, призначення авто
│   │   ├── telegram_auth.py     # verify_init_data() — HMAC перевірка Mini App
│   │   ├── telegram_notify.py   # синхронний виклик Telegram API (для веб-реєстрації)
│   │   ├── notifications.py     # notify_admin_new_registration()
│   │   └── management/commands/run_bot.py
│   ├── cars/                 # Car, CarSpecs, Trailer, CarStatusLog, Driver, RouteEvent, MonthlyCosts
│   ├── products/             # Product, ProductCategory, ProductLogistics
│   ├── customers/            # Customer, Store, StoreDeliveryAddress
│   ├── waybills/             # WaybillRecord
│   ├── logistics/            # HiredTransportTrip/HiredTripWaybill, CarrierShipment/CarrierShipmentWaybill/CarrierCost
│   └── analytics/            # ⏳ порожній — models.py/views.py лише заглушки, свідомо
│
├── config/
│   ├── settings.py           # REST_FRAMEWORK, TELEGRAM_*, DB, INSTALLED_APPS
│   ├── urls.py                # підключення apps.*.urls
│   ├── asgi.py / wsgi.py
│
├── task_description/          # Уся документація й контекст (цей файл — тут)
│   ├── transport/              # ← ти зараз тут: специфікація ЦЬОГО проєкту
│   ├── warehouse/               # НЕ цей проєкт — окремий, непов'язаний Django-застосунок
│   ├── file_1C/                 # Реальні вивантаження з 1С для дослідження імпорту
│   ├── IMPORT_1C_SPEC.md        # Дослідження форматів + відкриті питання (Крок 11)
│   ├── STATE.md                 # Поточний стан, оновлюється щосесії
│   ├── CLAUDE.md / AGENTS_GLOBAL.md / AI_AGENT_CONTEXT.md / TASK.md
│
├── DJANGO_CODING_GUIDE.md     # Покроковий гайд для ручного набору бекенду (Фаза 1-11)
├── TELEGRAM_BOT_SETUP.md      # Архітектура й розгортання бота
├── docker-compose.yml         # сервіси api + bot, network_mode: host
├── Dockerfile
├── requirements.txt / pyproject.toml / uv.lock
├── manage.py
└── .github/workflows/deploy.yml   # CI/CD: git pull + docker compose build/up на Pi
```

---

## Frontend — `vehicle_cost_tracker/`

```
vehicle_cost_tracker/
│
├── src/
│   ├── types/index.ts          # Всі TypeScript інтерфейси (03_TYPESCRIPT_TYPES.md — дзеркало)
│   │
│   ├── mocks/                  # ЛИШЕ 4 файли (07_MOCK_DATA.md для повного списку відсутнього)
│   │   ├── cars.json
│   │   ├── drivers.json
│   │   ├── route-events.json
│   │   └── waybills.json
│   │
│   ├── api/                    # 6 файлів: config, auth, cars, drivers, routeEvents, waybills
│   ├── hocks/                  # ⚠️ так, "hocks" не "hooks" — реальна назва папки в коді
│   │   ├── useAuthModal.ts
│   │   ├── useCars.ts
│   │   ├── useCurrentUser.ts
│   │   ├── useDayMode.ts
│   │   ├── useDrivers.ts
│   │   ├── useRouteEvents.ts
│   │   ├── useWaybillFilters.ts
│   │   └── useWaybills.ts
│   ├── utils/                  # calcProduct, calcSummary, calcTransportCost, clientFilter,
│   │                           # eventHelpers, formatters, parseQR — 7 файлів
│   │
│   ├── components/
│   │   ├── ui/                 # Badge, Button, EmptyState, ErrorBanner, Input, Pagination,
│   │   │                       # SortHeader, Spinner, ui.tsx
│   │   ├── layouts/             # DriverLayout, MainLayout, TopNav
│   │   ├── auth/                 # AuthModal
│   │   ├── driver/                # DayModeSwitch, ui.tsx
│   │   ├── waybills/              # WaybillFiltersBar, WaybillList, WaybillTable
│   │   ├── fleet/                  # ⏳ порожньо (Фаза 16)
│   │   ├── hired/                  # ⏳ порожньо (Крок 12 "Що далі")
│   │   ├── carriers/               # ⏳ порожньо (Крок 13 "Що далі")
│   │   └── analystics/             # ⏳ порожньо, і назва з друкарською помилкою
│   │                               # (не "analytics"! звернути увагу при створенні файлів)
│   │
│   ├── pages/
│   │   ├── driver/               # DriverDashboard, EventForm
│   │   ├── DriverMiniApp.tsx      # Telegram Mini App вхід + редірект за роллю
│   │   ├── LandingPage.tsx
│   │   ├── PlaceholderPage.tsx    # універсальна заглушка "в розробці"
│   │   ├── UnderConstruction.tsx  # старіша заглушка, дублює PlaceholderPage
│   │   ├── fleet/ hired/ carriers/ analystics/ admin/ waybills/   # ⏳ усі порожні
│   │
│   ├── styles/landing.css
│   ├── App.tsx                   # ⚠️ /driver-app — критичний маршрут, двічі губився при рефакторингу
│   ├── main.tsx
│   └── index.css
│
├── documents/                    # Design-докси ЦЬОГО репозиторію (аналог task_description/transport/
│   │                              # тут, історично розійшлись — див. нижче)
│   ├── 01_PROJECT_OVERVIEW.md ... 08_PROJECT_STRUCTURE.md
│
├── CODING_GUIDE.md               # Покроковий гайд для ручного набору фронтенду (Фаза 1-16)
├── Dockerfile / nginx.conf / docker-compose.yml
├── .env / .env.production        # VITE_USE_MOCK, VITE_API_BASE, VITE_TELEGRAM_BOT_USERNAME
├── package.json / tsconfig*.json / vite.config.ts
└── .github/workflows/deploy.yml
```

> ⚠️ **Два паралельні набори design-доксів для того самого продукту:**
> `vehicle_tracker_api/task_description/transport/*.md` (цей файл — тут)
> і `vehicle_cost_tracker/documents/*.md`. Історично розійшлись
> (створювались одночасно на старті, потім кожен репозиторій оновлював
> свою копію окремо, або й зовсім не оновлював). Якщо порівнюєш —
> `vehicle_cost_tracker/documents/01_PROJECT_OVERVIEW.md` ближчий до
> актуального бізнес-опису (менше розійшовся), а схема БД/типи повніше
> й точніше саме тут, у `task_description/transport/`, бо вони звірені
> з реальним Django-кодом безпосередньо 2026-08-24.

---

## Спільний хостинг

Обидва репозиторії деплояться на **один Raspberry Pi**
(`rasberry_kisliy@192.168.0.114`, домен `warehouse.mom`),
`network_mode: host` в обох `docker-compose.yml`. `nginx.conf`
фронтенду проксіює `/api/`, `/admin/`, `/static/` на бекенд
(`127.0.0.1:8000`), решту віддає React SPA (`try_files ... /index.html`).
CI/CD — окремий GitHub Actions workflow в кожному репозиторії, обидва
йдуть через SSH-тунель Cloudflare (Pi без публічної IP).

---

## Правила іменування (актуальні)

| Категорія | Конвенція | Приклад | Примітка |
|-----------|-----------|---------|------|
| Компоненти | PascalCase | `WaybillTable.tsx` | |
| Hooks | `use` + PascalCase, у папці `hocks/` | `useWaybillFilters.ts` | не `hooks/`! |
| Utils | camelCase | `calcTransportCost.ts` | |
| Типи | PascalCase | `HiredTransportTrip` | |
| Django apps | однина/множина за доменом | `cars`, `waybills`, `logistics` | |
| Django моделі | PascalCase, `db_table` — snake_case | `WaybillRecord` → `waybill_records` | |
| Змінні оточення | `VITE_` prefix (frontend), без префіксу (backend `.env`) | `VITE_USE_MOCK`, `TELEGRAM_BOT_TOKEN` | |
