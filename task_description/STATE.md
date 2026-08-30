# STATE.md — Стан проекту (Vehicle Cost Tracker, backend)

> Оновлюється після кожної значущої сесії. Детальна історія — `CHANGES.md`.

**Останнє оновлення:** 2026-08-30

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

- **2026-08-16 (пізніше того ж дня):** живий інцидент — `b.kisliy`
  зареєструвався й підтвердив себе через бота о 14:24 BST, ДО того як
  бекенд-фікс (`edf7db6`, кнопка "✅ Керівник") задеплоївся о 15:10 BST
  (46 хв різниці) — тому кнопки HEAD ще не було, підтвердив себе як
  "Менеджер". `Profile.role` для `user_id=5` (`tg_5137561181`) вручну
  виправлено на `head` прямим UPDATE в БД (бот не дає повторно
  пройти approval-flow для вже активного акаунту — тільки Django
  Admin/пряма правка для зміни ролі постфактум). Заразом перевірено:
  жодних `is_active=False` (pending) користувачів у БД немає; водій,
  описаний нижче як "підтверджений 10.08", у поточній БД взагалі
  відсутній (лишились лише user_id 1,2,3,5 — розрив на 4 натякає, що
  той запис або відхилили, або тестова БД відрізняється від того, що
  описано в записі 10.08) — пункт про ручний лінк `Profile.driver`
  нижче через це неактуальний, прибрано.
- **2026-08-16 (ще пізніше):** живий інцидент №2 — заявка від
  `+380966544621` через бота не дійшла до адміна взагалі. У логах
  `bot`-контейнера на Pi: `IntegrityError: duplicate key value violates
  unique constraint "drivers_pkey"` всередині `_create_driver_registration`
  (`apps/accounts/bot.py`). Причина — `drivers_id_seq` відставала від
  реальних даних (`MAX(id)=4`, послідовність стояла на `2`) — імовірно
  з часів тестових даних Кроку 10.2, які вставлялись напряму (fixture/
  SQL), а не через `Driver.objects.create()`, тому Postgres-sequence
  ніколи не підтягувалась. `transaction.atomic()` в
  `_create_driver_registration` відкотив весь запис (User+Driver+
  Profile) при падінні — заявник лишився без жодного сліду в БД, і
  `notify_admin_new_registration()` не викликався (виняток стався
  раніше по коду). Та сама проблема була і в `cars_id_seq` (`MAX(id)=4`,
  seq на `1`) — потенційна бомба уповільненої дії для будь-якого
  `POST /api/cars/` через Fleet CRUD, ще не спрацювала лише тому, що
  через API нових авто ще не створювали. Обидві послідовності
  виправлено напряму (`SELECT setval('drivers_id_seq', 4, true)`,
  `SELECT setval('cars_id_seq', 4, true)`). Заявнику треба
  зареєструватись повторно — старих даних не лишилось, конфлікту не буде.
- **2026-08-19:** `apps/logistics` (Фаза 11, набрана руками користувачем
  за Кроком 15.1-15.5) — виправлено після рев'ю:
  - `models.py`: `pallets_count` був `DecimalField` без `max_digits`/
    `decimal_places` (блокував `makemigrations`) → `SmallIntegerField`;
    `HiredTripWaybill.waybill_number` `max_length=20` → `50` (вирівняно
    з `WaybillRecord`/`CarrierShipmentWaybill`, окрема міграція
    `0002_alter_hiredtripwaybill_waybill_number`); прибрано зайвий
    `from unicodedata import decimal`; `CarrierShipmentWaybill.__str__`
    посилався на неіснуюче `self.shipment_ttn` замість `self.shipment.ttn`;
    `CarrierCost.Meta.db_table` був обгорнутий у `_()` (переклад
    замість імені таблиці).
  - `admin.py`: `line_display` → `list_display` (typo, Django мовчки
    ігнорував — колонки в адмінці не показувались).
  - `views.py` — тут була причина, чому падав **увесь** проєкт:
    клас `HiredTransporttripViewSet` (маленька `t`) не збігався з
    імпортом `HiredTransportTripViewSet` у `urls.py` → `ImportError`
    при кожному старті, бо `config/urls.py` вже підключає
    `apps.logistics.urls`. Також: `permission_classes=[IsAuthenticated(), ...]`
    (зайві дужки — екземпляр замість класу, впав би на першому ж
    запиті до `attach_waybill`); `serializer.validated_data.get["ttn"]`
    (квадратні дужки замість виклику `.get("ttn")` — `TypeError` на
    кожному `POST /api/carrier-costs/`); три зайвих імпорти
    (`multiprocessing.connection.deliver_challenge`, `from .. import
    waybills`, `from ..cars.views import WRITE_ACTIONS` — одразу
    перезаписаний локальним визначенням).
  - Перевірено: `manage.py check` чистий, `runserver` піднімається,
    усі три ендпоінти (`hired-transport-trips`/`carrier-shipments`/
    `carrier-costs`) віддають `403` без авторизації — очікувано (нижче).
