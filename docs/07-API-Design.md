# 07 — API Design

**Framework:** FastAPI. **Style:** REST (JSON) + WebSocket realtime. **Auth:** JWT (access+refresh) + RBAC. **Docs:** OpenAPI/Swagger tự sinh.

---

## 1. Nguyên tắc
- Versioned base path: `/api/v1`.
- Response chuẩn hóa: `{ "data": ..., "meta": ..., "error": null }`.
- Phân trang: `?page=&size=` + `meta.total`.
- Lọc/sắp xếp: `?filter[field]=&sort=-created_at`.
- Idempotency cho POST tạo tài nguyên nhạy cảm (header `Idempotency-Key`).
- Mọi timestamp ISO-8601 UTC.

---

## 2. Bản đồ endpoint

```mermaid
flowchart LR
    subgraph Auth
        A1[POST /auth/login]
        A2[POST /auth/refresh]
        A3[POST /auth/logout]
    end
    subgraph Config
        C1[/cameras/]
        C2[/rois/]
        C3[/rules/]
        C4[/employees/]
        C5[/departments/]
        C6[/users/]
    end
    subgraph Ops
        O1[/alerts/]
        O2[/tracks/]
        O3[/performance/]
        O4[/reports/]
        O5[/evidence/]
    end
    subgraph Realtime
        W1[WS /ws/live/:cam]
        W2[WS /ws/alerts]
    end
    subgraph Agent
        G1[POST /agent/metrics]
    end
```

---

## 3. Đặc tả endpoint chính

### 3.1 Auth
| Method | Path | Mô tả | Role |
|--------|------|-------|------|
| POST | `/api/v1/auth/login` | Đăng nhập → access+refresh | public |
| POST | `/api/v1/auth/refresh` | Làm mới token | public(+refresh) |
| POST | `/api/v1/auth/logout` | Thu hồi refresh | auth |
| GET | `/api/v1/auth/me` | Thông tin user hiện tại | auth |

```json
// POST /auth/login  request
{ "username": "admin", "password": "***" }
// response
{ "data": { "access_token": "jwt...", "refresh_token": "jwt...", "expires_in": 900 } }
```

### 3.2 Cameras
| Method | Path | Mô tả | Role |
|--------|------|-------|------|
| GET | `/cameras` | Danh sách + status | manager+ |
| POST | `/cameras` | Thêm camera | admin |
| GET | `/cameras/{id}` | Chi tiết | manager+ |
| PUT | `/cameras/{id}` | Sửa | admin |
| DELETE | `/cameras/{id}` | Xóa | admin |
| POST | `/cameras/{id}/test` | Test RTSP kết nối | admin |
| GET | `/cameras/{id}/stream` | URL live (HLS/MJPEG) | manager+ |

```json
// POST /cameras
{
  "code": "cam-01",
  "name": "Floor 3 - Zone A",
  "rtsp_main": "rtsp://user:pass@192.168.1.20:554/H264/ch1/main",
  "rtsp_sub": "rtsp://user:pass@192.168.1.20:554/H264/ch1/sub",
  "department_id": 2,
  "fps": 15
}
```

### 3.3 ROI
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/cameras/{id}/rois` | ROI của camera |
| POST | `/cameras/{id}/rois` | Tạo ROI (polygon) |
| PUT | `/rois/{id}` | Sửa polygon/gán employee |
| DELETE | `/rois/{id}` | Xóa |

```json
// POST /cameras/1/rois
{ "name": "desk-07", "kind": "desk",
  "polygon": [[0.10,0.20],[0.30,0.20],[0.30,0.55],[0.10,0.55]],
  "employee_id": "uuid-emp" }
```

### 3.4 Rules
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/rules` | Danh sách rule |
| GET | `/rules/{id}` | Chi tiết + params |
| PUT | `/rules/{id}` | Cập nhật ngưỡng (hot-reload) |
| POST | `/rules/{id}/toggle` | Bật/tắt |
| POST | `/rules/{id}/shadow` | Chạy shadow mode |

```json
// PUT /rules/phone_usage
{ "enabled": true,
  "params": { "on_seconds": 12, "conf_min_phone": 0.6, "cooldown_seconds": 120 },
  "score_weight": 2.0 }
```

