# Vehicle Cost Tracker — Структура файлів проєкту (v3)

---

## Повне дерево файлів

```
vehicle-tracker/
│
├── public/
│   ├── favicon.ico
│   └── icons/                              # PWA іконки (192×192, 512×512)
│
├── src/
│   │
│   ├── types/
│   │   └── index.ts                        # Всі TypeScript інтерфейси
│   │                                       # DeliveryChannel, CarStatus
│   │                                       # Car, Driver, Store, StoreDeliveryAddress
│   │                                       # HiredTransportTrip, CarrierShipment...
│   │
│   ├── mocks/
│   │   ├── cars.json                       # 3 авто (amountCar, statusCar, defaultTrackingMode)
│   │   ├── drivers.json                    # 3 водії → прив'язані до cars
│   │   ├── product-categories.json
│   │   ├── products.json
│   │   ├── product-logistics.json
│   │   ├── customers.json
│   │   ├── stores.json                     # 5 магазинів → прив'язані до customers
│   │   ├── store-delivery-addresses.json   # додаткові адреси
│   │   ├── route-events.json               # з palletsCount
│   │   ├── waybills.json                   # deliveryChannel: own/hired/carrier/null
│   │   │                                   # storeId у кожному рядку
│   │   ├── monthly-costs.json              # carId замість vehicleId
│   │   ├── hired-trips.json
│   │   ├── hired-trip-waybills.json
│   │   ├── carrier-shipments.json
│   │   ├── carrier-waybills.json
│   │   └── carrier-costs.json
│   │
│   ├── api/
│   │   ├── config.ts
│   │   ├── cars.ts
│   │   ├── drivers.ts
│   │   ├── routeEvents.ts
│   │   ├── waybills.ts                     # + checkWaybillChannel, fetchUnassigned
│   │   ├── stores.ts
│   │   ├── products.ts
│   │   ├── customers.ts
│   │   ├── hiredTransport.ts               # новий
│   │   ├── carriers.ts                     # новий
│   │   ├── monthlyCosts.ts
│   │   └── analytics.ts                    # + fetchChannelComparison
│   │
│   ├── hooks/
│   │   ├── useCars.ts
│   │   ├── useCurrentDriver.ts
│   │   ├── useRouteEvents.ts
│   │   ├── useDayMode.ts                   # localStorage (ключ: dayMode:{carId}:{date})
│   │   ├── useWaybills.ts                  # + useUnassignedWaybills
│   │   ├── useWaybillFilters.ts            # + deliveryChannel, storeId
│   │   ├── useWaybillChannelGuard.ts       # новий — перевірка ексклюзивності
│   │   ├── useDailySummary.ts
│   │   ├── useHiredTransport.ts            # новий
│   │   ├── useCarriers.ts                  # новий
│   │   ├── useMonthlyCosts.ts
│   │   └── useTransportCosts.ts            # + useChannelComparison
│   │
│   ├── utils/
│   │   ├── formatters.ts                   # + channelLabel()
│   │   ├── eventHelpers.ts                 # + requiresPallets()
│   │   ├── calcSummary.ts                  # + calcTotalPallets()
│   │   ├── calcProduct.ts
│   │   ├── calcTransportCost.ts            # + allocateHiredTripCost()
│   │   ├── parseQR.ts
│   │   ├── parseCsv.ts                     # + parseCsvToCarrierCosts()
│   │   └── clientFilter.ts                 # filterWaybills + deliveryChannel + storeId
│   │
│   ├── components/
│   │   │
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── LegalEntityBadge.tsx
│   │   │   ├── ChannelBadge.tsx            # own/hired/carrier/⚠️null
│   │   │   ├── CarStatusBadge.tsx          # active/repair/inactive
│   │   │   ├── Spinner.tsx
│   │   │   ├── SkeletonRow.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorBanner.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── SortHeader.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── DatePicker.tsx
│   │   │   ├── MonthPicker.tsx
│   │   │   └── Toast.tsx
│   │   │
│   │   ├── layouts/
│   │   │   ├── DriverLayout.tsx            # мобільний, bottom nav
│   │   │   └── MainLayout.tsx              # десктоп, sidebar
│   │   │
│   │   ├── driver/
│   │   │   ├── DayModeSwitch.tsx
│   │   │   ├── RouteTimeline.tsx           # + palletsCount на точках
│   │   │   ├── EventTypeButtons.tsx
│   │   │   ├── ScannedWaybillList.tsx      # + storeName у чіпах
│   │   │   ├── PalletsInput.tsx            # новий — великі кнопки +/−
│   │   │   ├── StoreConfirmModal.tsx        # новий — підтвердження точки при daily
│   │   │   ├── RejectionForm.tsx
│   │   │   ├── ReturnGoodsForm.tsx
│   │   │   └── ExtraCargoForm.tsx
│   │   │
│   │   ├── hired/                          # новий розділ
│   │   │   ├── HiredTripCard.tsx
│   │   │   └── HiredWaybillList.tsx
│   │   │
│   │   ├── carriers/                       # новий розділ
│   │   │   ├── CarrierShipmentCard.tsx
│   │   │   └── CarrierCostStatus.tsx
│   │   │
│   │   ├── fleet/
│   │   │   ├── CarCard.tsx                 # (перейменовано з VehicleCard)
│   │   │   ├── CarTable.tsx                # + CarStatusBadge + Палети
│   │   │   ├── DailyCostsChart.tsx
│   │   │   └── CostBreakdownPie.tsx
│   │   │
│   │   ├── waybills/
│   │   │   ├── WaybillFiltersBar.tsx       # + ChannelFilter + StoreFilter
│   │   │   ├── WaybillTable.tsx            # + ChannelBadge + Store
│   │   │   ├── WaybillLineTable.tsx
│   │   │   ├── CsvPreview.tsx
│   │   │   ├── ReturnMatchRow.tsx
│   │   │   └── UnassignedRow.tsx           # новий
│   │   │
│   │   └── analytics/
│   │       ├── KpiCard.tsx
│   │       ├── MileageLineChart.tsx
│   │       ├── TransportCostTable.tsx
│   │       ├── CustomerCostTable.tsx       # + розбивка по каналах
│   │       └── ChannelComparisonChart.tsx  # новий
│   │
│   ├── pages/
│   │   │
│   │   ├── driver/
│   │   │   ├── DriverDashboard.tsx
│   │   │   ├── EventForm.tsx               # + PalletsInput + StoreConfirmModal
│   │   │   ├── QRScanner.tsx
│   │   │   └── DriverHistory.tsx
│   │   │
│   │   ├── fleet/
│   │   │   ├── FleetList.tsx               # + CarStatusBadge + Палети
│   │   │   ├── CarDetail.tsx               # (перейменовано з VehicleDetail)
│   │   │   └── CarMonth.tsx
│   │   │
│   │   ├── waybills/
│   │   │   ├── WaybillList.tsx             # + ChannelBadge + StoreFilter
│   │   │   ├── WaybillDetail.tsx
│   │   │   ├── WaybillImport.tsx
│   │   │   ├── ReturnMatchingList.tsx
│   │   │   └── UnassignedWaybills.tsx      # новий
│   │   │
│   │   ├── hired/                          # новий розділ
│   │   │   ├── HiredTripList.tsx
│   │   │   ├── HiredTripForm.tsx
│   │   │   └── HiredTripDetail.tsx
│   │   │
│   │   ├── carriers/                       # новий розділ
│   │   │   ├── CarrierShipmentList.tsx
│   │   │   ├── CarrierShipmentForm.tsx
│   │   │   ├── CarrierShipmentDetail.tsx
│   │   │   └── CarrierCostsImport.tsx
│   │   │
│   │   ├── analytics/
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   ├── TransportCosts.tsx
│   │   │   ├── CustomerAnalytics.tsx       # + розбивка по каналах
│   │   │   ├── ChannelComparison.tsx       # новий
│   │   │   └── CarAnalytics.tsx
│   │   │
│   │   └── admin/
│   │       ├── AdminDashboard.tsx
│   │       ├── CarAdmin.tsx                # (перейменовано з VehicleAdmin)
│   │       ├── DriverAdmin.tsx
│   │       ├── ProductAdmin.tsx
│   │       ├── CustomerAdmin.tsx
│   │       ├── StoreAdmin.tsx              # новий — + додаткові адреси
│   │       └── MonthlyCostsAdmin.tsx       # auto-fill з cars.amount_car
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css                           # Tailwind + мобільні fix
│
├── .env
├── .env.production
├── .gitignore
├── eslint.config.js
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
└── vite.config.ts
```

