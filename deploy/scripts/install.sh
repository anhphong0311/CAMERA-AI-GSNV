#!/usr/bin/env bash
# AEMS One-line Production Installer — Ubuntu/Debian (Sprint 11)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== AEMS Production Installer ==="

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
fi

if [ ! -f .env.production ]; then
  cp .env.production.example .env.production
  echo "Created .env.production — EDIT SECRETS before continuing!"
  echo "Press Enter after editing .env.production..."
  read -r
fi

if [ ! -f deploy/ssl/fullchain.pem ]; then
  bash deploy/ssl/generate-self-signed.sh localhost
fi

mkdir -p logs data/evidence data/backups/db data/backups/config models

echo "Building and starting production stack..."
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build

echo "Running database migrations..."
docker compose -f docker-compose.production.yml exec -T backend alembic upgrade head || true

echo "=== AEMS deployed ==="
echo "  HTTPS:  https://localhost (self-signed)"
echo "  API:    https://localhost/api/v1/docs"
echo "  Grafana: http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
