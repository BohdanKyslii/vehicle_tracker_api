# Warehouse Expense Tracker — Схема бази даних (PostgreSQL)

> Базується на реальних моделях `warehouse/models.py`. Зміни порівняно
> з поточною Django-схемою позначені `-- NEW` / `-- CHANGED` з коментарем-обґрунтуванням.
> Це не "нова БД" — це той самий застосунок, доповнений полями й в'юхами,
> що знадобляться API-шару для SPA.

---

## Діаграма зв'язків

```
categories        (1) ──< (N) subcategories
warehouses         (1) ──< (N) expense_objects
categories         (1) ──< (N) expense_objects
subcategories       (1) ──< (N) expense_objects
cost_types          (1) ──< (N) expense_objects
expense_objects      (1) ──< (N) expense_records          [year, month]
expense_objects      (1) ──< (N) fixed_expense_history     [start_date]

Унікальність:
  expense_objects:  UNIQUE (warehouse_id, category_id, subcategory_id, name)
  expense_records:  UNIQUE (expense_object_id, year, month)
```

---

## Довідники

### `warehouses`

```sql
CREATE TABLE warehouses (
    id          SERIAL       PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,  -- NEW: архівація без видалення
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()  -- NEW: поточна модель не мала created_at
);
```

### `categories`

```sql
CREATE TABLE categories (
    id     SERIAL       PRIMARY KEY,
    name   VARCHAR(100) NOT NULL
);
```

### `subcategories`

```sql
CREATE TABLE subcategories (
    id           SERIAL       PRIMARY KEY,
    category_id  INTEGER      NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name         VARCHAR(100) NOT NULL
);

CREATE INDEX idx_subcategories_category ON subcategories (category_id);
```

### `cost_types`

```sql
CREATE TYPE cost_type_code AS ENUM ('fixed', 'variable');

CREATE TABLE cost_types (
    id     SERIAL          PRIMARY KEY,
    name   VARCHAR(50)     NOT NULL,           -- «Фіксована» / «Змінна» (відображення)
    code   cost_type_code  NOT NULL UNIQUE      -- NEW: замінює крихке порівняння name == "Фіксована"
);

COMMENT ON COLUMN cost_types.code IS
    'Явний код замість порівняння name-рядка в бізнес-логіці.
     Поточна реалізація (warehouse/views.py, utils.py) звіряє
     cost_type.name == "Фіксована" — це поле прибирає крихкість.';
```

### `expense_objects`

```sql
CREATE TABLE expense_objects (
    id             SERIAL        PRIMARY KEY,
    warehouse_id   INTEGER       NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    category_id    INTEGER       NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    subcategory_id INTEGER       NOT NULL REFERENCES subcategories(id) ON DELETE CASCADE,
    name           VARCHAR(200)  NOT NULL,
    cost_type_id   INTEGER       NOT NULL REFERENCES cost_types(id) ON DELETE CASCADE,
    is_active      BOOLEAN       NOT NULL DEFAULT TRUE,  -- NEW: архівація
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(), -- NEW

    UNIQUE (warehouse_id, category_id, subcategory_id, name)
);

CREATE INDEX idx_eo_warehouse  ON expense_objects (warehouse_id);
CREATE INDEX idx_eo_category   ON expense_objects (category_id);
CREATE INDEX idx_eo_cost_type  ON expense_objects (cost_type_id);
```

---

## Записи витрат

### `expense_records`

```sql
CREATE TABLE expense_records (
    id                 BIGSERIAL     PRIMARY KEY,
    expense_object_id  INTEGER       NOT NULL REFERENCES expense_objects(id) ON DELETE CASCADE,
    year               SMALLINT      NOT NULL CHECK (year >= 2020),
    month              SMALLINT      NOT NULL CHECK (month BETWEEN 1 AND 12),
    amount             NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
    comment            TEXT,
    is_auto_generated  BOOLEAN       NOT NULL DEFAULT FALSE,
    -- base_record_id: поле існує в поточній моделі, але ніде не заповнюється.
    -- REMOVED у новій схемі (див. task_description/warehouse/01_PROJECT_OVERVIEW.md §7.4);
    -- якщо трасування "згенеровано з" знадобиться — повернути як
    -- source_history_id REFERENCES fixed_expense_history(id) замість self-FK.
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    UNIQUE (expense_object_id, year, month)
);

CREATE INDEX idx_er_object      ON expense_records (expense_object_id);
CREATE INDEX idx_er_period      ON expense_records (year, month);
CREATE INDEX idx_er_auto        ON expense_records (is_auto_generated) WHERE is_auto_generated;

COMMENT ON COLUMN expense_records.is_auto_generated IS
    'TRUE, якщо запис створений автоматично через генерацію фіксованих
     витрат на місяць (аналог copy_fixed_expenses_to_month). Такі записи
     підлягають каскадному оновленню при зміні fixed_expense_history;
     вручну введені (FALSE) — ні (факт має пріоритет).';
```

### `fixed_expense_history`

```sql
CREATE TABLE fixed_expense_history (
    id                 SERIAL        PRIMARY KEY,
    expense_object_id  INTEGER       NOT NULL REFERENCES expense_objects(id) ON DELETE CASCADE,
    amount             NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    start_date         DATE          NOT NULL,
    comment            TEXT,
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_by_id      INTEGER       REFERENCES auth_user(id) ON DELETE SET NULL, -- CHANGED: FK замість CharField
    created_by_name    VARCHAR(150)  NOT NULL DEFAULT 'System'                     -- снепшот імені на момент запису
);

CREATE INDEX idx_feh_object      ON fixed_expense_history (expense_object_id);
CREATE INDEX idx_feh_start_date  ON fixed_expense_history (expense_object_id, start_date DESC);

COMMENT ON TABLE fixed_expense_history IS
    'Ефективно-датований журнал сум для об''єктів витрат з cost_type = fixed.
     "Актуальна" сума на дату D = останній рядок зі start_date <= D
     (див. VIEW expense_object_fixed_resolution нижче).';
```