---

## Архітектурні рішення (v3)

| Питання | Рішення | Чому |
|---------|---------|------|
| Ексклюзивність каналів | `deliveryChannel` в `waybill_records` + `checkWaybillChannel()` перед кожним скануванням | Швидка перевірка без JOIN; constraint на рівні UNIQUE в hired/carrier waybill таблицях |
| Палети | `palletsCount` в `route_events` | daily: загальна к-сть за день; full: к-сть на точку вивантаження |
| Магазини | Окрема таблиця `stores` → `store_delivery_addresses` | Один магазин = декілька адрес доставки |
| `cars` | Перейменовано з `vehicles` → відповідає довіднику `5.6 cars` з overview | |
| `amount_car` | Зберігається в `cars`, автоматично підставляється в `MonthlyCostsAdmin` | Логіст вводить один раз |
| Служби доставки | Окрема модель `carrier_shipments` + `carrier_costs` | Реєстри від НП/МЕ мають різну структуру — парсер адаптований |
| Найманий транспорт | `hired_transport_trips` + вільний ввід номера авто | Немає закріплення до довідника |
| `StoreConfirmModal` | Тільки для першого QR у daily-режимі | Спрощує сканування коли кілька накладних на одну точку |

---

## Правила іменування

| Категорія | Конвенція | Приклад |
|-----------|-----------|---------|
| Компоненти | PascalCase | `ChannelBadge.tsx`, `PalletsInput.tsx` |
| Hooks | `use` + PascalCase | `useWaybillChannelGuard.ts` |
| Utils | camelCase | `calcTransportCost.ts` |
| Типи | PascalCase | `HiredTransportTrip`, `CarrierCost` |
| Type aliases | PascalCase | `DeliveryChannel`, `CarStatus` |
| Mock файли | kebab-case | `hired-trip-waybills.json` |
| БД таблиці | snake_case | `hired_transport_trips`, `carrier_costs` |
| Змінні оточення | `VITE_` prefix | `VITE_USE_MOCK` |
