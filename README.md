# AI Employee Monitoring System (AEMS)

**Release v1.0.0** — Production Ready

Hệ thống giám sát nhân viên văn phòng bằng Computer Vision + Rule Engine + Real-time Dashboard.

## Trạng thái dự án

| Metric | Value |
|--------|-------|
| Version | **1.0.0** |
| Sprints | 12/12 hoàn thành |
| Backend tests | 359 passed |
| Code coverage | 91.5% (core modules) |
| API endpoints | 128 (REST + WebSocket) |
| Domain modules | 10 |

## Kiến trúc

```
Camera (RTSP) → Detection (YOLO) → Tracking (ByteTrack) → Behavior Features
    → Rule Engine → Event Processor → Telegram + Snapshot/Video → Dashboard
```

## Quick Start

### Docker (recommended)

```bash
cp .env.production.example .env.production
# Edit secrets
bash deploy/scripts/install.sh
```

### Development

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| API Docs | http://localhost:8080/api/v1/docs |
| Health | http://localhost:8080/api/v1/health/full |

## Documentation

| Document | Path |
|----------|------|
| Architecture | [docs/03-System-Architecture.md](docs/03-System-Architecture.md) |
| API Design | [docs/07-API-Design.md](docs/07-API-Design.md) |
| Deployment | [docs/deployment/Deployment-Guide.md](docs/deployment/Deployment-Guide.md) |
| User Manual | [docs/release-v1/User-Manual.md](docs/release-v1/User-Manual.md) |
| Admin Manual | [docs/release-v1/Administrator-Manual.md](docs/release-v1/Administrator-Manual.md) |
| Developer Guide | [docs/release-v1/Developer-Manual.md](docs/release-v1/Developer-Manual.md) |
| QA Report | [docs/reports/sprint12/QA-Report.md](docs/reports/sprint12/QA-Report.md) |
| Project Summary | [docs/reports/sprint12/Project-Summary.md](docs/reports/sprint12/Project-Summary.md) |

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Redis, Alembic
- **AI:** YOLO (Ultralytics), ByteTrack, ONNX/TensorRT
- **Frontend:** React 18, Vite, TypeScript, Tailwind, Shadcn UI
- **Infra:** Docker, Nginx, PostgreSQL, Prometheus, Grafana

## License

MIT — see [LICENSE](LICENSE)
