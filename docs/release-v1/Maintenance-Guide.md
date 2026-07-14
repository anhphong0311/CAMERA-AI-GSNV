# Maintenance Guide — AEMS v1.0.0

## Daily

- Check Grafana dashboard for anomalies
- Review error logs: `logs/error_*.log`
- Verify camera online count matches expected

## Weekly

- Run manual backup: `bash deploy/scripts/backup.sh`
- Review audit log for unauthorized access attempts
- Check disk usage (evidence folder)

## Monthly

- Test restore procedure on staging
- Review and rotate secrets if needed
- Update Docker images: `bash deploy/scripts/update.sh`
- Clean old evidence per retention policy

## Log Rotation

Automatic in production:
- Daily rotation at midnight
- 90-day retention
- ZIP compression

## Database Maintenance

```bash
# Vacuum (PostgreSQL)
docker compose exec postgres vacuumdb -U aems -d aems --analyze

# Migration check
docker compose exec backend alembic current
```

## Monitoring Maintenance

- Prometheus retention: 30 days (configured in compose)
- Grafana dashboards: auto-provisioned, backup `grafanadata` volume

## Update Procedure

```bash
bash deploy/scripts/backup.sh
bash deploy/scripts/update.sh 1.0.0
# Verify health
curl -k https://localhost/api/v1/health/full
```

## Rollback

```bash
bash deploy/scripts/rollback.sh 0.9.0
bash deploy/scripts/restore.sh data/backups/db/database_<timestamp>.sql
```

See also:
- [Backup-Restore-Guide.md](../deployment/Backup-Restore-Guide.md)
- [Troubleshooting-Guide.md](../deployment/Troubleshooting-Guide.md)
