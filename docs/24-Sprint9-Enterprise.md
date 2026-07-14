# Sprint 9 — Production Readiness & Enterprise Management

> Hoàn thiện hệ thống AEMS để sẵn sàng Production. **Không** phát triển AI mới,
> **không** đổi Rule/Detection Engine, **không** đổi Dashboard. Tất cả xây dựng
> dưới dạng module độc lập `app/modules/admin` + các API mới.

---

## 1. Kiến trúc

Module Enterprise Admin độc lập, giao tiếp qua **Service/API**, không truy cập trực
tiếp DB của module khác.

```
backend/app/modules/admin/
├── security/          # password policy, JWT access/refresh/rotation
├── rbac/              # permission registry, matrix, role hierarchy
├── repositories/      # entities + ABC + InMemory (default/test) + (SQL models sẵn sàng)
├── services/          # auth, user, role, audit, config, model, backup, restore,
│                      # storage, system monitor, health, scheduler
├── scheduler/         # AsyncScheduler (cron-lite, asyncio, không thêm dependency)
├── schemas/           # Pydantic DTO cho API
├── seed.py            # seed role/config/admin đầu tiên
└── dependencies.py    # DI container + guard get_current_user / require_permission
```

- **Repository pattern**: service phụ thuộc ABC; mặc định dùng `InMemory*`
  (thread-safe) — cùng pattern Sprint 7. ORM (`app/models/admin.py`) + migration
  `alembic/versions/004_admin.py` định nghĩa schema để lưu Database trong Production.
- **Cấu hình lưu Database**: Configuration Center (`config_entries`) là nguồn cấu
  hình runtime (`section.key = value`), không hardcode. `seed_defaults()` chỉ nạp
  giá trị mặc định lần đầu và có thể override hoàn toàn qua API.

---

## 2. Modules & tính năng

| Module | Nội dung |
|--------|----------|
| Authentication | JWT access/refresh, rotation, remember login, password policy, password expiration, session timeout, logout all devices |
| Authorization | RBAC (admin/supervisor/manager/viewer), permission matrix, module + API permission, role hierarchy |
| User Management | CRUD, enable/disable, reset password, force logout, avatar, department, last login |
| Role Management | CRUD role, permission group, role hierarchy, effective permissions |
| Permission | Registry (module × action), matrix |
| Audit Center | Ghi login/logout/create/update/delete/rule/camera/config/model change… |
| Configuration Center | telegram, camera, detection, tracking, behavior, rule, gpu, storage, retention, backup, scheduler, security, system |
| Camera Management | CRUD/enable/disable/restart/health (Sprint 2) + **RTSP Test** (`POST /cameras/rtsp-test`) |
| AI Model Management | register/switch/rollback/version/status/benchmark (metadata — không đổi engine) |
| Backup | database/config/rule/roi/ai_config + auto backup (scheduler) |
| Restore | config/rule/roi (database qua Restore Guide thủ công) |
| Scheduler | daily cleanup, backup, report, storage/video/snapshot cleanup |
| Storage | video/snapshot/event/log retention, auto cleanup, disk usage |
| System Monitor | CPU/GPU/VRAM/RAM/Disk/Temperature/Network/Camera Health/Inference FPS/Queue |
| Health Check | Database/Redis/Camera/GPU/Storage/Telegram/API/WebSocket |
| Maintenance | qua Scheduler + Storage cleanup + Backup |

---

## 3. API Endpoints (prefix `/api/v1`)

- `/auth` — `POST /login`, `POST /refresh`, `POST /logout`, `POST /logout-all`, `GET /me`, `GET /sessions`
- `/users` — CRUD + `/{id}/enable|disable|reset-password|force-logout`
- `/roles` — CRUD + `/{name}/effective-permissions`
- `/permissions` — `GET ""`, `GET /matrix`
- `/audit` — `GET ""` (filter action/module/user_id/limit)
- `/config` — `GET ""`, `GET /{section}`, `PUT ""`, `DELETE /{key}`
- `/system` — `GET /metrics`, `GET /health`, `GET /info`
- `/storage` — `GET /usage`, `GET /retention`, `POST /cleanup`
- `/models` — `GET ""`, `GET /status`, `POST ""`, `POST /{id}/switch`, `POST /{name}/rollback`, `POST /{id}/benchmark`, `DELETE /{id}`
- `/backup` — `GET ""`, `POST ""`, `GET /{id}`
- `/restore` — `POST /{backup_id}`
- `/scheduler` — `GET ""`, `POST /{name}/run`, `POST /{name}/toggle`
- `/metrics` — Prometheus exposition (text)

