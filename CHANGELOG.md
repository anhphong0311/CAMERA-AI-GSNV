# Changelog

All notable changes to the AI Employee Monitoring System (AEMS).

## [1.0.0] - 2026-07-06

**Release v1.0.0 — Production Ready**

First stable release after 12 development sprints.

### Added

- Complete AI pipeline: Camera → Detection → Tracking → Behavior → Rule Engine → Event → Telegram → Dashboard
- Enterprise admin: RBAC, JWT auth, audit, backup/restore, config center
- Real-time WebSocket dashboard with 16 pages
- Performance optimization: ONNX/TensorRT backends, frame scheduler, worker pool
- Production deployment: Docker, Nginx HTTPS, Prometheus, Grafana, Watchdog
- 359 automated backend tests, 91.5% code coverage on core modules
- Full documentation suite (user, admin, developer, deployment guides)

### Sprint Summary (1–12)

| Sprint | Focus |
|--------|-------|
| 1 | Foundation (FastAPI, PostgreSQL, Redis) |
| 2 | Camera Service (RTSP, reconnect) |
| 3 | AI Detection (YOLO) |
| 4 | Tracking (ByteTrack, ROI) |
| 5 | Behavior Features |
| 6 | Rule Engine |
| 7 | Event Processing & Telegram |
| 8 | Dashboard & WebSocket |
| 9 | Enterprise Admin & Security |
| 10 | Performance & Scaling |
| 11 | DevOps & Deployment |
| 12 | QA, UAT & Release |

### Known Issues

- Stub API routes (`/employees`, `/alerts`, `/dashboard`) return placeholder data — use module-specific endpoints
- GPU/TensorRT requires NVIDIA driver + CUDA on host; CPU fallback available
- RTSP camera tests require physical cameras; CI uses mocked streams
- Frontend E2E (Playwright) not yet in CI pipeline

### Breaking Changes

None — first release.

### Security

- JWT access/refresh with rotation
- Argon2 password hashing
- Rate limiting, security headers, RBAC permissions
- HTTPS required in production

[1.0.0]: https://github.com/your-org/aems/releases/tag/v1.0.0
