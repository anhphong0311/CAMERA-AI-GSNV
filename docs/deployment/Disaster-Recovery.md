# AEMS Disaster Recovery

## Recovery objectives

| Scenario | RTO target | RPO target |
|----------|------------|------------|
| Database failure | 30 min | Last backup (24h auto) |
| Redis failure | 5 min | Cache rebuild (no data loss for events) |
| Backend crash | 1 min | Auto restart |
| Full host failure | 2 hours | Last off-site backup |

## Database failure

1. Stop stack: `docker compose -f docker-compose.production.yml down`
2. Restore volume or recreate postgres
3. Restore SQL: `bash deploy/scripts/restore.sh <backup.sql>`
4. Start stack: `docker compose ... up -d`
5. Verify: `/api/v1/health/full`

## Redis failure

Redis is cache/queue — no persistent business data required for recovery.

```bash
docker compose -f docker-compose.production.yml restart redis backend ai-worker
```

## Camera failure

- AI worker auto-restarts (Docker `restart: always`)
- Camera module reconnects on disconnect (Sprint 2)
- Check RTSP URL in config; verify network/firewall

## GPU failure

1. System falls back to CPU inference (Sprint 10 backends)
2. Switch model backend in `config/performance.yaml` if needed
3. Watchdog alerts via Telegram

## Storage full

1. Watchdog alerts when disk < 500 MB free
2. Run storage cleanup: Admin API `/api/v1/storage/cleanup`
3. Adjust retention in config
4. Archive old evidence to external storage

## Telegram failure

- Alerts queue in watchdog logs
- System continues operating
- Fix token/chat_id and restart watchdog

## Full rebuild procedure

```bash
# On new host
git clone <repo>
cp .env.production.example .env.production  # restore secrets from vault
bash deploy/ssl/generate-self-signed.sh
bash deploy/scripts/install.sh
bash deploy/scripts/restore.sh /path/to/latest.sql
```

## Post-recovery checklist

- [ ] `/api/v1/health/full` returns healthy
- [ ] Cameras streaming
- [ ] Grafana shows metrics
- [ ] Test login and dashboard
- [ ] Verify backup job running
