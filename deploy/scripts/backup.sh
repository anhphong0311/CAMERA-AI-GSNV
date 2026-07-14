#!/usr/bin/env bash
# AEMS Automated Backup (Sprint 11) — Database + Config
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$ROOT/data/backups"
mkdir -p "$BACKUP_DIR/db" "$BACKUP_DIR/config"

source .env.production 2>/dev/null || true

echo "Backing up database..."
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-aems}" "${POSTGRES_DB:-aems}" \
  > "$BACKUP_DIR/db/database_${TS}.sql"

echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config/config_${TS}.tar.gz" config/

echo "Backup complete: $BACKUP_DIR"
