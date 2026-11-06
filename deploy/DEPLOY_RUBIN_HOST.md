# Перенесення Vehicle Tracker на хост rubin

Покрокова інструкція для окремої сесії розгортання. Підготовлено 2026-11-06,
на хості станом на цю дату нічого не змінено.

На хості працює прод `rubin_wine` і `reports`. Кожен крок, що змінює хост,
виконувати лише після підтвердження користувача.

## Як усе буде влаштовано

```
браузер -> nginx (контейнер rubin_wine, порти 80/443)
             -> vehicle-ui:8080 (nginx зі статикою фронтенду)
                  -> vehicle-api:8000 (gunicorn, /api, /admin, /static)
                       -> rubin-postgres-container:5432, база vehicle_tracker
           vehicle-bot (long polling, вхідних портів не має)
```

- Усі контейнери в наявній мережі `shared_net`, назовні портів не відкривають.
- Окрема база `vehicle_tracker` і окремий користувач `vehicle_app`.
- Домен працює як `brsm-reports.shop`: A-запис на хост без тунелю, сертифікат
  Let's Encrypt.
- Образи збирає GitHub Actions і завантажує на хост через SSH. На хості їх не
  збирати: вільно лише ~1,3 ГБ пам'яті, а swap уже зайнятий на 1,2 ГБ.

| Каталог на хості | Що там |
|---|---|
| `/opt/vehicle_tracker_api` | клон бекенду, `.env` |
| `/opt/vehicle_cost_tracker` | клон фронтенду |
| `/opt/vehicle_tracker_backups` | щоденні дампи БД |

## Перед стартом: що потрібно від користувача

- Доступ до DNS `warehouse.mom` у Cloudflare.
- Токен бота `@driver_car_bot` у `@BotFather`: копія на Pi втрачена, у локальному
  `.env` його немає. Без токена контейнер `vehicle-bot` перезапускатиметься по колу.
- `TELEGRAM_ADMIN_IDS`: Telegram ID адмінів через кому.
- Доступ до Settings обох репозиторіїв на GitHub.
- Вікно для передеплою `rubin_wine` на кроці 8 у неробочий час.
- Рішення, куди забирати бекапи поза хост (крок 9).

Паролі й токени користувач вводить сам у своєму терміналі, у чат їх не писати.

## Крок 1. Перевірка хоста

```bash
ssh rubin
df -h /; free -h; docker network inspect shared_net --format '{{.Name}}'
docker ps -a --format '{{.Names}}' | grep -E 'vehicle' || echo "імена вільні"
docker exec rubin-postgres-container sh -c \
  'psql -U "$POSTGRES_USER" -d postgres -Atc "select datname from pg_database"'
```

Орієнтири на 2026-11-06: вільно 21 ГБ диска, бази `vehicle_tracker` ще немає.
Якщо вільної пам'яті менше ~500 МБ, спершу розібратись із причиною.

## Крок 2. Злити гілки

Запушити й злити `feat/deploy-rubin-host` у `main` в обох репозиторіях. Деплой
при цьому не запуститься, бо змінної `DEPLOY_ENABLED` ще немає.

## Крок 3. Підготувати каталоги і `.env`

```bash
sudo mkdir -p /opt/vehicle_tracker_api /opt/vehicle_cost_tracker /opt/vehicle_tracker_backups
sudo chown rubin:rubin /opt/vehicle_tracker_api /opt/vehicle_cost_tracker /opt/vehicle_tracker_backups
git clone https://github.com/BohdanKyslii/vehicle_tracker_api.git /opt/vehicle_tracker_api
git clone https://github.com/BohdanKyslii/vehicle_cost_tracker.git /opt/vehicle_cost_tracker

cd /opt/vehicle_tracker_api
cp env.production.example .env && chmod 600 .env
SK=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
PW=$(openssl rand -hex 24)
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SK|; s|^DB_PASSWORD=.*|DB_PASSWORD=$PW|" .env
unset SK PW
```

