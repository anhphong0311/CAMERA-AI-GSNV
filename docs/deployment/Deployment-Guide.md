# AEMS Production Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- 16 GB RAM minimum (32 GB recommended with GPU)
- Ports: 80, 443, 3000 (Grafana), 9090 (Prometheus)
- Domain name (optional — self-signed cert works for internal use)

## Step 1: Configure Environment

```bash
cp .env.production.example .env.production
```

Edit secrets:

- `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY`
- `ADMIN_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`
- `DOMAIN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional alerts)

## Step 2: SSL Certificate

**Internal / testing:**

```bash
bash deploy/ssl/generate-self-signed.sh your-domain.local
```

**Let's Encrypt (public domain):**

```bash
bash deploy/ssl/certbot-init.sh your-domain.example.com admin@example.com
```

Certificates must exist at `deploy/ssl/fullchain.pem` and `deploy/ssl/privkey.pem`.

## Step 3: Deploy

**One-command install:**

```bash
bash deploy/scripts/install.sh
```

**Manual:**

```bash
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
docker compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Step 4: Verify

```bash
curl -k https://localhost/api/v1/health
curl -k https://localhost/api/v1/health/full
```

Open Grafana at http://localhost:3000 (credentials from `.env.production`).

## Step 5: Enable Daily Backup (optional)

```bash
docker compose -f docker-compose.production.yml --profile backup-cron up -d backup
```

## Architecture

| Container | Role |
|-----------|------|
| nginx | Reverse proxy, HTTPS, rate limit |
| frontend | React SPA (static) |
| backend | FastAPI API |
| ai-worker | Camera + AI pipeline |
| postgres | Database |
| redis | Cache / queue |
| prometheus | Metrics |
| grafana | Dashboards |
| watchdog | Health alerts |

## Update & Rollback

```bash
bash deploy/scripts/update.sh 11.0.0
bash deploy/scripts/rollback.sh 10.0.0
```

## Native Services (without Docker)

**Ubuntu systemd:**

```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl enable --now aems-backend aems-ai-worker aems-watchdog
```

**Windows (NSSM):**

```powershell
.\deploy\windows\install-services.ps1 -InstallPath C:\AEMS
```

## Firewall Recommendations

- Allow inbound: 443 (HTTPS), optionally 3000/9090 for admin only
- Block direct access to postgres (5432) and redis (6379) from public network
- Restrict `/metrics` to internal IPs (configured in nginx)

## Related Docs

- [Administrator Guide](Administrator-Guide.md)
- [Backup & Restore](Backup-Restore-Guide.md)
- [Troubleshooting](Troubleshooting-Guide.md)
