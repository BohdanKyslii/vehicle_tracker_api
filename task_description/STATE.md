# STATE.md — Стан проекту (Vehicle Cost Tracker, backend)

> Оновлюється після кожної значущої сесії. Детальна історія — `CHANGES.md`.

**Останнє оновлення:** 2026-08-10

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
- **2026-08-10:** перший реальний водій зареєструвався й був
  підтверджений в Telegram, але кнопка меню бота нічого не відкривала.
  Причина — у `vehicle_cost_tracker`: коміт `2327e97` (09.08, Фаза 11
  перепис `App.tsx` під `DriverLayout`/`MainLayout`) вдруге (перший раз
  було `d792cfa`, 04.08) тихо видалив маршрут `/driver-app` +
  імпорт `DriverMiniApp`. Окремо коміт `5ca19ea` тим же заходом
  спорожнив `src/api/cars.ts` (119 рядків `fetchCars`/`fetchCar`),
  через що `tsc -b` взагалі не збирався — деплої фронтенду мовчки
  падали з 09.08. Обидва файли відновлено, маршрут позначено
  коментарем `⚠️ НЕ ВИДАЛЯТИ`, задеплоєно на Pi вручну і запушено в
  `origin/main` (коміт `f0cd0cf`). Push фронтенду більше не
  заблокований — старий блокер нижче застарів.

## Наступні кроки

- Перевірити з реальним водієм, що `/driver-app` тепер справді
  відкривається кнопкою меню бота і логінить через `initData` (фікс
  10.08 задеплоєно, але наскрізно в живому Telegram ще не
  підтверджено самим водієм).
- Прив'язати `Profile.driver` підтвердженого водія до конкретної
  картки `Driver` в Django Admin (бот/кнопки цього не роблять
  автоматично).
- При будь-якому наступному великому переписуванні `App.tsx` у
  `vehicle_cost_tracker` — звірити, що маршрут `/driver-app` і
  `src/api/cars.ts` не зникли знову (вже двічі губили, див.
  `TELEGRAM_BOT_SETUP.md` і коментар `⚠️ НЕ ВИДАЛЯТИ` в `App.tsx`).
- Фаза 8 (`products`/`customers`/`waybills` views+urls) — дописана в
  `DJANGO_CODING_GUIDE.md`, код у репозиторії ще не набраний руками.

## Відомі блокери

- Немає активних. (Push фронтенду в `origin/main`, який раніше блокував
  конфлікт з 04.08 — розв'язано: `origin/main` фронтенду зараз включає
  весь Telegram-код і фікс від 10.08, коміт `f0cd0cf`.)
