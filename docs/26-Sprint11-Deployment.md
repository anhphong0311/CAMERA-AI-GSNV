# Sprint 11 — Enterprise Deployment, DevOps & Observability

**Version:** 11.0.0-sprint11  
**Phạm vi:** Production deployment only — không thay đổi Business Logic, AI, Detection, Tracking, Rule Engine, Dashboard.

---

## Tổng quan

Sprint 11 hoàn thiện hạ tầng triển khai production cho AEMS:

| Thành phần | Mô tả |
|------------|-------|
| Docker Production | Multi-stage Dockerfile cho backend, frontend, AI worker |
| Docker Compose | `docker-compose.production.yml` — full stack |
| Nginx | HTTPS, gzip, rate limit, WebSocket, security headers |
| SSL | Self-signed (nội bộ) + Let's Encrypt script |
| Health | `/api/v1/health` + `/api/v1/health/full` |
| Monitoring | Prometheus + Grafana dashboard |
| Logging | JSON structured logs, rotation, compression |
| Backup/Restore | Script + container profile `backup-cron` |
| Watchdog | Telegram alerts khi component lỗi |
| CI/CD | GitHub Actions: CI, Deploy, Release |
| Installers | `install.sh` / `install.ps1` one-command |

---

## Kiến trúc Production

```
Client → Nginx (443) → Frontend / Backend API
                              ↓
                         AI Worker
                              ↓
                    Redis ← → PostgreSQL
                              ↓
                         Storage / Backup
                              ↓
              Prometheus ← Grafana / Watchdog
```

---

## Quick Start

### Ubuntu

```bash
cp .env.production.example .env.production
# Chỉnh secrets trong .env.production
bash deploy/scripts/install.sh
```

### Windows

```powershell
Copy-Item .env.production.example .env.production
# Chỉnh secrets
.\deploy\scripts\install.ps1
```

### Truy cập

| Service | URL |
|---------|-----|
| HTTPS App | https://localhost |
| API Docs | https://localhost/api/v1/docs |
| Health | https://localhost/api/v1/health/full |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## Module Ops (`backend/app/modules/ops/`)

- `health.py` — Deep health aggregation
- `ai_worker.py` — Standalone AI pipeline entrypoint
- `watchdog.py` — Health polling + Telegram alerts

---

## Environment Files

| File | Mục đích |
|------|----------|
| `.env.production.example` | Production template |
| `.env.staging.example` | Staging template |
| `.env.development.example` | Local dev template |

---

## CI/CD Workflows

| Workflow | Trigger | Mục đích |
|----------|---------|----------|
| `ci.yml` | Push/PR | Lint, test, Docker build (dev + prod) |
| `deploy.yml` | main / manual | Validate compose, build prod images |
| `release.yml` | Tag `v*.*.*` | Release notes, semantic version images |

---

## Kiểm tra cuối Sprint

- [x] Production Dockerfiles
- [x] docker-compose.production.yml
- [x] Nginx HTTPS + WebSocket
- [x] Health `/health/full`
- [x] Prometheus + Grafana
- [x] Backup/Restore scripts
- [x] Watchdog
- [x] JSON logging + rotation
- [x] GitHub Actions CI/CD
- [x] Install/Update/Rollback scripts
- [x] systemd + Windows service templates
- [x] Documentation

---

## Tài liệu chi tiết

- [Deployment Guide](deployment/Deployment-Guide.md)
- [Administrator Guide](deployment/Administrator-Guide.md)
- [Troubleshooting Guide](deployment/Troubleshooting-Guide.md)
- [Backup & Restore Guide](deployment/Backup-Restore-Guide.md)
- [Disaster Recovery](deployment/Disaster-Recovery.md)
- [Release Checklist](deployment/Release-Checklist.md)

---

**Sprint 11 hoàn thành. Chờ Sprint 12.**
