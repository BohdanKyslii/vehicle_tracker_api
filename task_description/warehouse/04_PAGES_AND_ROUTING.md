# Warehouse Expense Tracker — Сторінки та маршрутизація

---

## Структура маршрутів (React Router v6)

```tsx
<BrowserRouter basename="/warehouse">
  <Routes>
    <Route path="/" element={<MainLayout />}>
      <Route index element={<Dashboard />} />

      {/* ── Записи витрат ─────────────────────────────── */}
      <Route path="expenses" element={<ExpensesList />} />
      <Route path="expenses/new" element={<AddExpenseRecord />} />

      {/* ── Масове внесення / рік-перевірка ─────────────── */}
      <Route path="monthly-entry" element={<MonthlyEntry />} />
      <Route path="year-review" element={<YearReview />} />

      {/* ── Фіксовані витрати ────────────────────────────── */}
      <Route path="fixed-expenses" element={<FixedExpensesManagement />} />
      <Route path="fixed-expenses/:objectId/history" element={<FixedExpenseHistory />} />

      {/* ── Довідники (раніше — тільки Django admin) ────── */}
      <Route path="objects" element={<ExpenseObjectsAdmin />} />
      <Route path="objects/new" element={<ExpenseObjectForm />} />
      <Route path="objects/:id/edit" element={<ExpenseObjectForm />} />
      <Route path="dictionaries" element={<DictionariesAdmin />} />

      {/* ── Імпорт / Експорт ─────────────────────────────── */}
      <Route path="import-export" element={<ImportExport />} />

      {/* ── Аналітика ─────────────────────────────────────── */}
      <Route path="analytics" element={<AnalyticsDashboard />} />
      <Route path="analytics/trends" element={<TrendsPage />} />
      <Route path="analytics/categories" element={<CategoryAnalysis />} />
      <Route path="analytics/warehouses" element={<WarehouseComparisonPage />} />
      <Route path="analytics/budget" element={<BudgetVsActualPage />} />
    </Route>

    <Route path="*" element={<NotFound />} />
  </Routes>
</BrowserRouter>
```

> `basename="/warehouse"` — узгоджено з підходом спільного хостингу на
> одному сайті поряд з `transport` (`basename="/transport"`), див.
> `08_PROJECT_STRUCTURE.md`.

---

## Сторінки детально

---

### `/` — Dashboard ⭐

**Переносить `dashboard.html` 1:1 + додає:**

- 4 KPI-картки: сума поточного місяця, к-сть записів, к-сть активних
  об'єктів, **частка фіксованих витрат** (нове, замінює нічим не
  підкріплений напис-заглушку «Об'єкти: Активні» з поточного шаблону).
- `MileageLineChart`-аналог → `MonthlyTrendChart` (лінія, 6 місяців,
  Recharts замість Chart.js, з можливістю перемкнути "загалом" /
  "фіксовані" / "змінні" окремими лініями).
- `CategoryDoughnutChart` — структура поточного місяця по категоріях.
- Таблиця останніх 10 записів (як є).
- Фільтр рік/місяць у шапці (`period_filter` — спільний патерн з `common`).

---

### `/expenses` — ExpensesList ⭐

**Переносить `expenses_list.html`.**

**Фільтри:**
```typescript
interface ExpenseRecordFilters {
  search?: string;
  warehouseId?: number;
  categoryId?: number;
  costTypeCode?: CostTypeCode | "all";
  year?: number;
  month?: number;
}
```

**Колонки:** Склад / Категорія / Підкатегорія / Об'єкт / Тип (badge:
зелений=Фіксована, жовтий=Змінна) / Місяць-рік / Сума / Коментар / Дії
(редагувати inline, видалити з підтвердженням).

**Зміна порівняно з поточним шаблоном:** видалення через модалку
підтвердження замість `confirm()`, і **заборона видаляти фіксований
запис напряму** — для нього показується підказка «Змініть через Історію
фіксованих витрат» з посиланням на `/fixed-expenses/:objectId/history`.

---