---

## VIEWs

### `warehouse_monthly_summary`

```sql
-- Підсумок по складу/місяцю: загальна сума, розбивка фіксовані/змінні.

CREATE VIEW warehouse_monthly_summary AS
SELECT
    eo.warehouse_id,
    er.year,
    er.month,
    SUM(er.amount)                                                    AS total_uah,
    SUM(er.amount) FILTER (WHERE ct.code = 'fixed')                   AS fixed_uah,
    SUM(er.amount) FILTER (WHERE ct.code = 'variable')                AS variable_uah,
    COUNT(*)                                                          AS records_count
FROM expense_records er
JOIN expense_objects eo ON eo.id = er.expense_object_id
JOIN cost_types ct       ON ct.id = eo.cost_type_id
GROUP BY eo.warehouse_id, er.year, er.month;
```

### `category_monthly_summary`

```sql
-- Підсумок по категорії/місяцю (для doughnut / breakdown-графіків).

CREATE VIEW category_monthly_summary AS
SELECT
    eo.warehouse_id,
    eo.category_id,
    c.name AS category_name,
    er.year,
    er.month,
    SUM(er.amount) AS total_uah
FROM expense_records er
JOIN expense_objects eo ON eo.id = er.expense_object_id
JOIN categories c       ON c.id = eo.category_id
GROUP BY eo.warehouse_id, eo.category_id, c.name, er.year, er.month;
```

### `expense_object_fixed_resolution`

```sql
-- Формалізує пріоритетну логіку визначення "якої суми" для об'єкта
-- на довільну цільову дату (замінює Python-логіку get_expense_objects_by_warehouse).
-- Викликається з параметром :target_date з боку застосунку (тут — як функція).

CREATE FUNCTION resolve_fixed_amount(p_expense_object_id INTEGER, p_target_date DATE)
RETURNS TABLE (amount NUMERIC(12,2), start_date DATE, status TEXT) AS $$
    -- 1) current: останній рядок зі start_date <= target
    SELECT amount, start_date, 'current'
    FROM fixed_expense_history
    WHERE expense_object_id = p_expense_object_id AND start_date <= p_target_date
    ORDER BY start_date DESC, created_at DESC
    LIMIT 1
$$ LANGUAGE sql STABLE;
-- Якщо порожньо — застосунок додатково перевіряє "future" (найближчий
-- start_date > target) і "fallback" (найновіший запис узагалі);
-- статус "none" — коли history для об'єкта немає взагалі.
-- Три додаткові кроки лишені на рівні API-шару (не SQL), бо задіюють
-- умовну послідовність запитів — див. 05_COMPONENTS_HOOKS_UTILS.md
-- (utils/resolveFixedAmount.ts) для еквівалентної TS-реалізації,
-- яку backend-розробник відтворює 1:1 у Django.
```

### `year_comparison`

```sql
-- Порівняння того самого місяця по роках (YoY).

CREATE VIEW year_comparison AS
SELECT
    eo.warehouse_id,
    er.month,
    er.year,
    SUM(er.amount) AS total_uah
FROM expense_records er
JOIN expense_objects eo ON eo.id = er.expense_object_id
GROUP BY eo.warehouse_id, er.month, er.year
ORDER BY er.month, er.year;
```

---

## Каскадне оновлення фіксованих витрат (правило, не SQL-тригер)

```
Функція cascade_fixed_expense_update(expense_object_id, new_amount,
                                      start_year, start_month, comment):

  1. UPSERT expense_records(expense_object_id, start_year, start_month):
       amount = new_amount, is_auto_generated = FALSE,
       comment = comment OR 'Оновлено фіксовану витрату'

  2. UPDATE expense_records
     SET amount = new_amount,
         comment = 'Автоматично оновлено з {start_month}/{start_year}'
     WHERE expense_object_id = :expense_object_id
       AND is_auto_generated = TRUE
       AND (year > start_year OR (year = start_year AND month > start_month))

  Повертає (updated_record, cascaded_count) — cascaded_count
  показується користувачу в підтвердженні перед застосуванням
  (див. 01_PROJECT_OVERVIEW.md §4.3, §10.1).
```

Це прямий SQL-еквівалент наявної, але не підключеної Python-функції
`warehouse/utils.py::update_fixed_expense`.

---

## Зауваження щодо міграції з поточної Django-схеми

| Зміна | Тип | Причина |
|-------|-----|---------|
| `cost_types.code` | Нова колонка + backfill (`'Фіксована'→'fixed'`, решта→`'variable'`) | Прибрати рядкове порівняння |
| `warehouses.is_active`, `warehouses.created_at` | Нові колонки, default | Архівація, аудит |
| `expense_objects.is_active`, `created_at` | Нові колонки, default | Архівація |
| `expense_records.base_record_id` | Видалити (мертве поле) | Ніде не використовується |
| `fixed_expense_history.created_by` (varchar) → `created_by_id` + `created_by_name` | Розбити на FK + снепшот | Дозволяє фільтрувати по користувачу, зберігаючи історичний текст |
| Views (`warehouse_monthly_summary`, `category_monthly_summary`, `year_comparison`) | Нові | Живлять аналітичні сторінки SPA без N+1 агрегації на бекенді вручну |

Усі зміни — адитивні (нові колонки/таблиці), окрім видалення
`base_record_id`, яке безпечне, бо поле ніде не читається й не
записується в поточному коді.
