# Warehouse Expense Tracker — Структура файлів проєкту

---

## Повне дерево файлів

```
warehouse-tracker/
│
├── public/
│   └── favicon.ico
│
├── src/
│   │
│   ├── types/
│   │   └── index.ts                        # Warehouse, ExpenseObject, ExpenseRecord,
│   │                                        # FixedExpenseHistoryEntry, FixedAmountResolution,
│   │                                        # CascadeUpdateResult, аналітичні типи
│   │
│   ├── mocks/
│   │   ├── warehouses.json
│   │   ├── categories.json
│   │   ├── subcategories.json
│   │   ├── cost-types.json                 # {name, code: fixed|variable}
│   │   ├── expense-objects.json
│   │   ├── expense-records.json
│   │   └── fixed-expense-history.json      # 4 кейси: current/future/fallback/none
│   │
│   ├── api/
│   │   ├── config.ts
│   │   ├── warehouses.ts
│   │   ├── dictionaries.ts                 # categories/subcategories/costTypes
│   │   ├── expenseObjects.ts
│   │   ├── expenseRecords.ts               # + generateFixedRecordsForMonth
│   │   ├── monthlyEntry.ts                 # виправляє непідключений backend-ендпоінт
│   │   ├── yearReview.ts
│   │   ├── fixedExpenseHistory.ts          # + previewCascadeUpdate
│   │   ├── analytics.ts                    # + budget/forecast/anomalies
│   │   ├── importExport.ts                 # xlsx через openpyxl-бекенд
│   │   └── auth.ts                         # fetchCurrentUser (гейтинг доступу)
│   │
│   ├── hooks/
│   │   ├── useWarehouses.ts
│   │   ├── useDictionaries.ts
│   │   ├── useExpenseObjects.ts
│   │   ├── useExpenseRecords.ts
│   │   ├── useMonthlyEntry.ts
│   │   ├── useYearGrid.ts
│   │   ├── useFixedExpenseHistory.ts       # + useCascadePreview
│   │   ├── useFixedAmountResolution.ts
│   │   ├── useAnalytics.ts
│   │   ├── useImportExport.ts
│   │   ├── useCurrentUser.ts
│   │   └── useExpenseRecordFilters.ts
│   │
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── resolveFixedAmount.ts           # ключова бізнес-логіка, unit-тестами покрита
│   │   ├── calcCascadeImpact.ts
│   │   ├── calcTrend.ts
│   │   ├── calcBudget.ts                   # + calcForecast
│   │   ├── calcAnomalies.ts
│   │   ├── parseXlsx.ts                    # клієнтський прев'ю
│   │   └── clientFilter.ts
│   │
│   ├── components/
│   │   │
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── CostTypeBadge.tsx
│   │   │   ├── ResolutionStatusBadge.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── SkeletonRow.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorBanner.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── SortHeader.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── MonthPicker.tsx
│   │   │   ├── YearPicker.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── FileDropzone.tsx
│   │   │
│   │   ├── layouts/
│   │   │   └── MainLayout.tsx              # sidebar: Дашборд/Записи/Фіксовані/Довідники/Аналітика
│   │   │
│   │   ├── expenses/
│   │   │   ├── ExpenseObjectPicker.tsx
│   │   │   ├── ExpenseRecordFiltersBar.tsx
│   │   │   ├── ExpenseRecordTable.tsx
│   │   │   └── ExpenseRecordForm.tsx
│   │   │
│   │   ├── fixed/
│   │   │   ├── FixedHistoryTimeline.tsx
│   │   │   ├── FixedHistoryForm.tsx
│   │   │   └── CascadeConfirmModal.tsx
│   │   │
│   │   ├── monthly-entry/
│   │   │   ├── MonthlyEntryGrid.tsx
│   │   │   ├── FixedAmountCell.tsx
│   │   │   └── GenerateFixedRecordsButton.tsx
│   │   │
│   │   ├── year-review/
│   │   │   ├── YearGrid.tsx
│   │   │   ├── YearGridCell.tsx
│   │   │   └── ClearWarningBanner.tsx
│   │   │
│   │   ├── objects/
│   │   │   ├── ExpenseObjectTable.tsx
│   │   │   ├── ExpenseObjectForm.tsx
│   │   │   └── DictionaryTabPanel.tsx
│   │   │
│   │   ├── import-export/
│   │   │   ├── XlsxPreviewTable.tsx
│   │   │   ├── ImportResultSummary.tsx
│   │   │   └── ExportPanel.tsx
│   │   │
│   │   └── analytics/
│   │       ├── KpiCard.tsx
│   │       ├── MonthlyTrendChart.tsx
│   │       ├── CategoryBreakdownChart.tsx
│   │       ├── WarehouseComparisonChart.tsx
│   │       ├── YoyChart.tsx
│   │       ├── BudgetVsActualTable.tsx
│   │       ├── ForecastCard.tsx
│   │       └── AnomalyList.tsx
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── expenses/
│   │   │   ├── ExpensesList.tsx
│   │   │   └── AddExpenseRecord.tsx
│   │   ├── monthly-entry/
│   │   │   └── MonthlyEntry.tsx
│   │   ├── year-review/
│   │   │   └── YearReview.tsx
│   │   ├── fixed-expenses/
│   │   │   ├── FixedExpensesManagement.tsx
│   │   │   └── FixedExpenseHistoryPage.tsx
│   │   ├── objects/
│   │   │   ├── ExpenseObjectsAdmin.tsx
│   │   │   ├── ExpenseObjectFormPage.tsx
│   │   │   └── DictionariesAdmin.tsx
│   │   ├── import-export/
│   │   │   └── ImportExport.tsx
│   │   └── analytics/
│   │       ├── AnalyticsDashboard.tsx
│   │       ├── TrendsPage.tsx
│   │       ├── CategoryAnalysis.tsx
│   │       ├── WarehouseComparisonPage.tsx
│   │       └── BudgetVsActualPage.tsx
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css                           # Tailwind
│
├── .env
├── .env.production
├── .gitignore
├── eslint.config.js
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
└── vite.config.ts                          # base: "/warehouse/" — див. нижче
```

