#!/bin/sh
# Щоденний дамп бази vehicle_tracker на хості rubin; зберігає останні 14 копій.
# Копія на тому самому хості не захищає від його втрати, тому дамп потрібно
# ще й забирати поза хост (крок 9 у deploy/DEPLOY_RUBIN_HOST.md).
set -eu

BACKUP_DIR="${BACKUP_DIR:-/opt/vehicle_tracker_backups}"
KEEP="${KEEP:-14}"
PG_CONTAINER="${PG_CONTAINER:-rubin-postgres-container}"
STAMP="$(date +%Y-%m-%d_%H%M)"
TARGET="$BACKUP_DIR/vehicle_tracker_$STAMP.dump"

mkdir -p "$BACKUP_DIR"
docker exec "$PG_CONTAINER" sh -c \
    'pg_dump -U "$POSTGRES_USER" -d vehicle_tracker -Fc' > "$TARGET.tmp"

# Порожній або битий дамп не повинен витіснити робочі копії
docker exec -i "$PG_CONTAINER" pg_restore --list < "$TARGET.tmp" > /dev/null
mv "$TARGET.tmp" "$TARGET"
ln -sf "$TARGET" "$BACKUP_DIR/latest.dump"

ls -1t "$BACKUP_DIR"/vehicle_tracker_*.dump | tail -n +"$((KEEP + 1))" | xargs -r rm -f
echo "$STAMP OK $(du -h "$TARGET" | cut -f1)"
