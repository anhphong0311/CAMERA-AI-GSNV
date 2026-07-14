# Sprint 4 — Object Tracking Engine

Tài liệu chi tiết: [`docs/19-Sprint4-Tracking-Engine.md`](../../../docs/19-Sprint4-Tracking-Engine.md)

## Nguyên tắc
Module **độc lập**: chỉ `DetectionResult → TrackingResult`.
KHÔNG detect/YOLO/pose/face/rule engine/telegram/dashboard/performance/database/alert.

## Cấu trúc
```
tracking/
├── config/           # TrackingConfig ← tracking.yaml
├── models/           # DTO: Track, TrackState, ROI, Timeline, TrackedObject, TrackingResult
├── bytetrack/        # Kalman, STrack, matching (Hungarian numpy), BYTETracker, adapter
├── tracking_engine/  # BaseTracker (abstraction), factory, TrackingEngine (per-camera)
├── track_manager/    # TrackManager: vòng đời NEW/TRACKING/LOST/RECOVERED/REMOVED
├── roi/              # ROIManager (point-in-polygon)
├── timeline/         # MotionAnalyzer + TimelineManager (ROI enter/leave/stay)
├── services/         # TrackingService (multi-camera)
├── repositories/     # InMemoryTrackingRepository (KHÔNG DB)
├── schemas/          # Pydantic API
├── utils/            # visualizer (overlay debug)
├── benchmark/        # BenchmarkService (FPS, ID switch, stability)
├── exceptions/       # custom errors
└── dependencies.py
```

## API (mount dưới /api/v1)
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/v1/tracking/process` | Chạy tracking từ 1 DetectionResult |
| GET | `/api/v1/tracking/live` | Kết quả mới nhất mọi camera |
| GET | `/api/v1/tracking/camera/{camera_id}` | Kết quả mới nhất 1 camera |
| GET | `/api/v1/tracking/track/{track_id}` | Chi tiết track (+timeline) |
| GET | `/api/v1/tracking/history?camera_id=` | Lịch sử TrackingResult |
| GET | `/api/v1/tracking/statistics` | Thống kê |
| POST | `/api/v1/tracking/benchmark` | Benchmark tracking |

## Thuật toán
ByteTrack (Kalman + association 2 tầng, Hungarian thuần numpy).
Đổi DeepSORT/OCSORT/StrongSORT: thêm class kế thừa `BaseTracker` + 1 nhánh trong
`create_tracker` — KHÔNG đổi TrackManager/Engine/Service/API.

## Test
```bash
cd backend
pytest tests/modules/tracking -v
```
Tất cả test chạy KHÔNG cần torch/GPU (tracking là CPU thuần).