---

## Спільний хостинг з `transport` на одному сайті

Обидва SPA (transport і warehouse) розробляються **різними розробниками**
незалежно один від одного, але мають працювати на одному домені під
одним Django-бекендом і однією сесією логіну. Найпростіший варіант,
що не вимагає координації між розробниками фронтендів під час білду:

```
Django (settings.CSRF_TRUSTED_ORIGINS вже готовий до цього паттерну)
├── /                     → common:home_selector (існуюча сторінка вибору модуля)
├── /login/, /logout/      → існуюча Django-автентифікація (сесійні cookie)
├── /transport/*           → статичні файли з transport-tracker/dist
│                            (vite.config: base: "/transport/")
├── /warehouse/*           → статичні файли з warehouse-tracker/dist
│                            (vite.config: base: "/warehouse/")
├── /shipment/...          → існуючий Django-рендеринг (без змін)
└── /api/transport/*, /api/warehouse/*
                            → окремі Django view-модулі/DRF-роутери,
                              кожен app відповідає за свій namespace
```

**Ключові рішення:**

| Питання | Рішення | Чому |
|---------|---------|------|
| Один shell-застосунок з lazy-load модулів чи два незалежні білди? | **Два незалежні Vite-білди**, кожен зі своїм `base` | Різні розробники, різні терміни релізів — не хочемо спільний build pipeline чи спільний `package.json` |
| Авторизація | Django session cookie (той самий домен, той самий `SESSION_COOKIE_AGE`) | Обидва SPA роблять `fetch` з `credentials: "include"` до свого `/api/{module}/*` — не потрібен окремий JWT/SSO |
| Гейтинг доступу в SPA | `GET /api/{module}/me/` → `CurrentUser.canAccessWarehouse` / `canAccessTransport` (обидва прапори в одній відповіді, оскільки `common/views.py::home_selector` вже рахує їх разом) | Кожен SPA перевіряє лише свій прапор, але бекенд віддає обидва — легше не розсинхронізувати логіку доступу |
| Спільний UI kit | **Не обов'язково спільний пакет** на MVP — кожен `components/ui/` дублюється незалежно (Button, Badge, Modal тощо) | Дублікація мінімальна (10-15 дрібних компонентів), а спільний npm-пакет між двома розробниками створює залежність релізів одне від одного |
| Навігація між модулями | Посилання назад на `/` (Django `home_selector`), а не React Router `Link` між SPA | Різні SPA — це різні JS-бандли; перехід між ними — звичайний `<a href>`, повний reload сторінки |
| CSRF | Кожен SPA читає `csrftoken` cookie і додає `X-CSRFToken` header у мутуючих запитах (стандартний Django-патерн) | Django CSRF middleware лишається увімкненим для сесійної автентифікації |

**Що це виключає:** окремий домен/піддомен для SPA, окремий
reverse-proxy шар (nginx location-блоки на `/transport/` і `/warehouse/`
достатньо), окремий auth-сервер.

---

## Правила іменування

| Категорія | Конвенція | Приклад |
|-----------|-----------|---------|
| Компоненти | PascalCase | `CostTypeBadge.tsx`, `FixedAmountCell.tsx` |
| Hooks | `use` + PascalCase | `useFixedAmountResolution.ts` |
| Utils | camelCase | `resolveFixedAmount.ts` |
| Типи | PascalCase | `FixedExpenseHistoryEntry`, `CascadeUpdateResult` |
| Type aliases | PascalCase | `CostTypeCode`, `FixedResolutionStatus` |
| Mock файли | kebab-case | `fixed-expense-history.json` |
| БД таблиці (Django) | snake_case | `fixed_expense_history`, `expense_objects` |
| Змінні оточення | `VITE_` prefix | `VITE_USE_MOCK`, `VITE_API_BASE` |
| Vite base path | відповідає модулю | `/warehouse/`, `/transport/` |
