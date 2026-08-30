# Vehicle Cost Tracker — Django Backend
# Покрокова інструкція з написання коду
# Відкрий у другому вікні WebStorm і пиши руками

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 1 — ІНІЦІАЛІЗАЦІЯ DJANGO ПРОЄКТУ
# ═══════════════════════════════════════════════════════════

## Крок 1.1 — Що таке Django і його структура

Django — це Python web-фреймворк із принципом "batteries included".
Аналог: Django для Python = Spring для Java, але простіший.

Ключові поняття:
- **Model**     — опис таблиці БД (як TypeScript інтерфейс + міграція)
- **Serializer** — перетворення моделі у JSON (як DTO у Java)
- **View**      — обробник запиту (як Controller)
- **URL**       — маршрут до View (як @RequestMapping)
- **App**       — модуль проєкту (як окремий мікросервіс)

```
Запит від React:
GET /api/cars/
     ↓
urls.py → знаходить потрібний View
     ↓
views.py → отримує дані з БД через Model
     ↓
serializers.py → перетворює у JSON
     ↓
Відповідь: [{"idCar": 1, "nameCar": "Sprinter"...}]
```

---

## Крок 1.2 — Створення проєкту

Відкрий термінал WebStorm у папці де тримаєш проєкти:

```bash
cd C:\Users\b.kisliy\PycharmProjects
mkdir vehicle_tracker_api
cd vehicle_tracker_api
```

Створи віртуальне середовище:
```bash
python -m venv venv
venv\Scripts\activate
```

Після активації побачиш `(venv)` на початку рядка термінала.
Аналог: virtualenv у Django проєктах які ти вже робив.

Встановлення залежностей:
```bash
pip install django
pip install djangorestframework
pip install psycopg2-binary
pip install python-dotenv
pip install django-cors-headers
pip install gunicorn
pip install Pillow
```

Що встановили:
- `django` — основний фреймворк
- `djangorestframework` — DRF, додає API функціонал
- `psycopg2-binary` — драйвер PostgreSQL для Python
- `python-dotenv` — читання .env файлів
- `django-cors-headers` — дозволяє React звертатись до API (CORS)
- `gunicorn` — production веб-сервер (замість вбудованого Django)
- `Pillow` — робота із зображеннями (може знадобитись)

Зберігаємо залежності:
```bash
pip freeze > requirements.txt
```

Створюємо Django проєкт:
```bash
django-admin startproject config .
```

Крапка в кінці = створити у поточній папці, не у підпапці.

Структура після створення:
```
vehicle_tracker_api/
├── config/
│   ├── __init__.py
│   ├── settings.py    ← головні налаштування
│   ├── urls.py        ← головні маршрути
│   ├── wsgi.py        ← для production сервера
│   └── asgi.py
├── venv/
├── manage.py          ← команди Django
└── requirements.txt
```

---

## Крок 1.3 — Створення .env файлу

Створи `.env` у корені проєкту:

```
# Django
SECRET_KEY=django-insecure-замінити-на-реальний-ключ
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,warehouse.mom,192.168.0.114

# PostgreSQL
DB_NAME=vehicle_tracker
DB_USER=vt_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# CORS — дозволяємо React звертатись до API
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://warehouse.mom
```

Створи `env.example` (комітимо у git без реальних значень):

```
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Створи `.gitignore`:

```
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# Environment
.env

# IDE
.idea/
*.swp
```

---

## Крок 1.4 — Налаштування settings.py

ВИДАЛИ весь вміст `config/settings.py` і напиши з нуля:

```python
# config/settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Завантажуємо .env файл
load_dotenv()

# BASE_DIR — шлях до кореня проєкту
# Path(__file__) — шлях до цього файлу (settings.py)
# .resolve() — абсолютний шлях
# .parent.parent — піднімаємось на 2 рівні вгору (з config/ у корінь)
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────
# БЕЗПЕКА
# ─────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY")

# Debug=True показує детальні помилки — ТІЛЬКИ для розробки
DEBUG = os.getenv("DEBUG", "False") == "True"

# Список дозволених хостів
# split(",") розбиває рядок "host1,host2" → ["host1", "host2"]
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# ─────────────────────────────────────────────────────────
# ЗАСТОСУНКИ
# ─────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонні бібліотеки
    "rest_framework",       # Django REST Framework
    "corsheaders",          # CORS для React
    # Наші застосунки (додамо пізніше)
    # "apps.cars",
    # "apps.drivers",
    # "apps.products",
    # "apps.waybills",
    # "apps.routes",
    # "apps.logistics",
    # "apps.analytics",
]

# ─────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────

