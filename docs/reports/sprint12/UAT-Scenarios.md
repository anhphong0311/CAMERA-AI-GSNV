# UAT Scenarios — Release v1.0.0

## Roles

| Role | Permissions |
|------|-------------|
| Admin | Full system access |
| Supervisor | View all, manage rules, confirm events |
| Viewer | Read-only dashboard |

---

## Scenario UAT-001: Phone Usage Detection (Supervisor)

**Flow:** Employee uses phone → Camera detects → Tracking → Rule → Telegram → Dashboard → Admin confirms

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | Employee | Uses phone at desk | — |
| 2 | System | Camera captures frame | Detection: person + phone |
| 3 | System | ByteTrack assigns track ID | Stable track ID |
| 4 | System | Behavior extracts phone_near_hand | Feature DTO populated |
| 5 | System | Rule PHONE_USAGE fires (>10s) | Event created |
| 6 | System | Snapshot saved + Telegram sent | Alert received on phone |
| 7 | Supervisor | Opens Dashboard → Alerts | Event visible with snapshot |
| 8 | Admin | Confirms event via API/UI | Status = CONFIRMED |

**Status:** PASS (automated E2E + manual staging verified)

---

## Scenario UAT-002: Admin User Management

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | Admin | Login | JWT tokens received |
| 2 | Admin | Create supervisor user | User created with role |
| 3 | Supervisor | Login | Access granted per RBAC |
| 4 | Viewer | Attempt DELETE /users | 403 Forbidden |

**Status:** PASS

---

## Scenario UAT-003: Camera Disconnect Recovery

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | System | Camera streaming | status=online |
| 2 | Operator | Disconnect network cable | status=offline |
| 3 | System | Auto reconnect (30s interval) | status=online |
| 4 | Watchdog | Poll /health/full | Telegram alert if >5min down |

**Status:** PASS (unit + integration)

---

## Scenario UAT-004: Dashboard Real-time

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | Viewer | Open Live Camera page | WebSocket connected |
| 2 | System | Detection broadcast | Bounding boxes update |
| 3 | Viewer | Open Statistics | Metrics reflect live data |

**Status:** PASS

---

## Scenario UAT-005: Backup & Restore (Admin)

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | Admin | Run backup.sh | SQL dump created |
| 2 | Admin | Simulate DB failure | System unhealthy |
| 3 | Admin | Run restore.sh | Data restored, health OK |

**Status:** PASS (documented procedure)
