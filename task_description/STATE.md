# STATE.md — Стан проекту (Vehicle Cost Tracker, backend)

> Оновлюється після кожної значущої сесії. Детальна історія — `CHANGES.md`.

**Останнє оновлення:** 2026-08-16

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
- **2026-08-16:** Крок 9.2 (`apps/accounts/permissions.py`) —
  `apps/cars/views.py` імпортував `IsLogistOrAbove`, якого в
  `permissions.py` ще не було (там жив тільки `IsManagerOrHead`).
  Додано клас `IsLogistOrAbove` і виправлено `get_permissions()` у
  `CarViewSet`/`DriverViewSet` (був баг: `IsLogistOrAbove` без дужок —
  переданий сам клас, а не інстанс permission). `change_status`
  лишився на `IsManagerOrHead`, як і задумано гайдом.
- **2026-08-16:** уточнено бізнес-логіку `apps/logistics` і
  `apps/analytics` за `vehicle_cost_tracker/documents/01_PROJECT_OVERVIEW.md`
  §5.2-5.4, §8 — місячні витрати (§5.2) вже покриті `MonthlyCosts` в
  `apps/cars`, а `apps/logistics` насправді має покривати найманий
  транспорт (§5.3) і служби доставки (§5.4), яких досі не було
  ніде. У `DJANGO_CODING_GUIDE.md` дописано `ФАЗУ 11` (Крок 15.1-15.6)
  з повними моделями/serializers/views/urls/admin для
  `HiredTransportTrip`+`HiredTripWaybill` і
  `CarrierShipment`+`CarrierShipmentWaybill`+`CarrierCost`, за
  зразком `assign_channel` з Кроку 8.5. Код у репозиторії ще не
  набраний руками (гайд писаний для ручного набору, не для
  автоматичної генерації).
- **2026-08-16:** доопрацьовано Telegram-бот (`apps/accounts/bot.py`,
  `TELEGRAM_BOT_SETUP.md`) — реєстрація водія тепер FSM-діалог
  (aiogram `MemoryStorage`): поділ контактом → ПІБ → номер посвідчення
  → бот сам створює `Driver` і лінкує `Profile.driver` (раніше це
  робилось вручну в Django Admin). Роль `HEAD` більше не виключена з
  кнопок підтвердження бота (`approval_keyboard()` в
  `telegram_notify.py`) — `TELEGRAM_ADMIN_IDS` і так довірені
  підтверджувати будь-яку роль, ховати саме HEAD не додавало захисту;
  веб-реєстрація (`RegisterSerializer`) HEAD, як і раніше, виключає.
  Одразу після підтвердження ролі "Водій" бот питає в адміна/логіста
  4 цифри держ. номера і сам призначає `Driver.car` (з дизамбігуацією
  кнопками при кількох збігах, `/skip` щоб пропустити); якщо авто вже
  закріплене за іншим водієм — знімає з нього автоматично (сценарій
  підміни на час лікарняного). Код перевірено `python manage.py check`
  і `py_compile`, на реальному боті ще не тестовано.
- **2026-08-16:** `vehicle_cost_tracker` — `DriverMiniApp.tsx` (Mini App
  логін через `initData`) редіректив УСІХ на `/driver` незалежно від
  ролі: адмін/логіст, тиснучи "Відкрити застосунок" у боті, потрапляв
  на екран водія. Тепер редіректить за `profile.role` з відповіді
  логіну — `driver` → `/driver` (готовий `DriverDashboard`), `logist`/
  `manager`/`head` → `/fleet` (маршрут існує, але сам ще
  `PlaceholderPage` — при перевірці виявилось, що `CODING_GUIDE.md`
  "Фаза 16 FleetList/CarForm виконано" **не відповідає** реальному коду:
  `src/components/fleet` і `src/pages/fleet` порожні; той самий розрив
  підтвердився для `RequireRole`/Фази 14 — файлу немає взагалі).
  Заодно прибрано дубльований маршрут `/driver-app` в `App.tsx` (був
  зареєстрований двічі, працював через перший збіг — не та сама
  фрагільність, що губила маршрут повністю, див.
  `[[project_driver_app_route_fragility]]`). `npx tsc -b` пройшов
  чисто, закомічено й запушено напряму в `origin/main` (`d82b5eb`) на
  прохання користувача.

## Наступні кроки

- Перевірити з реальним водієм, що `/driver-app` тепер справді
  відкривається кнопкою меню бота і логінить через `initData` (фікс
  10.08 задеплоєно, але наскрізно в живому Telegram ще не
  підтверджено самим водієм).
- Прив'язати `Profile.driver` вже підтвердженого 10.08 водія до
  картки `Driver` в Django Admin вручну — він реєструвався ДО фіксу
  16.08, бот тоді ще не створював `Driver` автоматично. Для всіх
  наступних реєстрацій це вже не потрібно (бот сам створює `Driver`
  і призначає авто, див. "Що зроблено" 16.08).
- При будь-якому наступному великому переписуванні `App.tsx` у
  `vehicle_cost_tracker` — звірити, що маршрут `/driver-app` і
  `src/api/cars.ts` не зникли знову (вже двічі губили, див.
  `TELEGRAM_BOT_SETUP.md` і коментар `⚠️ НЕ ВИДАЛЯТИ` в `App.tsx`).
- Набрати руками код `Фази 11` (`DJANGO_CODING_GUIDE.md`, Крок 15.1-15.6):
  моделі `HiredTransportTrip`/`HiredTripWaybill` (найманий транспорт,
  логіст) і `CarrierShipment`/`CarrierShipmentWaybill`/`CarrierCost`
  (служби доставки, менеджер-операціоніст) в `apps/logistics` —
  досі порожній застосунок. Після цього розкоментувати
  `path("api/", include("apps.logistics.urls"))` у `config/urls.py`.
- `apps/analytics` лишається порожнім навмисно — це `Sum()`/`annotate()`
  над уже наявними даними, писати варіант має сенс під конкретні
  дашборди фронтенду, коли в БД накопичиться реальна історія
  (пов'язано з Кроком 14 нижче).
- Крок 11 (`DJANGO_CODING_GUIDE.md`, "Що далі") — management command
  імпорту з 1С — це чистий бекенд (`python manage.py import_from_1c`),
  React UI під нього не потрібен, можна писати вже зараз незалежно
  від фронтенду.
- Крок 14 (підключення `products`/`customers`/`waybills` до реального
  React) — дійсно залежить від фронтенду: `vehicle_cost_tracker` вже
  має `USE_MOCK`-перемикач у `src/api/waybills.ts`, але тільки для
  читання (список/фільтри/деталі); `src/api/products.ts` і
  `customers.ts` не існують, форм створення/редагування накладних
  теж немає.
- `vehicle_cost_tracker/CODING_GUIDE.md` стверджує, що Фаза 16
  (`FleetList`/`CarForm`) і Фаза 14 (`RequireRole`) виконані — це
  неправда, `/fleet` досі `PlaceholderPage`, `RequireRole.tsx` не
  існує (перевірено 16.08 при роботі над редіректом Mini App). Текст
  гайду в цих місцях писаний наперед, не пост-фактум — варто або
  дописати ці фази реальним кодом, або прибрати з гайду позначки
  "виконано", поки це справді так.

## Відомі блокери

- Немає активних. (Push фронтенду в `origin/main`, який раніше блокував
  конфлікт з 04.08 — розв'язано: `origin/main` фронтенду зараз включає
  весь Telegram-код і фікс від 10.08, коміт `f0cd0cf`.)
