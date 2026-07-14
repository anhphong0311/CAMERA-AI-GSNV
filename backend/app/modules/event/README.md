# Event Processing & Notification Center (Sprint 7)

Trung tâm xử lý mọi `BehaviorEvent` sinh ra từ Rule Engine (Sprint 6): nhận →
validate → lưu → snapshot → video evidence → notification queue → Telegram
(retry / dedup / cooldown).

## Nguyên tắc

- **Độc lập**: KHÔNG chứa logic AI Detect / Tracking / Pose / Rule / Dashboard.
- **Đầu vào**: `BehaviorEventInput` (DTO riêng, decoupled khỏi Rule Engine).
  App layer chuyển `BehaviorEventDTO.to_dict()` → `BehaviorEventInput.from_dict()`.
- **Đầu ra**: `EventRecord`, `NotificationRecord`, `SnapshotRecord`, `VideoRecord`.
- **Non-blocking**: pipeline chạy trong threadpool ở background loop; camera không bị chặn.

## Kiến trúc

```
Rule Engine → AlertQueue → [bridge] → Event Queue → Event Processor
  → Snapshot Service → Video Recorder → EventStore (DB/RAM)
  → Notification Queue → Telegram Worker (retry/dedup/cooldown) → Telegram
```

## Event Lifecycle

`NEW → VALIDATING → PROCESSING → SNAPSHOT_CREATED → VIDEO_CREATED →
NOTIFICATION_SENT → COMPLETED`. Bất kỳ lỗi nào → `FAILED`.

## Thành phần

| Thư mục | Vai trò |
|---|---|
| `event_processor/` | Pipeline + state machine |
| `snapshot/` | Lưu JPG frame gần nhất |
| `video_recorder/` | Ring buffer 30s + xuất MP4 evidence (pre 10s + post 10s) |
| `notification/` | Provider interface, formatter, dedup/cooldown, worker |
| `telegram/` | TelegramProvider + Bot commands |
| `queue/` | Hàng đợi bounded thread-safe |
| `retry/` | RetryPolicy backoff (1s, 5s, 10s) |
| `history/` | Read-model notification/retry history |
| `repositories/` | EventStore (InMemory) + SqlEventStore (async) |
| `services/` | `EventService` facade |
| `schemas/` | DTO + records + API request models |
| `config/` | Loader cho 5 file YAML |

## Ring Buffer

Mỗi camera giữ ~30s frame gần nhất trong RAM (`RingBufferManager`). Khi event
xảy ra, cắt cửa sổ `[t - pre, t + post]` để xuất evidence. KHÔNG lưu toàn bộ video.

## Notification Channel Interface

`NotificationProvider` (ABC) cho phép thêm Email/Slack/Teams/Discord mà KHÔNG
sửa business logic (Open/Closed). Telegram là một implementation; `ProviderRegistry`
quản lý theo tên kênh.

## Cooldown & Deduplicate

`DedupCooldown` theo `(rule_id, track_id)`:
- Dedup: cùng rule + person trong 5 phút → bỏ qua.
- Cooldown: sau khi gửi, khóa 5 phút.

## Retry

`RetryPolicy`: tối đa 3 lần, backoff `[1s, 5s, 10s]`. `skipped` (provider chưa
sẵn sàng / bị dedup) → KHÔNG retry. Lỗi mạng/timeout → retry.

## Naming

- Snapshot: `Office01_TRACK12_PHONE_USAGE_20260705_091522.jpg`
- Video: `Office01_TRACK12_PHONE_USAGE_20260705_091522.mp4`

## Config (YAML)

`event.yaml`, `snapshot.yaml`, `recorder.yaml`, `notification.yaml`, `telegram.yaml`.
Secret Telegram nạp qua ENV `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

## API (prefix `/api/v1/processing`)

> Dùng prefix `/processing` để tách khỏi router `/events` của Rule Engine (Sprint 6).

- `GET  /processing/events` · `/events/live` · `/events/history` · `/events/statistics`
- `GET  /processing/events/{event_id}`
- `POST /processing/events/ingest` · `/events/retry` · `/events/resend`
- `GET  /processing/notifications`
- `GET  /processing/telegram/status` · `POST /processing/telegram/command`

## Database

Bảng độc lập (migration `003`): `event_records`, `event_notifications`,
`event_retries`. Bật `persist_db: true` để dùng `SqlEventStore`.

## Performance

Snapshot < 200ms · Video export < 5s · Telegram < 3s · Retry async (không block camera).

## Test

`backend/tests/modules/event/` — 33 test (config, naming, ring buffer, snapshot,
recorder, dedup, cooldown, retry, queue, worker, processor, telegram, bot, service,
integration).
