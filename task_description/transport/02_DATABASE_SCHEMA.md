# Vehicle Cost Tracker — Схема бази даних (PostgreSQL)

> **Оновлено 2026-08-24.** Ця версія звірена з реальними Django-моделями
> (`apps/cars`, `apps/products`, `apps/customers`, `apps/waybills`,
> `apps/logistics`, `apps/accounts`), а не лише з початковим планом.
> DDL нижче — це не буквальні `CREATE TABLE`, які виконував хтось
> вручну (таблиці створені через Django-міграції), а SQL-еквівалент
> реальної схеми, зручний для читання цілісної картини БД. Розбіжності
> з первинним планом позначені `>` цитатами.

---

## Діаграма зв'язків

```
product_categories      (1) ──< (N) product_categories  [self: parent/children]
product_categories      (1) ──< (N) products
products                (1) ──< (1) product_logistics
products                (1) ──< (N) waybill_records
customers               (1) ──< (N) stores
stores                  (1) ──< (N) store_delivery_addresses
stores                  (1) ──< (N) waybill_records
customers               (1) ──< (N) waybill_records
cars                     (1) ──< (1) car_specs
cars                     (1) ──< (1) trailers            [лише якщо car_specs.has_trailer]
cars                     (1) ──< (N) car_status_logs
cars                     (1) ──< (N) route_events
cars                     (1) ──< (N) monthly_costs
cars                     (1) ──< (1) drivers             [OneToOne, поточне закріплення]
drivers                 (1) ──< (N) route_events
drivers                 (1) ──< (1) profiles             [Telegram/веб-акаунт водія]
route_events            (N) >── (1) waybill_records      [waybill_number, "м'який" зв'язок — не FK]
hired_transport_trips   (1) ──< (N) hired_trip_waybills  [waybill_number]
carrier_shipments       (1) ──< (N) carrier_shipment_waybills [waybill_number]
carrier_shipments       (1) ──< (N) carrier_costs        [матчинг по ttn]

Канал доставки накладної (ексклюзивний):
  waybill_records.delivery_channel IN ('own', 'hired', 'carrier', NULL)
  Ексклюзивність — на рівні app-логіки (views), НЕ БД-constraint:
  unique=True на waybill_number у hired_trip_waybills/carrier_shipment_waybills
  + явна перевірка delivery_channel перед призначенням.
```

---

## Довідники

### `product_categories`

> Реалізовано з ієрархією (не було в первинному плані): `parent` —
> self-FK, `on_delete=SET_NULL`. Коренева категорія — `parent IS NULL`.

```sql
CREATE TABLE product_categories (
    id            SERIAL       PRIMARY KEY,
    name_category VARCHAR(150) NOT NULL UNIQUE,
    parent_id     INTEGER      REFERENCES product_categories(id) ON DELETE SET NULL,
    description   TEXT         NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pc_parent ON product_categories (parent_id);
```

### `products`

> `id_product` — `IntegerField PRIMARY KEY` (артикул із 1С як число),
> **не `VARCHAR`**, як планувалось спочатку.

```sql
CREATE TABLE products (
    id_product   INTEGER      PRIMARY KEY,
    name_product VARCHAR(255) NOT NULL,
    category_id  INTEGER      REFERENCES product_categories(id)
                              ON DELETE SET NULL DEFAULT 15,  -- "Інше"
    description  TEXT         NOT NULL DEFAULT '',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products (category_id);
```

### `product_logistics`

> Розрахункові поля (`unit_volume_cbm`, `box_volume_cbm`,
> `calculated_box_weight_kg`) реалізовані як Python `@property` на
> моделі, **не** як PostgreSQL `GENERATED ALWAYS AS ... STORED` колонки,
> як планувалось спочатку — рахуються на боці Django, не в БД.

