#!/usr/bin/env bash
# AEMS Update Script (Sprint 11)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="${1:-latest}"
export AEMS_VERSION="$VERSION"

echo "Updating AEMS to $VERSION..."
git pull origin main || true
docker compose -f docker-compose.production.yml --env-file .env.production pull || true
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
docker compose -f docker-compose.production.yml exec -T backend alembic upgrade head
echo "Update complete."
