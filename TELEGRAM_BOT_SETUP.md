# Telegram-бот водіїв — архітектура, налаштування, тестування

Цей файл — для вас (адміна) і для майбутньої підтримки/доопрацювання
функціоналу. Реалізовано за один сеанс 2026-08-04, ще не тестовано на
реальному Telegram-боті (тільки локально, з підробленим токеном/`initData`).

---

## 1. Як це влаштовано (архітектура)

Дві незалежні речі, які використовують один і той самий `Profile`:

1. **Реєстрація** — водій пише боту в Telegram, ділиться номером
   телефону кнопкою. Бот створює неактивний акаунт.
2. **Вхід (Mini App)** — Telegram відкриває сторінку `/driver-app` у
   власному WebView з підписаним `initData`; бекенд перевіряє підпис і
   логінить тим самим сесійним механізмом, що й звичайний
   username/password логін.

Окремо — **підтвердження адміном**: заявка йде і на пошту (як і
раніше), і в Telegram із кнопками вибору ролі.

### Backend (`vehicle_tracker_api`) — хто за що відповідає

| Файл | Відповідальність |
|---|---|
| `apps/accounts/bot.py` | Сам бот (aiogram, long polling). `/start` → кнопка "поділитись контактом". Обробник контакту створює `User(is_active=False)` + `Profile(role=DRIVER)`. Обробники `on_approve`/`on_reject` — callback від inline-кнопок адміна. |
| `apps/accounts/management/commands/run_bot.py` | Django-команда `python manage.py run_bot` — точка входу, яку запускає Docker (`docker-compose.yml`, сервіс `bot`). Просто викликає `bot.run()` через `asyncio.run`. |
| `apps/accounts/telegram_auth.py` | **Тільки для Mini App логіну.** Чиста функція `verify_init_data()` — перевіряє HMAC-підпис `initData`, який Telegram WebView передає фронтенду. Без Django/aiogram-залежностей, легко тестувати окремо. |
| `apps/accounts/telegram_notify.py` | **Тільки для сповіщень адміну.** Синхронний виклик Telegram Bot API (`sendMessage`) напряму через `urllib` (без нової залежності) — потрібен, бо `notifications.py` викликається з синхронного Django-коду (веб-реєстрація), а `aiogram` — асинхронна бібліотека. |
| `apps/accounts/notifications.py` | `notify_admin_new_registration()` — спільна точка для ОБОХ шляхів реєстрації (веб-форма і бот). Шле лист (якщо є `ADMIN_EMAIL`) і Telegram-повідомлення з кнопками (якщо є `TELEGRAM_ADMIN_IDS`) — незалежно одне від одного. |
| `apps/accounts/views.py` → `telegram_login` | `POST /api/auth/telegram/` — ендпоінт, який викликає фронтенд (Mini App) з `initData`. Повертає `not_registered` / `pending_approval` / логінить і повертає користувача. |
| `apps/accounts/models.py` → `Profile.telegram_id` | Єдине поле, що зв'язує Telegram-акаунт з `User`. `unique=True`. (Старе `Driver.telegram_id` в `apps/cars` видалено як дублікат.) |
| `config/settings.py` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_IDS` — з `.env`. |

### Frontend (`vehicle_cost_tracker`) — хто за що відповідає

| Файл | Відповідальність |
|---|---|
| `src/pages/DriverMiniApp.tsx` | Сторінка на маршруті `/driver-app` — те, що Telegram відкриває водію. На старті бере `initData` з `window.Telegram.WebApp`, логінить, показує один з 5 станів (loading/не зареєстровано/очікує/помилка/успіх). |
| `src/types/telegram-web-app.d.ts` | TS-типи для `window.Telegram.WebApp` (без нової npm-залежності — сам скрипт підключений тегом у `index.html`). |
| `src/api/auth.ts` → `loginWithTelegram()` | Викликає `POST /auth/telegram/`, той самий патерн, що й звичайний `login()`. |
| `src/hocks/useCurrentUser.ts` | Додано мутацію `loginWithTelegram`, пише результат у той самий React Query кеш `["currentUser"]`. |
| `src/components/auth/AuthModal.tsx` → `TelegramButton` | Кнопка-іконка (літачок) у формах входу/реєстрації — просто `<a href="https://t.me/<бот>">`, не форма. Рендериться лише якщо задано `VITE_TELEGRAM_BOT_USERNAME`. |
| `src/App.tsx` | Маршрут `/driver-app` (окремо від `/driver` — це офісна сторінка керування водіями, не чіпали). |

### Потік підтвердження адміном

```
Водій пише боту → бот створює User(is_active=False)
                → notify_admin_new_registration()
                     ├─ лист на ADMIN_EMAIL (якщо задано)
                     └─ Telegram-повідомлення кожному з TELEGRAM_ADMIN_IDS
                        з кнопками: ✅ Водій / ✅ Логіст / ✅ Менеджер / ❌ Відхилити