MIDDLEWARE = [
    # CorsMiddleware МАЄ бути першим у списку
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─────────────────────────────────────────────────────────
# БАЗА ДАНИХ
# ─────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ─────────────────────────────────────────────────────────
# ВАЛІДАЦІЯ ПАРОЛІВ
# ─────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────────────────
# ЛОКАЛІЗАЦІЯ
# ─────────────────────────────────────────────────────────

LANGUAGE_CODE = "uk"        # українська мова для Django admin
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True               # зберігаємо дати у UTC у БД

# ─────────────────────────────────────────────────────────
# СТАТИЧНІ ФАЙЛИ
# ─────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────────────
# CORS (дозволяємо React звертатись до API)
# ─────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

# ─────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    # Формат відповіді за замовчуванням — JSON
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Пагінація за замовчуванням
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
```

---

## Крок 1.5 — Перевірка налаштувань

```bash
python manage.py check
```

Якщо бачиш `System check identified no issues` — все налаштовано правильно ✅

Перевір підключення до БД:
```bash
python manage.py dbshell
```

Якщо підключилось — побачиш `psql` консоль. Вийди: `\q`

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 2 — СТРУКТУРА ЗАСТОСУНКІВ (APPS)
# ═══════════════════════════════════════════════════════════

## Крок 2.1 — Навіщо розбивати на apps

Django app — це модуль з моделями, серіалізаторами і views.
Аналог: окремий Django app = окремий React розділ (pages/fleet, pages/waybills...).

Ми розіб'ємо так:
```
apps/
├── cars/        ← авто, водії, маршрути
├── products/    ← товари, категорії, логістика
├── customers/   ← клієнти, магазини
├── waybills/    ← реєстр накладних із 1С
├── logistics/   ← найманий транспорт, служби доставки
└── analytics/   ← розрахунки, звіти
```

---

## Крок 2.2 — Створення папки apps і застосунків

```bash
mkdir apps
python manage.py startapp cars apps/cars
python manage.py startapp products apps/products
python manage.py startapp customers apps/customers
python manage.py startapp waybills apps/waybills
python manage.py startapp logistics apps/logistics
python manage.py startapp analytics apps/analytics
```

Кожна команда `startapp` створює:
```
apps/cars/
├── __init__.py
├── admin.py       ← реєстрація у Django Admin
├── apps.py        ← конфігурація застосунку
├── models.py      ← моделі (таблиці БД)
├── serializers.py ← (створимо вручну)
├── views.py       ← обробники запитів
├── urls.py        ← (створимо вручну)
└── tests.py
```

---

## Крок 2.3 — Виправлення apps.py у кожному застосунку

Django має знати повний шлях до app. Відкрий `apps/cars/apps.py`:

```python
# apps/cars/apps.py
from django.apps import AppConfig


class CarsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # ВАЖЛИВО: повний шлях з папкою apps
    name = "apps.cars"
    verbose_name = "Автопарк"  # назва у Django Admin українською
```

Зроби те саме для кожного застосунку:

```python
# apps/products/apps.py
class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"
    verbose_name = "Товари"

# apps/customers/apps.py
class CustomersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.customers"
    verbose_name = "Клієнти"

# apps/waybills/apps.py
class WaybillsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.waybills"
    verbose_name = "Накладні"

# apps/logistics/apps.py
class LogisticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.logistics"
    verbose_name = "Логістика"

# apps/analytics/apps.py
class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "Аналітика"
```

---

## Крок 2.4 — Реєстрація apps у settings.py

Відкрий `config/settings.py`, знайди `INSTALLED_APPS` і розкоментуй:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонні бібліотеки
    "rest_framework",
    "corsheaders",
    # Наші застосунки
    "apps.cars",
    "apps.products",
    "apps.customers",
    "apps.waybills",
    "apps.logistics",
    "apps.analytics",
]
```

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 3 — МОДЕЛІ (ТАБЛИЦІ БД)
# ═══════════════════════════════════════════════════════════

## Крок 3.1 — Що таке Django Model

Model — це Python клас який описує таблицю БД.
Django автоматично створює SQL з цього класу.

```python
# Замість написання SQL вручну:
# CREATE TABLE cars (
#     id SERIAL PRIMARY KEY,
#     name_car VARCHAR(100) NOT NULL,
#     ...
# );

# Пишемо Python клас:
class Car(models.Model):
    name_car = models.CharField(max_length=100)
    ...
# Django сам генерує SQL через міграції!
```

Типи полів:
```python
models.CharField(max_length=N)   # VARCHAR
models.TextField()               # TEXT
models.IntegerField()            # INTEGER
models.DecimalField(max_digits, decimal_places)  # NUMERIC
models.BooleanField()            # BOOLEAN
models.DateField()               # DATE
models.DateTimeField()           # TIMESTAMPTZ
models.ForeignKey(Model, on_delete=...)  # FK
```

---

## Крок 3.2 — Модель ProductCategory

Відкрий `apps/products/models.py`, ВИДАЛИ вміст і напиши:

```python
# apps/products/models.py
from django.db import models


class ProductCategory(models.Model):
    """
    Product category with support for parent-child hierarchy.
    Root categories: Вино, Китай, Сопутка (parent=None)
    Child categories reference their parent.
    """

    name_category = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Назва категорії",
    )
    # null=True, blank=True — поле може бути порожнім (коренева категорія)
    # on_delete=SET_NULL — якщо батьківська видалена, дочірня стає коренева
    # related_name — як звертатись до дочірніх: category.children.all()
    parent = models.ForeignKey(
        "self",                      # посилання на ту саму модель
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name="Батьківська категорія",
    )

    class Meta:
        db_table = "product_categories"        # назва таблиці у БД
        verbose_name = "Категорія товару"
        verbose_name_plural = "Категорії товарів"
        ordering = ["name_category"]

    def __str__(self):
        # __str__ — що показує Django Admin у списку
        if self.parent:
            return f"{self.parent.name_category} → {self.name_category}"
        return self.name_category

    @property
    def is_root(self) -> bool:
        """Returns True if this is a root category (no parent)."""
        return self.parent is None
```

---

## Крок 3.3 — Модель Product та ProductLogistics

Продовжуємо у `apps/products/models.py`:

```python
class Product(models.Model):
    """
    Product from the 1C accounting system.
    id_product is the 1C article code (not auto-generated).
    """

    # primary_key=True — цей рядок є первинним ключем замість auto id
    id_product = models.IntegerField(
        primary_key=True,
        verbose_name="Артикул (1С)",
    )
    name_product = models.CharField(
        max_length=255,
        verbose_name="Назва товару",
    )
    # ForeignKey — зовнішній ключ до ProductCategory
    # default=15 — категорія "Інше" за замовчуванням
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=15,
        related_name="products",
        verbose_name="Категорія",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Опис",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,   # автоматично при створенні
        verbose_name="Створено",
    )
    updated_at = models.DateTimeField(
        auto_now=True,       # автоматично при кожному збереженні
        verbose_name="Оновлено",
    )

    class Meta:
        db_table = "products"
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["name_product"]

    def __str__(self):
        return f"{self.id_product} — {self.name_product}"


class ProductLogistics(models.Model):
    """
    Logistics data for a product: dimensions and weight.
    Calculated fields (volume) are computed in utils, not stored.
    """

    # OneToOneField — один товар має одну логістику
    # Відрізняється від ForeignKey: унікальне з'єднання 1-до-1
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,      # видалили товар → видалили логістику
        related_name="logistics",
        verbose_name="Товар",
    )
    # Одиниця товару
    # max_digits=8 — максимум 8 цифр; decimal_places=3 — 3 після коми
    unit_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Вага одиниці (кг)",
    )
    unit_length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Довжина одиниці (см)",
    )
    unit_width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ширина одиниці (см)",
    )
    unit_height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Висота одиниці (см)",
    )
    # Ящик
    units_per_box = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Одиниць у ящику",
    )
    box_weight_kg = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True,
        verbose_name="Вага ящика (кг)",
    )
    box_length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Довжина ящика (см)",
    )
    box_width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ширина ящика (см)",
    )
    box_height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Висота ящика (см)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_logistics"
        verbose_name = "Логістика товару"
        verbose_name_plural = "Логістика товарів"

    def __str__(self):
        return f"Логістика: {self.product.name_product}"

    # Property — обчислюване поле, не зберігається у БД
    # Викликається як атрибут: logistics.unit_volume_cbm
    @property
    def unit_volume_cbm(self):
        """Unit volume in cubic meters."""
        if self.unit_length_cm and self.unit_width_cm and self.unit_height_cm:
            return float(self.unit_length_cm * self.unit_width_cm * self.unit_height_cm) / 1_000_000
        return None

    @property
    def box_volume_cbm(self):
        """Box volume in cubic meters."""
        if self.box_length_cm and self.box_width_cm and self.box_height_cm:
            return float(self.box_length_cm * self.box_width_cm * self.box_height_cm) / 1_000_000
        return None

    @property
    def calculated_box_weight_kg(self):
        """Calculated box weight = unit weight × units per box."""
        if self.unit_weight_kg and self.units_per_box:
            return float(self.unit_weight_kg) * self.units_per_box
        return None
```

---

## Крок 3.4 — Моделі Customer та Store

Відкрий `apps/customers/models.py`:

```python
# apps/customers/models.py
from django.db import models


class Customer(models.Model):
    """
    Customer (company) from 1C accounting system.
    id_customer is the 1C identifier.
    """

    id_customer = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="ID клієнта (1С)",
    )
    name_customer = models.CharField(
        max_length=255,
        verbose_name="Назва клієнта",
    )
    # Напрямок діяльності: Роздріб, Мережа, HoReCa
    network_customer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Напрямок діяльності",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        verbose_name = "Клієнт"
        verbose_name_plural = "Клієнти"
        ordering = ["name_customer"]

    def __str__(self):
        return self.name_customer


class Store(models.Model):
    """
    Store / retail point belonging to a customer.
    One customer can have multiple stores.
    """

    id_store = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="ID магазину (1С)",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.RESTRICT,     # не можна видалити клієнта якщо є магазини
        related_name="stores",
        verbose_name="Клієнт",
    )
    name_store = models.CharField(
        max_length=255,
        verbose_name="Назва магазину",
    )
    store_address = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Адреса магазину",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        verbose_name = "Магазин"
        verbose_name_plural = "Магазини"
        ordering = ["name_store"]

    def __str__(self):
        return f"{self.name_store} ({self.customer.name_customer})"


class StoreDeliveryAddress(models.Model):
    """
    Additional delivery addresses for a store.
    One store can have multiple delivery addresses.
    """

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="delivery_addresses",
        verbose_name="Магазин",
    )
    delivery_address = models.CharField(
        max_length=500,
        verbose_name="Адреса доставки",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Основна адреса",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Примітки",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_delivery_addresses"
        verbose_name = "Адреса доставки"
        verbose_name_plural = "Адреси доставки"

    def __str__(self):
        return f"{self.store.name_store}: {self.delivery_address}"
```

---

## Крок 3.5 — Моделі Car, CarSpecs, Trailer, Driver

Відкрий `apps/cars/models.py`:

```python
# apps/cars/models.py
from django.db import models


class Car(models.Model):
    """
    Vehicle from the company fleet.
    Includes fuel card and default tracking mode for the driver.
    """

    # Статус авто — choices обмежує значення поля
    class Status(models.TextChoices):
        ACTIVE = "active", "Активне"
        REPAIR = "repair", "Ремонт"
        INACTIVE = "inactive", "Неактивне"

    # Режим трекінгу водія
    class TrackingMode(models.TextChoices):
        DAILY = "daily", "Щоденний (одометр)"
        FULL = "full", "Повний (кожна точка)"

    name_car = models.CharField(
        max_length=100,
        verbose_name="Назва авто",
    )
    number_car = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Держ. номер",
    )
    fuel_card_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Номер паливної карти",
    )
    # Амортизація грн/міс — стала величина для розрахунків
    amount_car = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Амортизація (грн/міс)",
    )
    default_tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        default=TrackingMode.DAILY,
        verbose_name="Режим трекінгу (дефолт)",
    )
    status_car = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активне")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cars"
        verbose_name = "Авто"
        verbose_name_plural = "Автопарк"
        ordering = ["number_car"]

    def __str__(self):
        return f"{self.number_car} — {self.name_car}"


class CarStatusLog(models.Model):
    """
    History of car status changes.
    Used to calculate days in repair per month.
    """

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name="Авто",
    )
    status = models.CharField(
        max_length=20,
        choices=Car.Status.choices,
        verbose_name="Статус",
    )
    reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Причина / коментар",
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата зміни",
    )
    # Хто змінив — посилання на User (майбутня авторизація)
    changed_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Змінив",
    )

    class Meta:
        db_table = "car_status_logs"
        verbose_name = "Журнал статусів авто"
        verbose_name_plural = "Журнал статусів авто"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.car.number_car}: {self.status} ({self.changed_at.date()})"


class CarSpecs(models.Model):
    """
    Technical specifications of a vehicle.
    Stored separately to keep Car model clean.
    """

    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name="specs",
        verbose_name="Авто",
    )
    vin_code = models.CharField(
        max_length=17,
        blank=True,
        default="",
        verbose_name="VIN код",
    )
    year_manufactured = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Рік випуску",
    )
    weight_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Маса авто (кг)",
    )
    payload_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Вантажопідйомність (кг)",
    )
    length_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Довжина (см)",
    )
    width_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Ширина (см)",
    )
    height_cm = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Висота (см)",
    )
    # Гідроборт — за замовчуванням немає
    has_tail_lift = models.BooleanField(
        default=False,
        verbose_name="Гідроборт",
    )
    # Причіп — за замовчуванням немає
    has_trailer = models.BooleanField(
        default=False,
        verbose_name="Причіп",
    )

    class Meta:
        db_table = "car_specs"
        verbose_name = "Характеристики авто"
        verbose_name_plural = "Характеристики авто"

    def __str__(self):
        return f"Характеристики: {self.car.number_car}"


class Trailer(models.Model):
    """
    Trailer attached to a vehicle.
    Created only when car.specs.has_trailer = True.
    """

    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name="trailer",
        verbose_name="Авто",
    )
    model = models.CharField(
        max_length=100,
        verbose_name="Модель причепа",
    )
    number_trailer = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номерний знак",
    )
    year_manufactured = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Рік випуску",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        db_table = "trailers"
        verbose_name = "Причіп"
        verbose_name_plural = "Причепи"

    def __str__(self):
        return f"{self.number_trailer} — {self.model}"


class Driver(models.Model):
    """
    Driver assigned to a vehicle.
    Telegram-лінк живе на apps.accounts.Profile.telegram_id (авторизація),
    НЕ тут — Driver це доменна картка "водій+авто", Profile це обліковий
    запис. Один Profile(role=DRIVER) прив'язується до одного Driver через
    Profile.driver (див. Фазу 4.5 / TELEGRAM_BOT_SETUP.md).
    """

    name_driver = models.CharField(
        max_length=150,
        verbose_name="ПІБ водія",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Телефон",
    )
    drivers_license = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Посвідчення водія",
    )
    car = models.OneToOneField(
        Car,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="driver",
        verbose_name="Закріплене авто",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drivers"
        verbose_name = "Водій"
        verbose_name_plural = "Водії"
        ordering = ["name_driver"]

    def __str__(self):
        return self.name_driver
```

---

## Крок 3.6 — Модель WaybillRecord

Відкрий `apps/waybills/models.py`:

```python
# apps/waybills/models.py
from django.db import models
from apps.customers.models import Customer, Store
from apps.products.models import Product


class WaybillRecord(models.Model):
    """
    Single line from a 1C waybill import.
    quantity > 0 = shipment, quantity < 0 = return.
    Unique key: waybill_number + line_position.
    """

    class LegalEntity(models.TextChoices):
        ESP = "ESP", "ESP"
        OPT = "OPT", "OPT"
        RUBIN = "Rubin", "Rubin"

    class DeliveryChannel(models.TextChoices):
        OWN = "own", "Власне авто"
        HIRED = "hired", "Найманий транспорт"
        CARRIER = "carrier", "Служба доставки"

    legal_entity = models.CharField(
        max_length=10,
        choices=LegalEntity.choices,
        verbose_name="Юридична особа",
    )
    waybill_number = models.CharField(
        max_length=50,
        verbose_name="Номер накладної",
    )
    waybill_date = models.DateField(
        verbose_name="Дата накладної",
    )
    line_position = models.SmallIntegerField(
        verbose_name="Позиція в накладній",
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Клієнт",
    )
    # Копія назви на момент імпорту (клієнт може змінити назву)
    customer_name = models.CharField(max_length=255, verbose_name="Клієнт (копія)")
    store = models.ForeignKey(
        Store,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Магазин",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="waybill_records",
        verbose_name="Товар",
    )
    product_name = models.CharField(max_length=255, verbose_name="Товар (копія)")
    # quantity: + відвантаження, - повернення
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість",
    )
    price_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Ціна (грн)",
    )
    total_uah = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Сума (грн)",
    )
    comment = models.TextField(
        blank=True,
        default="",
        verbose_name="Коментар",
    )
    # Логістика (розраховується при імпорті)
    total_weight_kg = models.DecimalField(
        max_digits=12, decimal_places=3,
        null=True, blank=True,
        verbose_name="Загальна вага (кг)",
    )
    total_volume_cbm = models.DecimalField(
        max_digits=12, decimal_places=6,
        null=True, blank=True,
        verbose_name="Об'єм (м³)",
    )
    # Канал доставки: null = ще не призначено
    delivery_channel = models.CharField(
        max_length=10,
        choices=DeliveryChannel.choices,
        null=True,
        blank=True,
        verbose_name="Канал доставки",
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    import_batch_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="ID імпорту",
    )

    class Meta:
        db_table = "waybill_records"
        verbose_name = "Рядок накладної"
        verbose_name_plural = "Реєстр накладних"
        # Унікальний ключ: накладна + позиція
        unique_together = [["waybill_number", "line_position"]]
        ordering = ["-waybill_date", "waybill_number"]
        indexes = [
            models.Index(fields=["waybill_date"]),
            models.Index(fields=["waybill_number"]),
            models.Index(fields=["delivery_channel"]),
        ]

    def __str__(self):
        return f"{self.waybill_number} / поз.{self.line_position}"

    @property
    def is_return(self) -> bool:
        """Returns True if this line is a product return."""
        return self.quantity < 0
```

---

## Крок 3.7 — Модель RouteEvent

Відкрий `apps/cars/models.py`, додай після класу `Driver`:

```python
class RouteEvent(models.Model):
    """
    Single event in a driver's route.
    All tracking data is stored here — daily and full mode.
    """

    class EventType(models.TextChoices):
        DEPOT_START = "depot_start", "Старт зі складу"
        DELIVERY = "delivery", "Вивантаження"
        PARKING_END = "parking_end", "Кінець маршруту"
        DEPOT_RETURN = "depot_return", "Повернення на склад"
        REFUEL = "refuel", "Заправка"
        OTHER_COST = "other_cost", "Інші витрати"
        RETURN_GOODS = "return_goods", "Повернення товару"
        EXTRA_CARGO = "extra_cargo", "Додатковий вантаж"

    class TrackingMode(models.TextChoices):
        DAILY = "daily", "Щоденний"
        FULL = "full", "Повний"

    car = models.ForeignKey(
        Car,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name="Авто",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.RESTRICT,
        related_name="route_events",
        verbose_name="Водій",
    )
    tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        verbose_name="Режим трекінгу",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name="Тип події",
    )
    event_ts = models.DateTimeField(
        verbose_name="Час події",
    )
    odometer_km = models.IntegerField(
        null=True, blank=True,
        verbose_name="Одометр (км)",
    )
    pallets_count = models.SmallIntegerField(
        null=True, blank=True,
        verbose_name="Кількість палет",
    )

    # Для delivery
    waybill_number = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Номер накладної",
    )
    waybill_date = models.DateField(
        null=True, blank=True,
        verbose_name="Дата накладної",
    )
    customer_name = models.CharField(
        max_length=255, blank=True, default="",
        verbose_name="Клієнт",
    )

    # Відмова від поставки (delivery)
    rejection_full = models.BooleanField(
        null=True, blank=True,
        verbose_name="Повна відмова",
    )
    rejection_product_id = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Артикул (відмова)",
    )
    rejection_qty = models.DecimalField(
        max_digits=10, decimal_places=3,
        null=True, blank=True,
        verbose_name="Кількість (відмова)",
    )
    rejection_comment = models.TextField(blank=True, default="")

    # Для refuel
    fuel_liters = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="Паливо (л)",
    )
    fuel_cost_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Паливо (грн)",
    )
    ad_blue_liters = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name="AdBlue (л)",
    )
    ad_blue_cost_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="AdBlue (грн)",
    )

    # Для other_cost
    other_costs_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Інші витрати (грн)",
    )
    other_costs_comment = models.TextField(blank=True, default="")

    # Для return_goods
    return_client_waybill = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name="Накладна клієнта (повернення)",
    )

    # Для extra_cargo
    extra_from = models.CharField(max_length=255, blank=True, default="")
    extra_to = models.CharField(max_length=255, blank=True, default="")
    extra_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=3,
        null=True, blank=True,
    )
    extra_waybill = models.CharField(max_length=50, blank=True, default="")
    extra_comment = models.TextField(blank=True, default="")

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "route_events"
        verbose_name = "Подія маршруту"
        verbose_name_plural = "Події маршруту"
        ordering = ["event_ts"]
        indexes = [
            models.Index(fields=["car", "event_ts"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.car.number_car} | {self.event_type} | {self.event_ts}"


class MonthlyCosts(models.Model):
    """
    Monthly operating costs per vehicle, entered by the logistics manager.
    repair_actual_uah overrides the calculated rate if provided.
    """

    car = models.ForeignKey(
        Car,
        on_delete=models.RESTRICT,
        related_name="monthly_costs",
        verbose_name="Авто",
    )
    # Зберігаємо як перший день місяця: 2026-06-01
    month = models.DateField(verbose_name="Місяць")
    salary_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="ЗП водія (грн)",
    )
    taxes_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Податки із ЗП (грн)",
    )
    depreciation_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Амортизація (грн)",
    )
    # Якщо заповнено — пріоритет над розрахунковим
    repair_actual_uah = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Ремонт фактичний (грн)",
    )
    repair_rate_uah_km = models.DecimalField(
        max_digits=6, decimal_places=2, default=2.00,
        verbose_name="Ставка ремонту (грн/км)",
    )
    other_costs_uah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Інші витрати (грн)",
    )
    other_costs_comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_costs"
        verbose_name = "Місячні витрати"
        verbose_name_plural = "Місячні витрати"
        # Один запис на авто на місяць
        unique_together = [["car", "month"]]
        ordering = ["-month"]

    def __str__(self):
        return f"{self.car.number_car} — {self.month.strftime('%m.%Y')}"
```

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 4 — МІГРАЦІЇ
# ═══════════════════════════════════════════════════════════

## Крок 4.1 — Що таке міграції

Міграція — це файл Python який описує зміни у БД.
Django порівнює моделі з поточним станом БД і генерує SQL.

```
python manage.py makemigrations  → генерує файл міграції
python manage.py migrate         → застосовує міграцію до БД
```

Аналог: `ALTER TABLE` у SQL, але автоматично.

---

## Крок 4.2 — Генерація та застосування міграцій

```bash
# Генеруємо файли міграцій для всіх apps
python manage.py makemigrations products
python manage.py makemigrations customers
python manage.py makemigrations cars
python manage.py makemigrations waybills
python manage.py makemigrations logistics

# Переглянь що буде зроблено (без застосування):
python manage.py sqlmigrate products 0001

# Застосовуємо всі міграції до БД
python manage.py migrate
```

Перевір що таблиці створились:
```bash
python manage.py dbshell
\dt    # показати всі таблиці
\q     # вийти
```

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 4.5 — АВТОРИЗАЦІЯ КОРИСТУВАЧІВ
# ═══════════════════════════════════════════════════════════

> Ця фаза йде поза початковою нумерацією (див. `task_description/ROADMAP.md`).
> Причина: фронтенд (`CODING_GUIDE.md`, Фаза 4.5) не може продовжувати
> без робочого логіну/реєстрації, тож ця частина API робиться зараз,
> а Admin/Серіалізатори/Views для `cars`/`products`/... — одразу після.
> Працюй у гілці `feature/faza-4.5-auth` (див. ROADMAP.md).

## Крок 4.5.1 — Чому Django session + CSRF cookie, а не токен/JWT

React SPA і Django живуть на **одному домені** (nginx віддає `dist/`
і проксує `/api/` на той самий Django на тому ж сервері — так само,
як заплановано для `warehouse`, див. `task_description/warehouse/08_PROJECT_STRUCTURE.md`).
На одному домені токен/JWT — зайва складність: браузер сам зберігає
і надсилає cookie, не треба вручну класти токен у `localStorage` і
думати про його оновлення.

```
POST /api/auth/login/   → Django ставить sessionid cookie
Наступні запити         → браузер сам додає cookie
POST/PUT/DELETE запити  → потрібен додатково X-CSRFToken header
                           (Django CSRF-захист працює навіть для
                           сесійної автентифікації)
```

## Крок 4.5.2 — Фікс CORS middleware

`corsheaders` вже є в `INSTALLED_APPS`, але його **не додали в
MIDDLEWARE** — тобто CORS зараз фактично не працює. Відкрий
`config/settings.py`:

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ДОДАТИ, і саме першим
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

Додай туди ж, після `CORS_ALLOWED_ORIGINS`:

```python
# Дозволяємо React надсилати cookie разом із запитом
# (без цього браузер отримає sessionid, але не відправить його назад)
CORS_ALLOW_CREDENTIALS = True

# Django довіряє CSRF-токену тільки з цих origin
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,https://warehouse.mom",
).split(",")
```

Онови `.env` і `env.example` — додай рядок `CSRF_TRUSTED_ORIGINS=` за
тим самим принципом, що й `CORS_ALLOWED_ORIGINS`.

## Крок 4.5.3 — Створення apps/accounts

```bash
python manage.py startapp accounts apps/accounts
```

`apps/accounts/apps.py`:

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Користувачі"
```

Додай `"apps.accounts"` у `INSTALLED_APPS` (`config/settings.py`).

Своя модель `User` тут не потрібна — MVP використовує вбудований
`django.contrib.auth.models.User` (username, email, password вже є).
Якщо пізніше знадобляться додаткові поля (роль, телефон) —
розширюється через `OneToOneField(User)` окремою моделлю `Profile`,
без міграції самого `User`.

## Крок 4.5.4 — Серіалізатори

`apps/accounts/serializers.py`:

```python
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    # write_only — це поле приймається на вхід, але ніколи не повертається у відповіді
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        # create_user — хешує пароль (звичайний create() зберіг би його як є)
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
```

## Крок 4.5.5 — Views

`apps/accounts/views.py`:

```python
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """
    GET /api/auth/csrf/ — фронтенд викликає це ПЕРШИМ, ще до форми логіну,
    щоб браузер отримав csrftoken cookie (інакше перший POST впаде з 403).
    """
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ — {username, email, password}"""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user)  # одразу логінимо після реєстрації
    return Response(UserSerializer(user).data, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """POST /api/auth/login/ — {username, password}"""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"error": "Невірний логін або пароль"}, status=400)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/"""
    logout(request)
    return Response(status=204)


@api_view(["GET"])
@permission_classes([AllowAny])
def me(request):
    """
    GET /api/auth/me/ — поточний користувач.
    Фронтенд викликає це при завантаженні застосунку, щоб дізнатись,
    чи є активна сесія (замість того, щоб зберігати щось у localStorage).
    """
    if not request.user.is_authenticated:
        return Response({"user": None})
    return Response({"user": UserSerializer(request.user).data})
```

## Крок 4.5.6 — URLs

`apps/accounts/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path("auth/csrf/", views.csrf),
    path("auth/register/", views.register),
    path("auth/login/", views.login_view),
    path("auth/logout/", views.logout_view),
    path("auth/me/", views.me),
]
```

`config/urls.py` — додай:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
]
```

