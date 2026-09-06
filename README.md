# Vehicle Cost Tracker — Backend

Django REST API для обліку транспортних витрат (автопарк, водії,
накладні, найманий транспорт, аналітика). Розгорнутий у проді на
Raspberry Pi за адресою [warehouse.mom](https://warehouse.mom).

Фронтенд (React PWA) — окремий репозиторій `vehicle_cost_tracker`,
типи синхронізуються вручну між `src/types/index.ts` і моделями цього
бекенду.

## Стек

- Django 6 + Django REST Framework, сесійна авторизація (не JWT)
- PostgreSQL
- Telegram-бот на `aiogram` (реєстрація водіїв, `apps/accounts/bot.py`)
- Docker Compose (сервіси `api` + `bot`, `network_mode: host` — прямий
  доступ до Postgres на тому ж хості)
- Деплой — GitHub Actions → SSH через `cloudflared` → Pi →
  `git pull` + `docker compose up -d` (`.github/workflows/deploy.yml`)

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

> ⚠️ Локальний `.env` за замовчуванням у цій команді вже налаштований
> на прод-БД на Pi (`DB_HOST=192.168.0.114`) — команди `manage.py`
> впливають на реальні дані, не на пісочницю. Деталі — `STATE.md`.

## Продакшн

```bash
docker compose up -d --build
```

Обидва контейнери (`api`, `bot`) читають `.env` з кореня репозиторію на
Pi (`~/vehicle_tracker_api/.env`), у git цей файл не потрапляє.