Адмін тисне кнопку → on_approve/on_reject у bot.py
                   → is_active=True + Profile.role = обрана роль
                   → водію в Telegram надсилається "вас підтверджено"
```

Перевірка прав "тільки адмін може тиснути ці кнопки" — `_is_admin()` у
`bot.py`, звіряє `callback.from_user.id` зі списком `TELEGRAM_ADMIN_IDS`.

---

## 2. Що вам потрібно створити й додати

### 2.1 Сам бот

1. У Telegram напишіть **@BotFather** → `/newbot` → дайте ім'я й
   username (username мусить закінчуватись на `bot`, наприклад
   `vehicle_tracker_bot`). BotFather видасть **токен**
   (`123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
2. Дізнайтесь **свій Telegram ID** — напишіть **@userinfobot**, він
   одразу відповість числом (наприклад `987654321`). Якщо адмінів
   декілька — кожен пише @userinfobot окремо.
3. (Опційно, але бажано) `@BotFather` → `/setdescription`,
   `/setuserpic` — щоб бот виглядав як частина проєкту, а не тестовий.

### 2.2 Mini App у BotFather

`@BotFather` → `/newapp` (або `/mybots` → ваш бот → `Bot Settings` →
`Menu Button` → `Configure menu button`) → вкажіть:
- URL: `https://warehouse.mom/driver-app`
- Назва кнопки: наприклад "Відкрити застосунок"

Після цього в чаті бота з'явиться кнопка меню, яка відкриває Mini App.

### 2.3 Змінні середовища

**Backend** (`~/vehicle_tracker_api/.env` на Raspberry Pi):
```
TELEGRAM_BOT_TOKEN=<токен від BotFather>
TELEGRAM_ADMIN_IDS=987654321
# декілька адмінів — через кому: TELEGRAM_ADMIN_IDS=987654321,111222333
```

**Frontend** (`~/vehicle_cost_tracker/.env` на Raspberry Pi — файл там
уже має бути, з `VITE_API_BASE` тощо; якщо нема — гляньте
`env.example`-аналог або `VITE_API_BASE`/`VITE_USE_MOCK`, які вже
мають там бути з попереднього деплою):
```
VITE_TELEGRAM_BOT_USERNAME=vehicle_tracker_bot
```
(без `@`, просто username бота).

⚠️ **Важливо для фронтенду:** `VITE_*` змінні Vite "запікає" в код
**під час збірки** (`npm run build` всередині Docker), не читає їх під
час роботи. Просто перезапустити контейнер після зміни `.env` —
**недостатньо**, потрібен саме `docker compose build`.

---

## 3. Розгортання на Raspberry Pi

Бекенд-`docker-compose.yml` вже містить другий сервіс `bot`
(`python manage.py run_bot`, той самий образ, що й `api`). Він
підхопиться сам при наступному `git pull` + `docker compose build` —
CI/CD (`.github/workflows/deploy.yml`) робить це автоматично при push
у `main`, включно з щойно запушеними змінами цієї сесії.

**Але:** якщо `TELEGRAM_BOT_TOKEN` порожній, `run_bot` одразу падає з
`CommandError`, а `restart: unless-stopped` означає, що Docker буде
**постійно перезапускати контейнер по колу** (не шкідливо, просто шум
у логах), поки ви не додасте токен. Тому послідовність:

```bash
ssh pi-deploy   # або як ви зазвичай заходите на Pi

# 1. Додати токен і admin ID у .env ОБОХ репозиторіїв (backend + frontend)
nano ~/vehicle_tracker_api/.env      # TELEGRAM_BOT_TOKEN=..., TELEGRAM_ADMIN_IDS=...
nano ~/vehicle_cost_tracker/.env     # VITE_TELEGRAM_BOT_USERNAME=...

# 2. Перебудувати й підняти обидва
cd ~/vehicle_tracker_api && docker compose build && docker compose up -d
cd ~/vehicle_cost_tracker && docker compose build && docker compose up -d

# 3. Перевірити, що бот реально піднявся (без CommandError у циклі)
cd ~/vehicle_tracker_api && docker compose logs -f bot
```