Токен бота, `TELEGRAM_ADMIN_IDS` і за потреби пошту користувач вносить сам:
`nano /opt/vehicle_tracker_api/.env`. Не копіювати сюди коментарі з локальних `.env`.

## Крок 4. База даних

Створити базу й користувача:

```bash
cd /opt/vehicle_tracker_api
VEHICLE_PW=$(grep '^DB_PASSWORD=' .env | cut -d= -f2)
docker exec -i -e VEHICLE_PW="$VEHICLE_PW" rubin-postgres-container sh -c \
  'psql -q -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -v vehicle_pw="$VEHICLE_PW"' \
  < deploy/db/01_create_db.sql
unset VEHICLE_PW
```

Зняти дамп на ПК (PowerShell, пароль БД запитає сама команда). Дамп містить
хеші паролів, тому в git і чат він не потрапляє:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h localhost -U <DB_USER_з_локального_.env> -d vehicle_tracker -Fc --no-owner --no-acl -f "$env:TEMP\vehicle_tracker.dump"
scp "$env:TEMP\vehicle_tracker.dump" rubin:/tmp/vehicle_tracker.dump
Remove-Item "$env:TEMP\vehicle_tracker.dump"
```

Відновити на хості і видалити дамп:

```bash
docker exec -i rubin-postgres-container \
  pg_restore -h localhost -U vehicle_app -d vehicle_tracker --no-owner --no-acl --exit-on-error \
  < /tmp/vehicle_tracker.dump
rm /tmp/vehicle_tracker.dump
for t in waybill_records carrier_shipments carrier_costs stores products route_events profiles auth_user; do
  echo "$t $(docker exec rubin-postgres-container psql -h localhost -U vehicle_app -d vehicle_tracker -Atc "select count(*) from $t")"
done
```

Кількість рядків має збігатися з локальною БД. На 2026-11-06:

| Таблиця | Рядків |
|---|---|
| `waybill_records` | 4518 |
| `carrier_shipments` | 1033 |
| `carrier_costs` | 1295 |
| `stores` | 2405 |
| `products` | 1119 |
| `route_events` | 151 |
| `profiles` | 9 |
| `auth_user` | 9 |

**Що відомо про дані.** Локальна БД є єдиною копією: це знімок проду на
2026-09-28 плюс локальний імпорт перевізників від 2026-10-04. Усе, що внесли на
проді після знімка, втрачено. Накладні закінчуються 08.09.2026, відправлення
перевізників 30.09.2026.

**Попередження `migrate`.** Під час старту Django пише, що в моделях є зміни без
міграцій. Це відомий шум цього проєкту. У `django_migrations` є три рядки для
міграцій, яких немає в git (`cars 0006`, `customers 0002`, `products 0002`). На
роботу вони не впливають, видаляти їх не треба.

## Крок 5. Налаштувати GitHub Actions і перший запуск

Окремий ключ для деплою (на ПК, поза репозиторіями):

```bash
ssh-keygen -t ed25519 -N "" -C github-vehicle-deploy -f vehicle_deploy_key
ssh rubin 'cat >> ~/.ssh/authorized_keys' < vehicle_deploy_key.pub
ssh-keyscan -t ed25519 rubin.kyiv.ua > vehicle_known_hosts
```

Ключ відкликається видаленням рядка з `authorized_keys`.

В обох репозиторіях, Settings -> Secrets and variables -> Actions:

| Тип | Назва | Значення |
|---|---|---|
| Secret | `DEPLOY_SSH_KEY` | вміст `vehicle_deploy_key` |
| Secret | `DEPLOY_KNOWN_HOSTS` | вміст `vehicle_known_hosts` |
| Variable | `DEPLOY_HOST` | `rubin.kyiv.ua` |
| Variable | `DEPLOY_USER` | `rubin` |
| Variable | `DEPLOY_ENABLED` | `true` |

Після цього видалити локальні `vehicle_deploy_key*` і `vehicle_known_hosts`.
Запустити вручну (Actions -> Run workflow, гілка `main`) спершу **Deploy API**,
потім **Deploy UI**.

Перевірка на хості, ще без домену:

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep vehicle
docker logs --tail 20 vehicle-api
docker logs --tail 20 vehicle-bot
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' vehicle-api vehicle-bot vehicle-ui
free -h
docker exec nginx wget -q -O - --header='Host: warehouse.mom' http://vehicle-ui:8080/api/auth/csrf/
```