### `/expenses/new` — AddExpenseRecord

**Переносить `add_expense_record.html` + `ExpenseRecordStepForm`.**

Каскадні select'и: Склад → Категорія → Підкатегорія → Об'єкт витрат
(AJAX-подібні запити замінюються на `useSubcategories(categoryId)` /
`useExpenseObjects({ warehouseId, categoryId, subcategoryId })` через
TanStack Query, з debounce не потрібен — прості довідники).

**Поля:** склад\*, категорія\*, підкатегорія\*, об'єкт витрат\*, рік\*,
місяць\*, сума\*, коментар.

**Валідація (клієнт, дублює backend `unique_together`):** якщо запис
для обраних object+year+month вже існує → показати помилку одразу при
виборі місяця, не чекаючи submit (поточна форма перевіряє тільки при
`clean()` на сервері).

**Логіка після збереження (§4.2 з overview):**
```
Якщо obj.costType.code === "variable":
  → показати банер: «Згенеровано N фіксованих записів на {місяць}/{рік}»
    (результат виклику POST /api/expense-records/generate-fixed/)
```

---

### `/monthly-entry` — MonthlyEntry ⭐

**Переносить `monthly_expenses.html`, ВИПРАВЛЯЄ непідключений ендпоінт**
(§7.1 в overview) — реальний робочий `GET /api/warehouses/{id}/monthly-entry/?year=&month=`.

**Що відображає:** один рядок на `ExpenseObject` обраного складу,
згруповані візуально по категорії/підкатегорії (як і зараз — порожня
комірка, якщо збігається з попереднім рядком).

**Колонка "Сума" за типом:**

| Тип | Статус резолюції | Поведінка |
|-----|------|-----------|
| Фіксована | `current` | Заблоковано, зелений badge «Актуальна з {дата}» |
| Фіксована | `future` | Заблоковано, синій badge «Майбутня з {дата}» (не підставляється) |
| Фіксована | `fallback` | Заблоковано, жовтий badge «Остання: {дата}» |
| Фіксована | `none` | **Редаговано**, червоний badge «Немає історії» |
| Змінна | — | Завжди редаговано |

**Дії:**
- «Зберегти» → `POST /api/warehouses/{id}/monthly-entry/` (аналог
  `save_monthly_expenses`); фіксовані з 0 — заблоковано на рівні UI
  (кнопка disabled + tooltip), а не мовчки пропускається як зараз.
- «Згенерувати фіксовані записи за місяць» — явна кнопка (нове,
  замінює неявний побічний ефект з `/expenses/new`, див. §4.2 overview).

---

### `/year-review` — YearReview

**Переносить `check_monthly_expenses.html`.**

Грід: рядки = об'єкти витрат обраного складу, колонки = 12 місяців
року. Інпут у кожній клітинці.

**Дії:**
- «Перевірити всі» — підсвічує непорожні/ненульові клітинки (як зараз).
- «Зберегти» → `POST /api/warehouses/{id}/year-review/{year}/` — і
  явно попереджає: **«Клітинки, залишені порожніми або з 0, будуть
  видалені»** (модалка підтвердження перед сабмітом — зараз це
  відбувається без попередження, §4.5 overview).

---

### `/fixed-expenses` — FixedExpensesManagement ⭐

**Переносить `fixed_expenses_management.html`.**

Таблиця всіх об'єктів з `costType.code === "fixed"`: поточна сума
(з резолюції на сьогодні), дата останньої зміни історії + коментар,
останній місячний запис (сума + badge «авто», якщо `isAutoGenerated`).

**Форма додавання нового запису історії (модалка):**
```typescript
interface FixedExpenseHistoryForm {
  expenseObjectId: number;
  amount: number;
  startDate: string;
  comment?: string;
}
```

