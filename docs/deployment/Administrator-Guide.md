# AEMS Administrator Guide

## Daily Operations

### Check system health

```bash
curl -k https://localhost/api/v1/health/full | jq .
```

Status values: `healthy`, `degraded`, `unhealthy`.

### View logs

```bash
docker compose -f docker-compose.production.yml logs -f backend
docker compose -f docker-compose.production.yml logs -f ai-worker
```

Log files on host: `./logs/` (JSON in production, rotated daily, 90-day retention).

### Grafana dashboards

1. Open http://localhost:3000
2. Login with `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`
3. Dashboard: **AEMS Overview** (auto-provisioned)

Metrics: CPU, RAM, queue size, camera status, DB/Redis health.

### User management

Use Admin API at `/api/v1/auth/login` then `/api/v1/users` (Sprint 9 RBAC).

Default admin credentials are set in `.env.production` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).

## Configuration

| Source | Purpose |
|--------|---------|
| `.env.production` | Secrets, connection strings |
| `config/` | Rules, ROI, performance.yaml |
| Admin Config Center | Runtime config via API |

## Retention Policy (configurable)

| Data | Default | Env variable |
|------|---------|----------------|
| Snapshot | 30 days | `RETENTION_SNAPSHOT_DAYS` |
| Video | 30 days | `RETENTION_VIDEO_DAYS` |
| Log | 90 days | `RETENTION_LOG_DAYS` |
| Event | 365 days | `RETENTION_EVENT_DAYS` |

Admin storage service applies cleanup via `/api/v1/storage/retention`.

## Monitoring Alerts

Watchdog sends Telegram alerts when:

- Backend unreachable
- Database / Redis down
- Camera offline
- GPU offline
- Disk nearly full

Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env.production`.

## Security Checklist

- [ ] Change all default passwords
- [ ] Use Let's Encrypt for public deployments
- [ ] Restrict Grafana/Prometheus to VPN or internal network
- [ ] Enable JWT rotation (Sprint 9 auth)
- [ ] Review rate limits in nginx config
- [ ] Never commit `.env.production` to git

## Performance Baselines

| Metric | Target |
|--------|--------|
| API `/health` | < 100 ms |
| Cold start (backend) | < 60 s |
| Warm start | < 10 s |

Run benchmark via `/api/v1/system/benchmark` (Sprint 10).
