# Sprint 2 — Camera Service

Tài liệu chi tiết module Camera: xem [`docs/17-Sprint2-Camera-Service.md`](../../docs/17-Sprint2-Camera-Service.md)

## Chạy test

```bash
cd backend
pytest tests/modules/camera -v
```

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