**Ключова зміна порівняно з поточною реалізацією (§4.3 overview):**
```tsx
const mutation = useCreateFixedHistoryEntry();

const handleSubmit = async (form: FixedExpenseHistoryForm) => {
  const preview = await previewCascadeUpdate(form);  // GET-запит "на скільки записів вплине"
  if (preview.cascadedCount > 0) {
    setConfirmState({
      open: true,
      message: `Буде оновлено ${preview.cascadedCount} вже згенерованих
                 записів на майбутні місяці. Записи, введені вручну,
                 не змінюються.`,
      onConfirm: () => mutation.mutate(form),
    });
  } else {
    mutation.mutate(form);
  }
};
```

---

### `/fixed-expenses/:objectId/history` — FixedExpenseHistory

**Переносить `fixed_expense_history.html`** — список усіх записів
історії обраного об'єкта, `order by -start_date`, + badge «поточна»
на тому рядку, що зараз активний за резолюцією.

---

### `/objects` — ExpenseObjectsAdmin ⭐ (нове)

**Замінює прямі посилання на Django admin** з `expense_objects.html`.

Фільтри: склад, категорія, тип витрат. Статистика: к-сть об'єктів,
складів, категорій, типів (як зараз). Таблиця + кнопки «Редагувати» /
«Архівувати» (замість `DELETE`, щоб не ламати `expense_records`
історію — soft delete через `isActive`).

### `/objects/new`, `/objects/:id/edit` — ExpenseObjectForm (нове)

Проста форма: склад\*, категорія\*, підкатегорія\* (каскадно від
категорії), назва\*, тип витрат\*. Валідація унікальності
`(warehouse, category, subcategory, name)` — клієнтська підказка +
серверна 409 при колізії.

### `/dictionaries` — DictionariesAdmin (нове)

Три вкладки: Склади / Категорії та підкатегорії / Типи витрат.
Прості CRUD-таблиці (create/rename/archive), без окремих сторінок —
усе інлайново в модалках.

---

### `/import-export` — ImportExport (нове)

**Замінює management-команди `import_json`/`load_csv_data`.**

- Вкладка «Імпорт»: вибір складу (опційно), завантаження `.xlsx`,
  клієнтський прев'ю перших 10 рядків (`xlsx`/SheetJS), маппінг колонок,
  «Імпортувати» → `POST /api/import/expense-records/` (сервер парсить
  через `openpyxl`, повертає `ImportResult`).
- Вкладка «Експорт»: вибір `scope` (записи / об'єкти / історія
  фіксованих), склад (опційно), діапазон років → `GET /api/export/?scope=...`
  завантажує `.xlsx`, згенерований `openpyxl` на бекенді.

---

### `/analytics` — AnalyticsDashboard

**Розширює `analysis.html` — додає графіки, яких там зараз немає.**

- `MonthlyTrendChart` (лінія: total/fixed/variable) — замінює таблицю
  "Витрати по місяцях" зі зламаним прогрес-баром (§7.7 overview).
- `CategoryBreakdownChart` (горизонтальний bar або treemap).
- 4 KPI-картки: `totalYearlyUah`, `avgMonthlyUah`, `monthsCount`, `recordsCount`
  (як зараз, без змін).
- Детальна таблиця лишається (для експорту/аудиту), але тепер
  згорнута під акордеон "Показати деталізацію" — акцент зміщено на графіки.

### `/analytics/trends` — TrendsPage (нове)

`MonthlyTrendPoint[]` за обраний період, лінійний графік + перемикач
гранулярності (по місяцях / по кварталах).

### `/analytics/categories` — CategoryAnalysis (нове)

`CategoryBreakdown[]` + тренд по категоріях (stacked area chart —
кожна категорія власним кольором, видно як змінюється структура
з часом).

### `/analytics/warehouses` — WarehouseComparisonPage (нове)

`WarehouseComparison[]` — bar chart порівняння складів за період +
таблиця. KPI: найдорожчий/найдешевший склад, склад з найбільшою
часткою фіксованих витрат.

### `/analytics/budget` — BudgetVsActualPage (нове)

`BudgetVsActualRow[]` (план/факт) + `ForecastPoint[]` (прогноз
наступного місяця) + `AnomalyFlag[]` (список місяців/складів з
відхиленням > 20% від trailing average, підсвічені червоним).
