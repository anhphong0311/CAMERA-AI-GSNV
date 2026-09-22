# Sprint 2 — Camera Service

Tài liệu chi tiết module Camera: xem [`docs/17-Sprint2-Camera-Service.md`](../../docs/17-Sprint2-Camera-Service.md)

## Chạy test

```bash
cd backend
pytest tests/modules/camera -v
```

## Cảnh báo camera qua Telegram

Đặt `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` trong `.env` của Docker Compose
(cùng bot/chat đang dùng cho cảnh báo sự kiện), rồi khởi động lại backend.
Chỉ camera có `enabled=true` được theo dõi. Nếu worker không chạy, RTSP mất
kết nối, hoặc không có frame mới, hệ thống chờ 180 giây lúc khởi động và
30 giây sau khi camera từng có hình rồi gửi một thông báo
cho camera đó. Khi camera có frame trở lại, hệ thống gửi thông báo phục hồi.
Nếu Telegram tạm lỗi, lần kiểm tra tiếp theo sẽ thử gửi lại.

Điều chỉnh `telegram_alerts_enabled`, `alert_check_interval_seconds`,
`alert_grace_seconds`, `alert_startup_grace_seconds` và
`alert_stale_frame_seconds` trong `config/camera.yaml`.
Không cần thêm bot Telegram riêng.

## API Camera

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/v1/cameras` | Danh sách |
| POST | `/api/v1/cameras` | Tạo mới |
| GET | `/api/v1/cameras/{id}` | Chi tiết |
| PUT | `/api/v1/cameras/{id}` | Cập nhật |
| DELETE | `/api/v1/cameras/{id}` | Xóa |
| POST | `/api/v1/cameras/{id}/start` | Bắt đầu RTSP |
| POST | `/api/v1/cameras/{id}/stop` | Dừng |
| POST | `/api/v1/cameras/{id}/restart` | Restart |
| GET | `/api/v1/cameras/{id}/health` | Health |
| GET | `/api/v1/cameras/{id}/fps` | FPS metrics |
| GET | `/api/v1/cameras/{id}/frame` | Frame JPEG base64 |
