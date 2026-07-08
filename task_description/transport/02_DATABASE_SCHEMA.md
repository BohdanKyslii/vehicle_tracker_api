# Vehicle Cost Tracker — Схема бази даних (PostgreSQL)

---

## Діаграма зв'язків

```
product_categories      (1) ──< (N) products
products                (1) ──< (1) product_logistics
products                (1) ──< (N) waybill_records
customers               (1) ──< (N) stores
stores                  (1) ──< (N) store_delivery_addresses
stores                  (1) ──< (N) waybill_records
customers               (1) ──< (N) waybill_records
cars                    (1) ──< (N) route_events
cars                    (1) ──< (N) monthly_costs
drivers                 (1) ──< (N) route_events
route_events            (N) >── (1) waybill_records     [waybill_number]
hired_transport_trips   (1) ──< (N) hired_trip_waybills [waybill_number]
carrier_shipments       (1) ──< (N) carrier_costs
carrier_shipments       (1) ──< (N) carrier_waybills    [waybill_number]

Канал доставки накладної (ексклюзивний):
  waybill_records.delivery_channel IN ('own', 'hired', 'carrier', NULL)
```

---

## Довідники

### `product_categories`

```sql
CREATE TABLE product_categories (
    id_category   SERIAL       PRIMARY KEY,
    name_category VARCHAR(150) NOT NULL UNIQUE
);
```

### `products`

```sql
CREATE TABLE products (
    id_product   VARCHAR(50)  PRIMARY KEY,
    name_product VARCHAR(255) NOT NULL,
    id_category  INTEGER      REFERENCES product_categories(id_category)
                              ON DELETE SET NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products (id_category);
```

### `product_logistics`

