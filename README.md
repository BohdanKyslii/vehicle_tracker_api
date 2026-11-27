# Vehicle Cost Tracker — Backend

Django REST API для обліку транспортних витрат (автопарк, водії,
накладні, найманий транспорт, служби доставки, аналітика).

> ⚠️ **Стан на 2026-11-27: прод не працює.** Raspberry Pi
> (`warehouse.mom`) зламався, дані проду втрачено. Перенесення на хост
> rubin підготовлено в гілці `feat/deploy-rubin-host` (інструкція —
> `deploy/DEPLOY_RUBIN_HOST.md` у тій гілці), ще не виконано.
> Конфігурація деплою в `main` (`docker-compose.yml`,
> `.github/workflows/deploy.yml`) досі описує старий Pi.

Фронтенд (React PWA) — окремий репозиторій `vehicle_cost_tracker`,
типи синхронізуються вручну між `src/types/index.ts` і моделями цього
бекенду.

## Стек

- Django 6 + Django REST Framework, сесійна авторизація (не JWT)
- PostgreSQL
- Telegram-бот на `aiogram` (реєстрація водіїв, `apps/accounts/bot.py`)
- Docker Compose (сервіси `api` + `bot`)

## З чого почати

- **Документація проєкту й поточний стан** —
  [`task_description/README.md`](task_description/README.md) (бізнес-логіка,
  архітектура, `STATE.md` з живою історією сесій).
- **Покрокове відтворення бекенду з нуля** —
  [`DJANGO_CODING_GUIDE.md`](DJANGO_CODING_GUIDE.md) (Фази 1-13, зі
  змістом на початку файлу).
- **Telegram-бот** — `TELEGRAM_BOT_SETUP.md` (локальний файл, не в git).

## Локальний запуск

```bash
cp env.example .env        # заповнити DB_*, TELEGRAM_BOT_TOKEN тощо
python manage.py migrate
python manage.py runserver 8001
```

Порт **8001**, не 8000: на машині розробника 8000 зайнятий іншим
проєктом (див. `task_description/AGENTS_GLOBAL.md`). Бот окремим
процесом: `python manage.py run_bot`.

> ⚠️ Локальна БД `vehicle_tracker` зараз є **єдиною копією даних
> проду** (знімок 2026-09-28 + локальні імпорти жовтня). Не виконувати
> на ній руйнівних команд, поки дані не перенесено на новий хост.

## Що не потрапляє в git / образ

- `.gitignore` — `.env`, дампи БД (`dump-*.sql`, `*.dump`), зразки
  файлів з 1С (`task_description/**/*.xls*`, `*.pdf`, `*.csv`),
  кеші й IDE-файли.
- `.dockerignore` — документація (`*.md`, `task_description/`),
  `.git`, `venv`, кеші: в образ іде лише код застосунку.