Якщо в логах `bot` бачите щось на кшталт `Start polling` (без
повторюваних traceback) — бот живий.

**Фронтенд ще не запушено** (був конфлікт з `origin/main`, лишили як
є за вашим проханням) — доки не розберетесь і не запушите, кнопка
Telegram на сайті й `/driver-app` на проді не з'являться.

---

## 4. Як протестувати

### 4.1 Реєстрація водія
1. У Telegram знайдіть свого бота за username, натисніть `/start`.
2. Натисніть кнопку "Надіслати номер телефону".
3. Має прийти: "Дякуємо! Заявку надіслано...".
4. Перевірте:
   - Лист на `ADMIN_EMAIL` (якщо задано) — або в консолі контейнера
     `api`, якщо `EMAIL_BACKEND` досі `console` (лист просто друкується
     в лог, нічого реально не надсилається — див. `env.example`).
   - Повідомлення в Telegram кожному з `TELEGRAM_ADMIN_IDS`, з кнопками
     ролей.

### 4.2 Підтвердження
1. У Telegram-повідомленні від бота натисніть роль (наприклад
   "✅ Водій").
2. Повідомлення має оновитись міткою "✅ Підтверджено як Водій".
3. Водію в Telegram має прийти "Вас підтверджено!".
4. Перевірте в Django Admin (`/admin/auth/user/`) — новий `User`
   активний, у вкладеній `Profile` — роль і `telegram_id`.
5. **Окремо, вручну** — прив'яжіть `Profile.driver` до конкретної
   картки водія (`Driver`) в Django Admin. Бот/кнопки цього не роблять
   автоматично — це свідоме рішення (дозволяє диспетчеру звірити, що
   це саме той водій, перш ніж давати доступ до конкретного авто).

### 4.3 Mini App / вхід
1. У чаті бота натисніть кнопку меню (та, що налаштували в п. 2.2).
2. Має відкритись `/driver-app` всередині Telegram і одразу залогінити
   (без пароля) — побачите "Вітаємо, tg_<id>!" (плейсхолдер, реальний
   дашборд водія — ще не збудований, це подальші фази `ROADMAP.md`).
3. Якщо акаунт ще не підтверджено — побачите "Заявку надіслано.
   Очікуйте підтвердження диспетчера."

### 4.4 Кнопка на сайті
Відкрийте `https://warehouse.mom/` → "Вхід" або "Створити акаунт" →
має з'явитись іконка-літачок поруч з "G" (тільки після того, як
запушите й задеплоїте фронтенд, п. 3).

---

## 5. На що зважати при доопрацюванні

- **Безпека:** `verify_init_data()` (`telegram_auth.py`) — єдине
  місце, що підтверджує, що запит справді від Telegram, а не
  підроблений. Якщо чіпатимете цю логіку — обов'язково прогнати
  сценарії: валідний / підроблений / протермінований `initData` (є
  готовий приклад самотесту в історії цієї сесії, можна відтворити
  через `manage.py shell`).
- **`_is_admin()` у `bot.py`** — єдине, що не дає стороннику натиснути
  кнопку підтвердження, якщо повідомлення комусь переслали. Не
  прибирайте цю перевірку.
- Кнопка "Відхилити" видаляє `User` лише якщо він ще `is_active=False`
  (захист від випадкового подвійного натискання на вже підтвердженого).
- Наразі немає проактивного пуша водію, коли диспетчер прив'язує
  `Profile.driver` в Admin — водій дізнається про підтвердження
  акаунту (крок 4.2.3), але не про прив'язку до конкретного авто.
  Можна додати пізніше сигналом Django (`post_save` на `Profile`).
- `Mini App`-сторінка (`DriverMiniApp.tsx`) зараз — лише
  плейсхолдер-заглушка після успішного логіну. Реальний функціонал
  водія (маршрути, одометр тощо) — окрема, ще не почата робота
  (`ROADMAP.md`, фази 8+ фронтенду).
