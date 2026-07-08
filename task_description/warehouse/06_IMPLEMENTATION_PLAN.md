# Warehouse Expense Tracker — Покроковий план реалізації

---

## Загальний таймлайн

```
Тиждень 1 — Foundation (типи, моки, утиліти резолюції фіксованих сум)
Тиждень 2 — Записи витрат: список, додавання, масове внесення за місяць
Тиждень 3 — Фіксовані витрати (історія + каскад) + рік-перевірка
Тиждень 4 — Довідники в SPA (об'єкти/склади/категорії) + імпорт/експорт Excel
Тиждень 5 — Аналітика (графіки, план/факт, прогноз) + polish
```

---

## ТИЖДЕНЬ 1 — Foundation

### Крок 1.1 — Ініціалізація

```bash
npm create vite@latest warehouse-tracker -- --template react-ts
cd warehouse-tracker
npm install react-router-dom @tanstack/react-query
npm install tailwindcss @tailwindcss/vite
npm install recharts xlsx date-fns
npm install -D @tanstack/react-query-devtools
```

### Крок 1.2 — Типи (`src/types/index.ts`)

Перенести з `03_TYPESCRIPT_TYPES.md`. Пріоритетні для тижня 1:
`Warehouse`, `Category`, `Subcategory`, `CostType`, `ExpenseObject`,
`ExpenseRecord`, `FixedExpenseHistoryEntry`, `FixedAmountResolution`.

### Крок 1.3 — Mock JSON файли

```
src/mocks/
├── warehouses.json            3 склади
├── categories.json            6 категорій (Оренда, Комунальні, ЗП, Ремонт, Матеріали, Інше)
├── subcategories.json         12-15 підкатегорій
├── cost-types.json            2 записи: Фіксована(code=fixed), Змінна(code=variable)
├── expense-objects.json       ~20 об'єктів, різні склади/типи
├── expense-records.json       6 місяців × ~15 об'єктів (частина is_auto_generated=true)
└── fixed-expense-history.json 4-5 об'єктів з 2-3 записами історії кожен
                                (демонструє current/future/fallback/none кейси)
```

### Крок 1.4 — Utils (найважливіше — резолюція фіксованих сум)

1. `formatters.ts`
2. `resolveFixedAmount.ts` — **пріоритет №1**, бо на ньому тримається
   і `/monthly-entry`, і `/fixed-expenses`. Покрити unit-тестами всі
   4 статуси (`current`/`future`/`fallback`/`none`) — це та логіка, що
   в поточному Django-коді ніде не протестована (0 тестів у `warehouse/tests.py`).
3. `calcCascadeImpact.ts`
4. `clientFilter.ts`

### Крок 1.5 — API + React Query setup

```typescript
// api/config.ts
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/warehouse";
```

Патерн mock-режиму для резолюції (аналог `checkWaybillChannel` у transport):
```typescript
export async function resolveFixedAmount(expenseObjectId: number, targetDate: string) {
  if (USE_MOCK) {
    const history = (mockFixedHistory as FixedExpenseHistoryEntry[])
      .filter(h => h.expenseObjectId === expenseObjectId);
    return resolveFixedAmountLocal(history, targetDate); // з utils/resolveFixedAmount.ts
  }
  const res = await fetch(`${API_BASE}/expense-objects/${expenseObjectId}/fixed-resolution/?date=${targetDate}`);
  return res.json();
}
```

---

## ТИЖДЕНЬ 2 — Записи витрат

### Крок 2.1 — UI компоненти

`CostTypeBadge`, `ResolutionStatusBadge`, `ExpenseObjectPicker`
(каскадні select'и — заміна AJAX-partials `category_dropdown_options.html`
на звичайні React Query хуки).

### Крок 2.2 — ExpensesList

```tsx
// Перенесення expenses_list.html: фільтри рік/місяць/склад автозастосовуються
const { filters, setFilters } = useExpenseRecordFilters();
const { data, isLoading } = useExpenseRecords(filters, sort, pagination);
```