Остання команда має повернути JSON. Під час репетиції `vehicle-api` займав ~93 МБ,
`vehicle-ui` ~11 МБ.

## Крок 6. Змінити паролі

У відновленій базі ті самі паролі, що були на Pi. Користувач змінює їх сам:

```bash
docker exec vehicle-api python manage.py shell -c \
  "from django.contrib.auth.models import User; print(list(User.objects.filter(is_superuser=True).values_list('username', flat=True)))"
docker exec -it vehicle-api python manage.py changepassword <логін>
```

Обов'язково для всіх суперкористувачів і тестових акаунтів.

## Крок 7. DNS і сертифікат

У Cloudflare для `warehouse.mom`:

1. Видалити CNAME на старий тунель для `warehouse.mom` і `www`, якщо є.
2. Додати A-записи `@` і `www` на IP хоста (той самий, що в `rubin.kyiv.ua`), режим
   **DNS only** (сіра хмара),
   як у `brsm-reports.shop`.

Коли `nslookup warehouse.mom` покаже IP хоста, спершу пробний запуск:

```bash
docker run --rm \
  -v rubin_wine_certbot-etc:/etc/letsencrypt \
  -v /home/rubin/rubin_wine/certbot-www:/var/www/html \
  certbot/certbot certonly --webroot -w /var/www/html \
  -d warehouse.mom -d www.warehouse.mom \
  --email <email_користувача> --agree-tos --no-eff-email --dry-run
```

Якщо успішно, повторити без `--dry-run`. Змінювати nginx для цього не треба:
порт 80 перенаправляє на `https://rubin.kyiv.ua/.well-known/acme-challenge/...`,
цей шлях віддається з тієї самої теки, а Let's Encrypt проходить за редиректом.
Сам пробний запуск ще не виконувався. Якщо він не пройде, спершу додати в nginx лише
блок `listen 80` із `deploy/nginx/warehouse.conf`, а блок `443` окремим MR.

Якщо запису `www` немає, прибрати `www.warehouse.mom` і з команди, і зі сниппета nginx.

## Крок 8. Nginx у репозиторії rubin_wine

Переконатися, що сертифікат є:

```bash
docker run --rm -v rubin_wine_certbot-etc:/etc/letsencrypt certbot/certbot certificates | grep -A3 warehouse
```

У репозиторії `rubin_wine` від `dev` створити гілку, вставити вміст
`deploy/nginx/warehouse.conf` у блок `http {}` файлу `nginx/nginx.conf`, далі MR
`dev` -> `main`. Правити файл прямо на сервері не можна: незакомічені зміни там уже
ламали деплой.

**Вплив на прод.** Деплой `main` виконує `docker compose down` і `up --build`. На
кілька хвилин зупиняться `rubin_wine`, nginx і Postgres, разом із ними `reports` і
vehicle tracker. Так буде за кожного деплою `rubin_wine`: контейнери vehicle tracker
працюватимуть далі, а API поверне помилки, поки Postgres не підніметься. Планувати
на неробочий час.

## Крок 9. Бекапи

Саме відсутність копій призвела до втрати даних на Pi.

```bash
sh /opt/vehicle_tracker_api/deploy/backup_db.sh
crontab -e
# 15 2 * * * sh /opt/vehicle_tracker_api/deploy/backup_db.sh >> /home/rubin/vehicle_backup.log 2>&1
```

