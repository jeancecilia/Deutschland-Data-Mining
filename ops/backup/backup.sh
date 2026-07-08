#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_DIR="$ROOT_DIR/backups/$STAMP"
POSTGRES_USER="${POSTGRES_USER:-kdp}"
POSTGRES_DB="${POSTGRES_DB:-kdp_pipeline}"

mkdir -p "$TARGET_DIR"

docker compose --project-directory "$ROOT_DIR" exec -T postgres sh -c \
  "pg_dump -U '$POSTGRES_USER' '$POSTGRES_DB'" > "$TARGET_DIR/postgres.sql"

docker compose --project-directory "$ROOT_DIR" exec -T postgres sh -c \
  "tar czf - -C /var/lib/postgresql/data ." > "$TARGET_DIR/postgres_data.tar.gz"

docker compose --project-directory "$ROOT_DIR" exec -T redis sh -c \
  "tar czf - -C /data ." > "$TARGET_DIR/redis_data.tar.gz"

if [ -d "$ROOT_DIR/backend/generated_reports" ]; then
  tar czf "$TARGET_DIR/generated_reports.tar.gz" -C "$ROOT_DIR/backend" generated_reports
fi

if [ -n "${BACKUP_EXTERNAL_DIR:-}" ]; then
  mkdir -p "$BACKUP_EXTERNAL_DIR"
  cp -R "$TARGET_DIR" "$BACKUP_EXTERNAL_DIR/"
fi

printf 'Backup written to %s\n' "$TARGET_DIR"
