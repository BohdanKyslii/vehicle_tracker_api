# Warehouse Expense Tracker — Компоненти, Hooks, Utils

---

## `api/` — шар отримання даних

```typescript
// api/config.ts
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/warehouse";

// api/warehouses.ts
export async function fetchWarehouses(includeArchived?: boolean): Promise<Warehouse[]>
export async function createWarehouse(data: { name: string }): Promise<Warehouse>
export async function archiveWarehouse(id: number): Promise<void>

// api/dictionaries.ts
export async function fetchCategories(): Promise<Category[]>
export async function fetchSubcategories(categoryId?: number): Promise<Subcategory[]>
export async function fetchCostTypes(): Promise<CostType[]>
export async function createCategory(data: { name: string }): Promise<Category>
export async function createSubcategory(data: { categoryId: number; name: string }): Promise<Subcategory>

// api/expenseObjects.ts
export async function fetchExpenseObjects(filters: {
  warehouseId?: number; categoryId?: number; costTypeCode?: CostTypeCode; includeArchived?: boolean;
}): Promise<ExpenseObject[]>
export async function fetchExpenseObject(id: number): Promise<ExpenseObject>
export async function createExpenseObject(data: ExpenseObjectCreate): Promise<ExpenseObject>
export async function updateExpenseObject(id: number, data: Partial<ExpenseObjectCreate>): Promise<ExpenseObject>
export async function archiveExpenseObject(id: number): Promise<void>

// api/expenseRecords.ts
export async function fetchExpenseRecords(
  filters: ExpenseRecordFilters,
  sort: SortParams,
  pagination: PaginationParams,
): Promise<PaginatedResponse<ExpenseRecord>>
export async function createExpenseRecord(data: ExpenseRecordCreate): Promise<ExpenseRecord>
export async function deleteExpenseRecord(id: number): Promise<void>
export async function generateFixedRecordsForMonth(
  warehouseId: number, year: number, month: number,
): Promise<{ createdCount: number }>
// ^ явна дія, замінює неявний побічний ефект add_expense_record → copy_fixed_expenses_to_month

// api/monthlyEntry.ts
export async function fetchMonthlyEntry(
  warehouseId: number, year: number, month: number,
): Promise<MonthlyEntryRow[]>
// ВИПРАВЛЯЄ непідключений get_expense_objects_by_warehouse (overview §7.1)
export async function saveMonthlyEntry(
  warehouseId: number, year: number, month: number,
  rows: { expenseObjectId: number; amount: number; comment?: string }[],
): Promise<MonthlyEntrySaveResult>

// api/yearReview.ts
export async function fetchYearGrid(warehouseId: number, year: number): Promise<YearGridData>
export async function saveYearGrid(
  warehouseId: number, year: number, cells: YearGridCell[],
): Promise<YearGridSaveResult>

// api/fixedExpenseHistory.ts
export async function fetchFixedExpenseHistory(expenseObjectId: number): Promise<FixedExpenseHistoryEntry[]>
export async function previewCascadeUpdate(
  data: FixedExpenseHistoryCreate,
): Promise<{ cascadedCount: number }>
export async function createFixedExpenseHistoryEntry(
  data: FixedExpenseHistoryCreate,
): Promise<CascadeUpdateResult>
export async function resolveFixedAmount(
  expenseObjectId: number, targetDate: string,
): Promise<FixedAmountResolution>

// api/analytics.ts
export async function fetchDashboardKpis(year: number, month: number): Promise<DashboardKpis>
export async function fetchMonthlyTrend(params: {
  warehouseId?: number; monthsBack: number;
}): Promise<MonthlyTrendPoint[]>
export async function fetchCategoryBreakdown(params: {
  warehouseId?: number; year: number; month: number;
}): Promise<CategoryBreakdown[]>
export async function fetchYearlyAnalysis(params: {
  warehouseId?: number; yearFrom: number; yearTo: number;
}): Promise<YearlyAnalysisData>
export async function fetchWarehouseComparison(params: {
  yearFrom: number; yearTo: number;
}): Promise<WarehouseComparison[]>
export async function fetchYoyComparison(warehouseId?: number): Promise<YoyComparisonPoint[]>
export async function fetchBudgetVsActual(params: {
  warehouseId?: number; year: number; month: number;
}): Promise<BudgetVsActualRow[]>
export async function fetchForecast(warehouseId?: number): Promise<ForecastPoint[]>
export async function fetchAnomalies(params: { thresholdPct: number }): Promise<AnomalyFlag[]>

// api/importExport.ts
export async function importExpenseRecordsXlsx(file: File, warehouseId?: number): Promise<ImportResult>
export async function exportXlsx(req: ExportRequest): Promise<Blob>

// api/auth.ts
export async function fetchCurrentUser(): Promise<CurrentUser>
```

---

## `hooks/` — React Query хуки

