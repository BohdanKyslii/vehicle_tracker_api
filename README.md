# Vehicle Cost Tracker — Backend

Django REST API для обліку транспортних витрат (автопарк, водії,
накладні, найманий транспорт, аналітика). Прод на Raspberry Pi
(warehouse.mom) втрачено; перенесення на хост rubin описане в
[`deploy/DEPLOY_RUBIN_HOST.md`](deploy/DEPLOY_RUBIN_HOST.md).

Фронтенд (React PWA) — окремий репозиторій `vehicle_cost_tracker`,
типи синхронізуються вручну між `src/types/index.ts` і моделями цього
бекенду.

## Стек

- Django 6 + Django REST Framework, сесійна авторизація (не JWT)
- PostgreSQL
- Telegram-бот на `aiogram` (реєстрація водіїв, `apps/accounts/bot.py`)
- Docker Compose (сервіси `api` + `bot`, мережа `shared_net`, Postgres у
  контейнері `rubin-postgres-container`)
- Деплой — GitHub Actions збирає образ і завантажує на хост через SSH
  (`.github/workflows/deploy.yml`); вмикається змінною `DEPLOY_ENABLED`

## З чого почати

- **Документація проєкту й поточний стан** —
  [`task_description/README.md`](task_description/README.md) (бізнес-логіка,
  архітектура, `STATE.md` з живою історією сесій).
- **Покрокове відтворення бекенду з нуля** —
  [`DJANGO_CODING_GUIDE.md`](DJANGO_CODING_GUIDE.md) (Фази 1-12, зі
  змістом на початку файлу).
- **Telegram-бот** — [`TELEGRAM_BOT_SETUP.md`](TELEGRAM_BOT_SETUP.md)
  (локальний файл, не в git — токенів не містить, але це internal
  ops-нотатка; попроси в команди, якщо файлу немає локально).

## Локальний запуск

```bash
cp env.example .env        # заповнити DB_*, TELEGRAM_BOT_TOKEN тощо
python manage.py migrate
python manage.py runserver
```

Бот окремим процесом: `python manage.py run_bot`.

> Локальна БД `vehicle_tracker` зараз є єдиною копією даних проду.
> Не виконувати на ній руйнівних команд, поки дані не перенесено на хост.

## Продакшн

Покрокова інструкція: [`deploy/DEPLOY_RUBIN_HOST.md`](deploy/DEPLOY_RUBIN_HOST.md).
Шаблон змінних: `env.production.example`.

Обидва контейнери (`api`, `bot`) читають `.env` з
`/opt/vehicle_tracker_api/.env`, у git цей файл не потрапляє.
