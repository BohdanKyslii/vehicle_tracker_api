# STATE.md — Стан проекту (Vehicle Cost Tracker, backend)

> Оновлюється після кожної значущої сесії. Детальна історія — `CHANGES.md`.

**Останнє оновлення:** 2026-08-09

---

## Поточна фаза

Backend (`vehicle_tracker_api`, Django/DRF) розгорнутий на Raspberry Pi
(Docker Compose, сервіси `api` + `bot`, `network_mode: host`, напряму
до Postgres на тому ж хості). Фронтенд — окремий репозиторій
`vehicle_cost_tracker` (React PWA), синхронізація типів вручну
(`src/types/index.ts` ↔ Django-моделі).

## Що зроблено

- `cars` (Фаза 6-7) — задеплоєно на Pi.
- Telegram-реєстрація водіїв (бот `aiogram`, `apps/accounts/bot.py`) +
  вхід через Telegram Mini App (`initData`, HMAC-перевірка) +
  підтвердження заявки з вибором ролі прямо в Telegram. Архітектура —
  `TELEGRAM_BOT_SETUP.md`.
- **2026-08-09:** реальний бот створено через `@BotFather` —
  `@driver_car_bot`. `TELEGRAM_BOT_TOKEN` і `TELEGRAM_ADMIN_IDS`
  прописані в `~/vehicle_tracker_api/.env` на Pi, контейнери `api` і
  `bot` перестворені (`docker compose up -d --force-recreate bot api`
  — rebuild не потрібен, бо це backend env-змінні, не `VITE_*`).
  Логи підтверджують `Start polling` без помилок — бот живий у
  проді.

## Наступні кроки

- Протестувати наскрізний сценарій у реальному Telegram: `/start` →
  "Надіслати номер телефону" → сповіщення `TELEGRAM_ADMIN_IDS` з
  кнопками ролей → підтвердження → прив'язка `Profile.driver` в
  Django Admin.
- Фронтенд (`vehicle_cost_tracker`): Mini App сторінка + кнопка
  Telegram на сайті — за станом на 2026-08-04 закомічені локально, але
  push був заблокований конфліктом з `origin/main`, ще не розв'язано.
  Без цього кроку `VITE_TELEGRAM_BOT_USERNAME` на Pi не задіється і
  `/driver-app` на проді не з'явиться.
- Фаза 8 (`products`/`customers`/`waybills` views+urls) — дописана в
  `DJANGO_CODING_GUIDE.md`, код у репозиторії ще не набраний руками.

## Відомі блокери

- Push фронтенду в `origin/main` (конфлікт) — статус на момент цього
  запису невідомий, треба перевірити в репозиторії `vehicle_cost_tracker`.
