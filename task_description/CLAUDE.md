# CLAUDE.md — Швидкий довідник для Claude Code

Контекст проекту для Claude Code. Перед кодом обов'язково читай `AGENTS_GLOBAL.md`.

---

## Проект

**Expenses** — Django веб-додаток для обліку витрат компанії.

**Модулі:** Transport (автопарк) | Warehouse (склад) | Shipment (відвантаження)

**Tech Stack:**
- Django 6.0 + PostgreSQL
- Bootstrap 5 + django-crispy-forms
- django-filter, openpyxl, reportlab
- python-decouple (.env конфіг)
- Ruff (90 символів, подвійні лапки)
- Pre-commit: black, ruff, isort, trailing-whitespace
- GitLab CI/CD

---

## Стиль коду

```bash
ruff format .       # Форматування
ruff check .        # Лінтинг (має бути 0 помилок)
pre-commit run --all-files  # Повна перевірка
```

**Правила:**
- Line length: **90**
- Quotes: **double (`"`)**
- Docstrings: перший рядок — дієслово, крапка в кінці
- `isinstance(x, A | B)` замість `isinstance(x, (A, B))`

---

## Команди

```bash
python manage.py runserver          # Запуск
python manage.py makemigrations     # Нові міграції
python manage.py migrate            # Застосувати міграції
python manage.py shell              # Django shell
python manage.py createsuperuser    # Суперкористувач
```

---

## Алгоритм роботи над завданням

1. Читай `AGENTS_GLOBAL.md` — глобальні правила
2. Читай `TASK.md` — конкретне завдання
3. Читай `AI_AGENT_CONTEXT.md` — технічний контекст
4. Переглянь `images/` — скриншоти (якщо є)
5. Плануй реалізацію за патернами проекту
6. Пиши код → `ruff check .` → коміт

---

## Патерни (обов'язкові)

### Views — тільки CBV для CRUD
```python
class ExpenseListView(LoginRequiredMixin, ListView):
    model = ExpenseRecord
    template_name = "warehouse/expenses_list.html"
    context_object_name = "expenses"
    paginate_by = 50
```

### Forms — crispy-forms
```python
class ExpenseRecordForm(forms.ModelForm):
    class Meta:
        model = ExpenseRecord
        fields = ["expense_object", "month", "year", "amount", "comment"]

    def __init__(self, *args, **kwargs):
        """Initialize form with crispy layout."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
```

### Models — DecimalField + PROTECT
```python
amount = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    verbose_name="Сума",
)
warehouse = models.ForeignKey(
    Warehouse,
    on_delete=models.PROTECT,
    verbose_name="Склад",
)
car = models.ForeignKey(
    Car,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
)
```

### URLs — namespace:action
```python
# warehouse/urls.py
app_name = "warehouse"
urlpatterns = [
    path("", views.ExpenseListView.as_view(), name="expense_list"),
    path("create/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("<int:pk>/", views.ExpenseDetailView.as_view(), name="expense_detail"),
]
# Використання: {% url 'warehouse:expense_list' %}
```

---

## Структура Apps

```
accounts/   → реєстрація, login, logout, профіль
common/     → home_selector, template tags (custom_filters.py)
warehouse/  → Warehouse, Category, ExpenseObject, ExpenseRecord, FixedExpenseHistory
transport/  → Car, MonthlyCarExpense, MileageRecord, LogisticsExpense, FuelPrice
shipment/   → Shop, Product, ProductPackaging, ExpenseInvoice, DeliveryRoute
```

---

## Важливо

- `.env` — ніколи не комітити (в `.gitignore`)
- Всі секрети через `config("VAR")` з python-decouple
- `ruff check .` — 0 помилок перед кожним комітом
- Міграції — для кожної зміни моделей
- Фінансові поля — тільки `DecimalField`
- Pre-commit hooks спрацьовують автоматично — якщо fail, re-stage і commit знову
