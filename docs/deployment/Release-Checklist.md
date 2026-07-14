# AEMS Release Checklist

## Pre-release

- [ ] All CI checks green (`ci.yml`)
- [ ] Backend tests pass: `cd backend && pytest -q`
- [ ] Frontend build succeeds: `cd frontend && npm run build`
- [ ] Production compose validates: `docker compose -f docker-compose.production.yml config`
- [ ] Version bumped in `main.py` and `.env.production.example`
- [ ] CHANGELOG / release notes prepared

## Build & tag

```bash
git tag -a v11.0.0 -m "Sprint 11 — Production Deployment"
git push origin v11.0.0
```

GitHub Actions `release.yml` will:

1. Run full test suite
2. Build production Docker images
3. Create GitHub Release with notes
4. Push tagged images to registry (if configured)

## Deploy to production

- [ ] Backup database: `bash deploy/scripts/backup.sh`
- [ ] Update: `bash deploy/scripts/update.sh 11.0.0`
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify health endpoints
- [ ] Smoke test dashboard and WebSocket
- [ ] Monitor Grafana for 30 minutes

## Post-release verification

- [ ] HTTPS working
- [ ] WebSocket connected
- [ ] Prometheus scraping `/metrics`
- [ ] Watchdog operational
- [ ] Backup cron running (if enabled)

## Rollback procedure

If critical issues detected within rollback window:

```bash
bash deploy/scripts/rollback.sh 10.0.0
bash deploy/scripts/restore.sh data/backups/db/database_<pre-release>.sql
```

Document incident and root cause before re-attempting release.

## Semantic versioning

| Change type | Version bump |
|-------------|--------------|
| Breaking API / schema | MAJOR |
| New sprint features | MINOR |
| Hotfix / patch | PATCH |

Current: **11.0.0** (Sprint 11)