## Крок 4.5.7 — Перевірка

```bash
python manage.py migrate   # auth-таблиці вже є, але переконайся
python manage.py runserver
```

PowerShell (сесія зберігається між запитами через `-SessionVariable`):

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/csrf/" -SessionVariable s
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register/" -Method POST `
  -WebSession $s `
  -Body (@{username="test"; email="test@test.com"; password="Str0ngPass!23"} | ConvertTo-Json) `
  -ContentType "application/json"
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me/" -WebSession $s
```

Якщо `me` повертає `{"user": {"id": 1, "username": "test", ...}}` —
сесія працює. Далі переходь у `vehicle_cost_tracker`, `CODING_GUIDE.md`,
Фаза 4.5.

---

## Крок 4.5.8 — Ролі, Telegram-бот, підтвердження реєстрацій (поза цим гайдом)

`apps/accounts` виріс за межі того, що описано вище: `Profile.role`
(`driver`/`logist`/`manager`/`head`), `Profile.telegram_id` +
`Profile.driver` (лінк на картку водія з Фази 3.5), Telegram-бот
(`apps/accounts/bot.py`, aiogram, `python manage.py run_bot`) для
самореєстрації водіїв і підтвердження заявок кнопками прямо в чаті,
`telegram_auth.py` (перевірка `initData` для Mini App логіну),
`permissions.py` (`HasRole`/`IsManagerOrHead` — маленькі
permission-класи; **поки не підключені до жодного ViewSet**, дивись
Фазу 9), `notifications.py`/`telegram_notify.py` (лист/Telegram
адміну про нову заявку).

Це реальний, задеплоєний функціонал — але він писався поза цим гайдом
(нема сенсу дублювати тут покроково). Повний опис: **`TELEGRAM_BOT_SETUP.md`**
у корені цього репо. Ключове, що треба тримати в голові рухаючись далі
гайдом:

- Реєстрація (веб-форма АБО Telegram-бот) створює `User(is_active=False)`
  + `Profile` — користувач НЕ може залогинитись, поки адмін не
  підтвердить (через Django Admin або кнопку в Telegram).
- Лінк `Profile.driver → Driver` (Фаза 3.5) ставиться ВРУЧНУ адміном
  через Django Admin — бот цього не автоматизує.
- `role == 'head'` не можна вибрати при самореєстрації (тільки
  `driver`/`logist`/`manager`) — головного признача лише вручну.

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 5 — DJANGO ADMIN
# ═══════════════════════════════════════════════════════════

## Крок 5.1 — Реєстрація моделей у Admin

Django Admin — вбудований інтерфейс для роботи з даними.
Відкрий `apps/products/admin.py`:

```python
# apps/products/admin.py
from django.contrib import admin
from .models import ProductCategory, Product, ProductLogistics


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_category", "parent", "is_root"]
    list_filter = ["parent"]
    search_fields = ["name_category"]