```typescript
// hooks/useWarehouses.ts
export function useWarehouses(includeArchived?: boolean)
export function useCreateWarehouse()
export function useArchiveWarehouse()

// hooks/useDictionaries.ts
export function useCategories()
export function useSubcategories(categoryId?: number)
export function useCostTypes()

// hooks/useExpenseObjects.ts
export function useExpenseObjects(filters)
export function useExpenseObject(id: number)
export function useCreateExpenseObject()
export function useUpdateExpenseObject()
export function useArchiveExpenseObject()

// hooks/useExpenseRecords.ts
export function useExpenseRecords(filters, sort, pagination)
export function useCreateExpenseRecord()
// Інвалідує: ["expense-records"], ["dashboard-kpis"], ["monthly-trend"]
export function useDeleteExpenseRecord()
export function useGenerateFixedRecords()

// hooks/useMonthlyEntry.ts
export function useMonthlyEntry(warehouseId: number, year: number, month: number)
export function useSaveMonthlyEntry()

// hooks/useYearGrid.ts
export function useYearGrid(warehouseId: number, year: number)
export function useSaveYearGrid()

// hooks/useFixedExpenseHistory.ts
export function useFixedExpenseHistory(expenseObjectId: number)
export function useCascadePreview()
export function useCreateFixedHistoryEntry()
// Інвалідує: ["fixed-history", expenseObjectId], ["expense-records"], ["monthly-entry"]

// hooks/useFixedAmountResolution.ts
export function useFixedAmountResolution(expenseObjectId: number, targetDate: string)

// hooks/useAnalytics.ts
export function useDashboardKpis(year: number, month: number)
export function useMonthlyTrend(params)
export function useCategoryBreakdown(params)
export function useYearlyAnalysis(params)
export function useWarehouseComparison(params)
export function useYoyComparison(warehouseId?: number)
export function useBudgetVsActual(params)
export function useForecast(warehouseId?: number)
export function useAnomalies(thresholdPct: number)

// hooks/useImportExport.ts
export function useImportExpenseRecords()
export function useExport()

// hooks/useCurrentUser.ts
export function useCurrentUser()
// Гейтинг: якщо !canAccessWarehouse → редірект на сторінку "немає доступу"
// (аналог групи "Warehouse" з common/views.py::home_selector)

// hooks/useExpenseRecordFilters.ts
// Стан фільтрів у URL search params
export function useExpenseRecordFilters()
```

---

## `utils/` — Бізнес-логіка

```typescript
// utils/resolveFixedAmount.ts
// Пряма TS-реалізація Python-логіки get_expense_objects_by_warehouse
// (overview §4.4) —klієнтський fallback/попередній перегляд перед
// підтвердженим запитом до API; бекенд лишається джерелом істини.

export function resolveFixedAmount(
  history: FixedExpenseHistoryEntry[],
  targetDate: string,
): FixedAmountResolution {
  const sorted = [...history].sort((a, b) => a.startDate.localeCompare(b.startDate));
  const current = [...sorted].reverse().find(h => h.startDate <= targetDate);
  if (current) {
    return { status: "current", amount: current.amount, effectiveDate: current.startDate,
      comment: `Актуальна з ${formatDate(current.startDate)}`, isEditable: false, expenseObjectId: current.expenseObjectId };
  }
  const future = sorted.find(h => h.startDate > targetDate);
  if (future) {
    return { status: "future", amount: future.amount, effectiveDate: future.startDate,
      comment: `Майбутня з ${formatDate(future.startDate)}`, isEditable: false, expenseObjectId: future.expenseObjectId };
  }
  const fallback = sorted.at(-1);
  if (fallback) {
    return { status: "fallback", amount: fallback.amount, effectiveDate: fallback.startDate,
      comment: `Остання: ${formatDate(fallback.startDate)}`, isEditable: false, expenseObjectId: fallback.expenseObjectId };
  }
  return { status: "none", amount: null, effectiveDate: null,
    comment: "Немає записів в історії фіксованих витрат", isEditable: true, expenseObjectId: 0 };
}

// utils/calcCascadeImpact.ts
// Клієнтський попередній підрахунок (для UX — швидкий preview перед
// підтвердженим запитом), еквівалент update_fixed_expense (§4.3 overview).
export function countCascadeCandidates(
  records: ExpenseRecord[],
  expenseObjectId: number,
  startYear: number,
  startMonth: number,
): number {
  return records.filter(r =>
    r.expenseObjectId === expenseObjectId &&
    r.isAutoGenerated &&
    (r.year > startYear || (r.year === startYear && r.month > startMonth)),
  ).length;
}

// utils/calcTrend.ts
export function buildMonthlyTrend(records: ExpenseRecord[], objects: ExpenseObject[]): MonthlyTrendPoint[]
export function buildCategoryBreakdown(records: ExpenseRecord[], objects: ExpenseObject[]): CategoryBreakdown[]
export function buildYoyComparison(records: ExpenseRecord[]): YoyComparisonPoint[]

// utils/calcBudget.ts
// planned (fixed) = поточна резолюція fixed_expense_history на 1-е число місяця.
// planned (variable) = trailing 3-міс. середнє того ж об'єкта.
export function calcBudgetVsActual(
  records: ExpenseRecord[],
  objects: ExpenseObject[],
  fixedHistoryByObject: Record<number, FixedExpenseHistoryEntry[]>,
  year: number, month: number,
): BudgetVsActualRow[]

export function calcForecast(
  objects: ExpenseObject[],
  fixedHistoryByObject: Record<number, FixedExpenseHistoryEntry[]>,
  trailingRecords: ExpenseRecord[],
): ForecastPoint[]

// utils/calcAnomalies.ts
export function detectAnomalies(
  summaries: { warehouseId: number; year: number; month: number; totalUah: number }[],
  thresholdPct: number,
): AnomalyFlag[]

// utils/parseXlsx.ts
// Клієнтський прев'ю перед відправкою файлу на backend (реальний
// парсинг — openpyxl на Django-стороні, узгоджено зі стеком проєкту).
export function previewXlsx(file: File): Promise<{ headers: string[]; rows: unknown[][] }>

// utils/formatters.ts
export function formatUah(v: number): string
export function formatDate(iso: string): string
export function formatMonthYear(year: number, month: number): string
export function formatPct(v: number): string
export function costTypeLabel(code: CostTypeCode): string   // «Фіксована» / «Змінна»
export function resolutionStatusLabel(status: FixedResolutionStatus): string

// utils/clientFilter.ts
export function filterExpenseRecords(items: ExpenseRecord[], filters: ExpenseRecordFilters): ExpenseRecord[]
export function sortItems<T>(items: T[], sort: SortParams): T[]
export function paginate<T>(items: T[], pagination: PaginationParams): PaginatedResponse<T>
```