Swagger/Redoc: `/api/v1/docs`, `/api/v1/redoc`.

---

## 4. Bảo mật (Security)

- **Password hashing**: Argon2 (ưu tiên) → fallback `pbkdf2_sha256` khi thiếu backend.
- **JWT rotation**: refresh token có `jti`, lưu ở `UserSession`; mỗi lần refresh sẽ
  thu hồi token cũ và phát cặp mới. Logout all = revoke toàn bộ session của user.
- **Session timeout**: cấu hình `security.session_timeout_minutes` (Config Center).
- **Rate limit**: fixed-window theo IP (`security_middleware`), `RATE_LIMIT_PER_MINUTE`.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`,
  `Referrer-Policy`, `HSTS` (khi không phải development), `X-Request-ID`.
- **CORS**: giữ cấu hình sẵn có. **HTTPS** khuyến nghị ở tầng Nginx.
- **SQL Injection**: dùng ORM/tham số hoá; input chỉ ảnh hưởng dữ liệu, không execute.
- **Secret management**: `SECRET_KEY`, `ADMIN_PASSWORD`… nạp từ env (không hardcode).

---

## 5. Monitoring & Logging

- `GET /api/v1/system/metrics`: CPU/GPU/VRAM/RAM/Disk/Temperature/Network + camera
  health/inference fps/queue (qua provider).
- `GET /metrics`: Prometheus text (`aems_http_requests_total`, latency avg, status/method).
- `GET /api/v1/system/health`: tổng hợp Database/Redis/GPU/Storage/Telegram/WS/API.
- Logging: Loguru structured + audit log DB (Audit Center).

---

## 6. Admin Guide (vận hành)

1. Đăng nhập admin mặc định: `ADMIN_USERNAME` / `ADMIN_PASSWORD` (env, đổi ngay sau
   lần đầu qua `POST /users/{id}/reset-password`).
2. Tạo user + gán role: `POST /users`.
3. Chỉnh cấu hình hệ thống: `PUT /config` với `{key, value}` (vd `system.company_name`).
4. Quản lý model: `POST /models` → `POST /models/{id}/switch` → `POST /models/{name}/rollback`.
5. Theo dõi sức khỏe & tài nguyên: `GET /system/health`, `GET /system/metrics`.

## 7. Backup Guide

- Tạo backup: `POST /api/v1/backup` với `{"kind": "config"}` (hoặc `rule|roi|ai_config|database`).
- Backup `config` ghi JSON vào `storage.backup_path` (mặc định `./data/backups`).
- Backup `database` dùng `pg_dump` nếu có; nếu không tạo file marker (`status=skipped`).
- Tự động: bật `backup.auto_enabled=true`, chu kỳ `backup.interval_seconds` (Scheduler `auto_backup`).

## 8. Restore Guide

- `POST /api/v1/restore/{backup_id}` khôi phục `config/rule/roi` (áp dụng qua service đích).
- **Database**: khôi phục thủ công bằng `psql`/`pg_restore`:
  ```bash
  psql "$DATABASE_URL" < data/backups/database_YYYYmmdd_HHMMSS.sql
  ```

## 9. Deployment Guide (tóm tắt)

1. Cấu hình `.env` (SECRET_KEY, DATABASE_URL, REDIS, ADMIN_*, RATE_LIMIT_PER_MINUTE…).
2. `alembic upgrade head` (tạo bảng, gồm migration `004`).
3. `docker compose up -d` (Nginx reverse proxy + HTTPS khuyến nghị).
4. Kiểm tra `/api/v1/health`, `/api/v1/system/health`, `/metrics`.

---

## 10. Testing

`backend/tests/modules/admin/`:

- `test_security_core.py` — password policy + JWT tokens (unit).
- `test_rbac.py` — permission/matrix/hierarchy (unit).
- `test_services.py` — user/role/config/model/backup/restore/storage/audit (unit).
- `test_api_integration.py` — JWT + RBAC + CRUD qua TestClient (integration).
- `test_security.py` — security headers, rate limit 429, auth enforcement, SQLi-safe (security).

Chạy: `cd backend && python -m pytest tests/modules/admin -q` (48 tests).
Toàn bộ backend: `python -m pytest -q` (299 tests pass).

---

## 11. Ràng buộc đã tuân thủ

- ❌ Không thêm AI mới, không đổi Rule/Detection Engine, không đổi Dashboard.
- ✅ Module độc lập, giao tiếp qua Service/API; cấu hình lưu Database; không hardcode.
