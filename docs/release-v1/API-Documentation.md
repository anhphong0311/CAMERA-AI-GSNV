# API Documentation — AEMS v1.0.0

## Base URL

```
Production: https://your-domain/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username": "admin", "password": "..."}

Response: { "data": { "access_token": "...", "refresh_token": "..." } }
```

Use header: `Authorization: Bearer <access_token>`

## Endpoint Summary (128 total)

| Group | Prefix | Count | Description |
|-------|--------|------:|-------------|
| Auth | `/auth` | 4 | Login, refresh, me, logout |
| Users | `/users` | 6 | CRUD users |
| Roles | `/roles` | 5 | RBAC roles |
| Permissions | `/permissions` | 2 | Permission registry |
| Cameras | `/cameras` | 12 | Camera CRUD + stream |
| AI | `/ai` | 5 | Detection control |
| Tracking | `/tracking` | 7 | Track queries |
| Behavior | `/behavior` | 6 | Feature extraction |
| Rules | `/rules` | 11 | Rule CRUD + evaluate |
| Events | `/events` | 16 | Events + processing |
| Telegram | `/telegram` | 3 | Bot commands |
| Realtime | `/realtime`, `/ws` | 6 | WebSocket + metrics |
| Admin | `/config`, `/audit`, `/backup`... | 25 | Enterprise admin |
| Performance | `/performance`, `/gpu`... | 7 | Benchmarks |
| Health | `/health` | 2 | Basic + full health |

## Interactive Docs

- **Swagger UI:** `/api/v1/docs`
- **ReDoc:** `/api/v1/redoc`

## WebSocket

```
wss://your-domain/api/v1/ws
```

Channels: `system`, `detection`, `tracking`, `alert`

## Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

Full API design: [docs/07-API-Design.md](../07-API-Design.md)