**Заборона прямого видалення фіксованого запису:**
```tsx
{record.expenseObject?.costType?.code === "fixed" ? (
  <Tooltip text="Змініть через Історію фіксованих витрат">
    <Button variant="ghost" disabled>Видалити</Button>
  </Tooltip>
) : (
  <Button variant="danger" onClick={() => confirmDelete(record.id)}>Видалити</Button>
)}
```

### Крок 2.3 — AddExpenseRecord + генерація фіксованих

```tsx
const createRecord = useCreateExpenseRecord();
const generateFixed = useGenerateFixedRecords();

const handleSubmit = (form: ExpenseRecordCreate) => {
  createRecord.mutate(form, {
    onSuccess: async (record) => {
      if (record.expenseObject?.costType?.code === "variable") {
        const result = await generateFixed.mutateAsync({
          warehouseId: form.expenseObjectId /* через object → warehouse */,
          year: form.year, month: form.month,
        });
        if (result.createdCount > 0) {
          toast.success(`Згенеровано ${result.createdCount} фіксованих записів`);
        }
      }
      navigate("/expenses");
    },
  });
};
```

### Крок 2.4 — MonthlyEntry (виправлення непідключеного ендпоінта)

```tsx
export function MonthlyEntry() {
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [year, month] = useSelectedPeriod();
  const { data: rows, isLoading } = useMonthlyEntry(warehouseId!, year, month);
  const save = useSaveMonthlyEntry();

  // Валідація перед сабмітом: фіксовані з draft="0" — блокуються в UI
  const canSubmit = rows?.every(r =>
    r.expenseObject.costType?.code !== "fixed" || Number(r.amountDraft) > 0
  );

  return (/* грід рядків MonthlyEntryGrid + GenerateFixedRecordsButton */);
}
```

---

## ТИЖДЕНЬ 3 — Фіксовані витрати + рік-перевірка

### Крок 3.1 — FixedExpensesManagement з cascade-попередженням

```tsx
export function FixedExpensesManagement() {
  const preview = useCascadePreview();
  const create = useCreateFixedHistoryEntry();

  const handleSubmit = async (form: FixedExpenseHistoryCreate) => {
    const { cascadedCount } = await preview.mutateAsync(form);
    if (cascadedCount > 0) {
      setConfirm({
        message: `Буде оновлено ${cascadedCount} вже згенерованих записів
                   на майбутні місяці. Записи, введені вручну, не зміняться.`,
        onConfirm: () => create.mutate(form, { onSuccess: () => setModalOpen(false) }),
      });
    } else {
      create.mutate(form, { onSuccess: () => setModalOpen(false) });
    }
  };
  // ...
}
```

Це прямо усуває розбіжність описану в `01_PROJECT_OVERVIEW.md` §4.3 —
у поточному Django-застосунку `update_fixed_expense()` існує, але
ніколи не викликається.

### Крок 3.2 — FixedExpenseHistory (timeline)

`FixedHistoryTimeline` — рендерить `history`, позначає рядок, що
відповідає `resolveFixedAmount(history, today).effectiveDate`.

### Крок 3.3 — YearReview з попередженням про видалення

```tsx
const handleSave = () => {
  const emptyCells = cells.filter(c => !c.amount || c.amount <= 0);
  if (emptyCells.length > 0) {
    setConfirm({
      message: `${emptyCells.length} клітинок порожні або з 0 — відповідні
                 записи будуть ВИДАЛЕНІ. Продовжити?`,
      onConfirm: () => saveYearGrid.mutate({ warehouseId, year, cells }),
    });
  } else {
    saveYearGrid.mutate({ warehouseId, year, cells });
  }
};
```

---

## ТИЖДЕНЬ 4 — Довідники в SPA + Excel

### Крок 4.1 — ExpenseObjectsAdmin / ExpenseObjectForm

Замінює прямі посилання на `admin:warehouse_expenseobject_add`.
Валідація унікальності `(warehouse, category, subcategory, name)` —
клієнтська перевірка через `useExpenseObjects` кеш + серверна 409.

### Крок 4.2 — DictionariesAdmin

Три вкладки (Warehouse / Category+Subcategory / CostType) —
`DictionaryTabPanel` спільний компонент, кожна вкладка передає свій
набір колонок і мутацій.

