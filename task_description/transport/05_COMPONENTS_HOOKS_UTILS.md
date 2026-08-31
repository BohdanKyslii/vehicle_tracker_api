# Vehicle Cost Tracker — Компоненти, Hooks, Utils

> **Оновлено 2026-08-24.** Нижче — реальний інвентар файлів
> (`vehicle_cost_tracker/src/`) на сьогодні, не первинний план.
> Хуки живуть у `src/hocks/` (так, з друкарською помилкою — так
> історично склалось у реальному коді, не виправляти без окремого
> завдання, бо зачепить усі імпорти). Усе, чого немає в реальних
> файлах, позначено ⏳ і винесено в окремий розділ унизу — не
> вигадується, а фіксується як "заплановано, не існує".

---

## `api/` — шар отримання даних (реальний інвентар: 6 файлів)

```typescript
// api/config.ts
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000';
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
export async function apiFetch<T>(path: string, options?: FetchOptions): Promise<T>
// credentials: 'include' + X-CSRFToken header (з cookie) — сесійна авторизація, не Bearer/JWT
export function mockDelay(ms = 300): Promise<void>

// api/auth.ts
export function fetchCsrf(): Promise<{ csrfToken: string }>
export function fetchCurrentUser(): Promise<{ user: CurrentUser | null }>
export function login(username, password): Promise<CurrentUser>
export function register(username, email, password, role): Promise<RegisterResult>
export function logout(): Promise<void>
export function loginWithTelegram(initData: string): Promise<CurrentUser>

// api/cars.ts
export async function fetchCars(): Promise<Car[]>
export async function fetchCar(id: number): Promise<Car>
// Мапить snake_case відповідь DRF (RawCar/RawCarSpecs/RawTrailer) → camelCase Car.
// DecimalField бекенду серіалізується як РЯДОК у JSON — усюди явний Number(...).
// ⚠️ Немає updateCar() — первинний план його очікував, у коді нема (CRUD для /fleet ще не набраний).

// api/drivers.ts
export async function fetchDrivers(): Promise<Driver[]>
export async function fetchCurrentDriver(): Promise<Driver>
// GET /drivers/me/ — визначається бекендом по сесії (Profile.driver)

// api/routeEvents.ts
export async function fetchTodayEvents(carId: number): Promise<RouteEvent[]>
export async function fetchLastOdometer(carId: number): Promise<number | null>
export async function createRouteEvent(data: RouteEventCreate): Promise<RouteEvent>
// ⚠️ Немає fetchEventsByDate/fetchEventsByRange — первинний план їх очікував, у коді нема.

// api/waybills.ts
export async function fetchWaybills(filters, sort, pagination): Promise<PaginatedResponse<WaybillSummary>>
export async function fetchWaybillDetail(number: string): Promise<WaybillRecord[]>
export async function checkWaybillChannel(number): Promise<{ waybillNumber; deliveryChannel }>
export async function fetchUnassignedWaybills(): Promise<WaybillSummary[]>
// ⚠️ Немає importWaybillsCsv() — Крок 11 (імпорт з 1С) ще не реалізований ні на бекенді, ні тут.
```

**Немає взагалі** (первинний план очікував, файлів не існує):
`api/stores.ts`, `api/products.ts`, `api/customers.ts`,
`api/hiredTransport.ts`, `api/carriers.ts`, `api/monthlyCosts.ts`,
`api/analytics.ts`.

---

## `hocks/` — React Query хуки (реальний інвентар: 8 файлів)

```typescript
// hocks/useCars.ts
export function useCars()
export function useCar(id: number)

// hocks/useDrivers.ts
export function useCurrentDriver()

// hocks/useRouteEvents.ts
export function useTodayEvents(carId: number)      // refetchInterval: 60_000
export function useLastOdometer(carId: number)
export function useCreateRouteEvent()               // інвалідує route-events + last-odometer

// hocks/useDayMode.ts
// localStorage ключ: `dayMode:${today}` (без carId у ключі — на відміну
// від первинного плану `dayMode:{carId}:{date}`; режим спільний на
// поточний день незалежно від carId)
export function useDayMode(carDefaultMode: TrackingMode)

// hocks/useWaybills.ts
export function useWaybills(filters, sort, pagination)   // placeholderData: keepPreviousData
export function useWaybillDetail(waybillNumber: string)
export function useCheckWaybillChannel(waybillNumber: string)
export function useUnassignedWaybills()

// hocks/useWaybillFilters.ts
// Стан фільтрів у URL search params (не в useState) — фільтри
// переживають перезавантаження сторінки
export function useWaybillFilters()

// hocks/useAuthModal.ts
export function useAuthModal()   // isOpen, isSignup, openLogin, openSignup, close, switchTo

// hocks/useCurrentUser.ts
export function useCurrentUser()
// { user, isLoading, login, register, logout, loginWithTelegram, ...Error }
// TanStack Query cache key: ["currentUser"]
```