class ProductLogisticsInline(admin.StackedInline):
    """
    Inline — редагування логістики прямо на сторінці товару.
    StackedInline = вертикальне розташування полів.
    """
    model = ProductLogistics
    extra = 0   # не показувати порожні форми
    fields = [
        ("unit_weight_kg", "units_per_box"),
        ("unit_length_cm", "unit_width_cm", "unit_height_cm"),
        ("box_weight_kg",),
        ("box_length_cm", "box_width_cm", "box_height_cm"),
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id_product", "name_product", "category", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["id_product", "name_product"]
    list_editable = ["is_active"]   # редагування прямо у списку
    inlines = [ProductLogisticsInline]
```

Відкрий `apps/customers/admin.py`:

```python
# apps/customers/admin.py
from django.contrib import admin
from .models import Customer, Store, StoreDeliveryAddress


class StoreDeliveryAddressInline(admin.TabularInline):
    """TabularInline = горизонтальне (таблиця) розташування."""
    model = StoreDeliveryAddress
    extra = 1


class StoreInline(admin.TabularInline):
    model = Store
    extra = 0
    show_change_link = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id_customer", "name_customer", "network_customer", "is_active"]
    list_filter = ["is_active", "network_customer"]
    search_fields = ["id_customer", "name_customer"]
    inlines = [StoreInline]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["id_store", "name_store", "customer", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["id_store", "name_store"]
    inlines = [StoreDeliveryAddressInline]
```

Відкрий `apps/cars/admin.py`:

```python
# apps/cars/admin.py
from django.contrib import admin
from .models import Car, CarSpecs, CarStatusLog, Trailer, Driver, RouteEvent, MonthlyCosts


class CarSpecsInline(admin.StackedInline):
    model = CarSpecs
    extra = 0


class TrailerInline(admin.StackedInline):
    model = Trailer
    extra = 0


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ["number_car", "name_car", "status_car", "default_tracking_mode", "is_active"]
    list_filter = ["status_car", "default_tracking_mode", "is_active"]
    search_fields = ["number_car", "name_car", "fuel_card_number"]
    inlines = [CarSpecsInline, TrailerInline]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["name_driver", "car", "phone", "drivers_license", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name_driver", "phone"]


@admin.register(CarStatusLog)
class CarStatusLogAdmin(admin.ModelAdmin):
    list_display = ["car", "status", "changed_at", "changed_by"]
    list_filter = ["status"]
    readonly_fields = ["changed_at"]


@admin.register(RouteEvent)
class RouteEventAdmin(admin.ModelAdmin):
    list_display = ["car", "driver", "event_type", "event_ts", "odometer_km"]
    list_filter = ["event_type", "tracking_mode"]
    search_fields = ["car__number_car", "waybill_number"]
    date_hierarchy = "event_ts"


@admin.register(MonthlyCosts)
class MonthlyCostsAdmin(admin.ModelAdmin):
    list_display = ["car", "month", "salary_uah", "depreciation_uah", "repair_actual_uah"]
    list_filter = ["month"]
```

---

## Крок 5.2 — Створення суперкористувача і перевірка Admin

```bash
python manage.py createsuperuser
```

Вводиш: username, email, password

```bash
python manage.py runserver
```

Відкрий: http://localhost:8000/admin
Увійди і перевір що всі моделі відображаються.

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 6 — СЕРІАЛІЗАТОРИ (JSON ↔ Model)
# ═══════════════════════════════════════════════════════════

## Крок 6.1 — Що таке серіалізатор

Серіалізатор — перетворює об'єкт моделі у JSON і навпаки.
Аналог: DTO у Java, або Marshmallow schema у Python.

```
Car object → CarSerializer → {"idCar": 1, "nameCar": "Sprinter"}
{"idCar": 1, "nameCar": "Sprinter"} → CarSerializer → Car object
```

---

## Крок 6.2 — Серіалізатори для products

Створи файл `apps/products/serializers.py`:

```python
# apps/products/serializers.py
from rest_framework import serializers
from .models import ProductCategory, Product, ProductLogistics


class ProductCategorySerializer(serializers.ModelSerializer):
    # SerializerMethodField — поле яке рахується методом get_<field>
    is_root = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = [
            "id", "name_category", "parent", "parent_name", "is_root",
        ]

    def get_is_root(self, obj) -> bool:
        """obj — це екземпляр ProductCategory."""
        return obj.parent is None

    def get_parent_name(self, obj) -> str | None:
        return obj.parent.name_category if obj.parent else None


class ProductLogisticsSerializer(serializers.ModelSerializer):
    # Поля що розраховуються (read_only — тільки для читання)
    unit_volume_cbm = serializers.SerializerMethodField()
    box_volume_cbm = serializers.SerializerMethodField()
    calculated_box_weight_kg = serializers.SerializerMethodField()

    class Meta:
        model = ProductLogistics
        fields = [
            "unit_weight_kg", "unit_length_cm", "unit_width_cm", "unit_height_cm",
            "units_per_box", "box_weight_kg",
            "box_length_cm", "box_width_cm", "box_height_cm",
            "unit_volume_cbm", "box_volume_cbm", "calculated_box_weight_kg",
        ]

    def get_unit_volume_cbm(self, obj):
        return obj.unit_volume_cbm

    def get_box_volume_cbm(self, obj):
        return obj.box_volume_cbm

    def get_calculated_box_weight_kg(self, obj):
        return obj.calculated_box_weight_kg


class ProductSerializer(serializers.ModelSerializer):
    # Вкладений серіалізатор (read_only — тільки для читання)
    category_name = serializers.CharField(
        source="category.name_category",
        read_only=True,
    )
    logistics = ProductLogisticsSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id_product", "name_product", "category", "category_name",
            "description", "is_active", "logistics",
            "created_at", "updated_at",
        ]
```

---

## Крок 6.3 — Серіалізатори для cars

Створи файл `apps/cars/serializers.py`:

```python
# apps/cars/serializers.py
from rest_framework import serializers
from .models import Car, CarSpecs, Trailer, Driver, RouteEvent, MonthlyCosts, CarStatusLog


class CarSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarSpecs
        exclude = ["id", "car"]


class TrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trailer
        exclude = ["id", "car"]


class CarSerializer(serializers.ModelSerializer):
    specs = CarSpecsSerializer(read_only=True)
    trailer = TrailerSerializer(read_only=True)
    # source — звідки брати значення
    driver_name = serializers.CharField(
        source="driver.name_driver",
        read_only=True,
    )

    class Meta:
        model = Car
        fields = [
            "id", "name_car", "number_car", "fuel_card_number",
            "amount_car", "default_tracking_mode",
            "status_car", "is_active",
            "specs", "trailer", "driver_name",
        ]


class DriverSerializer(serializers.ModelSerializer):
    car_number = serializers.CharField(
        source="car.number_car",
        read_only=True,
    )
    car_name = serializers.CharField(
        source="car.name_car",
        read_only=True,
    )

    class Meta:
        model = Driver
        fields = [
            "id", "name_driver", "phone", "drivers_license",
            "car", "car_number", "car_name", "is_active",
        ]


class RouteEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteEvent
        fields = "__all__"  # всі поля


class RouteEventCreateSerializer(serializers.ModelSerializer):
    """Серіалізатор для створення події — без id і created_at."""
    class Meta:
        model = RouteEvent
        exclude = ["id", "created_at"]


class MonthlyCostsSerializer(serializers.ModelSerializer):
    car_number = serializers.CharField(source="car.number_car", read_only=True)
    # SerializerMethodField для розрахункового поля
    repair_cost_uah = serializers.SerializerMethodField()
    total_cost_uah = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyCosts
        fields = [
            "id", "car", "car_number", "month",
            "salary_uah", "taxes_uah", "depreciation_uah",
            "repair_actual_uah", "repair_rate_uah_km",
            "other_costs_uah", "other_costs_comment",
            "repair_cost_uah", "total_cost_uah",
        ]

    def get_repair_cost_uah(self, obj):
        """Повертає фактичні або розраховані витрати на ремонт."""
        if obj.repair_actual_uah is not None:
            return float(obj.repair_actual_uah)
        # Потрібен загальний пробіг — передається через context
        total_km = self.context.get("total_km", 0)
        return float(obj.repair_rate_uah_km) * total_km

    def get_total_cost_uah(self, obj):
        repair = self.get_repair_cost_uah(obj)
        return float(
            obj.salary_uah + obj.taxes_uah + obj.depreciation_uah + obj.other_costs_uah
        ) + repair


class CarStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarStatusLog
        fields = ["id", "car", "status", "reason", "changed_at", "changed_by"]
        read_only_fields = ["changed_at"]
```

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 7 — VIEWS ТА URLS
# ═══════════════════════════════════════════════════════════

## Крок 7.1 — Що таке ViewSet

ViewSet — клас який автоматично створює CRUD endpoints.
Один ViewSet = GET list, GET detail, POST, PUT, PATCH, DELETE.

```
CarViewSet → автоматично:
GET    /api/cars/          → список авто
GET    /api/cars/1/        → одне авто
POST   /api/cars/          → створити
PUT    /api/cars/1/        → оновити повністю
PATCH  /api/cars/1/        → оновити частково
DELETE /api/cars/1/        → видалити
```

---

## Крок 7.2 — Views для cars

Відкрий `apps/cars/views.py`:

```python
# apps/cars/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Car, Driver, RouteEvent, MonthlyCosts, CarStatusLog
from .serializers import (
    CarSerializer, DriverSerializer, RouteEventSerializer,
    RouteEventCreateSerializer, MonthlyCostsSerializer, CarStatusLogSerializer,
)


class CarViewSet(viewsets.ModelViewSet):
    """
    CRUD для автопарку.
    Додатковий endpoint: /api/cars/{id}/status_logs/
    """
    queryset = Car.objects.select_related("specs", "trailer", "driver").all()
    serializer_class = CarSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number_car", "name_car", "fuel_card_number"]
    ordering_fields = ["number_car", "name_car", "status_car"]
    ordering = ["number_car"]

    def get_queryset(self):
        """Фільтрація по статусу і режиму трекінгу."""
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status_car=status_filter)
        mode = self.request.query_params.get("tracking_mode")
        if mode:
            qs = qs.filter(default_tracking_mode=mode)
        return qs

    # @action — додатковий endpoint на конкретне авто
    @action(detail=True, methods=["get"])
    def status_logs(self, request, pk=None):
        """GET /api/cars/{id}/status_logs/ — журнал статусів."""
        car = self.get_object()
        logs = car.status_logs.all()
        serializer = CarStatusLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """POST /api/cars/{id}/change_status/ — змінити статус."""
        car = self.get_object()
        new_status = request.data.get("status")
        reason = request.data.get("reason", "")

        if new_status not in [s.value for s in Car.Status]:
            return Response(
                {"error": "Невірний статус"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        car.status_car = new_status
        car.save()

        CarStatusLog.objects.create(
            car=car,
            status=new_status,
            reason=reason,
            changed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(CarSerializer(car).data)


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.select_related("car").all()
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name_driver", "phone"]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        GET /api/drivers/me/ — поточний водій.
        Поки повертає першого активного (до авторизації).
        """
        driver = Driver.objects.filter(is_active=True).first()
        if not driver:
            return Response({"error": "Водія не знайдено"}, status=404)
        return Response(DriverSerializer(driver).data)


class RouteEventViewSet(viewsets.ModelViewSet):
    queryset = RouteEvent.objects.select_related("car", "driver").all()
    filter_backends = [filters.OrderingFilter]
    ordering = ["event_ts"]

    def get_serializer_class(self):
        """Різний серіалізатор для читання і запису."""
        if self.action in ["create", "update", "partial_update"]:
            return RouteEventCreateSerializer
        return RouteEventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        car_id = self.request.query_params.get("car_id")
        date = self.request.query_params.get("date")

        if car_id:
            qs = qs.filter(car_id=car_id)
        if date == "today":
            from django.utils import timezone
            today = timezone.localdate()
            qs = qs.filter(event_ts__date=today)
        elif date:
            qs = qs.filter(event_ts__date=date)

        return qs

    @action(detail=False, methods=["get"])
    def last_odometer(self, request):
        """GET /api/route-events/last_odometer/?car_id=1"""
        car_id = request.query_params.get("car_id")
        if not car_id:
            return Response({"error": "car_id required"}, status=400)

        last = (
            RouteEvent.objects
            .filter(car_id=car_id, odometer_km__isnull=False)
            .order_by("-event_ts")
            .first()
        )
        return Response({"odometer_km": last.odometer_km if last else None})


class MonthlyCostsViewSet(viewsets.ModelViewSet):
    queryset = MonthlyCosts.objects.select_related("car").all()
    serializer_class = MonthlyCostsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        car_id = self.request.query_params.get("car_id")
        month = self.request.query_params.get("month")
        if car_id:
            qs = qs.filter(car_id=car_id)
        if month:
            qs = qs.filter(month__startswith=month)
        return qs
```

---

## Крок 7.3 — URLs для cars

Створи файл `apps/cars/urls.py`:

```python
# apps/cars/urls.py
from rest_framework.routers import DefaultRouter
from .views import CarViewSet, DriverViewSet, RouteEventViewSet, MonthlyCostsViewSet

# Router автоматично генерує всі URL для ViewSet
router = DefaultRouter()
router.register(r"cars", CarViewSet, basename="cars")
router.register(r"drivers", DriverViewSet, basename="drivers")
router.register(r"route-events", RouteEventViewSet, basename="route-events")
router.register(r"monthly-costs", MonthlyCostsViewSet, basename="monthly-costs")

urlpatterns = router.urls
```

---

## Крок 7.4 — Головний urls.py

Відкрий `config/urls.py`:

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Всі API endpoints починаються з /api/
    path("api/", include("apps.cars.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.waybills.urls")),
    path("api/", include("apps.logistics.urls")),
]
```

---

## Крок 7.5 — Перевірка API

```bash
python manage.py runserver
```

Відкрий у браузері:
- http://localhost:8000/api/cars/ → список авто (порожній)
- http://localhost:8000/api/drivers/ → список водіїв
- http://localhost:8000/admin/ → Django Admin

Або через PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/cars/" -Method GET
```

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 8 — VIEWS ТА URLS ДЛЯ PRODUCTS, CUSTOMERS, WAYBILLS
# ═══════════════════════════════════════════════════════════

> `products` уже має серіалізатори (Крок 6.2) — тут тільки views/urls.
> `customers` і `waybills` не мали серіалізаторів взагалі — пишемо все
> з нуля, за тим самим патерном, що й `cars` у Фазі 6-7.

## Крок 8.1 — Views та URLs для products

Відкрий `apps/products/views.py`:

```python
# apps/products/views.py
from rest_framework import filters, viewsets

from .models import Product, ProductCategory
from .serializers import ProductCategorySerializer, ProductSerializer


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """CRUD для категорій товарів (з ієрархією parent/children)."""

    queryset = ProductCategory.objects.select_related("parent").all()
    serializer_class = ProductCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name_category"]
    ordering_fields = ["name_category"]
    ordering = ["name_category"]

    def get_queryset(self):
        """?root=true — тільки кореневі категорії (без parent)."""
        qs = super().get_queryset()
        if self.request.query_params.get("root") == "true":
            qs = qs.filter(parent__isnull=True)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD для товарів. Логістика — вкладено (read_only) через ProductSerializer."""

    queryset = Product.objects.select_related("category", "logistics").all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["id_product", "name_product"]
    ordering_fields = ["name_product", "id_product"]
    ordering = ["name_product"]

    def get_queryset(self):
        """Фільтрація по категорії і активності."""
        qs = super().get_queryset()
        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs
```

Створи `apps/products/urls.py`:

```python
# apps/products/urls.py
from rest_framework.routers import DefaultRouter

from .views import ProductCategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"product-categories", ProductCategoryViewSet, basename="product-categories")
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = router.urls
```

---

## Крок 8.2 — Серіалізатори для customers

Створи файл `apps/customers/serializers.py`:

```python
# apps/customers/serializers.py
from rest_framework import serializers

from .models import Customer, Store, StoreDeliveryAddress


class StoreDeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreDeliveryAddress
        fields = ["id", "store", "delivery_address", "is_primary", "notes", "created_at"]
        read_only_fields = ["created_at"]


class StoreSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name_customer",
        read_only=True,
    )
    # related_name="delivery_addresses" на StoreDeliveryAddress.store — DRF сам робить JOIN
    delivery_addresses = StoreDeliveryAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Store
        fields = [
            "id_store", "customer", "customer_name", "name_store",
            "store_address", "is_active", "delivery_addresses", "updated_at",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    # SerializerMethodField — скільки магазинів у клієнта (для списку клієнтів)
    stores_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id_customer", "name_customer", "network_customer",
            "is_active", "stores_count", "created_at", "updated_at",
        ]

    def get_stores_count(self, obj) -> int:
        return obj.stores.count()
```

---

## Крок 8.3 — Views та URLs для customers

Відкрий `apps/customers/views.py`:

```python
# apps/customers/views.py
from rest_framework import filters, viewsets

from .models import Customer, Store, StoreDeliveryAddress
from .serializers import CustomerSerializer, StoreDeliveryAddressSerializer, StoreSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.prefetch_related("stores").all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name_customer", "network_customer"]
    ordering_fields = ["name_customer"]
    ordering = ["name_customer"]

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.select_related("customer").prefetch_related("delivery_addresses").all()
    serializer_class = StoreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name_store", "store_address"]

    def get_queryset(self):
        """?customer_id=... — магазини конкретного клієнта."""
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs


class StoreDeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = StoreDeliveryAddress.objects.select_related("store").all()
    serializer_class = StoreDeliveryAddressSerializer

    def get_queryset(self):
        """?store_id=... — адреси конкретного магазину."""
        qs = super().get_queryset()
        store_id = self.request.query_params.get("store_id")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs
```

Створи `apps/customers/urls.py`:

```python
# apps/customers/urls.py
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, StoreDeliveryAddressViewSet, StoreViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"stores", StoreViewSet, basename="stores")
router.register(
    r"store-delivery-addresses", StoreDeliveryAddressViewSet, basename="store-delivery-addresses"
)

urlpatterns = router.urls
```

---

## Крок 8.4 — Серіалізатори для waybills

Створи файл `apps/waybills/serializers.py`:

```python
# apps/waybills/serializers.py
from rest_framework import serializers

from .models import WaybillRecord


class WaybillRecordSerializer(serializers.ModelSerializer):
    # Property з моделі (quantity < 0) — треба задекларувати явно,
    # ModelSerializer сам бачить тільки поля БД, не @property.
    is_return = serializers.BooleanField(read_only=True)

    class Meta:
        model = WaybillRecord
        fields = [
            "id", "legal_entity", "waybill_number", "waybill_date", "line_position",
            "customer", "customer_name", "store", "product", "product_name",
            "quantity", "price_uah", "total_uah", "comment",
            "total_weight_kg", "total_volume_cbm", "volumetric_weight_kg",
            "delivery_channel", "is_return",
            "imported_at", "import_batch_id",
        ]
        read_only_fields = ["imported_at"]
```

---

## Крок 8.5 — Views та URLs для waybills

Відкрий `apps/waybills/views.py`:

```python
# apps/waybills/views.py
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import WaybillRecord
from .serializers import WaybillRecordSerializer


class WaybillRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD для реєстру накладних (рядки, імпортовані з 1С).
    Додатковий endpoint: /api/waybill-records/{id}/assign_channel/
    """

    queryset = WaybillRecord.objects.select_related("customer", "store", "product").all()
    serializer_class = WaybillRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["waybill_number", "customer_name", "product_name"]
    ordering_fields = ["waybill_date", "waybill_number", "total_uah"]
    ordering = ["-waybill_date", "waybill_number"]

    def get_queryset(self):
        """Фільтри: клієнт, товар, юрособа, канал доставки, діапазон дат."""
        qs = super().get_queryset()
        params = self.request.query_params

        customer_id = params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        product_id = params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)

        legal_entity = params.get("legal_entity")
        if legal_entity:
            qs = qs.filter(legal_entity=legal_entity)

        delivery_channel = params.get("delivery_channel")
        if delivery_channel:
            qs = qs.filter(delivery_channel=delivery_channel)

        date_from = params.get("date_from")
        if date_from:
            qs = qs.filter(waybill_date__gte=date_from)
        date_to = params.get("date_to")
        if date_to:
            qs = qs.filter(waybill_date__lte=date_to)

        return qs

    @action(detail=False, methods=["get"])
    def unassigned(self, request):
        """GET /api/waybill-records/unassigned/ — рядки без каналу доставки."""
        qs = self.get_queryset().filter(delivery_channel__isnull=True)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def assign_channel(self, request, pk=None):
        """
        POST /api/waybill-records/{id}/assign_channel/ — {"delivery_channel": "own"}
        Канал можна призначити лише один раз — ексклюзивність каналів
        це критична бізнес-вимога (див. task_description/STATE.md).
        """
        record = self.get_object()
        channel = request.data.get("delivery_channel")

        if channel not in [c.value for c in WaybillRecord.DeliveryChannel]:
            return Response({"error": "Невірний канал доставки"}, status=400)
        if record.delivery_channel:
            return Response({"error": "Канал доставки вже призначено"}, status=400)

        record.delivery_channel = channel
        record.save()
        return Response(WaybillRecordSerializer(record).data)
```

Створи `apps/waybills/urls.py`:

```python
# apps/waybills/urls.py
from rest_framework.routers import DefaultRouter

from .views import WaybillRecordViewSet

router = DefaultRouter()
router.register(r"waybill-records", WaybillRecordViewSet, basename="waybill-records")

urlpatterns = router.urls
```

---

## Крок 8.6 — Головний urls.py

Відкрий `config/urls.py` і розкоментуй `products`/`customers`/`waybills`
(`logistics` лишається закоментованим — моделі для нього ще не написані,
див. `task_description/STATE.md`):

```python
# config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.cars.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.waybills.urls")),
    # path("api/", include("apps.logistics.urls")),  # моделі ще не написані
]
```

---

## Крок 8.7 — Перевірка

```bash
python manage.py check
python manage.py runserver
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/products/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/customers/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/waybill-records/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/waybill-records/unassigned/" -Method GET
```

Усі три мають повернути `200` з порожнім `results: []` (БД ще без даних).

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 9 — РОЛІ ТА ПРАВА ДОСТУПУ ДЛЯ АВТОПАРКУ
# ═══════════════════════════════════════════════════════════

> Навіщо: `apps/cars` (Car/Driver/RouteEvent/MonthlyCosts) — єдиний
> застосунок із повним CRUD, вже підключеним до реального фронтенду
> (`vehicle_cost_tracker`). Але жоден endpoint зараз не перевіряє ні
> авторизацію, ні роль — `REST_FRAMEWORK` у `settings.py` не має
> `DEFAULT_PERMISSION_CLASSES`, тому DRF мовчки підставляє `AllowAny`:
> будь-хто без логіну може створити/видалити авто чи чужу подію
> маршруту через `POST/DELETE /api/cars/...`. Ця фаза — мінімальний
> захист перед тим, як логіст отримає UI для додавання авто (Фаза 10)
> і водій — реальний QR-сканер (`CODING_GUIDE.md`, Фаза 15).

## Крок 9.1 — IsAuthenticated за замовчуванням

Відкрий `config/settings.py`, онови `REST_FRAMEWORK`:

```python
# config/settings.py
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # Без логіну — явна відмова замість тихого доступу до всього API.
    # На практиці DRF тут віддає 403, не 401 — бо SessionAuthentication
    # (перший автентифікатор за замовчуванням) не має WWW-Authenticate
    # челенджа, і DRF занижує 401 → 403 (деталі й перевірка — Крок 15.6).
    # Аутентифікація (SessionAuthentication) вже стандартна в DRF,
    # окремо налаштовувати не треба — сесія+CSRF з Фази 4.5 і так працює.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

`GET /api/auth/csrf/`, `/api/auth/register/`, `/api/auth/login/` — самі
залишаються доступними без логіну (`apps/accounts/views.py` явно
задає їм `permission_classes = [AllowAny]`, перевір і onNeeded додай).

---

## Крок 9.2 — Тільки logist/manager/head можуть змінювати автопарк

`apps/accounts/permissions.py` вже має `IsManagerOrHead` (Крок 4.5.8) —
але його ніде не підключено. Водій має бачити список авто (свою
картку), але не створювати/видаляти авто чи інших водіїв. Онови
`apps/cars/views.py`:

```python
# apps/cars/views.py
from apps.accounts.permissions import IsManagerOrHead
from rest_framework.permissions import IsAuthenticated

WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


class CarViewSet(viewsets.ModelViewSet):
    ...  # queryset, serializer_class, filter_backends — без змін

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки logist/manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    # status_logs/change_status лишаються — але change_status теж
    # де-факто "запис", тому явно захисти й цей @action:
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsManagerOrHead])
    def change_status(self, request, pk=None):
        ...  # тіло без змін


class DriverViewSet(viewsets.ModelViewSet):
    ...  # queryset, serializer_class, filter_backends — без змін

    def get_permissions(self):
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]
```

`IsManagerOrHead.allowed_roles = ('manager', 'head')` — зверни увагу,
`logist` там НЕМАЄ, хоча в задачі йдеться про "логіста". Якщо логіст
має право додавати авто (а по задачі — має), онови сам permission-клас
у `apps/accounts/permissions.py`:

```python
# apps/accounts/permissions.py
class IsLogistOrAbove(HasRole):
    allowed_roles = ('logist', 'manager', 'head')
```

і використай `IsLogistOrAbove` замість `IsManagerOrHead` у
`get_permissions()` вище (обидва класи можна лишити — `IsManagerOrHead`
ще знадобиться там, де саме логіст не повинен мати доступу, наприклад
Крок 18 "Що далі" — підтвердження реєстрацій).

---

## Крок 9.3 — Реальний GET /api/drivers/me/

Зараз `me` повертає першого-ліпшого активного водія в БД незалежно від
того, хто залогинений — це заглушка з Фази 7, яку треба замінити тепер,
коли є `Profile.driver`:

```python
# apps/cars/views.py
class DriverViewSet(viewsets.ModelViewSet):
    ...

    @action(detail=False, methods=["get"])
    def me(self, request):
        """GET /api/drivers/me/ — водій поточної сесії (Profile.driver)."""
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.driver_id:
            return Response(
                {"error": "Профіль не прив'язаний до картки водія — зверніться до диспетчера"},
                status=404,
            )
        return Response(DriverSerializer(profile.driver).data)
```

Лінк `Profile.driver` і досі ставиться вручну в Django Admin (Крок
4.5.8) — це нормально, це організаційний крок диспетчера/адміна при
онбордингу нового водія, не те, що можна автоматизувати без ризику
прив'язати не того користувача не до того авто.

---

## Крок 9.4 — Водій бачить і пише тільки свої події маршруту

`RouteEventViewSet` зараз віддає й приймає ВСІ події без обмежень —
будь-хто залогинений може прочитати чи змінити чужий маршрут. Виправ:

```python
# apps/cars/views.py
class RouteEventViewSet(viewsets.ModelViewSet):
    ...

    def get_queryset(self):
        qs = super().get_queryset()
        profile = getattr(self.request.user, "profile", None)

        # Водій бачить лише свої події; logist/manager/head — усі
        if profile and profile.role == "driver":
            qs = qs.filter(driver_id=profile.driver_id)

        car_id = self.request.query_params.get("car_id")
        date = self.request.query_params.get("date")
        if car_id:
            qs = qs.filter(car__id=car_id)
        if date == "today":
            from django.utils import timezone
            qs = qs.filter(event_ts__date=timezone.localdate())
        elif date:
            qs = qs.filter(event_ts__date=date)
        return qs

    def perform_create(self, serializer):
        """Водій не може підписати подію на іншого водія — driver форсується з сесії."""
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.role == "driver":
            serializer.save(driver_id=profile.driver_id, car_id=profile.driver.car_id)
        else:
            serializer.save()
```

Без цього водій, знаючи чужий `driver`/`car` id, міг би через DevTools
відправити `POST /api/route-events/` з чужими id і підмінити чиюсь
статистику пробігу/пального — `perform_create` це закриває на бекенді
(єдине надійне місце, фронтенд-перевірку завжди можна обійти).

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 10 — CRUD АВТОПАРКУ ДЛЯ ЛОГІСТА
# ═══════════════════════════════════════════════════════════

> Навіщо: `CarViewSet`/`DriverViewSet` вже повний `ModelViewSet` —
> API для створення/редагування авто і водіїв технічно вже існує
> (`POST/PATCH/DELETE /api/cars/`, `/api/drivers/`). Чого бракує — це
> `specs`/`trailer` (VIN, вага, причіп) записуються лише окремо через
> Django Admin, бо в `CarSerializer` вони `read_only=True` (Крок 6.3).
> Логісту на фронтенді (`CODING_GUIDE.md`, Фаза 16) потрібна ОДНА форма
> "додати авто", яка одразу приймає характеристики й причіп.

## Крок 10.1 — specs/trailer стають записуваними (nested write)

DRF за замовчуванням не вміє писати вкладені серіалізатори — треба
самому перевизначити `create()`/`update()`. Онови `apps/cars/serializers.py`:

```python
# apps/cars/serializers.py
class CarSerializer(serializers.ModelSerializer):
    specs = CarSpecsSerializer(required=False)
    trailer = TrailerSerializer(required=False)
    driver_name = serializers.CharField(source="driver.name_driver", read_only=True)

    class Meta:
        model = Car
        fields = [
            "id", "name_car", "number_car", "fuel_card_number",
            "amount_car", "default_tracking_mode",
            "status_car", "is_active",
            "specs", "trailer", "driver_name",
        ]

    def create(self, validated_data):
        specs_data = validated_data.pop("specs", None)
        trailer_data = validated_data.pop("trailer", None)
        car = Car.objects.create(**validated_data)
        if specs_data:
            CarSpecs.objects.create(car=car, **specs_data)
        if trailer_data:
            Trailer.objects.create(car=car, **trailer_data)
        return car

    def update(self, instance, validated_data):
        specs_data = validated_data.pop("specs", None)
        trailer_data = validated_data.pop("trailer", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if specs_data is not None:
            CarSpecs.objects.update_or_create(car=instance, defaults=specs_data)
        if trailer_data is not None:
            Trailer.objects.update_or_create(car=instance, defaults=trailer_data)
        return instance
```

`specs`/`trailer` лишаються `required=False` — логіст може спершу
завести авто без характеристик і дозаповнити пізніше тим самим
`PATCH /api/cars/{id}/`.

---

## Крок 10.2 — Створення водія й закріплення за авто

`DriverViewSet` уже приймає `car` як звичайне записуване поле —
окремих змін не треба, тільки права з Кроку 9.2. Єдине бізнес-правило,
яке варто перевірити: `Driver.car` — `OneToOneField`, тобто на рівні
БД одне авто не може мати двох активних водіїв одночасно (спроба
призначити зайняте авто впаде з `IntegrityError`/400 — DRF поверне це
як validation error автоматично, додаткового коду не треба).

---

## Крок 10.3 — Перевірка

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/cars/" -Method POST `
  -WebSession $s -ContentType "application/json" `
  -Body (@{
    name_car = "Sprinter"; number_car = "АА1234ВВ"
    amount_car = "15000.00"; default_tracking_mode = "daily"
    status_car = "active"; is_active = $true
    specs = @{ vin_code = "WD..."; has_tail_lift = $true; has_trailer = $false }
  } | ConvertTo-Json -Depth 5)
```

Відповідь має містити `"specs": {"vin_code": "WD...", ...}` одразу в
тілі створеного авто — без окремого запиту в Django Admin.

---

## Крок 10.4 — Примітка: сканування накладних і бекенд

Функціонал "водій сканує накладну" НЕ потребує нової моделі чи
endpoint'у на бекенді. `RouteEvent` (Фаза 3.7) вже має поля
`waybill_number`/`waybill_date`/`customer_name` саме для типу події
`delivery` — фронтенд (`parseQR.ts`, `CODING_GUIDE.md` Фаза 15) лише
розпізнає QR-код камерою й підставляє готові значення в ту саму форму
`EventForm`, яка вже відправляє `POST /api/route-events/` (Фаза 6-7,
захищено Кроком 9.4 вище). Це навмисно — задача сканера полягає в
тому, щоб водій не набирав номер накладної вручну, а не в тому, щоб
з'явився новий тип даних.

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 11 — APPS/LOGISTICS: НАЙМАНИЙ ТРАНСПОРТ І СЛУЖБИ ДОСТАВКИ
# ═══════════════════════════════════════════════════════════

> Навіщо: `01_PROJECT_OVERVIEW.md` §5.3-5.4 описує два канали доставки,
> для яких досі немає моделей — **найманий транспорт** (вносить логіст)
> і **служби доставки** (вносить менеджер-операціоніст). Місячні
> витрати власного автопарку (§5.2) уже реалізовані як `MonthlyCosts`
> у `apps/cars` (Крок 3.5) — це не сюди. `apps/logistics` зареєстрований
> у `INSTALLED_APPS` (Крок 2.4), але моделі й views для нього ще не
> написані — `config/urls.py` містить закоментований рядок саме тому.
> `WaybillRecord.delivery_channel` (Крок 3.6) уже має варіанти
> `own`/`hired`/`carrier` — цій фазі лишається тільки прив'язати накладні
> до конкретного рейсу/відправлення й виставити канал, за зразком
> `assign_channel` з Кроку 8.5.

## Крок 15.1 — Моделі HiredTransportTrip / CarrierShipment

Відкрий `apps/logistics/models.py`:

```python
# apps/logistics/models.py
from django.db import models


class HiredTransportTrip(models.Model):
    """
    Single trip by hired (non-fleet) transport (§5.3 01_PROJECT_OVERVIEW.md).
    Entered by the logist, one row per trip — cost is actual, from the carrier.
    """

    car_number = models.CharField(
        max_length=20,
        verbose_name="Номер авто (найманий)",
    )
    route_name = models.CharField(
        max_length=255,
        verbose_name="Назва маршруту",
    )
    trip_date = models.DateField(verbose_name="Дата рейсу")
    pallets_count = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Кількість палет",
    )
    cost_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Вартість доставки (грн)",
    )
    comment = models.TextField(blank=True, default="", verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hired_transport_trips"
        verbose_name = "Рейс найманого транспорту"
        verbose_name_plural = "Рейси найманого транспорту"
        ordering = ["-trip_date"]

    def __str__(self):
        return f"{self.car_number} — {self.route_name} ({self.trip_date})"


class HiredTripWaybill(models.Model):
    """
    Waybill attached to a hired-transport trip.
    waybill_number is unique — a waybill can belong to only one channel/trip.
    """

    trip = models.ForeignKey(
        HiredTransportTrip,
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name="Рейс",
    )
    waybill_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер накладної",
    )

    class Meta:
        db_table = "hired_trip_waybills"
        verbose_name = "Накладна найманого рейсу"
        verbose_name_plural = "Накладні найманого рейсу"

    def __str__(self):
        return f"{self.trip} — {self.waybill_number}"


class CarrierShipment(models.Model):
    """
    Shipment handed off to a delivery service (§5.4 01_PROJECT_OVERVIEW.md).
    Entered by the manager when assigning waybills to НП / Міст Експрес / etc.
    """

    class Carrier(models.TextChoices):
        NOVA_POSHTA = "nova_poshta", "Нова Пошта"
        MIST_EXPRESS = "mist_express", "Міст Експрес"
        OTHER = "other", "Інша служба"

    carrier = models.CharField(
        max_length=20,
        choices=Carrier.choices,
        verbose_name="Служба доставки",
    )
    ttn = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="ТТН",
    )
    shipment_date = models.DateField(verbose_name="Дата відправки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "carrier_shipments"
        verbose_name = "Відправлення служби доставки"
        verbose_name_plural = "Відправлення служб доставки"
        ordering = ["-shipment_date"]

    def __str__(self):
        return f"{self.ttn} ({self.get_carrier_display()})"


class CarrierShipmentWaybill(models.Model):
    """
    Waybill included in a carrier shipment. One ТТН can cover several waybills.
    """

    shipment = models.ForeignKey(
        CarrierShipment,
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name="Відправлення",
    )
    waybill_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер накладної",
    )

    class Meta:
        db_table = "carrier_shipment_waybills"
        verbose_name = "Накладна відправлення"
        verbose_name_plural = "Накладні відправлення"

    def __str__(self):
        return f"{self.shipment.ttn} — {self.waybill_number}"


class CarrierCost(models.Model):
    """
    Row from the weekly carrier cost registry import, matched to a
    CarrierShipment by ttn (§5.4). shipment stays null until a matching
    CarrierShipment.ttn is found — registries can arrive before or after
    the shipment is registered.
    """

    shipment = models.ForeignKey(
        CarrierShipment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="costs",
        verbose_name="Відправлення",
    )
    ttn = models.CharField(max_length=50, verbose_name="ТТН")
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Вага відправлення (кг)",
    )
    cost_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Вартість доставки (грн)",
    )
    cost_date = models.DateField(verbose_name="Дата")
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "carrier_costs"
        verbose_name = "Витрата служби доставки"
        verbose_name_plural = "Витрати служб доставки"
        ordering = ["-cost_date"]
        indexes = [models.Index(fields=["ttn"])]

    def __str__(self):
        return f"{self.ttn} — {self.cost_uah} грн"
```

`HiredTripWaybill.waybill_number` і `CarrierShipmentWaybill.waybill_number` —
`unique=True` навмисно: одна накладна не може одночасно бути в двох рейсах
чи відправленнях, це той самий принцип ексклюзивності каналів, що й
`WaybillRecord.delivery_channel` (Крок 3.6).

---

## Крок 15.2 — Міграції

```bash
python manage.py makemigrations logistics
python manage.py migrate
```

---

## Крок 15.3 — Admin

Відкрий `apps/logistics/admin.py`:

```python
# apps/logistics/admin.py
from django.contrib import admin

from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)


class HiredTripWaybillInline(admin.TabularInline):
    model = HiredTripWaybill
    extra = 0


@admin.register(HiredTransportTrip)
class HiredTransportTripAdmin(admin.ModelAdmin):
    list_display = ["car_number", "route_name", "trip_date", "cost_uah"]
    list_filter = ["trip_date"]
    search_fields = ["car_number", "route_name"]
    inlines = [HiredTripWaybillInline]


class CarrierShipmentWaybillInline(admin.TabularInline):
    model = CarrierShipmentWaybill
    extra = 0


@admin.register(CarrierShipment)
class CarrierShipmentAdmin(admin.ModelAdmin):
    list_display = ["ttn", "carrier", "shipment_date"]
    list_filter = ["carrier", "shipment_date"]
    search_fields = ["ttn"]
    inlines = [CarrierShipmentWaybillInline]


@admin.register(CarrierCost)
class CarrierCostAdmin(admin.ModelAdmin):
    list_display = ["ttn", "shipment", "weight_kg", "cost_uah", "cost_date"]
    list_filter = ["cost_date"]
    search_fields = ["ttn"]
```

---

## Крок 15.4 — Серіалізатори

Створи `apps/logistics/serializers.py`:

```python
# apps/logistics/serializers.py
from rest_framework import serializers

from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)


class HiredTripWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiredTripWaybill
        fields = ["id", "waybill_number"]


class HiredTransportTripSerializer(serializers.ModelSerializer):
    waybills = HiredTripWaybillSerializer(many=True, read_only=True)

    class Meta:
        model = HiredTransportTrip
        fields = [
            "id", "car_number", "route_name", "trip_date",
            "pallets_count", "cost_uah", "comment",
            "waybills", "created_at",
        ]
        read_only_fields = ["created_at"]


class CarrierShipmentWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierShipmentWaybill
        fields = ["id", "waybill_number"]


class CarrierShipmentSerializer(serializers.ModelSerializer):
    waybills = CarrierShipmentWaybillSerializer(many=True, read_only=True)

    class Meta:
        model = CarrierShipment
        fields = ["id", "carrier", "ttn", "shipment_date", "waybills", "created_at"]
        read_only_fields = ["created_at"]


class CarrierCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierCost
        fields = ["id", "shipment", "ttn", "weight_kg", "cost_uah", "cost_date", "imported_at"]
        # shipment виставляється автоматично матчингом по ttn — див. Крок 15.5
        read_only_fields = ["shipment", "imported_at"]
```

---

## Крок 15.5 — Views та URLs

Відкрий `apps/logistics/views.py`. Права — за ролями з `01_PROJECT_OVERVIEW.md`
§2: найманий транспорт вносить **логіст** (`IsLogistOrAbove`, Крок 9.2),
служби доставки — **менеджер-операціоніст** (`IsManagerOrHead`, Крок 4.5.8):

```python
# apps/logistics/views.py
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsLogistOrAbove, IsManagerOrHead
from apps.waybills.models import WaybillRecord

from .models import (
    CarrierCost,
    CarrierShipment,
    CarrierShipmentWaybill,
    HiredTransportTrip,
    HiredTripWaybill,
)
from .serializers import (
    CarrierCostSerializer,
    CarrierShipmentSerializer,
    HiredTransportTripSerializer,
)

WRITE_ACTIONS = ["create", "update", "partial_update", "destroy"]


class HiredTransportTripViewSet(viewsets.ModelViewSet):
    """
    CRUD для рейсів найманого транспорту (§5.3).
    Додатковий endpoint: /api/hired-transport-trips/{id}/attach_waybill/
    """

    queryset = HiredTransportTrip.objects.prefetch_related("waybills").all()
    serializer_class = HiredTransportTripSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["car_number", "route_name"]
    ordering_fields = ["trip_date", "cost_uah"]
    ordering = ["-trip_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки logist/manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsLogistOrAbove()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsLogistOrAbove])
    def attach_waybill(self, request, pk=None):
        """
        POST /api/hired-transport-trips/{id}/attach_waybill/ — {"waybill_number": "..."}
        Прив'язує накладну до рейсу й виставляє WaybillRecord.delivery_channel="hired".
        Ексклюзивність каналів — та сама вимога, що й у Кроці 8.5 (assign_channel).
        """
        trip = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response({"error": "waybill_number обов'язковий"}, status=400)

        if HiredTripWaybill.objects.filter(waybill_number=waybill_number).exists():
            return Response(
                {"error": "Накладна вже прив'язана до рейсу найманого транспорту"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        already_other_channel = records.exclude(
            delivery_channel__in=[None, WaybillRecord.DeliveryChannel.HIRED]
        ).exists()
        if already_other_channel:
            return Response({"error": "Накладна вже призначена іншому каналу доставки"}, status=400)

        HiredTripWaybill.objects.create(trip=trip, waybill_number=waybill_number)
        records.update(delivery_channel=WaybillRecord.DeliveryChannel.HIRED)

        return Response(HiredTransportTripSerializer(trip).data)


class CarrierShipmentViewSet(viewsets.ModelViewSet):
    """
    CRUD для відправлень служб доставки (§5.4).
    Додатковий endpoint: /api/carrier-shipments/{id}/attach_waybill/
    """

    queryset = CarrierShipment.objects.prefetch_related("waybills", "costs").all()
    serializer_class = CarrierShipmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ttn"]
    ordering_fields = ["shipment_date"]
    ordering = ["-shipment_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsManagerOrHead])
    def attach_waybill(self, request, pk=None):
        """
        POST /api/carrier-shipments/{id}/attach_waybill/ — {"waybill_number": "..."}
        Аналог attach_waybill у HiredTransportTripViewSet, тільки канал "carrier".
        """
        shipment = self.get_object()
        waybill_number = request.data.get("waybill_number")
        if not waybill_number:
            return Response({"error": "waybill_number обов'язковий"}, status=400)

        if CarrierShipmentWaybill.objects.filter(waybill_number=waybill_number).exists():
            return Response(
                {"error": "Накладна вже прив'язана до відправлення служби доставки"},
                status=400,
            )

        records = WaybillRecord.objects.filter(waybill_number=waybill_number)
        already_other_channel = records.exclude(
            delivery_channel__in=[None, WaybillRecord.DeliveryChannel.CARRIER]
        ).exists()
        if already_other_channel:
            return Response({"error": "Накладна вже призначена іншому каналу доставки"}, status=400)

        CarrierShipmentWaybill.objects.create(shipment=shipment, waybill_number=waybill_number)
        records.update(delivery_channel=WaybillRecord.DeliveryChannel.CARRIER)

        return Response(CarrierShipmentSerializer(shipment).data)


class CarrierCostViewSet(viewsets.ModelViewSet):
    """Реєстр витрат від служб доставки (щотижневий імпорт, матчинг по ТТН)."""

    queryset = CarrierCost.objects.select_related("shipment").all()
    serializer_class = CarrierCostSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["cost_date"]
    ordering = ["-cost_date"]

    def get_permissions(self):
        """Читання — будь-який залогинений; запис — тільки manager/head."""
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsManagerOrHead()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Матчинг по ТТН — якщо відправлення вже зареєстроване, лінкуємо автоматично."""
        ttn = serializer.validated_data.get("ttn")
        shipment = CarrierShipment.objects.filter(ttn=ttn).first()
        serializer.save(shipment=shipment)
```

Створи `apps/logistics/urls.py`:

```python
# apps/logistics/urls.py
from rest_framework.routers import DefaultRouter

from .views import CarrierCostViewSet, CarrierShipmentViewSet, HiredTransportTripViewSet

router = DefaultRouter()
router.register(r"hired-transport-trips", HiredTransportTripViewSet, basename="hired-transport-trips")
router.register(r"carrier-shipments", CarrierShipmentViewSet, basename="carrier-shipments")
router.register(r"carrier-costs", CarrierCostViewSet, basename="carrier-costs")

urlpatterns = router.urls
```

Відкрий `config/urls.py` і розкоментуй `logistics`:

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.cars.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.waybills.urls")),
    path("api/", include("apps.logistics.urls")),
]
```

---

## Крок 15.6 — Перевірка

```bash
python manage.py check
python manage.py runserver
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/hired-transport-trips/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/carrier-shipments/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/carrier-costs/" -Method GET
```

Усі три мають повернути `403` без авторизації (не `401`, попри коментар
у Кроці 9.1 — DRF-деталь: `DEFAULT_AUTHENTICATION_CLASSES` тут за
замовчуванням `[SessionAuthentication, BasicAuthentication]`, і DRF
бере `WWW-Authenticate`-заголовок для 401-відповіді з ПЕРШОГО
автентифікатора в списку (`APIView.handle_exception`); `SessionAuthentication.authenticate_header()`
завжди повертає `None` — сесійна автентифікація не має челенджа на
кшталт Basic-auth — тому DRF свідомо занижує `401 → 403`
(`exc.status_code = status.HTTP_403_FORBIDDEN`), і так для будь-якого
ендпоінта в цьому проєкті, не лише логістики. Перевірено 19.08.2026:
`/api/cars/` (Фаза 9, давно робочий) віддає той самий `403`) і `200`
з порожнім `results: []` після логіну.

> **Аналітика (§8, `apps/analytics`)** свідомо лишається поза цією фазою —
> це запити `annotate()`/`Sum()` над уже наявними даними (`RouteEvent`,
> `MonthlyCosts`, `WaybillRecord`, тепер і `HiredTransportTrip`/`CarrierCost`),
> тому має сенс писати її вже під конкретні дашборди фронтенду, коли
> в БД накопичиться реальна історія — див. Крок 14 нижче.

---

# ═══════════════════════════════════════════════════════════
# ЩО ДАЛІ
# ═══════════════════════════════════════════════════════════

## Наступні кроки:

### Крок 11 — Завантаження реальних даних із 1С (management command)
### Крок 12 — Docker + розгортання на Raspberry Pi
### Крок 13 — GitHub Actions CI/CD
### Крок 14 — Підключення products/customers/waybills до реального React
Cars/Drivers/RouteEvents (Фази 6-10) вже підключені й живі в проді —
цей крок лишається тільки для products/customers/waybill-records
(Фаза 8), коли з'явиться відповідний UI на фронтенді
(`VITE_USE_MOCK=false`).

---

## Корисні Django команди:

```bash
python manage.py runserver          # запуск dev сервера
python manage.py makemigrations     # генерація міграцій
python manage.py migrate            # застосування міграцій
python manage.py createsuperuser    # створення адміна
python manage.py shell              # Python консоль з Django
python manage.py dbshell            # консоль PostgreSQL
python manage.py check              # перевірка конфігурації

# У shell можна тестувати моделі:
# >>> from apps.cars.models import Car
# >>> Car.objects.all()
# >>> Car.objects.create(name_car="Sprinter", number_car="АА1234ВВ")
```

## Корисні концепції Python/Django:

```python
# QuerySet — ледачий запит до БД (не виконується поки не потрібно)
cars = Car.objects.all()          # ще не запит до БД
cars = Car.objects.filter(...)    # ще не запит
list(cars)                        # ось тут виконується SQL

# select_related — JOIN у одному запиті (уникаємо N+1 проблему)
# Без: 100 авто = 100 запитів до drivers
# З:   100 авто = 1 запит з JOIN
Car.objects.select_related("driver", "specs").all()

# F() — посилання на поле у БД (для порівнянь і обчислень)
from django.db.models import F
Car.objects.filter(amount_car__gt=F("monthly_costs__depreciation_uah"))

# annotate() — додаємо обчислюване поле до QuerySet
from django.db.models import Count, Sum
Car.objects.annotate(events_count=Count("route_events"))
```
