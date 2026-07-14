# Sprint 1 — Foundation

Tài liệu triển khai Sprint 1: khởi tạo monorepo, backend skeleton, frontend layout, Docker stack.

## Đã hoàn thành

- Backend FastAPI + SQLAlchemy models + Alembic migration `001`
- API skeleton: auth, users, employees, cameras, alerts, rules, dashboard, health
- Frontend layout: Login, Dashboard, Sidebar, Navbar, Loading, 404
- Docker: postgres, redis, backend, frontend, nginx

## Luồng khởi động

```mermaid
sequenceDiagram
    participant U as User
    participant N as Nginx :8080
    participant F as Frontend
    participant B as Backend :8000
    participant P as PostgreSQL
    participant R as Redis
    U->>N: GET /
    N->>F: proxy SPA
    U->>N: GET /api/v1/health
    N->>B: proxy API
    B->>P: SELECT 1
    B->>R: PING
    B-->>U: HealthData JSON
```

## Bước tiếp theo (Sprint 2)

- Auth JWT thật + seed admin user
- CRUD cameras/employees/rules
- Không bắt đầu AI/YOLO cho đến khi được chỉ định
