# Test Case Catalog — Release v1.0.0

Format: Test ID | Description | Pre-condition | Steps | Expected | Priority

---

## E2E Pipeline

| ID | Description | Pre-condition | Steps | Expected | Priority |
|----|-------------|---------------|-------|----------|----------|
| E2E-001 | Phone usage detection to event | Rules loaded | Simulate phone DTOs over 18s → RuleService.process | PHONE event created | P0 |
| E2E-002 | Detection to tracking | TrackingConfig | DetectionResult with 2 persons → TrackingService.process | Tracks assigned | P0 |
| E2E-003 | Tracking to behavior | BehaviorConfig | TrackingResult + poses → BehaviorService.process | Features extracted count≥1 | P0 |
| E2E-004 | Module import regression | None | Import all 10 modules | No ImportError | P1 |

## Camera

| ID | Description | Pre-condition | Steps | Expected | Priority |
|----|-------------|---------------|-------|----------|----------|
| CAM-001 | RTSP reconnect | HealthMonitor | disconnect → reconnect | reconnect_count≥1 | P0 |
| CAM-002 | Frame buffer overflow | FrameBuffer max=5 | Push 10 frames | Oldest evicted | P1 |
| CAM-003 | FPS calculation | FPSMonitor | on_frame x30 | fps≈30 | P1 |

## Security

| ID | Description | Pre-condition | Steps | Expected | Priority |
|----|-------------|---------------|-------|----------|----------|
| SEC-001 | Security headers | Middleware on | POST /auth/login | X-Frame-Options, X-Request-ID | P0 |
| SEC-002 | Rate limit | limit=3/min | 6 login attempts | 429 returned | P0 |
| SEC-003 | SQL injection safe | Admin app | username=`admin' OR '1'='1` | 401, no error | P0 |
| SEC-004 | JWT invalid | Protected route | Bearer invalid.token | 401 | P0 |
| SEC-005 | RBAC enforcement | No token | GET /config | 401 | P0 |

## Failover

| ID | Description | Pre-condition | Steps | Expected | Priority |
|----|-------------|---------------|-------|----------|----------|
| FO-001 | Redis down | Mock redis=false | HealthService.check | status=degraded | P0 |
| FO-002 | Postgres down | Mock execute fail | HealthService.check | status=unhealthy | P0 |
| FO-003 | Backend unreachable | Watchdog | Invalid URL poll | unhealthy + alert | P1 |
| FO-004 | Component degraded | Watchdog mock | redis ok=false | alert fired | P1 |

## Admin / Auth

| ID | Description | Pre-condition | Steps | Expected | Priority |
|----|-------------|---------------|-------|----------|----------|
| ADM-001 | Login success | Admin seeded | POST login valid creds | 200 + tokens | P0 |
| ADM-002 | Refresh rotation | Valid refresh | POST /auth/refresh | New access token | P0 |
| ADM-003 | Permission guard | Viewer role | Access admin endpoint | 403 | P1 |

*(Full catalog: 359 automated test functions map to these categories)*
