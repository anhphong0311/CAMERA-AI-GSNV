# Installation Guide — AEMS v1.0.0

## Option 1: Docker (Recommended)

### Ubuntu

```bash
git clone <repo-url> aems && cd aems
cp .env.production.example .env.production
# Edit secrets
bash deploy/scripts/install.sh
```

### Windows

```powershell
git clone <repo-url> aems; cd aems
Copy-Item .env.production.example .env.production
# Edit secrets
.\deploy\scripts\install.ps1
```

## Option 2: Docker Compose Manual

```bash
cp .env.production.example .env.production
bash deploy/ssl/generate-self-signed.sh localhost
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
docker compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Option 3: Native (Ubuntu systemd)

```bash
# Install Python 3.12, PostgreSQL 16, Redis 7
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl enable --now aems-backend aems-ai-worker aems-watchdog
```

## Option 4: Native (Windows Service)

```powershell
# Requires NSSM
.\deploy\windows\install-services.ps1 -InstallPath C:\AEMS
```

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 / Windows 10 | Ubuntu 24.04 |
| RAM | 16 GB | 32 GB |
| CPU | 8 cores | 16 cores |
| GPU | Optional | NVIDIA RTX 3060+ |
| Disk | 100 GB SSD | 500 GB SSD |
| Docker | 24+ | Latest |

## Post-Install

1. Open https://localhost (accept self-signed cert)
2. Login with admin credentials from `.env.production`
3. Configure cameras in Admin panel
4. Verify `/api/v1/health/full`

See [Deployment-Guide.md](../deployment/Deployment-Guide.md) for details.
