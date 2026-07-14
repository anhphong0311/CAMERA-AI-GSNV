# Architecture Documentation — AEMS v1.0.0

## System Overview

```
┌─────────┐     ┌───────┐     ┌─────────┐     ┌──────────┐
│ Client  │────▶│ Nginx │────▶│ FastAPI │────▶│ Modules  │
│ Browser │     │ HTTPS │     │ Backend │     │ (10)     │
└─────────┘     └───────┘     └────┬────┘     └────┬─────┘
                                   │                │
                    ┌──────────────┼────────────────┤
                    ▼              ▼                ▼
              ┌──────────┐  ┌──────────┐    ┌─────────────┐
              │PostgreSQL│  │  Redis   │    │  AI Worker  │
              └──────────┘  └──────────┘    └──────┬──────┘
                                                    │
                                              ┌─────▼─────┐
                                              │  Cameras  │
                                              │  (RTSP)   │
                                              └───────────┘
```

## Module Architecture

| Module | Responsibility |
|--------|---------------|
| camera | RTSP ingest, frame buffer, reconnect |
| ai | YOLO detection, inference |
| tracking | ByteTrack, ROI, timeline |
| behavior | Pose features, temporal analysis |
| rule_engine | Rule parser, executor, cooldown |
| event | Processing, Telegram, evidence |
| realtime | WebSocket hub, broadcaster |
| admin | Auth, RBAC, backup, audit |
| performance | GPU, queue, ONNX/TensorRT |
| ops | Health, watchdog, AI worker |

## Data Flow

1. **CameraWorker** grabs RTSP frames
2. **DetectionService** runs YOLO inference
3. **TrackingService** assigns track IDs
4. **BehaviorService** extracts features
5. **RuleService** evaluates rules → events
6. **EventService** saves snapshot, sends Telegram
7. **RealtimeBroadcaster** pushes to Dashboard

## Database (25 tables)

Core: `cameras`, `detections`, `trackings`, `event_records`, `rules`, `users`, `roles`, `permissions`, `audit_logs`, `config_entries`, ...

Full ERD: [docs/06-Database-Design.md](../06-Database-Design.md)

## Security Architecture

- JWT access (15min) + refresh (7d) with rotation
- RBAC: admin > supervisor > manager > viewer
- Rate limiting per IP
- Audit log for all admin actions

## Deployment Architecture

See [docs/09-Deployment-Architecture.md](../09-Deployment-Architecture.md)

## Design Documents

| Doc | Topic |
|-----|-------|
| 01-SRS.md | Requirements |
| 03-System-Architecture.md | System design |
| 04-AI-Architecture.md | AI pipeline |
| 05-Rule-Engine-Design.md | Rules |
| 07-API-Design.md | REST/WS API |