Перевірити відновлення у тимчасову базу:

```bash
docker exec rubin-postgres-container sh -c 'createdb -U "$POSTGRES_USER" vehicle_restore_test'
docker exec -i rubin-postgres-container sh -c 'pg_restore -U "$POSTGRES_USER" -d vehicle_restore_test --no-owner --no-acl' \
  < /opt/vehicle_tracker_backups/latest.dump
docker exec rubin-postgres-container sh -c 'psql -U "$POSTGRES_USER" -d vehicle_restore_test -Atc "select count(*) from waybill_records"'
docker exec rubin-postgres-container sh -c 'dropdb -U "$POSTGRES_USER" vehicle_restore_test'
```

**Копія поза хостом обов'язкова**, бо дамп на тому самому VPS не захищає від втрати
VPS. Найпростіший варіант, якщо користувач не вибере інший: щоденне завдання на ПК.

```powershell
schtasks /Create /SC DAILY /ST 09:30 /TN "VehicleTrackerBackup" /TR "scp rubin:/opt/vehicle_tracker_backups/latest.dump <шлях_на_ПК>\vehicle_tracker_backup_latest.dump"
```

## Крок 10. Фінальна перевірка

- [ ] `https://warehouse.mom` відкривається, сертифікат валідний.
- [ ] Вхід працює, списки накладних, авто й магазинів заповнені.
- [ ] `https://warehouse.mom/admin/` відкривається зі стилями.
- [ ] Mini App у `@driver_car_bot` відкривається, новий водій може подати заявку,
      адмін отримує її в Telegram.
- [ ] Імпорт невеликого файлу проходить.
- [ ] Звичайний push у `main` деплоїться через Actions.
- [ ] `https://rubin.kyiv.ua` і `https://brsm-reports.shop` працюють.

Якщо браузер показує стару версію, причина може бути в кеші PWA: перевірити хеш
JS-файлу, за потреби зняти service worker і почистити кеш. У Telegram Mini App
закрити застосунок повністю.

## Крок 11. Прибрати старе

- Видалити в Cloudflare старий тунель і запис `ssh.warehouse.mom`.
- Видалити секрет `PI_SSH_KEY` в обох репозиторіях.
- Якщо Pi відремонтують, не запускати на ньому `bot` зі старим токеном: Telegram не
  дозволяє двох одночасних отримувачів оновлень.

## Відкат

Сайти `rubin_wine` і `reports` від кроків 1-7 не залежать, тож їх не зачепить:

```bash
cd /opt/vehicle_cost_tracker && docker compose down
cd /opt/vehicle_tracker_api && docker compose down
```

Якщо вже виконано крок 8, спершу відкотити MR у `rubin_wine`. Базу не видаляти без
окремого рішення користувача: зараз це дані, копія яких є лише на ПК.

## Що перевірено і що ні

Репетиція на ПК 2026-11-06, контейнери видалено:

- зібрано обидва образи з цих Dockerfile;
- на Postgres 18 створено базу скриптом, інший користувач не може підключитись;
- дамп локальної БД відновлено, кількість рядків збігається, усі міграції застосовані;
- через nginx зі сниппетом працюють `/`, `/driver`, `/api/auth/csrf/`, `/admin/login/`,
  CSS і JS адмінки; без входу `/api/cars/` повертає 403;
- `backup_db.sh` створює дамп і видаляє старі копії.

Не перевірялось: робота бота (немає токена), випуск сертифіката, запуск workflow на
GitHub, робота на самому хості, сценарії після входу в систему.

## Окремі задачі, не частина переносу

Причину 502 на Pi від 2026-10-05 не встановлено, логи втрачено. На чистій збірці
цього коду API стартує нормально.

Репозиторій публічний, тому зауваження щодо безпеки хоста сюди не записувати:
вони лежать у локальному файлі `DEPLOY_PREP_FOR_ME.md` у теці фронтенду, поза git.
