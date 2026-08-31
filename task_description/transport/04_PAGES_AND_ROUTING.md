# Vehicle Cost Tracker — Сторінки та маршрутизація

> **Оновлено 2026-08-24.** Нижче — реальний `App.tsx` на сьогодні, не
> план. Кожен маршрут позначено: ✅ реальна сторінка / ⏳ `PlaceholderPage`
> ("в розробці", маршрут існує, контенту нема). Первинний план (весь
> цей файл раніше) описував кінцевий стан без розрізнення готове/ні —
> тепер розрізняємо явно, бо це і є найкорисніша інформація для
> вирішення "з чого продовжувати".

---

## Структура маршрутів (реальний `App.tsx`)

```tsx
<Routes>
  {/* ── Водій (мобільний) ────────────────────────── */}
  <Route path="/driver" element={<DriverLayout />}>
    <Route index element={<DriverDashboard />} />       {/* ✅ */}
    <Route path="event/new" element={<EventForm />} />  {/* ✅ */}
    <Route path="scan" element={<PlaceholderPage title="Сканер QR" />} />     {/* ⏳ Фаза 15 фронтенду */}
    <Route path="history" element={<PlaceholderPage title="Історія" />} />   {/* ⏳ */}
  </Route>

  {/* Telegram Mini App — логінить через initData, редіректить за роллю */}
  <Route path="/driver-app" element={<DriverMiniApp />} />  {/* ✅ real, редірект за profile.role — 2026-08-19 */}

  {/* ── Автопарк ─────────────────────────────────── */}
  <Route path="/fleet" element={<MainLayout />}>
    <Route index element={<PlaceholderPage title="Автопарк" />} />        {/* ⏳ Фаза 16 фронтенду */}
    <Route path=":carId" element={<PlaceholderPage title="Деталі авто" />} /> {/* ⏳ */}
  </Route>

  {/* ── Накладні ─────────────────────────────────── */}
  <Route path="/waybills" element={<MainLayout />}>
    <Route index element={<WaybillList />} />                                  {/* ✅ Фаза 11 фронтенду */}
    <Route path=":waybillNumber" element={<PlaceholderPage title="Деталі накладної" />} /> {/* ⏳ Крок 11 "ЩО ДАЛІ" */}
    <Route path="import" element={<PlaceholderPage title="Імпорт із 1С" />} /> {/* ⏳ Крок 11 бекенду ще пишеться */}
    <Route path="unassigned" element={<PlaceholderPage title="Не призначені" />} /> {/* ⏳ */}
    <Route path="returns" element={<PlaceholderPage title="Матчинг повернень" />} /> {/* ⏳ */}
  </Route>

  {/* ── Найманий транспорт ───────────────────────── */}
  <Route path="/hired" element={<MainLayout />}>
    <Route index element={<PlaceholderPage title="Найманий транспорт" />} />  {/* ⏳ Крок 12 "ЩО ДАЛІ" */}
    <Route path="new" element={<PlaceholderPage title="Новий рейс" />} />     {/* ⏳ */}
    <Route path=":tripId" element={<PlaceholderPage title="Деталі рейсу" />} /> {/* ⏳ */}
  </Route>

  {/* ── Служби доставки ──────────────────────────── */}
  <Route path="/carriers" element={<MainLayout />}>
    <Route index element={<PlaceholderPage title="Служби доставки" />} />     {/* ⏳ Крок 13 "ЩО ДАЛІ" */}
    <Route path="new" element={<PlaceholderPage title="Нове відправлення" />} /> {/* ⏳ */}
    <Route path="import-costs" element={<PlaceholderPage title="Імпорт реєстру витрат" />} /> {/* ⏳ */}
  </Route>

  {/* ── Аналітика ────────────────────────────────── */}
  <Route path="/analytics" element={<MainLayout />}>
    <Route index element={<PlaceholderPage title="Аналітика" />} />                  {/* ⏳ Крок 14 "ЩО ДАЛІ" */}
    <Route path="transport-costs" element={<PlaceholderPage title="Транспортна собівартість" />} /> {/* ⏳ */}
    <Route path="customers" element={<PlaceholderPage title="По клієнтах" />} />      {/* ⏳ */}
    <Route path="channels" element={<PlaceholderPage title="Порівняння каналів" />} /> {/* ⏳ */}
  </Route>

  {/* ── Адміністрування ──────────────────────────── */}
  <Route path="/admin" element={<MainLayout />}>
    <Route index element={<PlaceholderPage title="Адміністрування" />} />  {/* ⏳ */}
    <Route path="cars" element={<PlaceholderPage title="Авто" />} />
    <Route path="drivers" element={<PlaceholderPage title="Водії" />} />
    <Route path="products" element={<PlaceholderPage title="Товари" />} />
    <Route path="customers" element={<PlaceholderPage title="Клієнти" />} />
    <Route path="stores" element={<PlaceholderPage title="Магазини" />} />
    <Route path="monthly-costs" element={<PlaceholderPage title="Місячні витрати" />} />
  </Route>

  <Route path="/" element={<Navigate to="/driver" replace />} />
  <Route path="*" element={<div>404</div>} />
</Routes>
```

