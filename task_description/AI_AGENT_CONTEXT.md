# AI_AGENT_CONTEXT.md — Технічний контекст проекту Expenses

Технічний контекст для AI-агентів. Читати після `AGENTS_GLOBAL.md`.

---

## Проект

**Назва:** Expenses
**Тип:** Django веб-додаток для обліку витрат компанії
**БД:** PostgreSQL (`expenses`)
**Середовище:** Локальний сервер (без Docker)
**Python:** 3.11+
**Django:** 6.0

---

## Конфігурація (.env)

```env
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=expenses
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
POSTGRES_HOST_CONTAINER=localhost
POSTGRES_PORT_CONTAINER=5432

DJANGO_SUPERUSER_USERNAME=...
DJANGO_SUPERUSER_EMAIL=...
DJANGO_SUPERUSER_PASSWORD=...

TIME_ZONE=Europe/Kiev
```

Налаштування через `python-decouple`. Файл `.env` — завжди в `.gitignore`.

---

## Installed Apps (settings.py)

```python
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    ...
    # Third-party
    "crispy_forms",
    "crispy_bootstrap5",
    "django_filters",
    "debug_toolbar",
    # Project
    "accounts",
    "common",
    "warehouse",
    "shipment",
    "transport",
]
```

---

## URL структура

| Prefix        | App       | Namespace   |
|---------------|-----------|-------------|
| `/`           | common    | —           |
| `/accounts/`  | accounts  | `accounts`  |
| `/transport/` | transport | `transport` |
| `/warehouse/` | warehouse | `warehouse` |
| `/shipment/`  | shipment  | `shipment`  |
| `/admin/`     | Django admin | —        |

Home page (`/`) — `common.views.home_selector` визначає куди перенаправити.

---

## Ключові моделі та поля

### Transport — `Car`
```python
license_plate, brand, model, year, vin
vehicle_type  # truck/van/ref/awning
fuel_types    # ManyToMany або MultiSelect
status        # active/inactive/repair/sold/scrapped
is_rental, purchase_price, purchase_date
fuel_card_number
```

### Transport — `MonthlyCarExpense`
```python
car (FK→Car, PROTECT), month, year  # unique_together
fuel_cost, fuel_liters, mileage
repair_cost, rent_cost, salary_cost
insurance, washing, parking, fines, other
# @property: total_expenses, cost_per_km, fuel_consumption
```

### Transport — `LogisticsExpense`
```python
expense_type  # logistics_salary/hired_transport/nova_poshta/other
date, amount, description
# Для hired_transport: vehicle_info, driver_name, route
# Для nova_poshta: tracking_number, parcel_weight, destination
```

### Warehouse — `ExpenseRecord`
```python
expense_object (FK→ExpenseObject, PROTECT)
month, year, amount
is_auto_generated (bool)
base_record (FK→self, SET_NULL)  # джерело для авто-генерації
comment
```

### Warehouse — `FixedExpenseHistory`
```python
expense_object (FK→ExpenseObject, PROTECT)
start_date, end_date (nullable)
amount
comment
```

### Shipment — `ExpenseInvoice`
```python
source  # ESP/OPT/RUB
invoice (номер накладної)
date
shop (FK→Shop, PROTECT)
warehouse (FK→Warehouse, PROTECT)
car (FK→Car, SET_NULL, nullable)
route (FK→DeliveryRoute, SET_NULL, nullable)
sum_price, sum_prod
# unique_together: (source, invoice)
```

### Shipment — `ExpenseInvoiceItem`
```python
invoice (FK→ExpenseInvoice, CASCADE)
product (FK→Product, PROTECT)
warehouse (FK→Warehouse, PROTECT)
quantity, price, sum_price, sum_prod
line_number
calculated_delivery_cost (nullable)
packing_cost (nullable)
# unique_together: (invoice, line_number)
```

---

## Шаблони та UI

### Структура шаблонів
```
templates/
├── transport/
│   ├── base.html           # Базовий для модулю
│   ├── car_list.html
│   ├── car_detail.html
│   ├── expense_form.html
│   └── ...
├── warehouse/
│   ├── base.html
│   ├── dashboard.html
│   ├── expenses_list.html
│   ├── manage_fixed_expenses.html
│   └── ...
├── shipment/
│   ├── home.html
│   ├── route_list.html
│   ├── route_form.html
│   ├── route_detail.html
│   └── ...
└── common/
    └── home_selector.html
```

### Загальні UI-патерни
- Bootstrap 5 скрізь
- Фільтри `django-filter` на списках
- Динамічні dropdown через AJAX (наприклад: Категорія → Субкатегорія → Стаття)
- Django messages для success/error повідомлень
- Пагінація на списках
- Адаптивний дизайн (mobile-friendly)

---

## Кастомні template tags

Файл: `common/templatetags/custom_filters.py`

- `floatformat` — форматування числа з заданою кількістю знаків після коми
- `cut` — видалення підрядка
- `get_category_class` — CSS-клас для категорії витрат
- `get_choice_display` — відображення людиночитаємого значення з choices

---

## Бізнес-логіка

### Авто-генерація фіксованих витрат
- При переході на новий місяць — копіюються всі `ExpenseRecord` з `CostType.name="Фіксована"`
- Сума береться з останнього запису `FixedExpenseHistory`
- `is_auto_generated=True`, `base_record` вказує на джерело

### Розрахунок вартості авто
- `MonthlyCarExpense.total_expenses` = сума всіх витрат за місяць
- `MonthlyCarExpense.cost_per_km` = `total_expenses / mileage`
- `Car.cost_per_km` = середнє за весь час

### Логістичні витрати
- Типи: зарплата водія, найманий транспорт, Нова Пошта, інші
- Для НП: трекінг-номер, вага, пункт призначення
- Для найманого: інформація про авто, водій, маршрут

### Маршрути відвантаження
- `DeliveryRoute` групує `ExpenseInvoice` за рейсом
- `is_calculated` — чи розраховані витрати доставки по позиціях
- Після розрахунку заповнюється `ExpenseInvoiceItem.calculated_delivery_cost`

---

## Типові помилки та як їх уникнути

| Неправильно | Правильно |
|-------------|-----------|
| `CharField` для сум | `DecimalField(max_digits=12, decimal_places=2)` |
| Хардкод у settings.py | `config("VAR")` через python-decouple |
| `on_delete=CASCADE` скрізь | `PROTECT` за замовч., `SET_NULL` для необов'язкових |
| FBV для CRUD | CBV (ListView, CreateView, etc.) |
| Ручне стилювання форм | `django-crispy-forms` з bootstrap5 |
| Перевірки прав тільки в шаблоні | `LoginRequiredMixin` або `@login_required` |
| Рядки довше 90 символів | Перенести на наступний рядок |
| Single quotes | Double quotes (`"`) |
| `isinstance(x, (A, B))` | `isinstance(x, A \| B)` (Python 3.10+) |

---

## Імпорт даних

Підтримуються три джерела накладних:
- **ESP** — система обліку постачальника
- **OPT** — оптова система
- **RUB** — внутрішня система Rubin

Скрипти імпорту: `data_to_import/import_data.py`
Формати: Excel (.xlsx), CSV, JSON