**Немає взагалі** (первинний план очікував): `useWaybillChannelGuard.ts`,
`useDailySummary.ts`, `useHiredTransport.ts`, `useCarriers.ts`,
`useMonthlyCosts.ts`, `useTransportCosts.ts`.

---

## `utils/` — Бізнес-логіка (реальний інвентар: 7 файлів)

```
calcProduct.ts          — розрахунки по товару (вага/об'єм рядка)
calcSummary.ts           — денний підсумок з масиву RouteEvent
calcTransportCost.ts     — розподіл транспортних витрат
clientFilter.ts          — filterWaybills / sortItems / paginate (клієнтська фільтрація для mock-режиму)
eventHelpers.ts          — довідкові функції по типах подій маршруту
formatters.ts            — formatUah/formatKm/formatDate/... форматування чисел і дат
parseQR.ts               — розбір QR-коду накладної
```

**Немає взагалі** (первинний план очікував): `parseCsv.ts` (потрібен для
Крок 11 — імпорт з 1С — і для майбутнього імпорту реєстру служб
доставки).

> Точний список експортованих функцій із кожного файлу тут навмисно не
> дублюється — фіксувати кожен раз при кожній зміні дорожче, ніж просто
> відкрити файл. Дивись безпосередньо `src/utils/*.ts`.

---

## `components/` — реальний інвентар

```
components/
├── auth/
│   └── AuthModal.tsx          — форма входу/реєстрації, чотирипанельна (Фаза 3)
├── driver/
│   ├── DayModeSwitch.tsx      — перемикач daily/full
│   └── ui.tsx                 — дрібні UI-шматки специфічні для водійського екрана
├── layouts/
│   ├── DriverLayout.tsx       — мобільний layout (Outlet + водійська навігація)
│   ├── MainLayout.tsx         — десктоп layout (Outlet + TopNav)
│   └── TopNav.tsx             — верхнє меню сайту
├── ui/
│   ├── Badge.tsx
│   ├── Button.tsx
│   ├── EmptyState.tsx
│   ├── ErrorBanner.tsx
│   ├── Input.tsx
│   ├── Pagination.tsx
│   ├── SortHeader.tsx
│   ├── Spinner.tsx
│   └── ui.tsx                 — інші дрібні спільні UI-примітиви в одному файлі
└── waybills/
    ├── WaybillFiltersBar.tsx
    ├── WaybillList.tsx
    └── WaybillTable.tsx
```

**Порожні директорії** (заведені під майбутнє, файлів усередині
немає): `components/fleet/`, `components/hired/`, `components/carriers/`,
`components/analystics/` (так, з друкарською помилкою — `analytics`
написано як `analystics`; звернути увагу при створенні файлів туди,
щоб не плодити паралельно правильну й неправильну назву).

**Немає взагалі, first-class компонентів з первинного плану**:
`ChannelBadge`, `CarStatusBadge`, `LegalEntityBadge`, `PalletsInput`,
`Modal`, `Select`, `Textarea`, `DatePicker`, `MonthPicker`, `Toast`,
`SkeletonRow`, `RouteTimeline`, `EventTypeButtons`, `ScannedWaybillList`,
`StoreConfirmModal`, `RejectionForm`, `ReturnGoodsForm`, `ExtraCargoForm`
— первинний план очікував їх для Фаз 13-16, реалізовано тільки те, що
дійсно знадобилось Фазі 13 (`DayModeSwitch`).

---

## `pages/` — реальний інвентар

```
pages/
├── driver/
│   ├── DriverDashboard.tsx
│   └── EventForm.tsx
├── DriverMiniApp.tsx           — Telegram Mini App вхід
├── LandingPage.tsx
├── PlaceholderPage.tsx         — universal "в розробці" заглушка (title prop)
└── UnderConstruction.tsx       — старіший варіант заглушки (Фаза 3), лишився поряд з PlaceholderPage
```

**Порожні директорії:** `pages/fleet/`, `pages/hired/`, `pages/carriers/`,
`pages/analystics/`, `pages/admin/`, `pages/waybills/` (сама
`WaybillList` живе не тут, а в `components/waybills/` — App.tsx
імпортує її напряму з `components/`, не через сторінку-обгортку).

> `UnderConstruction.tsx` і `PlaceholderPage.tsx` — по суті дублюють
> одна одну (обидві — заглушка з заголовком). Не консолідовано,
> просто фіксую для орієнтиру, якщо колись прибиратимеш дублювання.