```sql
CREATE TABLE product_logistics (
    id_product      VARCHAR(50) PRIMARY KEY
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
    -- розрахункові об'єми (generated columns)
    unit_volume_cbm NUMERIC(10,6) GENERATED ALWAYS AS (
        (unit_length_cm * unit_width_cm * unit_height_cm) / 1000000.0
    ) STORED,
    box_volume_cbm  NUMERIC(10,6) GENERATED ALWAYS AS (
        (box_length_cm * box_width_cm * box_height_cm) / 1000000.0
    ) STORED,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `customers`

```sql
CREATE TABLE customers (
    id_customer      VARCHAR(50)  PRIMARY KEY,
    name_customer    VARCHAR(255) NOT NULL,
    network_customer VARCHAR(150),
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### `stores` — Торгові точки / магазини клієнта

```sql
CREATE TABLE stores (
    id_store       VARCHAR(50)  PRIMARY KEY,
    id_customer    VARCHAR(50)  NOT NULL
                   REFERENCES customers(id_customer) ON DELETE RESTRICT,
    name_store     VARCHAR(255) NOT NULL,
    store_address  VARCHAR(500),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stores_customer ON stores (id_customer);

COMMENT ON TABLE stores IS
    'Торгові точки / магазини клієнта. Один клієнт — багато торгових точок.';
```

### `store_delivery_addresses` — Додаткові адреси доставки

```sql
CREATE TABLE store_delivery_addresses (
    id               SERIAL       PRIMARY KEY,
    id_store         VARCHAR(50)  NOT NULL
                     REFERENCES stores(id_store) ON DELETE CASCADE,
    delivery_address VARCHAR(500) NOT NULL,
    is_primary       BOOLEAN      NOT NULL DEFAULT FALSE,
    notes            TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sda_store ON store_delivery_addresses (id_store);

COMMENT ON TABLE store_delivery_addresses IS
    'Одна торгова точка може мати кілька адрес доставки.';
```

---

## Власний автопарк

### `cars` — Авто власного автопарку

```sql
CREATE TABLE cars (
    id_car                SERIAL       PRIMARY KEY,
    name_car              VARCHAR(100) NOT NULL,
    number_car            VARCHAR(20)  NOT NULL UNIQUE,
    amount_car            NUMERIC(12,2) NOT NULL DEFAULT 0,
    default_tracking_mode VARCHAR(10)  NOT NULL DEFAULT 'daily'
                          CHECK (default_tracking_mode IN ('daily', 'full')),
    status_car            VARCHAR(20)  NOT NULL DEFAULT 'active'
                          CHECK (status_car IN ('active', 'repair', 'inactive')),
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN cars.amount_car IS
    'Амортизація авто (грн/міс) — стала величина, логіст може коригувати';
COMMENT ON COLUMN cars.default_tracking_mode IS
    'Дефолтний режим трекінгу, що задає логіст. Водій може змінити на поточний день.';
```

### `drivers` — Водії

```sql
CREATE TABLE drivers (
    id_driver  SERIAL       PRIMARY KEY,
    name_driver VARCHAR(150) NOT NULL,
    phone       VARCHAR(20),
    id_car      INTEGER      REFERENCES cars(id_car) ON DELETE SET NULL,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drivers_car ON drivers (id_car);

COMMENT ON COLUMN drivers.id_car IS 'Поточне закріплене авто';
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
    customer_id      VARCHAR(50)   REFERENCES customers(id_customer) ON DELETE SET NULL,
    customer_name    VARCHAR(255)  NOT NULL,
    store_id         VARCHAR(50)   REFERENCES stores(id_store) ON DELETE SET NULL,
    product_id       VARCHAR(50)   REFERENCES products(id_product) ON DELETE SET NULL,
    product_name     VARCHAR(255)  NOT NULL,
    -- quantity: + відвантаження, - повернення
    quantity         NUMERIC(10,3) NOT NULL,
    price_uah        NUMERIC(12,2) NOT NULL,
    total_uah        NUMERIC(14,2) NOT NULL,
    comment          TEXT,
    -- логістика (з product_logistics при імпорті)
    total_weight_kg       NUMERIC(12,3),
    total_volume_cbm      NUMERIC(12,6),
    volumetric_weight_kg  NUMERIC(12,3),
    -- канал доставки (NULL = ще не призначено)
    delivery_channel  delivery_channel,
    -- службові
    imported_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    import_batch_id   VARCHAR(50),

    UNIQUE (waybill_number, line_position)
);

CREATE INDEX idx_wr_date          ON waybill_records (waybill_date);
CREATE INDEX idx_wr_number        ON waybill_records (waybill_number);
CREATE INDEX idx_wr_customer      ON waybill_records (customer_id);
CREATE INDEX idx_wr_store         ON waybill_records (store_id);
CREATE INDEX idx_wr_product       ON waybill_records (product_id);
CREATE INDEX idx_wr_legal         ON waybill_records (legal_entity);
CREATE INDEX idx_wr_channel       ON waybill_records (delivery_channel);
-- Партіальні індекси
CREATE INDEX idx_wr_returns       ON waybill_records (waybill_number)
    WHERE quantity < 0;
CREATE INDEX idx_wr_unassigned    ON waybill_records (waybill_date)
    WHERE delivery_channel IS NULL;

COMMENT ON COLUMN waybill_records.quantity IS
    'Додатнє — відвантаження; від''ємне — повернення';
COMMENT ON COLUMN waybill_records.delivery_channel IS
    'Канал доставки: own=власне авто, hired=найманий транспорт, carrier=служба доставки.
     NULL = ще не призначено. Унікальність каналу забезпечується на рівні app-логіки.';
```

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
    car_id           INTEGER          NOT NULL REFERENCES cars(id_car),
    driver_id        INTEGER          NOT NULL REFERENCES drivers(id_driver),
    tracking_mode    VARCHAR(10)      NOT NULL CHECK (tracking_mode IN ('daily', 'full')),
    event_type       route_event_type NOT NULL,
    event_ts         TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    odometer_km      INTEGER,
    -- кількість палет (depot_start daily / delivery full)
    pallets_count    SMALLINT,

    -- для delivery
    waybill_number   VARCHAR(50),
    waybill_date     DATE,
    customer_name    VARCHAR(255),

    -- відмова від поставки (delivery, full)
    rejection_full       BOOLEAN,
    rejection_product_id VARCHAR(50),
    rejection_qty        NUMERIC(10,3),
    rejection_comment    TEXT,

    -- для refuel
    fuel_liters      NUMERIC(8,2),
    fuel_cost_uah    NUMERIC(10,2),
    ad_blue_liters   NUMERIC(8,2),
    ad_blue_cost_uah NUMERIC(10,2),

    -- для other_cost
    other_costs_uah     NUMERIC(10,2),
    other_costs_comment TEXT,

    -- для return_goods
    return_client_waybill VARCHAR(50),

    -- для extra_cargo
    extra_from       VARCHAR(255),
    extra_to         VARCHAR(255),
    extra_weight_kg  NUMERIC(10,3),
    extra_waybill    VARCHAR(50),
    extra_comment    TEXT,

    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_re_car_ts   ON route_events (car_id, event_ts);
CREATE INDEX idx_re_date     ON route_events (DATE(event_ts));
CREATE INDEX idx_re_waybill  ON route_events (waybill_number)
    WHERE waybill_number IS NOT NULL;
CREATE INDEX idx_re_type     ON route_events (event_type);

COMMENT ON COLUMN route_events.pallets_count IS
    'Кількість палет: для daily — на весь день; для full — на точку вивантаження';
COMMENT ON COLUMN route_events.tracking_mode IS
    'Режим, обраний водієм на поточний день (може відрізнятись від cars.default_tracking_mode)';
```

### `monthly_costs` — Місячні витрати по авто

```sql
CREATE TABLE monthly_costs (
    id                   SERIAL        PRIMARY KEY,
    car_id               INTEGER       NOT NULL REFERENCES cars(id_car),
    month                DATE          NOT NULL,
    salary_uah           NUMERIC(10,2) NOT NULL DEFAULT 0,
    taxes_uah            NUMERIC(10,2) NOT NULL DEFAULT 0,
    depreciation_uah     NUMERIC(10,2) NOT NULL DEFAULT 0,
    repair_actual_uah    NUMERIC(10,2),
    repair_rate_uah_km   NUMERIC(6,2)  NOT NULL DEFAULT 2.00,
    other_costs_uah      NUMERIC(10,2) NOT NULL DEFAULT 0,
    other_costs_comment  TEXT,
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
    car_number     VARCHAR(30)   NOT NULL,   -- вільний ввід
    route_name     VARCHAR(255)  NOT NULL,   -- «Пирятин, Полтава, Харків»
    trip_date      DATE          NOT NULL,
    pallets_count  SMALLINT,
    cost_uah       NUMERIC(12,2) NOT NULL,
    comment        TEXT,
    created_by     INTEGER,                  -- id логіста (майбутнє)
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_htt_date       ON hired_transport_trips (trip_date);
CREATE INDEX idx_htt_car_number ON hired_transport_trips (car_number);

COMMENT ON TABLE hired_transport_trips IS
    'Рейси найманого транспорту. Авто вводиться вільним текстом (не з довідника).';
COMMENT ON COLUMN hired_transport_trips.route_name IS
    'Довільна назва маршруту, напр. "Пирятин, Полтава, Харків"';
```

### `hired_trip_waybills` — Прив'язка накладних до рейсу найманого транспорту

```sql
CREATE TABLE hired_trip_waybills (
    id             SERIAL        PRIMARY KEY,
    trip_id        INTEGER       NOT NULL
                   REFERENCES hired_transport_trips(id) ON DELETE CASCADE,
    waybill_number VARCHAR(50)   NOT NULL,
    scanned_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    UNIQUE (waybill_number)  -- накладна може бути тільки в одному рейсі
);

CREATE INDEX idx_htw_trip    ON hired_trip_waybills (trip_id);
CREATE INDEX idx_htw_waybill ON hired_trip_waybills (waybill_number);

COMMENT ON COLUMN hired_trip_waybills.waybill_number IS
    'UNIQUE: накладна може бути призначена тільки до одного рейсу.
     Додатково перевіряємо, що waybill_records.delivery_channel IS NULL перед вставкою.';
```

---

## Служби доставки

### `carrier_shipments` — Відправлення через службу доставки

```sql
CREATE TABLE carrier_shipments (
    id               SERIAL        PRIMARY KEY,
    carrier_name     VARCHAR(100)  NOT NULL,  -- «Нова Пошта», «Міст Експрес»
    ttn              VARCHAR(100)  NOT NULL,  -- номер ТТН у службі
    shipment_date    DATE          NOT NULL,
    comment          TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    UNIQUE (carrier_name, ttn)
);

CREATE INDEX idx_cs_date    ON carrier_shipments (shipment_date);
CREATE INDEX idx_cs_carrier ON carrier_shipments (carrier_name);
```

### `carrier_waybills` — Прив'язка накладних до відправлення

```sql
CREATE TABLE carrier_waybills (
    id               SERIAL      PRIMARY KEY,
    shipment_id      INTEGER     NOT NULL
                     REFERENCES carrier_shipments(id) ON DELETE CASCADE,
    waybill_number   VARCHAR(50) NOT NULL,
    scanned_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (waybill_number)  -- накладна тільки в одній службі
);

CREATE INDEX idx_cw_shipment ON carrier_waybills (shipment_id);
CREATE INDEX idx_cw_waybill  ON carrier_waybills (waybill_number);
```

### `carrier_costs` — Реєстр витрат від служб доставки

```sql
CREATE TABLE carrier_costs (
    id              BIGSERIAL     PRIMARY KEY,
    shipment_id     INTEGER       REFERENCES carrier_shipments(id) ON DELETE SET NULL,
    carrier_name    VARCHAR(100)  NOT NULL,
    ttn             VARCHAR(100)  NOT NULL,
    cost_date       DATE          NOT NULL,
    weight_kg       NUMERIC(10,3),
    cost_uah        NUMERIC(12,2) NOT NULL,
    -- службові
    import_batch_id VARCHAR(50),
    imported_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cc_ttn     ON carrier_costs (carrier_name, ttn);
CREATE INDEX idx_cc_date    ON carrier_costs (cost_date);

COMMENT ON TABLE carrier_costs IS
    'Реєстр витрат, імпортований від служби доставки.
     Матчиться з carrier_shipments по (carrier_name, ttn).';
```

---

## VIEWs

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
