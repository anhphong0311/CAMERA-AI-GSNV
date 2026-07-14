# Administrator Manual — AEMS v1.0.0

*(Extends [Administrator-Guide.md](../deployment/Administrator-Guide.md))*

## User Management

```bash
# Via API
POST /api/v1/auth/login
GET  /api/v1/users
POST /api/v1/users
PUT  /api/v1/users/{id}
```

## Roles

| Role | Capabilities |
|------|-------------|
| admin | Full access |
| supervisor | Rules, events, cameras, reports |
| manager | View + limited config |
| viewer | Read-only |

## Configuration Center

- `GET /api/v1/config` — list all config keys
- `PUT /api/v1/config/{key}` — update runtime config

## Backup Schedule

```bash
# Daily backup container
docker compose -f docker-compose.production.yml --profile backup-cron up -d backup

# Manual
bash deploy/scripts/backup.sh
```

## Audit Log

`GET /api/v1/audit?limit=100` — all admin actions logged

## Retention

Configure via Admin API or `.env.production`:
- Snapshots: 30 days
- Videos: 30 days
- Logs: 90 days
- Events: 365 days

## Maintenance Windows

1. Announce downtime
2. Run backup
3. Apply update: `bash deploy/scripts/update.sh 1.0.0`
4. Verify health
5. Monitor 30 minutes

See [Maintenance-Guide.md](Maintenance-Guide.md)
