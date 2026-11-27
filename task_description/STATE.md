# STATE.md — Стан проекту (Vehicle Cost Tracker, backend)

> Оновлюється після кожної значущої сесії. Детальна історія — `CHANGES.md`.

**Останнє оновлення:** 2026-11-27 (перенос на rubin)

> **Спершу прочитай це.** З 2026-11-27 прод `warehouse.mom` працює на хості
> rubin (Docker: `vehicle-api`, `vehicle-bot`, `vehicle-ui` у мережі `shared_net`,
> БД `vehicle_tracker` у `rubin-postgres-container`, nginx — у репозиторії
> `rubin_wine`). Деплой — push у `main` → GitHub Actions. Інструкція й відкат —
> `deploy/DEPLOY_RUBIN_HOST.md`. Згадки про Raspberry Pi нижче описують старий стан.

---

## Поточна фаза

Backend (`vehicle_tracker_api`, Django/DRF) розгорнутий на хості rubin
(Docker Compose, сервіси `api` + `bot`, мережа `shared_net`, Postgres у
`rubin-postgres-container`; до 10.2026 — Raspberry Pi). Фронтенд — окремий репозиторій
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
- **2026-09-06 (наведення ладу в репозиторії):** git тягнув у прод
  зайве: `task_description/file_1C/` (сирі зразки з 1С, 7.7MB, ніколи
  не мав бути в git — не трекався, просто прибраний з диска),
  `task_description/task_description/ruff_check.md` (дублюючий вкладений
  каталог) і `mentor_summary_draft.md` (чернетка для ментора) видалено
  остаточно; `TELEGRAM_BOT_SETUP.md` і весь `task_description/warehouse/`
  (окремий непов'язаний застосунок) прибрано з git (`git rm --cached`) і
  додано в `.gitignore`, але лишено на диску. Заразом виправлено сам
  `.gitignore` — рядок `task_description/` знято (він не діяв на вже
  затрекані файли, але тихо виключав би з git будь-які НОВІ файли в
  цій директорії, а саме туди ця сесія вносить правки) і замінено
  точковими правилами; знято й застарілий рядок `DJANGO_CODING_GUIDE.md`
  (файл активно трекається). Побічно знайдено й виправлено: корінний
  `readme.md` існував порожнім (0 байт, трекався в нижньому регістрі) —
  перейменовано в `README.md` і заповнено реальним змістом (стек,
  посилання на документацію, локальний/прод запуск).
  `task_description/CLAUDE.md` описував ФРОНТЕНД-стек
  (React/Vite/Tailwind) у бекенд-репозиторії (copy-paste з іншого репо)
  — переписано під Django/DRF. `task_description/TASK.md` і
  `TASK_template.md` були шаблонами чужого старого проєкту (CBV,
  Bootstrap5, django-crispy-forms, django-filter, apps
  `transport/warehouse/shipment`) — переписано під реальний
  ViewSet/serializer-патерн і реальні apps. `DJANGO_CODING_GUIDE.md`
  отримав клікабельний зміст (якорі `#faza-N` на всі 12+1 фаз) і нову
  `Фазу 13` — раніше зовсім не задокументований Admin API для `/panel`
  (`AdminUserViewSet`, `IsHeadOnly`, комміт `507f70c`); розділ "Що
  далі" виправлено — Docker/CI-CD там значились як майбутні кроки, хоча
  реально вже задеплоєні (`Dockerfile`, `docker-compose.yml`,
  `.github/workflows/deploy.yml`). Історію git не переписували
  (`filter-repo`/force-push) — секретів у видалених з трекання файлах
  не знайдено, лише зупинили подальше трекання.

- **2026-09-17 … 09-25 (поза гайдом, напряму в коді):** реєстр
  накладних по номеру — `WaybillRecord` отримав `assigned_car`/
  `hired_car_number`/`carrier_ttn`; ендпоінти `GET /waybill-records/summary/`
  (агрегація по накладній, `shipped_qty`, вага/об'єм з `ProductLogistics`
  під час запиту — `total_weight_kg` у записі завжди `null`),
  `by-number/<n>/`, `by-number/<n>/assign-channel/`. Автолінк сканів
  водія → канал `own` в обидва боки (імпорт після скану й скан після
  імпорту, `link_waybill_to_own_channel`). `MonthlyCosts` +
  `fuel_cost_uah`/`fuel_liters`. `GET /products/delivered_in_month/`.
  Разові ендпоінти (`backfill_own_channel` — 129 накладних / 1245
  рядків, `missing_logistics_for_own`, `bulk_import_logistics` — 160
  товарів) відпрацювали й видалені.
- **2026-09-28:** локальний бекенд переведено на локальну Postgres
  (знімок проду), dev-сервер — порт **8001** (8000 зайнятий
  `rubin_project`, див. `AGENTS_GLOBAL.md` §2).
- **2026-10-04 … 10-05:** служби доставки —
  `CarrierShipmentWaybill.waybill_number` більше не глобально
  унікальний (одна накладна в ТТН посилки й у ТТН зворотної доставки,
  unique тепер `(shipment, waybill_number)`); `bulk_import` для
  відправлень і для витрат (ідемпотентні); `GET /carrier-shipments/review/`;
  `detach_waybill`; витрати, що прийшли раніше за відправлення, тепер
  підхоплюються при його створенні. Виправлено баг ексклюзивності
  каналів: накладні з `delivery_channel=NULL` вважались "іншим каналом",
  тому `attach_waybill` падав для кожної нерозподіленої накладної
  (і carrier, і hired).
- **Жовтень–листопад 2026: Raspberry Pi зламався.** Прод
  `warehouse.mom` не працює, дані проду втрачено. Єдина копія — локальна
  БД `vehicle_tracker` (знімок проду 2026-09-28 + локальний імпорт
  перевізників 2026-10-04); локальні дампи від 2026-11-14 лежать у
  `task_description/dump-vehicle_tracker-*.sql` (не в git). Перенесення
  на хост rubin підготовлено 2026-11-06 у гілці `feat/deploy-rubin-host`
  обох репо (образ збирає GitHub Actions, БД у
  `rubin-postgres-container`, деплой вмикається `DEPLOY_ENABLED`),
  інструкція — `deploy/DEPLOY_RUBIN_HOST.md` у тій гілці. Ще не виконано.
- **2026-11-27:** оновлено `README.md`, `ROADMAP.md` (був застиглий на
  2026-08-04), цей файл. `.gitignore` доповнено дампами БД, зразками
  файлів з 1С, кешами; додано `.dockerignore` (ідентичний гілці
  `feat/deploy-rubin-host`) — документація й `task_description/` не
  потрапляють в образ.

- **2026-11-27: прод перенесено на хост rubin.** Гілку
  `feat/deploy-rubin-host` злито в `main` обох репо. БД відновлено зі
  свіжого дампу локальної БД (30 таблиць, кількості рядків збіглися,
  sequences в порядку). Новий токен бота, SMTP-пошта, сертифікат Let's
  Encrypt (`warehouse.mom` + `www`, до 2027-02-25, продовжує
  `renew-ssl.sh` хоста). Nginx — MR !274 у `rubin_wine`. Ліміт пам'яті
  бота піднято до 256m (займав 169 з 192 МБ). Бекап: cron на хості щодня
  02:15 (`deploy/backup_db.sh`, 14 копій у `/opt/vehicle_tracker_backups`,
  тестове відновлення пройшло) + завдання Windows `VehicleTrackerBackup`
  о 09:30 забирає `latest.dump` на ПК розробника. Дані: знімок проду
  2026-09-28 + імпорт перевізників 2026-10-04 — новіше треба дозалити.

## Наступні кроки

- 🔴 **Завершити перенос** (кроки 6, 10, 11 `deploy/DEPLOY_RUBIN_HOST.md`):
  змінити паролі всіх акаунтів; перевірити вхід, Mini App з реальним
  водієм (URL у `@BotFather`), імпорт файлу; прибрати старий тунель
  Cloudflare і запис `ssh.warehouse.mom`, секрет `PI_SSH_KEY`.
- Дозалити дані після 2026-09-28: накладні 1С після 08.09.2026,
  відправлення перевізників після 30.09.2026, витрати НП.
- Відкладено (коли буде час): скринька `@warehouse.mom` на cPanel — окрема
  зміна DNS (MX і `mail` зараз ведуть на хост rubin, де пошти немає).
  Деталі — `vehicle_cost_tracker/obsidian/tasks.md`. Листи застосунку від
  цього не залежать.
- Прибрати локальне сміття, яке лишилось untracked (не в git, але
  заважає): `apps/cars/migrations/0006_*.py` (самоописаний no-op,
  "варто видалити вручну"), `apps/customers/migrations/0002_*.py` і
  `apps/products/migrations/0002_*.py` (лише порожні `AlterField` від
  розбіжності версій Django, 2026-09-17), файл
  `python.exe manage.py check` у корені (збережений вивід `git diff`).
  Перед видаленням міграцій перевірити, чи не записані вони в
  `django_migrations` локальної БД.
- Аналітика по найманому транспорту / компаніях / категоріях /
  товарах / клієнтах і матчинг повернень — фронтенд має заглушки
  (`ROADMAP.md`).
- Наповнення `ProductLogistics` (вага/габарити) — від нього залежать
  вага/об'єм у `summary` і грн/кг в аналітиці (поки це нижня межа).
- Новий ЄСП/ОПТ `.xls`-зразок класти поза git (`.gitignore` уже
  покриває `task_description/**/*.xls`).
- При великому переписуванні `App.tsx` у `vehicle_cost_tracker` —
  звірити, що маршрут `/driver-app` і `src/api/cars.ts` не зникли
  (двічі губили, коментар `⚠️ НЕ ВИДАЛЯТИ`).

## Відомі блокери

- Немає. Обережно з деплоєм `rubin_wine`: він робить `docker compose down`
  і на кілька хвилин зупиняє Postgres, тобто й API vehicle tracker.
