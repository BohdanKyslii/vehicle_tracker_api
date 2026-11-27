-- Окрема база і окремий користувач vehicle tracker у rubin-postgres-container.
-- Запускати від адміна кластера, команда є у deploy/DEPLOY_RUBIN_HOST.md.
-- Пароль передається змінною psql vehicle_pw.
-- Бази rubin_wine, reports і metabase цей скрипт не змінює.

CREATE ROLE vehicle_app LOGIN PASSWORD :'vehicle_pw' NOSUPERUSER NOCREATEDB NOCREATEROLE;

CREATE DATABASE vehicle_tracker OWNER vehicle_app ENCODING 'UTF8' TEMPLATE template0;

REVOKE ALL ON DATABASE vehicle_tracker FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE vehicle_tracker TO vehicle_app;
