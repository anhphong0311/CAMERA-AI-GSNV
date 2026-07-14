#!/usr/bin/env bash
# AEMS Rollback Script (Sprint 11)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PREV="${1:?Previous version tag required, e.g. 10.0.0}"
export AEMS_VERSION="$PREV"
echo "Rolling back to $PREV..."
docker compose -f docker-compose.production.yml --env-file .env.production up -d
echo "Rollback complete. Verify health: curl -k https://localhost/api/v1/health/full"
