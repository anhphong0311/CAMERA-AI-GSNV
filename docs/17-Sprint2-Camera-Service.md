# 17 — Sprint 2: Camera Service

**Trạng thái:** Hoàn thành Sprint 2. Module độc lập — **không có AI/YOLO/Rule Engine**.

---

## 1. Mục tiêu đã đạt

| Yêu cầu | Trạng thái |
|---------|------------|
| Quản lý camera CRUD API | ✓ |
| Kết nối RTSP (OpenCV FFmpeg) | ✓ |
| Đọc frame liên tục | ✓ |
| FrameBuffer bounded queue | ✓ |
| Multi-camera (bulkhead) | ✓ |
| Auto Reconnect 1→3→5→10→30s | ✓ |
| FPS Monitor | ✓ |
| Health Monitor | ✓ |
| Unit Tests | ✓ |

---

## 2. Cấu trúc module

```
backend/app/modules/camera/
├── camera_manager/     # CameraManager — điều phối multi-cam
├── stream_reader/      # RTSPClient — OpenCV đọc stream
├── frame_buffer/       # FrameBuffer — queue thread-safe
├── stream_worker/      # FrameGrabber + CameraWorker
├── health_check/       # HealthMonitor
├── fps_monitor/        # FPSMonitor
├── reconnect/          # ReconnectPolicy
├── models/             # FramePacket, CameraRuntimeStatus
├── schemas/            # Pydantic API
├── services/           # CameraService
├── repositories/       # CameraRepository
├── utils/              # config_loader, frame_codec
├── exceptions/         # CameraException hierarchy
└── dependencies.py     # DI + lifecycle
```

---

## 3. Luồng hoạt động (Sequence)

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant SVC as CameraService
    participant MGR as CameraManager
    participant W as CameraWorker (thread)
    participant RTSP as RTSPClient
    participant BUF as FrameBuffer
    participant DB as PostgreSQL

    API->>SVC: POST /cameras/{id}/start
    SVC->>MGR: start_camera(id, rtsp_url)
    MGR->>W: start thread
    loop Worker loop
        W->>RTSP: connect / read_frame
        RTSP-->>W: BGR numpy frame
        W->>BUF: push(FramePacket)
        W->>W: FPSMonitor + HealthMonitor
        W->>MGR: on_status_change callback
        MGR->>DB: async heartbeat persist
    end
    API->>SVC: GET /cameras/{id}/frame
    SVC->>BUF: latest()
    SVC-->>API: JPEG base64
```

---

## 4. Multi-camera (Bulkhead)

```mermaid
flowchart TB
    MGR[CameraManager]
    MGR --> W1[Worker cam-1]
    MGR --> W2[Worker cam-2]
    MGR --> WN[Worker cam-N]
    W1 --> B1[Buffer 1]
    W2 --> B2[Buffer 2]
    WN --> BN[Buffer N]
    W1 --> R1[RTSP 1]
    W2 --> R2[RTSP 2]
```

Một camera lỗi → worker reconnect độc lập, không crash process.

---

## 5. Auto Reconnect

```mermaid
stateDiagram-v2
    [*] --> Connecting
    Connecting --> Streaming: connect OK
    Connecting --> WaitReconnect: fail
    Streaming --> WaitReconnect: frame lost
    WaitReconnect --> Connecting: delay elapsed
    note right of WaitReconnect: 1s → 3s → 5s → 10s → 30s (loop)
```

---

## 6. Cấu hình `config/camera.yaml`

| Tham số | Mặc định | Ý nghĩa |
|---------|----------|---------|
| reconnect_delays | [1,3,5,10,30] | Backoff reconnect |
| queue_size | 30 | Max frame trong buffer |
| target_fps | 15 | FPS đọc mục tiêu |
| timeout_seconds | 10 | Timeout mở RTSP |
| auto_start_enabled | true | Auto-start camera enabled khi boot |

---

## 7. Database (migration 002)

Bổ sung cột `cameras`:
- `location`
- `last_online`
- `last_heartbeat`

Chạy migration:
```bash
docker compose exec backend alembic upgrade head
```

---

## 8. Test

```bash
cd backend
pytest tests/modules/camera -v
```

Coverage: FrameBuffer, ReconnectPolicy, RTSPClient (mock), HealthMonitor, CameraManager (mock).

---

## 9. Sprint 3 (chưa làm)

- AI / YOLO / ByteTrack
- Rule Engine
- Telegram
- Dashboard business logic

**Dừng tại đây — chờ xác nhận Sprint 3.**
