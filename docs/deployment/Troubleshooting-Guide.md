# AEMS Troubleshooting Guide

## Container won't start

```bash
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs backend --tail 100
```

Common causes:

| Symptom | Fix |
|---------|-----|
| `postgres` unhealthy | Check `POSTGRES_PASSWORD`, disk space |
| `backend` crash loop | Run migrations: `alembic upgrade head` |
| `nginx` exit | Missing SSL certs in `deploy/ssl/` |
| `ai-worker` restart | Ensure backend is healthy first |

## HTTPS / SSL errors

- Self-signed: browser warning is expected — add exception or use real cert
- `nginx: SSL certificate not found` → run `deploy/ssl/generate-self-signed.sh`
- Let's Encrypt: ensure port 80 open for ACME challenge

## WebSocket disconnects

1. Verify nginx `proxy_params.conf` has Upgrade headers
2. Frontend must use `wss://` when HTTPS is enabled
3. Check nginx error log: `docker logs aems-nginx`

## Health check degraded

```bash
curl -k https://localhost/api/v1/health/full
```

Inspect failing component in `components` object:

- `database` → postgres connectivity
- `redis` → password mismatch
- `ai_worker` → model path / GPU driver
- `camera` → RTSP URL / network
- `storage` → disk full (< 500 MB free)

## Database connection refused

```bash
docker compose -f docker-compose.production.yml exec postgres pg_isready -U aems
```

Verify `DATABASE_URL` uses hostname `postgres` inside Docker network.

## Redis auth failure

Ensure `REDIS_PASSWORD` matches in `.env.production` and backend env.

## Grafana empty dashboards

1. Check Prometheus targets: http://localhost:9090/targets
2. Backend must expose `/metrics` with `ENABLE_METRICS=true`
3. Restart grafana: `docker compose ... restart grafana`

## Watchdog not alerting

- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Check watchdog logs: `docker logs aems-watchdog`
- Alerts have 5-minute cooldown per component

## Load / stress issues

Use Sprint 10 endpoints:

- `/api/v1/system/stress` — stress test
- `/api/v1/system/queue` — queue depth
- `/api/v1/system/gpu` — GPU status

## Getting help

Collect diagnostics:

```bash
docker compose -f docker-compose.production.yml ps > diag.txt
curl -k https://localhost/api/v1/health/full >> diag.txt
docker compose -f docker-compose.production.yml logs --tail 200 >> diag.txt
```
