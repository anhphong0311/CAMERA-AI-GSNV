# Sprint — Evidence Engine & Phone Detection Improvement

## Tổng quan

Sprint cải tiến **Evidence Engine** và **Phone Detection** mà không thay đổi Dashboard, kiến trúc tổng thể, hay Database schema.

## Thành phần mới

| Module | Vai trò |
|--------|---------|
| `event/evidence/engine.py` | Evidence Engine — orchestrator độc lập |
| `event/evidence/frame_buffer.py` | Circular buffer 30s, `get_frame` / `get_snapshot` / `get_video` |
| `event/evidence/snapshot_manager.py` | Snapshot tại `evidence_time` |
| `event/evidence/video_manager.py` | Video 10s trước + 10s sau evidence |
| `event/evidence/deferred.py` | Hàng đợi video post-roll (không block thread) |
| `config/evidence.yaml` | Cấu hình phone timer, leave, video |

## Luồng Event

```
Rule Engine (WAITING → ACTIVE → CONFIRMED | CANCELLED → FINISHED)
    ↓ CONFIRMED only
AlertQueue → EventProcessor → EvidenceEngine
    → Snapshot @ evidence_time
    → Video (deferred nếu chưa đủ post-roll)
    → NotificationWorker → Telegram
```

## Phone Timer

- YOLO chỉ sinh detection; Behavior theo **Track ID**
- Điều kiện: `phone_detected` + `hand_near_phone` + `phone_person_near` + duration > 10s
- Phone mất **≤ 2 giây**: timer tiếp tục
- Phone mất **> 2 giây**: reset timer, lifecycle = `CANCELLED`
- `evidence_time` = thời điểm đạt 10 giây (snapshot đúng lúc)

## Leave Event (AWAY_FROM_DESK)

- Bắt đầu theo dõi khi `away_from_desk` → `ACTIVE`
- Quay lại trước 5 phút → `CANCELLED`, không Telegram
- Quá 5 phút → `CONFIRMED`, snapshot tại **lúc bắt đầu rời** (`start_time`)

## Frame Buffer

- Camera `FrameBuffer`: circular 30s, truy vấn theo timestamp
- Evidence `FrameBufferManager`: buffer riêng, fed từ camera grabber + AI pipeline
- Không đọc lại RTSP khi lấy evidence

## Telegram

Chỉ gửi khi event `CONFIRMED` và video sẵn sàng (hoặc đã hết thời gian chờ post-roll).

Format:
```
🚨 AI Employee Monitoring
📷 Camera : DH5
👤 Track ID : 15
⚠ Hành vi : Sử dụng điện thoại
⏱ Thời lượng : 12 giây
🕒 14:35:20
📷 Snapshot
📹 Video Evidence
```

## Cấu hình

- `config/evidence.yaml` — phone/leave/video/buffer
- `config/camera.yaml` — `queue_size: 450`, `buffer_size: 450`
- `config/rules.yaml` — thêm `phone_person_near`

## Kiểm tra

```bash
cd backend
python -m pytest tests/modules/event/test_evidence_frame_buffer.py \
  tests/modules/rule_engine/test_phone_timer.py \
  tests/modules/rule_engine/test_integration_rule_engine.py -q
```