### Крок 4.3 — ImportExport

```typescript
// utils/parseXlsx.ts — клієнтський прев'ю
export async function previewXlsx(file: File) {
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf);
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
  return { headers: rows[0] as string[], rows: rows.slice(1, 11) };
}
```

Сам імпорт (валідація + запис у БД) виконується на Django-боці через
`openpyxl` (уже в стеку проєкту) — SPA лише готує прев'ю та відправляє
файл `multipart/form-data`.

Очікувані колонки (аналог маппінгу з `import_json`/`load_csv_data`):
```
Склад, Категорія, Підкатегорія, Об'єкт витрат, Тип витрат, Рік, Місяць, Сума, Коментар
```

---

## ТИЖДЕНЬ 5 — Аналітика + polish

### Крок 5.1 — Dashboard: Chart.js → Recharts

```tsx
<MonthlyTrendChart data={trend} lines={["total", "fixed", "variable"]} />
<CategoryBreakdownChart data={categoryBreakdown} />
```

### Крок 5.2 — AnalyticsDashboard: виправлення зламаного прогрес-бару

Поточний `analysis.html` рендерить прогрес-бар з захардкодженою
шириною `10%` замість реального `percentage` — у новому компоненті
ширина біндиться напряму до значення:
```tsx
<div className="h-2 bg-blue-500 rounded" style={{ width: `${row.percentage}%` }} />
```
І додається `MonthlyTrendChart` над таблицею — таблиця згортається
під акордеон.

### Крок 5.3 — Нова аналітика: план/факт + прогноз + аномалії

```tsx
export function BudgetVsActualPage() {
  const { data: rows } = useBudgetVsActual({ warehouseId, year, month });
  const { data: forecast } = useForecast(warehouseId);
  const { data: anomalies } = useAnomalies({ thresholdPct: 20 });

  return (
    <>
      <BudgetVsActualTable rows={rows} />
      <ForecastCard points={forecast} />
      {anomalies?.length > 0 && <AnomalyList items={anomalies} />}
    </>
  );
}
```

### Крок 5.4 — WarehouseComparison + Yoy

```tsx
<WarehouseComparisonChart data={comparison} />
<YoyChart data={yoy} />
```

### Крок 5.5 — Polish

- Гейтинг доступу через `useCurrentUser().canAccessWarehouse` (аналог
  `common/views.py::home_selector`) — редірект на «немає доступу», якщо
  false.
- Порожні/помилкові стани (`EmptyState`, `ErrorBanner`) на всіх списках.
- Toast-повідомлення для всіх мутацій.

---

## Чеклист перед demo

```
Foundation
  ✅ types: CostType(code), FixedAmountResolution, CascadeUpdateResult
  ✅ mocks: fixed-expense-history (4 кейси: current/future/fallback/none)
  ✅ utils: resolveFixedAmount (покрито тестами всі 4 статуси)

Записи витрат
  ✅ ExpensesList з фільтрами + заборона прямого видалення fixed-запису
  ✅ AddExpenseRecord + явна генерація фіксованих (кнопка, не тільки побічний ефект)
  ✅ MonthlyEntry — РЕАЛЬНО робочий ендпоінт (виправлений баг з overview §7.1)

Фіксовані витрати
  ✅ FixedExpensesManagement з попереднім переглядом каскаду (виправлений §4.3 баг)
  ✅ FixedHistoryTimeline
  ✅ YearReview з попередженням про видалення нульових клітинок

Довідники
  ✅ ExpenseObjectsAdmin — CRUD у SPA (не Django admin)
  ✅ DictionariesAdmin (Warehouse/Category/Subcategory/CostType)
  ✅ Excel імпорт/експорт (openpyxl на бекенді)

Аналітика
  ✅ Dashboard — Recharts замість Chart.js, KPI: частка фіксованих
  ✅ AnalyticsDashboard — графіки замість голих таблиць, виправлений прогрес-бар
  ✅ WarehouseComparison, Yoy, BudgetVsActual, Forecast, Anomalies — усе нове

Гейтинг доступу
  ✅ useCurrentUser + canAccessWarehouse
```
