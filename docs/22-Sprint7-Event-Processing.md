# Sprint 7 — Event Processing & Notification Center

Trạng thái: **HOÀN THÀNH**. App version `7.0.0-sprint7`.

## 1. Mục tiêu

Xây dựng trung tâm xử lý mọi `BehaviorEvent` từ Rule Engine (Sprint 6):
nhận → kiểm tra → lưu → snapshot → video evidence → notification queue →
Telegram, kèm retry / deduplicate / cooldown và vòng đời event đầy đủ.

Module hoàn toàn độc lập: **không** chứa AI Detect / Tracking / Pose / Rule /
Dashboard / Statistics / User Management / ROI Editor / Rule Editor.

## 2. Kiến trúc

```
Rule Engine → AlertQueue → [bridge loop] → Event Queue → Event Processor
   → Snapshot Service → Video Recorder (Ring Buffer)
   → EventStore (RAM + tùy chọn DB)
   → Notification Queue → Telegram Worker (retry/dedup/cooldown) → Telegram Bot
```

`backend/app/modules/event/` gồm: `event_processor/`, `snapshot/`,
`video_recorder/`, `notification/`, `telegram/`, `queue/`, `retry/`, `history/`,
`repositories/`, `services/`, `schemas/`, `config/`, `tests/`, `utils/`, `exceptions/`.

Cầu nối Sprint 6 → 7 nằm ở `dependencies._bridge_loop`: định kỳ lấy event từ
`RuleService.alert_queue()` và `ingest` vào Event Center; xử lý chạy trong
threadpool (`asyncio.to_thread`) để không block camera.

## 3. Event Lifecycle

`NEW → VALIDATING → PROCESSING → SNAPSHOT_CREATED → VIDEO_CREATED →
NOTIFICATION_SENT → COMPLETED`; lỗi bất kỳ → `FAILED`
(`EventStateMachine` kiểm soát chuyển trạng thái).

## 4. Snapshot & Video Evidence

- **Snapshot**: lấy frame gần nhất từ ring buffer, ghi JPG (`cv2.imwrite`),
  đặt tên `Camera_Track_Rule_Timestamp.jpg`. Mục tiêu < 200ms.
- **Ring Buffer**: mỗi camera giữ ~30s frame trong RAM.
- **Video Recorder**: cắt cửa sổ `[t-10s, t+10s]`, xuất MP4 (`cv2.VideoWriter`,
  fallback codec mp4v→XVID→MJPG). Chỉ lưu evidence, không lưu toàn bộ video.
  Mục tiêu export < 5s.

## 5. Notification

- **Queue riêng**: Behavior Event → Notification Queue → Telegram Worker
  (không gửi Telegram trực tiếp trong pipeline).
- **Provider interface** (`NotificationProvider`): thêm Email/Slack/Teams/Discord
  không sửa business logic. `ProviderRegistry` quản lý theo tên kênh.
- **Telegram**: `TelegramProvider` (httpx) gửi text + `sendPhoto` (snapshot) +
  `sendVideo`. Chưa cấu hình token/chat_id → `skipped` (không lỗi).
- **Bot commands**: `/start /help /status /cameras /events /latest`.
- **Cooldown & Dedup** (`DedupCooldown`): cùng rule + person trong 5 phút → bỏ qua;
  sau khi gửi khóa 5 phút.
- **Retry** (`RetryPolicy`): 3 lần, backoff `1s, 5s, 10s`, async.

## 6. Định dạng cảnh báo

```
🚨 AI ALERT
Camera: Office01
Employee: Track #15
Rule: PHONE_USAGE
Duration: 18s
Confidence: 96%
Severity: HIGH
Time: 2026-07-05 09:15:22
ROI: Desk 05
```

## 7. Database

Migration `003_event_processing`: `event_records`, `event_notifications`,
`event_retries` (bảng độc lập, không FK cứng để giữ tính tách biệt). Runtime mặc
định dùng `InMemoryEventStore`; bật `persist_db: true` để dùng `SqlEventStore` (async).

## 8. API (`/api/v1/processing`)

`GET /events`, `/events/{id}`, `/events/live`, `/events/history`,
`/events/statistics`, `POST /events/ingest`, `/events/retry`, `/events/resend`,
`GET /notifications`, `GET /telegram/status`, `POST /telegram/command`.

> Prefix `/processing` để tránh đụng router `/events` của Rule Engine (Sprint 6);
> không sửa kiến trúc sprint trước.

## 9. Config

`config/event.yaml`, `snapshot.yaml`, `recorder.yaml`, `notification.yaml`,
`telegram.yaml` (mount read-only trong docker-compose; ENV secret Telegram).

## 10. Logging & Error Handling

Log: Event Created, Snapshot Saved, Video Saved, Telegram Sent, Retry,
Notification Failed. Xử lý lỗi: Snapshot/Recorder/Telegram Timeout/Network/Disk Full
(exceptions riêng, không làm sập pipeline).

## 11. Test

`backend/tests/modules/event/` — **33 test** pass (unit: config, naming, ring buffer,
snapshot, recorder, dedup, cooldown, retry, queue, worker, processor, telegram
provider, bot; integration: Rule Engine event → Processor → Snapshot → Video →
Notification → Telegram). Chạy chung Sprint 6 + 7: **90 test pass**.

## 12. Checklist cuối sprint

- [x] BehaviorEvent được lưu (EventStore RAM + SqlEventStore/DB schema).
- [x] Snapshot tạo thành công.
- [x] Video Evidence tạo (cắt từ ring buffer pre/post).
- [x] Ring Buffer hoạt động.
- [x] Telegram gửi thành công (provider + memory provider test).
- [x] Retry hoạt động (3 lần, backoff).
- [x] Deduplicate hoạt động.
- [x] Cooldown hoạt động.
- [x] API Event hoạt động.
- [x] Notification Queue hoạt động.
- [x] Unit Test Pass.
- [x] Integration Test Pass.
- [x] App assemble + routes đăng ký (Docker build sẵn sàng).