- **2026-08-19:** з'ясовано остаточно, чому DRF в цьому проєкті всюди
  віддає `403`, а не `401` без логіну (гайд, Крок 9.1/15.6, раніше
  помилково стверджував `401`) — `APIView.handle_exception()` бере
  `WWW-Authenticate` для 401-відповіді з ПЕРШОГО автентифікатора в
  `DEFAULT_AUTHENTICATION_CLASSES` (`[SessionAuthentication,
  BasicAuthentication]`); `SessionAuthentication.authenticate_header()`
  завжди `None` → DRF свідомо занижує `401 → 403`. Це стосується
  **всього** проєкту (перевірено на `/api/cars/`, той самий `403`), не
  специфіка логістики. Виправлено коментарі в обох місцях гайду.
- **2026-08-20:** досліджено реальні вивантаження з 1С
  (`task_description/file_1C/SalesLineItem_history.csv` — РУБІН,
  `Переміщення зі складів на АЗС.xls` — ЄСП) для підготовки Кроку 11
  (`DJANGO_CODING_GUIDE.md`). Знахідки й 12 відкритих питань — у
  новому `task_description/IMPORT_1C_SPEC.md`. Ключове: РУБІН і
  ЄСП/ОПТ мають **різні** формати (CSV vs legacy `.xls`, різні
  колонки); `product_articl` (РУБІН) і `Код` (ЄСП) — схоже, спільний
  артикул на всі юрособи. Файл ще чекає відповідей користувача — Крок
  11 гайду поки не написаний.
- **2026-08-24:** оновлено весь `task_description/transport/`
  (8 файлів: `01_PROJECT_OVERVIEW.md` … `08_PROJECT_STRUCTURE.md`) —
  звірено з реальним кодом обох репозиторіїв, `DJANGO_CODING_GUIDE.md`,
  `CODING_GUIDE.md` і `IMPORT_1C_SPEC.md`. Ключові виправлення:
  `products`/`customers`/`stores` PK — `IntegerField`, не `VARCHAR`, як
  планувалось; додано `car_specs`/`trailers`/`car_status_logs`/`profiles`
  (яких не було в первинному плані); `06_IMPLEMENTATION_PLAN.md`
  повністю переписано — старий план "Тиждень 1-5" замінено таблицею
  реального прогресу по Фазах обох гайдів + рекомендованим порядком
  продовження (зараз: Фаза 14→16 фронтенду, бо Mini App-редірект
  2026-08-19 веде логіста/адміна на `/fleet`, а там порожня заглушка).
  **Не займали** `task_description/warehouse/` (окремий, непов'язаний
  Django-застосунок) — не плутати з `transport/`.
- **2026-08-24 (продовження):** оновлено й кореневі `README.md` та
  `AGENTS_GLOBAL.md` (v3 → v4) — прибрано твердження "бекенд майбутній,
  поза scope MVP" / "Mock-дані, у майбутньому DRF"; додано реальний
  backend tech stack, попередження про `403` замість `401`,
  застереження про `task_description/warehouse/` (не цей проєкт) і про
  те, що обидва `*_CODING_GUIDE.md` — сценарії для ручного набору, не
  changelog.
- **2026-08-24 (продовження 2):** оновлено й `AI_AGENT_CONTEXT.md`
  (v3 → v4) — крім загальної застарілості ("MVP на Mock-даних"), там
  були й фактичні помилки незалежно від дати: `RouteEvent.type` замість
  реального `eventType`, вигадані значення enum (`'fuel'`,
  `'depot_finish'` — таких нема, реальних 8: `depot_start`/`delivery`/
  `parking_end`/`depot_return`/`refuel`/`other_cost`/`return_goods`/
  `extra_cargo`), компоненти й хуки, яких у коді ніколи не було
  (`ChannelBadge`, `PalletsInput`, `StoreConfirmModal`,
  `useWaybillChannelGuard`). Виправлено на реальний інвентар,
  посилання на `transport/03_TYPESCRIPT_TYPES.md` і `05_...` для
  повного списку.

