#!/usr/bin/env bash
# AEMS Restore Script (Sprint 11)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
BACKUP_FILE="${1:?SQL backup file required}"
source .env.production 2>/dev/null || true

echo "Restoring database from $BACKUP_FILE..."
docker compose -f docker-compose.production.yml exec -T postgres \
  psql -U "${POSTGRES_USER:-aems}" -d "${POSTGRES_DB:-aems}" < "$BACKUP_FILE"
echo "Database restore complete."