> ⚠️ **`/admin` фрагільний у проді.** `nginx.conf` проксіює запити з
> префіксом `/admin/` (зі слешем) напряму на Django Admin, минаючи React
> SPA — тому React-роут `/admin` реально доступний тільки через
> client-side навігацію (клік по `<Link>`), не через прямий перехід за
> URL/оновлення сторінки. Саме через цю фрагільність майбутній
> внутрішній адмін-екран (Крок 15 "ЩО ДАЛІ" — підтвердження реєстрацій)
> свідомо спроєктований на `/panel`, не `/admin` — див.
> `TELEGRAM_BOT_SETUP.md` і `CODING_GUIDE.md` Крок 15.

> ⚠️ **Маршрут `/driver-app` — критичний, двічі губився** при
> переписуванні `App.tsx` (див. `⚠️ НЕ ВИДАЛЯТИ` коментар прямо в
> коді). Це продакшн-точка входу з Telegram (кнопка меню бота).

---

## Реальний фронтир (де саме зупинились)

| Розділ | Статус | Джерело |
|---|---|---|
| `/driver` (DriverDashboard, EventForm) | ✅ реально | Фаза 13 `CODING_GUIDE.md` |
| `/driver-app` (Mini App + редірект за роллю) | ✅ реально | Фаза 4.5.6 + правка 2026-08-19 |
| `/waybills` (список) | ✅ реально | Фаза 11 `CODING_GUIDE.md` |
| `/waybills/:waybillNumber` (деталі) | ⏳ | Крок 11 "ЩО ДАЛІ" `CODING_GUIDE.md` |
| `RequireRole` (гейт по ролі на клієнті) | ⏳ не набрано | Фаза 14 `CODING_GUIDE.md` — файлу `RequireRole.tsx` не існує |
| `/driver/scan` (QRScanner) | ⏳ не набрано | Фаза 15 `CODING_GUIDE.md` |
| `/fleet` (FleetList/CarForm) | ⏳ не набрано | Фаза 16 `CODING_GUIDE.md` — **пріоритетно**, бо адмін/логіст тепер редіректиться сюди з Mini App і бачить заглушку |
| `/hired`, `/carriers` | ⏳ не набрано | Крок 12/13 "ЩО ДАЛІ" — залежать від бекенд `apps.logistics` (готовий, але й собі не набраний руками повністю — див. `STATE.md`) |
| `/analytics/*` | ⏳ не набрано | Крок 14 "ЩО ДАЛІ", і бекенд `apps.analytics` теж порожній |
| `/admin/*` | ⏳ не набрано | Django Admin поки заміняє |

---

## Сторінки детально (реалізовані)

### `/driver` — DriverDashboard ✅

**Що відображає:**
- Ім'я водія, авто (номер + назва), поточна дата
- `DayModeSwitch` — перемикач daily/full з дефолтом від логіста
- Поточний одометр
- Timeline подій поточного дня

### `/driver/event/new` — EventForm ✅

**Query param:** `?type=depot_start|delivery|refuel|...`

Форма змінюється за типом події й режимом (daily/full) — див.
`CODING_GUIDE.md` Фаза 13 для деталей полів.

### `/driver-app` — DriverMiniApp ✅

Логінить через Telegram `initData` (`POST /api/auth/telegram/`),
далі — `<Navigate>` за `profile.role`:
`driver` → `/driver`, `logist`/`manager`/`head` → `/fleet`
(реалізовано 2026-08-19; до цього — жорстко на `/driver` для всіх ролей).

### `/waybills` — WaybillList ✅

**Фільтри** (`WaybillFilters`, реалізовані):
`search`, `status`, `deliveryChannel` (own/hired/carrier/unassigned/all),
`legalEntity`.

---

## Сторінки в плані, ще не реалізовані

Первинний план нижче лишається орієнтиром "як має виглядати", коли
дійде черга — детальні очікувані поля не дублюю тут вдруге, вони вже є
в `03_TYPESCRIPT_TYPES.md` (`WaybillFilters`, `HiredTransportTripCreate`,
`CarrierShipmentCreate` тощо) і в `CODING_GUIDE.md` (Крок 12-16 "ЩО ДАЛІ").

Ключове, що не мало сенсу лишати "як план" і варто перевірити при
реалізації:

- **`UnassignedWaybills`** (`/waybills/unassigned`) — призначення
  каналу вручну для накладних без `delivery_channel`. Бекенд-ендпоінт
  `GET /api/waybill-records/unassigned/` вже є (Крок 8.5).
- **`HiredTripForm`** — логіка "перевірка ексклюзивності при скануванні"
  тепер реалізована на бекенді як `POST /api/hired-transport-trips/{id}/attach_waybill/`
  (Крок 15.5, Фаза 11), а не як окремий `GET /waybills/{number}/channel/`
  виклик перед кожним сканом, як планувалось спочатку.
- **`CarrierShipmentForm`** — аналогічно, `POST /api/carrier-shipments/{id}/attach_waybill/`.
- **`CarrierCostsImport`** — бекенд-парсер під конкретний формат
  реєстру НП/Міст Експрес ще не написаний (модель і CRUD є, upload
  немає) — див. `01_PROJECT_OVERVIEW.md` §10 п.11.
