# CLAUDE.md — Швидкий довідник для AI Агентів (v4)

Контекст проекту для AI-агентів. Перед роботою обов'язково читай `AGENTS_GLOBAL.md`.

> **Оновлено 2026-09-06.** Попередня версія (v3) описувала цей
> репозиторій (бекенд `vehicle_tracker_api`) через React/Vite/Tailwind
> стек — це помилково скопійований опис фронтенд-репозиторію
> (`vehicle_cost_tracker`). Нижче — реальний стек цього репозиторію.

---

## Проект

**Vehicle Cost Tracker** — Django REST API для обліку транспортних
витрат (автопарк, водії, накладні, найманий транспорт, аналітика).
Фронтенд (React PWA) — окремий репозиторій `vehicle_cost_tracker`.

**Технічний стек:**
- Django 6 + Django REST Framework
- PostgreSQL
- Сесійна авторизація (Django session + CSRF, не JWT)
- Telegram-бот на `aiogram` (`apps/accounts/bot.py`)
- Docker Compose (`api` + `bot`, `network_mode: host`)

---

## Команди (Project Root)

```bash
python manage.py runserver     # Локальний dev-сервер
python manage.py run_bot       # Telegram-бот окремим процесом
python manage.py migrate       # Застосувати міграції
python manage.py makemigrations
python manage.py check         # Швидка перевірка без запуску сервера
ruff check .                   # Лінтер
```

---

## Стиль коду та правила

- **Views:** `viewsets.ModelViewSet` + `DefaultRouter`, не function-based views.
- **Права доступу:** `get_permissions()` за роллю, класи в
  `apps/accounts/permissions.py` (`IsAuthenticated`, `IsManagerOrHead`,
  `IsManagerOrHeadOnly`, `IsLogistOrAbove`, `IsHeadOnly` — див. файл,
  кожен клас має докстрінг з поясненням "чому саме ці ролі").
- **Моделі:** `verbose_name`/`help_text` українською на кожному полі,
  явний `db_table` (`snake_case`), `on_delete=PROTECT`/`SET_NULL`, не
  `CASCADE` без явної потреби.
- **Серіалізатори/DecimalField:** DRF серіалізує `DecimalField` у JSON
  як рядок, не число — про це знає фронтенд (`mapCar()` тощо), на
  бекенді нічого додатково робити не треба, просто пам'ятай при
  дебазі "чому число прийшло рядком".
- **Авторизація без логіну:** DRF тут завжди повертає `403`, не `401`
  (стандартна поведінка `SessionAuthentication` без
  `WWW-Authenticate`-заголовка) — це для всього API, не баг конкретного
  ендпоінту.

---

## Патерни коду

### 1. ViewSet з рольовими правами
```python
class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    def get_permissions(self):
        if self.action in WRITE_ACTIONS:
            return [IsLogistOrAbove()]
        return [IsAuthenticated()]
```

### 2. Модель з українськими підписами
```python
class Car(models.Model):
    name_car = models.CharField(max_length=100, verbose_name="Назва авто")
    status_car = models.CharField(
        max_length=20, choices=CarStatus.choices, verbose_name="Статус",
    )

    class Meta:
        db_table = "cars"
```

### 3. Permission-клас з поясненням ролей
```python
class IsManagerOrHeadOnly(HasRole):
    """Логіст навмисно виключений — див. докстрінг у permissions.py."""
    allowed_roles = ("manager", "head")
```

---

## Алгоритм роботи

1. Перевірити `STATE.md` — на якому етапі проект.
2. Прочитати `TASK.md` — що треба зробити.
3. Ознайомитись з `transport/` документацією якщо завдання складне.
4. Покроковий гайд реалізації — `DJANGO_CODING_GUIDE.md` (корінь
   репозиторію) для нового функціоналу за зразком уже реалізованих фаз.
5. Оновити `STATE.md` після завершення роботи.
