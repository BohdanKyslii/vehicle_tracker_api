# AGENTS_GLOBAL.md — Глобальні правила проекту Expenses

Цей документ містить правила, стандарти та архітектурні рішення для проекту **Expenses**.
Обов'язковий до ознайомлення перед будь-яким завданням.

---

## 1. Огляд проекту

**Expenses** — система автоматизації обліку, аналізу та управління витратами компанії.

**Три функціональних модулі:**

| Модуль    | Призначення                                                            |
|-----------|------------------------------------------------------------------------|
| Transport | Облік витрат автопарку (пальне, ремонти, страховки, логістика)         |
| Warehouse | Облік витрат складського комплексу (фіксовані та змінні витрати)       |
| Shipment  | Управління відвантаженнями (магазини, продукти, накладні, маршрути)    |

**Користувачі:** адміністратор, співробітники з доступом до свого модулю.

---

## 2. Tech Stack

| Компонент    | Технологія                                   |
|--------------|----------------------------------------------|
| Backend      | Django 6.0                                   |
| Database     | PostgreSQL                                   |
| Frontend     | Bootstrap 5 + Django Templates               |
| Forms        | django-crispy-forms + crispy-bootstrap5      |
| Filtering    | django-filter                                |
| Reports      | openpyxl, reportlab                          |
| Config       | python-decouple (.env файл)                  |
| Linter       | Ruff (line-length: 90, double quotes)        |
| Pre-commit   | black, ruff, isort, trailing-whitespace      |
| CI/CD        | GitLab                                       |
| Static files | whitenoise                                   |
| Data import  | pandas, openpyxl                             |

---

## 3. Структура Django Apps

```
expenses/               # Головний пакет (settings.py, urls.py, wsgi.py)
accounts/               # Аутентифікація та профіль користувача
common/                 # Спільні утиліти, template tags, home selector
warehouse/              # Облік витрат складського комплексу
transport/              # Облік витрат автопарку
shipment/               # Відвантаження, продукти, накладні, маршрути
templates/              # Всі HTML-шаблони (розбиті по app)
data_to_import/         # Скрипти імпорту даних
task_description/       # Документація та завдання
```

---

## 4. Моделі по модулях

### Transport
- `Car` — авто (марка, модель, VIN, тип палива, статус, оренда, паливна картка)
- `MonthlyCarExpense` — щомісячний журнал витрат (пальне, ремонт, оренда, зарплата...)
- `MileageRecord` — облік пробігу (одометр, відстань, авто-розрахунок)
- `LogisticsExpense` — логістичні витрати (зарплата, найм, Нова Пошта)
- `FuelPrice` — довідник цін на паливо

### Warehouse
- `Warehouse` — об'єкти складу
- `Category` / `Subcategory` — дворівнева класифікація витрат
- `CostType` — тип витрат (Фіксована / Змінна)
- `ExpenseObject` — статті витрат (Warehouse + Category + Subcategory + CostType)
- `ExpenseRecord` — фактичні суми за місяць (з підтримкою авто-генерації)
- `FixedExpenseHistory` — журнал змін сум фіксованих витрат

### Shipment
- `Region` — регіони доставки
- `CategoryShop` / `Shop` — категорії та точки доставки (АЗС, магазини)
- `CategoryProduct` / `Product` — каталог продуктів
- `ProductPackaging` — логістичні параметри (вага, тара, штучна кількість)
- `ExpenseInvoice` — заголовок накладної (джерело: ESP/OPT/RUB, авто, маршрут)
- `ExpenseInvoiceItem` — рядки накладної (продукт, кількість, ціна, розрахункова доставка)
- `DeliveryRoute` — маршрути для групування накладних

### Accounts
- Розширення стандартного `User` Django (реєстрація, профіль, зміна пароля)

---

## 5. Стиль коду

### Форматування
```bash
ruff format .       # Форматування
ruff check .        # Перевірка лінтером
```

**Правила:**
- Line length: **90 символів**
- Quotes: **Double (`"`)**
- Imports: isort (profile=black)

### Docstrings
- Обов'язкові для всіх публічних функцій, класів, методів
- Перший рядок — дієслово в наказовому способі, закінчується крапкою
- Приклад: `"""Calculate total expenses for the month."""`

### Django патерни

**Views — Class-Based Views:**
```python
class ExpenseListView(LoginRequiredMixin, ListView):
    model = ExpenseRecord
    template_name = "warehouse/expenses_list.html"
    context_object_name = "expenses"
```
- FBV тільки для AJAX/API ендпоінтів

**Models:**
- `on_delete=models.PROTECT` — за замовчуванням (захист від випадкового видалення)
- `on_delete=models.SET_NULL` — коли зв'язок необов'язковий (`null=True, blank=True`)
- Фінансові поля — тільки `DecimalField(max_digits=12, decimal_places=2)`
- Обчислення — в `save()` або `@property`
- Рядкове представлення — в `__str__()`

**Forms:**
- `ModelForm` з `django-crispy-forms` та `bootstrap5`
- Валідація в `clean()` та `clean_<field>()`

**URLs:**
- Namespace: `app_name:model_action`
- Приклади: `warehouse:expense_list`, `transport:car_detail`, `shipment:invoice_create`

**Templates:**
- Спадкування: `templates/transport/base.html` → `templates/transport/car_list.html`
- Кастомні фільтри та теги — у `common/templatetags/custom_filters.py`

**Permissions:**
- `@login_required` для FBV
- `LoginRequiredMixin` як перший батьківський клас у CBV

---

## 6. Команди розробки

```bash
# Запуск
python manage.py runserver

# Міграції
python manage.py makemigrations
python manage.py migrate

# Лінтинг та форматування
ruff check .
ruff format .

# Pre-commit (перевірка всіх файлів)
pre-commit run --all-files

# Shell
python manage.py shell
```

---

## 7. Git Workflow

**Гілки:**
- `feature/short-name` — нова функціональність
- `bugfix/issue-name` — виправлення

**Коміти (Conventional Commits):**
```
feat(transport): add bulk mileage entry form
fix(warehouse): correct fixed expense auto-generation
refactor(shipment): extract invoice import to service
docs: update task description files
```

**Перед кожним комітом:**
1. `ruff check .` — 0 помилок
2. `ruff format .` — форматування
3. Pre-commit hooks спрацьовують автоматично

---

## 8. Безпека

- Всі секрети — тільки у `.env` (у `.gitignore`, ніколи не комітити!)
- `SECRET_KEY`, паролі БД — тільки через `python-decouple`
- `DEBUG=False` у продакшні
- CSRF-токени у всіх формах
- Перевірка прав доступу на бекенді (не тільки в шаблонах)