### 3.5 Alerts
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/alerts` | Lọc theo rule/emp/cam/time/status |
| GET | `/alerts/{id}` | Chi tiết + reason + evidence |
| PATCH | `/alerts/{id}` | Ack/close/mark false_positive |
| GET | `/alerts/{id}/evidence` | Signed URL ảnh+video |

```json
// GET /alerts?rule_id=phone_usage&from=2026-07-01&status=open&page=1&size=20
{
  "data": [{
    "id": "uuid", "rule_id": "phone_usage", "camera_id": 1,
    "employee": {"id":"..","full_name":"Nguyen A"},
    "confidence": 0.88, "duration_s": 12.4, "severity": "medium",
    "reason": {"phone_conf":0.72,"wrist_dist":0.11,"sustained_s":12.4},
    "started_at": "2026-07-01T03:10:00Z", "status": "open",
    "snapshot_url": "...", "video_url": "..."
  }],
  "meta": { "total": 134, "page": 1, "size": 20 }
}
```

### 3.6 Tracks & Timeline
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/tracks` | Lọc theo camera/time |
| GET | `/employees/{id}/timeline?day=` | Timeline hành vi theo ngày |

```json
// GET /employees/{id}/timeline?day=2026-07-01
{ "data": { "segments": [
  {"from":"08:00","to":"10:15","state":"working"},
  {"from":"10:15","to":"10:20","state":"phone"},
  {"from":"10:20","to":"10:50","state":"away"} ] } }
```

### 3.7 Performance & Reports
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/performance?employee_id=&from=&to=` | Điểm & breakdown |
| GET | `/performance/department/{id}` | Tổng hợp phòng ban |
| GET | `/reports/daily?date=` | Báo cáo ngày |
| GET | `/reports/export?type=csv|pdf` | Xuất báo cáo |
| GET | `/reports/heatmap?camera_id=&date=` | Dữ liệu heatmap |

### 3.8 Agent (tùy chọn)
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/agent/metrics` | Nhận kb/mouse/idle từ desktop agent |

```json
// POST /agent/metrics  (auth bằng agent token riêng)
{ "employee_code":"E123","ts":"2026-07-01T03:00:00Z",
  "kb_events":42,"mouse_events":88,"idle_s":0,"active_window":"VSCode" }
```

---

## 4. WebSocket realtime

```mermaid
sequenceDiagram
    participant UI
    participant WS as WS /ws/live/cam-01
    participant RD as Redis PubSub
    UI->>WS: connect (JWT in query/subprotocol)
    WS->>WS: authz check camera access
    WS->>RD: subscribe cam-01 channel
    loop realtime
        RD-->>WS: {tracks, objects, ts}
        WS-->>UI: overlay frame data (throttled 5-10 fps)
    end
```

| Channel | Payload |
|---------|---------|
| `/ws/live/{camera_id}` | detections/tracks/poses để overlay |
| `/ws/alerts` | alert mới realtime (toàn hệ hoặc theo phòng ban) |
| `/ws/system` | trạng thái camera/worker |

Payload overlay:
```json
{ "camera_id":"cam-01","ts":1751350000.15,
  "tracks":[{"id":42,"bbox":[0.1,0.2,0.2,0.6],"roi":"desk-07"}],
  "objects":[{"cls":"phone","bbox":[0.15,0.3,0.18,0.35]}] }
```

---

## 5. Chuẩn lỗi (Error contract)
```json
{ "data": null,
  "error": { "code":"CAMERA_RTSP_UNREACHABLE",
             "message":"Không kết nối được RTSP",
             "details":{"camera_id":1} } }
```

| HTTP | Ý nghĩa |
|------|---------|
| 400 | Validation (Pydantic) |
| 401 | Chưa auth / token hết hạn |
| 403 | Không đủ quyền (RBAC) |
| 404 | Không tồn tại |
| 409 | Xung đột (dedup/idempotency) |
| 422 | Body sai schema |
| 429 | Rate limit |
| 500/503 | Lỗi hệ thống/không sẵn sàng |

---

## 6. Bảo mật API
- JWT access ngắn hạn (15') + refresh (7d, rotate + revoke list ở Redis).
- RBAC bằng dependency FastAPI (`require_role`).
- Rate limit (slowapi/redis) cho `/auth/*` và endpoint nặng.
- CORS whitelist domain dashboard.
- Evidence qua **signed URL** hết hạn ngắn, không public bucket.
- Agent dùng token riêng, scope tối thiểu.

---

## 7. Versioning & tương thích
- Path versioning `/v1`; thay đổi phá vỡ → `/v2`.
- Message contract (WS/Redis) có field `schema_version`.
- Deprecation header + changelog.

---

## 8. Best Practices
- Pydantic v2 schemas tách `Create/Update/Read`.
- Async endpoints + async DB session.
- OpenAPI mô tả đầy đủ ví dụ; sinh client TS cho frontend.
- Pagination bắt buộc cho list lớn (alerts/detections).

## 9. Risk
- WS quá tải khi nhiều client xem live → throttle + giới hạn subscriber.

## 10. Performance
- Cache thống kê/heatmap ở Redis; ETag cho GET; nén gzip/br.
