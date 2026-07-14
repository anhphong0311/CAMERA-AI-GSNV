# AEMS Backup & Restore Guide

## What is backed up

| Item | Method | Location |
|------|--------|----------|
| PostgreSQL database | pg_dump | `data/backups/db/` |
| Configuration | tar archive | `data/backups/config/` |
| Rules / ROI | Included in config tar | `config/` |

Admin module also supports API backup via `/api/v1/backup` (Sprint 9).

## Manual backup

```bash
bash deploy/scripts/backup.sh
```

Output:

- `data/backups/db/database_YYYYMMDD_HHMMSS.sql`
- `data/backups/config/config_YYYYMMDD_HHMMSS.tar.gz`

## Automated backup (Docker)

Enable daily backup container:

```bash
docker compose -f docker-compose.production.yml --profile backup-cron up -d backup
```

Runs pg_dump every 24 hours; keeps 7 days of SQL files.

## Restore database

```bash
bash deploy/scripts/restore.sh data/backups/db/database_20260706_120000.sql
```

Or via Admin API: `/api/v1/restore` (Sprint 9).

## Restore configuration

```bash
tar -xzf data/backups/config/config_YYYYMMDD_HHMMSS.tar.gz -C .
docker compose -f docker-compose.production.yml restart backend ai-worker
```

## Best practices

1. Schedule off-site copy of `data/backups/`
2. Test restore monthly on staging
3. Backup before every upgrade
4. Encrypt backups at rest for production

## Retention

| Type | Default retention |
|------|-------------------|
| Auto SQL backups | 7 days (container) |
| Manual backups | Administrator managed |
| Snapshots | 30 days |
| Videos | 30 days |
| Logs | 90 days |
| Events | 365 days |

Configure via `.env.production` retention variables or Admin Config Center.