---

## `components/ui/` — Атомарні компоненти

```
Button.tsx             — primary/secondary/ghost/danger; sm/md/lg
Badge.tsx
CostTypeBadge.tsx       — fixed=зелений, variable=жовтий
ResolutionStatusBadge.tsx — current=зелений, future=синій, fallback=жовтий, none=червоний
Spinner.tsx
SkeletonRow.tsx
EmptyState.tsx
ErrorBanner.tsx
Pagination.tsx
SortHeader.tsx
Modal.tsx
ConfirmDialog.tsx       — використовується для cascade-попередження і видалення
Input.tsx
Select.tsx
Textarea.tsx
MonthPicker.tsx
YearPicker.tsx
Toast.tsx
FileDropzone.tsx        — для імпорту .xlsx
```

---

## `components/expenses/`

```
ExpenseObjectPicker.tsx
  — каскадні select'и: склад → категорія → підкатегорія → об'єкт
  Props: { value, onChange, warehouseId?: fixed }

ExpenseRecordFiltersBar.tsx
ExpenseRecordTable.tsx  — + CostTypeBadge, заборона видалення fixed напряму
ExpenseRecordForm.tsx   — форма /expenses/new
```

---

## `components/fixed/`

```
FixedHistoryTimeline.tsx
  Props: { history: FixedExpenseHistoryEntry[]; currentDate: string }
  — вертикальна шкала записів, підсвічує "поточний" за резолюцією

FixedHistoryForm.tsx
  — форма додавання запису + виклик useCascadePreview перед сабмітом

CascadeConfirmModal.tsx
  Props: { cascadedCount: number; onConfirm; onCancel }
```

---

## `components/monthly-entry/`

```
MonthlyEntryGrid.tsx
  — один рядок на ExpenseObject, групування по категорії/підкатегорії
    (merged-cell візуальний патерн з поточного monthly_expenses.html)

FixedAmountCell.tsx
  Props: { resolution: FixedAmountResolution }
  — locked-інпут + ResolutionStatusBadge, editable лише при status="none"

GenerateFixedRecordsButton.tsx
  — явна кнопка генерації (заміна неявного побічного ефекту)
```

---

## `components/year-review/`

```
YearGrid.tsx            — рядки=об'єкти, колонки=12 місяців
YearGridCell.tsx         — інпут + підсвітка при "Перевірити всі"
ClearWarningBanner.tsx   — попередження про видалення порожніх/нульових клітинок
```

---

## `components/objects/`

```
ExpenseObjectTable.tsx
ExpenseObjectForm.tsx
DictionaryTabPanel.tsx   — спільний компонент для Category/Subcategory/CostType CRUD
```

---

## `components/import-export/`

```
XlsxPreviewTable.tsx     — перші 10 рядків + маппінг колонок
ImportResultSummary.tsx  — imported/updated/skipped/errors
ExportPanel.tsx          — вибір scope + фільтри + кнопка завантаження
```

---

## `components/analytics/`

```
KpiCard.tsx
MonthlyTrendChart.tsx      — recharts LineChart, лінії: total/fixed/variable
CategoryBreakdownChart.tsx — recharts BarChart або Treemap
WarehouseComparisonChart.tsx — recharts BarChart, згруповано по складах
YoyChart.tsx                — recharts LineChart, окрема лінія на рік
BudgetVsActualTable.tsx     — + delta % з кольоровим кодуванням (>0 червоний, <0 зелений)
ForecastCard.tsx
AnomalyList.tsx              — список AnomalyFlag з deviationPct badge
```