```sql
CREATE TABLE product_logistics (
    product_id      INTEGER PRIMARY KEY
                    REFERENCES products(id_product) ON DELETE CASCADE,
    unit_weight_kg  NUMERIC(8,3),
    unit_length_cm  NUMERIC(8,2),
    unit_width_cm   NUMERIC(8,2),
    unit_height_cm  NUMERIC(8,2),
    units_per_box   SMALLINT,
    box_weight_kg   NUMERIC(8,3),
    box_length_cm   NUMERIC(8,2),
    box_width_cm    NUMERIC(8,2),
    box_height_cm   NUMERIC(8,2),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- unit_volume_cbm / box_volume_cbm / calculated_box_weight_kg —
    -- НЕ зберігаються в БД, обчислюються @property на моделі при читанні
);
```

### `customers`

> `id_customer` — `IntegerField PRIMARY KEY`, не `VARCHAR`.

```sql
CREATE TABLE customers (
    id_customer      INTEGER      PRIMARY KEY,
    name_customer    VARCHAR(255) NOT NULL,
    network_customer VARCHAR(150) NOT NULL DEFAULT '',
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### `stores` — Торгові точки / магазини клієнта

> `id_store` — `IntegerField PRIMARY KEY`, не `VARCHAR`.
> `customer_id` — `on_delete=RESTRICT` (не можна видалити клієнта, поки
> є магазини).

```sql
CREATE TABLE stores (
    id_store       INTEGER      PRIMARY KEY,
    customer_id    INTEGER      NOT NULL
                   REFERENCES customers(id_customer) ON DELETE RESTRICT,
    name_store     VARCHAR(255) NOT NULL,
    store_address  VARCHAR(500) NOT NULL DEFAULT '',
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stores_customer ON stores (customer_id);
```

### `store_delivery_addresses` — Додаткові адреси доставки

```sql
CREATE TABLE store_delivery_addresses (
    id               SERIAL       PRIMARY KEY,
    store_id         INTEGER      NOT NULL
                     REFERENCES stores(id_store) ON DELETE CASCADE,
    delivery_address VARCHAR(500) NOT NULL,
    is_primary       BOOLEAN      NOT NULL DEFAULT FALSE,
    notes            TEXT         NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sda_store ON store_delivery_addresses (store_id);
```

---

## Власний автопарк

### `cars` — Авто власного автопарку

> PK — стандартний Django `id` (не `id_car`, як у первинному плані).
> Додано `fuel_card_number` (не було в плані).

```sql
CREATE TABLE cars (
    id                     SERIAL       PRIMARY KEY,
    name_car               VARCHAR(100) NOT NULL,
    number_car             VARCHAR(17)  NOT NULL UNIQUE,
    fuel_card_number       BIGINT,
    amount_car             NUMERIC(12,2) NOT NULL DEFAULT 0,
    default_tracking_mode  VARCHAR(10)  NOT NULL DEFAULT 'daily'
                           CHECK (default_tracking_mode IN ('daily', 'full')),
    status_car             VARCHAR(20)  NOT NULL DEFAULT 'active'
                           CHECK (status_car IN ('active', 'repair', 'inactive')),
    is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN cars.amount_car IS
    'Амортизація авто (грн/міс) — стала величина, логіст може коригувати';
```

### `car_specs` — Технічні характеристики авто (1:1)

> Немає в первинному плані — реалізовано в Крок 3.5
> `DJANGO_CODING_GUIDE.md`.

```sql
CREATE TABLE car_specs (
    car_id             INTEGER      PRIMARY KEY REFERENCES cars(id) ON DELETE CASCADE,
    vin_code           VARCHAR(17)  NOT NULL DEFAULT '',
    year_manufactured  SMALLINT,
    weight_kg          NUMERIC(10,2),
    payload_kg         NUMERIC(10,2),
    length_cm          NUMERIC(8,2),
    width_cm           NUMERIC(8,2),
    height_cm          NUMERIC(8,2),
    has_tail_lift      BOOLEAN      NOT NULL DEFAULT FALSE,  -- гідроборт
    has_trailer        BOOLEAN      NOT NULL DEFAULT FALSE
);
```

### `trailers` — Причіп (1:1, тільки якщо `car_specs.has_trailer`)

```sql
CREATE TABLE trailers (
    car_id            INTEGER      PRIMARY KEY REFERENCES cars(id) ON DELETE CASCADE,
    name_trailer      VARCHAR(150) NOT NULL DEFAULT '',
    vin_code          VARCHAR(17)  NOT NULL DEFAULT '',
    model             VARCHAR(100) NOT NULL,
    number_trailer    VARCHAR(20)  NOT NULL UNIQUE,
    year_manufactured SMALLINT,
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE
);
```

### `car_status_logs` — Журнал зміни статусів авто

> Немає в первинному плані. Потрібен для підрахунку днів у ремонті за
> місяць.

```sql
CREATE TABLE car_status_logs (
    id          BIGSERIAL    PRIMARY KEY,
    car_id      INTEGER      NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
    status      VARCHAR(20)  NOT NULL,   -- той самий CHECK, що й cars.status_car
    reason      TEXT         NOT NULL DEFAULT '',
    changed_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    changed_by  INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE INDEX idx_csl_car ON car_status_logs (car_id, changed_at);
```

### `drivers` — Водії

> `car_id` — **`OneToOneField`** (`UNIQUE`), не звичайний FK, як у
> первинному плані: одне авто = один активний водій одночасно на рівні
> БД-constraint, не лише app-логіки.

```sql
CREATE TABLE drivers (
    id               SERIAL       PRIMARY KEY,
    name_driver      VARCHAR(150) NOT NULL,
    phone            VARCHAR(20)  NOT NULL DEFAULT '',
    drivers_license  VARCHAR(50)  NOT NULL DEFAULT '',  -- не було в плані
    car_id           INTEGER      UNIQUE
                     REFERENCES cars(id) ON DELETE SET NULL,
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN drivers.car_id IS
    'Поточне закріплене авто. UNIQUE — одне авто не може мати двох
     активних водіїв одночасно (DB-рівень, не тільки app-логіка).';
```

### `profiles` — Акаунт водія/логіста/менеджера/керівника (авторизація)

> Немає в первинному плані взагалі — весь шар авторизації
> (`apps.accounts`) з'явився пізніше (Фаза 4.5, потім Telegram-бот).
> Не є частиною домену "автопарк", але прив'язана до `drivers`.

```sql
CREATE TYPE profile_role AS ENUM ('driver', 'logist', 'manager', 'head');

CREATE TABLE profiles (
    id           SERIAL       PRIMARY KEY,
    user_id      INTEGER      NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    role         profile_role NOT NULL,
    phone        VARCHAR(17)  NOT NULL DEFAULT '',
    telegram_id  BIGINT       UNIQUE,
    driver_id    INTEGER      UNIQUE REFERENCES drivers(id) ON DELETE SET NULL
);

COMMENT ON COLUMN profiles.driver_id IS
    'Тільки для role=driver — лінк на картку Driver. Реєстрація через
     Telegram-бота створює Driver і лінкує його автоматично (2026-08-16+);
     старіші акаунти могли лінкуватись вручну в Django Admin.';
```

---

## Реєстр накладних

### `waybill_records` — Рядки накладних із 1С

```sql
CREATE TYPE delivery_channel AS ENUM ('own', 'hired', 'carrier');

CREATE TABLE waybill_records (
    id               BIGSERIAL     PRIMARY KEY,
    legal_entity     VARCHAR(10)   NOT NULL
                     CHECK (legal_entity IN ('ESP', 'OPT', 'Rubin')),
    waybill_number   VARCHAR(50)   NOT NULL,
    waybill_date     DATE          NOT NULL,
    line_position    SMALLINT      NOT NULL,
    customer_id      INTEGER       REFERENCES customers(id_customer) ON DELETE SET NULL,
    customer_name    VARCHAR(255)  NOT NULL,   -- копія на момент імпорту
    store_id         INTEGER       REFERENCES stores(id_store) ON DELETE SET NULL,
    product_id       INTEGER       REFERENCES products(id_product) ON DELETE SET NULL,
    product_name     VARCHAR(255)  NOT NULL,   -- копія на момент імпорту
    -- quantity: + відвантаження, - повернення
    quantity         NUMERIC(10,3) NOT NULL,
    price_uah        NUMERIC(12,2) NOT NULL,
    total_uah        NUMERIC(14,2) NOT NULL,
    comment          TEXT          NOT NULL DEFAULT '',
    -- логістика (з product_logistics при імпорті)
    total_weight_kg       NUMERIC(12,3),
    total_volume_cbm      NUMERIC(12,6),
    volumetric_weight_kg  NUMERIC(12,3),
    -- канал доставки (NULL = ще не призначено)
    delivery_channel  delivery_channel,
    -- службові
    imported_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    import_batch_id   VARCHAR(50)  NOT NULL DEFAULT '',

    UNIQUE (waybill_number, line_position)
);

CREATE INDEX idx_wr_date          ON waybill_records (waybill_date);
CREATE INDEX idx_wr_number        ON waybill_records (waybill_number);
CREATE INDEX idx_wr_channel       ON waybill_records (delivery_channel);
-- Реалізовано (Крок 3.6): ordering = ["-waybill_date", "waybill_number"]

COMMENT ON COLUMN waybill_records.quantity IS
    'Додатнє — відвантаження; від''ємне — повернення (підтверджено для
     Rubin; для ESP/OPT — статус з''ясовується, IMPORT_1C_SPEC.md Q7).';
COMMENT ON COLUMN waybill_records.delivery_channel IS
    'Канал доставки: own=власне авто, hired=найманий транспорт, carrier=служба доставки.
     NULL = ще не призначено. Ексклюзивність — на рівні app-логіки (views), не DB-constraint.';
```

> **Крок 11 (імпорт з 1С) ще не реалізований** — модель і API вже є,
> потрібен upload-ендпоінт + парсери під CSV (Rubin) і XLS (ESP/OPT).
> Деталі формату джерел — `task_description/IMPORT_1C_SPEC.md`.

---

## Власний автопарк — трекінг

### `route_events` — Події маршруту

```sql
CREATE TYPE route_event_type AS ENUM (
    'depot_start',   -- ранок, склад              (daily + full)
    'delivery',      -- вивантаження               (тільки full)
    'parking_end',   -- кінець дня, парковка       (тільки full)
    'depot_return',  -- повернення на склад         (тільки full)
    'refuel',        -- заправка                   (daily + full)
    'other_cost',    -- інші витрати               (daily + full)
    'return_goods',  -- повернення товару           (daily + full)
    'extra_cargo'    -- додатковий вантаж           (daily + full)
);

CREATE TABLE route_events (
    id               BIGSERIAL        PRIMARY KEY,
    car_id           INTEGER          NOT NULL REFERENCES cars(id) ON DELETE RESTRICT,
    driver_id        INTEGER          NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT,
    tracking_mode    VARCHAR(10)      NOT NULL CHECK (tracking_mode IN ('daily', 'full')),
    event_type       route_event_type NOT NULL,
    event_ts         TIMESTAMPTZ      NOT NULL,
    odometer_km      INTEGER,
    -- кількість палет (depot_start daily / delivery full)
    pallets_count    SMALLINT,

    -- для delivery
    waybill_number   VARCHAR(50)      NOT NULL DEFAULT '',
    waybill_date     DATE,
    customer_name    VARCHAR(255)     NOT NULL DEFAULT '',

    -- відмова від поставки (delivery, full)
    rejection_full         BOOLEAN,
    rejection_product_id   VARCHAR(50)  NOT NULL DEFAULT '',
    rejection_qty          NUMERIC(10,3),
    rejection_comment      TEXT         NOT NULL DEFAULT '',

    -- для refuel
    fuel_liters      NUMERIC(8,2),
    fuel_cost_uah    NUMERIC(10,2),
    ad_blue_liters   NUMERIC(8,2),
    ad_blue_cost_uah NUMERIC(10,2),

    -- для other_cost
    other_costs_uah     NUMERIC(10,2),
    other_costs_comment TEXT NOT NULL DEFAULT '',

    -- для return_goods
    return_client_waybill VARCHAR(50) NOT NULL DEFAULT '',

    -- для extra_cargo
    extra_from       VARCHAR(255) NOT NULL DEFAULT '',
    extra_to         VARCHAR(255) NOT NULL DEFAULT '',
    extra_weight_kg  NUMERIC(10,3),
    extra_waybill    VARCHAR(50)  NOT NULL DEFAULT '',
    extra_comment    TEXT         NOT NULL DEFAULT '',

    notes            TEXT NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_re_car_ts ON route_events (car_id, event_ts);
CREATE INDEX idx_re_type   ON route_events (event_type);

COMMENT ON COLUMN route_events.pallets_count IS
    'Кількість палет: для daily — на весь день; для full — на точку вивантаження';
```

> `rejection_product_id` посилається на `products.id_product` лише
> текстово (не FK) — реальна модель зберігає його як `CharField`, без
> `REFERENCES`.

### `monthly_costs` — Місячні витрати по авто

```sql
CREATE TABLE monthly_costs (
    id                   SERIAL        PRIMARY KEY,
    car_id               INTEGER       NOT NULL REFERENCES cars(id) ON DELETE RESTRICT,
    month                DATE          NOT NULL,   -- перше число місяця
    salary_uah           NUMERIC(10,2) NOT NULL DEFAULT 0,
    taxes_uah            NUMERIC(10,2) NOT NULL DEFAULT 0,
    depreciation_uah     NUMERIC(10,2) NOT NULL DEFAULT 0,
    repair_actual_uah    NUMERIC(10,2),
    repair_rate_uah_km   NUMERIC(6,2)  NOT NULL DEFAULT 2.00,
    other_costs_uah      NUMERIC(10,2) NOT NULL DEFAULT 0,
    other_costs_comment  TEXT          NOT NULL DEFAULT '',
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    UNIQUE (car_id, month)
);

COMMENT ON COLUMN monthly_costs.repair_actual_uah IS
    'Якщо заповнено — пріоритет над repair_rate_uah_km × km_total';
```

---

## Найманий транспорт

### `hired_transport_trips` — Рейси найманого транспорту

```sql
CREATE TABLE hired_transport_trips (
    id             SERIAL        PRIMARY KEY,
    car_number     VARCHAR(20)   NOT NULL,   -- вільний ввід, не з довідника
    route_name     VARCHAR(255)  NOT NULL,   -- «Пирятин, Полтава, Харків»
    trip_date      DATE          NOT NULL,
    pallets_count  SMALLINT,
    cost_uah       NUMERIC(10,2) NOT NULL,
    comment        TEXT          NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_htt_date ON hired_transport_trips (trip_date);
```

### `hired_trip_waybills` — Прив'язка накладних до рейсу найманого транспорту

```sql
CREATE TABLE hired_trip_waybills (
    id             SERIAL        PRIMARY KEY,
    trip_id        INTEGER       NOT NULL
                   REFERENCES hired_transport_trips(id) ON DELETE CASCADE,
    waybill_number VARCHAR(50)   NOT NULL UNIQUE  -- накладна тільки в одному рейсі
);

CREATE INDEX idx_htw_trip ON hired_trip_waybills (trip_id);
```

---

## Служби доставки

> Первинний план мав окремі поля `carrier_name` (вільний текст) у
> `carrier_shipments`/`carrier_costs`. Реальна реалізація —
> `CarrierShipment.carrier` як `CharField` із `choices`
> (`nova_poshta` / `mist_express` / `other`), не вільний текст.

### `carrier_shipments` — Відправлення через службу доставки

```sql
CREATE TABLE carrier_shipments (
    id             SERIAL        PRIMARY KEY,
    carrier        VARCHAR(20)   NOT NULL
                   CHECK (carrier IN ('nova_poshta', 'mist_express', 'other')),
    ttn            VARCHAR(50)   NOT NULL UNIQUE,
    shipment_date  DATE          NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cs_date ON carrier_shipments (shipment_date);
```

### `carrier_shipment_waybills` — Прив'язка накладних до відправлення

> Первинний план називав цю таблицю `carrier_waybills` — реальна назва
> `carrier_shipment_waybills`.

```sql
CREATE TABLE carrier_shipment_waybills (
    id             SERIAL      PRIMARY KEY,
    shipment_id    INTEGER     NOT NULL
                   REFERENCES carrier_shipments(id) ON DELETE CASCADE,
    waybill_number VARCHAR(50) NOT NULL UNIQUE  -- накладна тільки в одній службі
);

CREATE INDEX idx_csw_shipment ON carrier_shipment_waybills (shipment_id);
```

### `carrier_costs` — Реєстр витрат від служб доставки

```sql
CREATE TABLE carrier_costs (
    id              BIGSERIAL     PRIMARY KEY,
    shipment_id     INTEGER       REFERENCES carrier_shipments(id) ON DELETE SET NULL,
    ttn             VARCHAR(50)   NOT NULL,   -- копія, для матчингу навіть без shipment
    weight_kg       NUMERIC(10,3) NOT NULL,
    cost_uah        NUMERIC(10,2) NOT NULL,
    cost_date       DATE          NOT NULL,
    imported_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cc_ttn ON carrier_costs (ttn);

COMMENT ON TABLE carrier_costs IS
    'Реєстр витрат, імпортований від служби доставки. Матчиться з
     carrier_shipments по ttn при створенні (perform_create), не
     окремим ендпоінтом.';
```

> ⚠️ **Ще не реалізовано в цьому проєкті:** імпорт-ендпоінт для
> `carrier_costs` (щотижневий реєстр витрат від НП/Міст Експрес) —
> модель і `CRUD`-viewset є, парсера/upload-форми немає.

---

## VIEWs

> Нижче — SQL-начерки з первинного плану аналітичних VIEW. **Жодного з
> них не створено в реальній БД** — `apps.analytics` свідомо
> відкладений до накопичення реальних даних (див. `01_PROJECT_OVERVIEW.md`
> §10, п.9). Залишено як орієнтир логіки розрахунку, не як актуальний DDL.

### `daily_summaries`

```sql
-- Підсумок дня з route_events.
-- daily: пробіг = depot_start сьогодні − depot_start вчора.
-- Враховує pallets_count.

CREATE VIEW daily_summaries AS
WITH ordered_starts AS (
    SELECT
        car_id, driver_id, tracking_mode,
        DATE(event_ts)                      AS event_date,
        odometer_km,
        pallets_count,
        LAG(odometer_km) OVER (
            PARTITION BY car_id ORDER BY event_ts
        )                                   AS prev_odometer,
        LAG(DATE(event_ts)) OVER (
            PARTITION BY car_id ORDER BY event_ts
        )                                   AS prev_date
    FROM route_events
    WHERE event_type = 'depot_start'
),
daily_mileage AS (
    SELECT car_id, event_date, tracking_mode,
           odometer_km - prev_odometer      AS mileage_km,
           pallets_count
    FROM ordered_starts
    WHERE prev_date = event_date - INTERVAL '1 day'
)
SELECT
    re.car_id,
    re.driver_id,
    re.tracking_mode,
    re.event_date                           AS date,
    dm.mileage_km                           AS total_mileage_km,
    dm.pallets_count,
    SUM(re.fuel_liters)                     AS fuel_liters,
    SUM(re.fuel_cost_uah)                   AS fuel_cost_uah,
    SUM(re.ad_blue_liters)                  AS ad_blue_liters,
    SUM(re.ad_blue_cost_uah)                AS ad_blue_cost_uah,
    SUM(re.other_costs_uah)                 AS other_costs_uah,
    COUNT(*) FILTER (WHERE re.event_type = 'delivery')     AS deliveries_count,
    COUNT(*) FILTER (WHERE re.event_type = 'return_goods') AS returns_count,
    COUNT(*) FILTER (WHERE re.event_type = 'extra_cargo')  AS extra_cargo_count
FROM (
    SELECT car_id, driver_id, tracking_mode, DATE(event_ts) AS event_date,
           event_type, fuel_liters, fuel_cost_uah,
           ad_blue_liters, ad_blue_cost_uah, other_costs_uah
    FROM route_events
) re
LEFT JOIN daily_mileage dm
    ON dm.car_id = re.car_id AND dm.event_date = re.event_date
GROUP BY re.car_id, re.driver_id, re.tracking_mode, re.event_date,
         dm.mileage_km, dm.pallets_count;
```

### `transport_cost_per_waybill`

```sql
-- Розподіл місячних витрат власного автопарку по накладних.
-- Враховує тільки відвантаження (quantity > 0) і канал 'own'.
-- Пропорція: cost_i = total_monthly × (sale_i / Σ sales авто за місяць).

CREATE VIEW transport_cost_per_waybill AS
WITH monthly_totals AS (
    SELECT re.car_id,
           DATE_TRUNC('month', wr.waybill_date) AS month,
           SUM(wr.total_uah)                    AS total_sales_uah
    FROM waybill_records wr
    JOIN route_events re
        ON re.waybill_number = wr.waybill_number
       AND re.event_type IN ('delivery', 'depot_start')
    WHERE wr.quantity > 0 AND wr.delivery_channel = 'own'
    GROUP BY re.car_id, DATE_TRUNC('month', wr.waybill_date)
),
monthly_expenses AS (
    SELECT mc.car_id, mc.month,
           mc.salary_uah + mc.taxes_uah + mc.depreciation_uah
           + COALESCE(mc.repair_actual_uah,
               mc.repair_rate_uah_km * COALESCE(ds.total_km, 0))
           + mc.other_costs_uah                AS total_cost_uah
    FROM monthly_costs mc
    LEFT JOIN (
        SELECT car_id,
               DATE_TRUNC('month', date)       AS month,
               SUM(total_mileage_km)           AS total_km
        FROM daily_summaries
        GROUP BY car_id, DATE_TRUNC('month', date)
    ) ds ON ds.car_id = mc.car_id AND ds.month = mc.month
)
SELECT
    wr.legal_entity,
    wr.waybill_number,
    wr.waybill_date,
    wr.customer_id,
    wr.customer_name,
    wr.store_id,
    re.car_id,
    SUM(wr.total_uah)                           AS sale_uah,
    SUM(wr.total_weight_kg)                     AS total_weight_kg,
    SUM(wr.total_volume_cbm)                    AS total_volume_cbm,
    me.total_cost_uah
        * (SUM(wr.total_uah) / NULLIF(mt.total_sales_uah, 0))
                                                AS allocated_cost_uah,
    ROUND(
        me.total_cost_uah
        * (SUM(wr.total_uah) / NULLIF(mt.total_sales_uah, 0))
        / NULLIF(SUM(wr.total_uah), 0) * 100, 2
    )                                           AS cost_pct_of_sale
FROM waybill_records wr
JOIN route_events re
    ON re.waybill_number = wr.waybill_number
   AND re.event_type IN ('delivery', 'depot_start')
JOIN monthly_totals mt
    ON mt.car_id = re.car_id
   AND mt.month = DATE_TRUNC('month', wr.waybill_date)
JOIN monthly_expenses me
    ON me.car_id = re.car_id
   AND me.month = DATE_TRUNC('month', wr.waybill_date)
WHERE wr.quantity > 0 AND wr.delivery_channel = 'own'
GROUP BY wr.legal_entity, wr.waybill_number, wr.waybill_date,
         wr.customer_id, wr.customer_name, wr.store_id,
         re.car_id, mt.total_sales_uah, me.total_cost_uah;
```