- **2026-08-30:** усі 12 відкритих питань `IMPORT_1C_SPEC.md` (Q1-Q12)
  закриті користувачем ще 2026-08-20; цю сесію переведено в код гайду —
  `DJANGO_CODING_GUIDE.md`, нова `# ФАЗА 12 — ІМПОРТ НАКЛАДНИХ З 1С`
  (Кроки 16.1-16.8, лише текст гайду, руками код ще не набирався,
  той самий підхід "спершу гайд" що й для решти фаз). Ключові рішення:
  парсинг на бекенді (`xlrd==2.0.1` для legacy ЄСП/ОПТ `.xls`,
  стандартний `csv` для РУБІН cp1251); перезаливка автоматично за
  датами з файлу в одній транзакції; незнайдений
  Customer/Store — автостворення із синтетичними ID (900 000 000+),
  Product завжди має реальний 1С-артикул (єдиний довідник, Q1);
  `total_uah` для ЄСП/ОПТ = `СуммаВх` (собівартість, не роздрібна
  `СуммаР`) — свідомо зафіксований побічний ефект: аналітика "% від
  продажу" для цього каналу рахуватиме "% від собівартості",
  `calcTransportCost.ts` не чіпали. Новий ендпоінт
  `POST /api/waybill-records/import_file/` на вже існуючому
  `WaybillRecordViewSet`. Заразом закрито реальну діру в правах —
  `WaybillRecordViewSet` досі не мав `permission_classes` узагалі
  (писати міг будь-який залогинений, включно з водієм); для CRUD-запису
  й `import_file` заведено НОВИЙ клас `IsManagerOrHeadOnly`
  (`apps/accounts/permissions.py`) замість наявного `IsManagerOrHead`
  — той навмисно впускає й `logist` (лишено заради `Car.change_status`
  і `CarrierShipment`/`CarrierCost` з Фази 11), а бізнес-процес імпорту
  (§1 спеку — "менеджер-операціоніст в офісі") explicitly logist не
  включає. Синхронізовано з фронтендом: `vehicle_cost_tracker/
  CODING_GUIDE.md` вже мав чорновий `# ФАЗА 22` (Кроки 22.1-22.8,
  написаний наперед за планом `woolly-dancing-hopcroft.md`) — ендпоінт
  і форма відповіді збіглись 1-в-1, підправлено тільки Крок 22.1 під
  реальну назву permission-класу. **Ще не перевірено на реальному
  оновленому ЄСП/ОПТ-зразку** — Q2 вимагає нової колонки `name_store`
  (додає ІТ), якої немає в наявному
  `task_description/file_1C/Переміщення зі складів на АЗС.xls`; перший
  реальний оновлений файл або підтвердить `EXPECTED_HEADER` у
  `esp_opt_xls.py`, або впаде з `HeaderMismatchError` — це очікувано,
  не баг.

## Наступні кроки

- Набрати руками код `Фази 12` (`apps/waybills/importers/`,
  `matching.py`, `importing.py`, оновлений `views.py`,
  `IsManagerOrHeadOnly` у `apps/accounts/permissions.py`,
  `xlrd==2.0.1` у `requirements.txt`) за щойно дописаним `Кроком
  16.1-16.8` у `DJANGO_CODING_GUIDE.md` — сам код ще не набраний.
- Отримати від ІТ оновлений ЄСП/ОПТ `.xls`-зразок із доданою колонкою
  `name_store` (Q2) — без нього Крок 16.8 п.3 (перевірка на реальному
  файлі) неможливо пройти до кінця, лише перевірити, що
  `HeaderMismatchError` коректно ловить розбіжність.
- Перевірити інші таблиці на той самий розсинхрон sequence/MAX(id), що
  щойно знайшли в `drivers`/`cars` (інцидент №2 вище) — перевірено
  вибірково лише 4 таблиці (`auth_user`, `profiles`, `drivers`, `cars`),
  решта (`products`, `customers`, `waybill_records`, `route_events`,
  `monthly_costs`...) не перевірялись. Якщо десь так само сідали
  тестові дані напряму через SQL/fixture в обхід ORM — та сама пастка
  чекає там. Варто або пройтись `setval(seq, MAX(id))` по всіх
  таблицях одним разом, або з'ясувати ЯК саме `drivers`/`cars` отримали
  дані з ручним `id` (яка команда/фікстура це робила), щоб не
  повторити для наступних тестових даних.
- Перевірити з реальним водієм, що `/driver-app` тепер справді
  відкривається кнопкою меню бота і логінить через `initData` (фікс
  10.08 задеплоєно, але наскрізно в живому Telegram ще не
  підтверджено самим водієм — і сам обліковий запис того водія в
  поточній БД не знайдено, див. запис вище; можливо доведеться
  зареєструвати заново).
- При будь-якому наступному великому переписуванні `App.tsx` у
  `vehicle_cost_tracker` — звірити, що маршрут `/driver-app` і
  `src/api/cars.ts` не зникли знову (вже двічі губили, див.
  `TELEGRAM_BOT_SETUP.md` і коментар `⚠️ НЕ ВИДАЛЯТИ` в `App.tsx`).
- ~~Набрати руками код `Фази 11`~~ — зроблено 19.08 (моделі, admin,
  serializers, views, urls; `config/urls.py` підключено; всі баги з
  рев'ю виправлено, `manage.py check`/`runserver` чисті). Не
  перевірено ще: реальний `POST`/`attach_waybill`/матчинг по ТТН від
  залогиненого користувача (поки що тестували лише анонімний `GET`
  → `403`) — варто прогнати хоча б раз через залогинену сесію
  (Django Admin session або DRF browsable API), перш ніж вважати
  Фазу 11 остаточно готовою.
- `apps/analytics` лишається порожнім навмисно — це `Sum()`/`annotate()`
  над уже наявними даними, писати варіант має сенс під конкретні
  дашборди фронтенду, коли в БД накопичиться реальна історія
  (пов'язано з Кроком 14 нижче).
- ~~Крок 11 — management command імпорту з 1С~~ — застаріло: замість
  CLI-команди зробили upload-ендпоінт + форму на фронтенді (менеджер
  сам вивантажує файл щотижня, §1 `IMPORT_1C_SPEC.md`). Гайд написано
  як `Фазу 12` (Кроки 16.1-16.8) 2026-08-30, деталі — у записі вище.
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
