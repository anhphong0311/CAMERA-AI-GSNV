# Behavior Feature Engine (Sprint 5)

Module **Human Pose & Behavior Feature Extraction** — trích xuất đặc trưng hành vi
từ `TrackingResult` (Sprint 4) để **Rule Engine (Sprint 6)** sử dụng.

> Đây **KHÔNG** phải Action Recognition, **KHÔNG** phải Rule Engine, **KHÔNG** tạo
> Alert. Module chỉ trích xuất đặc trưng (feature extraction).

## Nguyên tắc độc lập

Không làm: Detect Object · Tracking · Rule · Telegram · Dashboard · Database ·
Alert · Performance Score.

```
Camera → Detection → Tracking → [Behavior Feature Engine] → BehaviorFeatureDTO → Sprint 6
```

- **Input:** `TrackingResult` (hoặc `TrackingView`) + frame (chạy pose) + detections
  (ngữ cảnh phone/cup/bottle/food/monitor/chair — tùy chọn).
- **Output:** `BehaviorFeatureDTO` chuẩn hóa cho mỗi track.

## Cấu trúc

```
backend/app/modules/behavior/
├── config/          # behavior.yaml loader (Pydantic)
├── exceptions/      # PoseError, InvalidSkeleton, MissingJoint, BufferOverflow
├── models/          # Keypoints, PoseResult, Feature DTO, BehaviorFeatureDTO, TrackView
├── pose/            # PoseEstimator (interface) + YOLOPoseEstimator + factory
├── head/            # HeadFeatureExtractor
├── body/            # BodyFeatureExtractor
├── hand/            # HandFeatureExtractor
├── sitting/         # SittingFeatureExtractor
├── motion/          # MotionFeatureExtractor
├── gaze/            # GazeFeatureExtractor (ước lượng)
├── feature_engine/  # PoseAssociator, ObjectContext, InteractionExtractor, engine
├── history/         # TemporalBuffer (300 frame) + HistoryManager
├── repositories/    # BehaviorRepository (in-memory, KHÔNG DB)
├── services/        # BehaviorService (facade) + BenchmarkService
├── schemas/         # Pydantic API schemas
├── utils/           # geometry + visualizer (debug overlay)
└── dependencies.py  # DI + lifecycle
```

## Pose model — có thể thay đổi

`PoseEstimator` là interface (Dependency Inversion). Hiện dùng **YOLO11-pose**
(Ultralytics, lazy import). Đổi sang MediaPipe = thêm 1 nhánh trong
`pose/factory.py`, **không** sửa extractors / engine / service / API.

Keypoints theo chuẩn **COCO-17**.

## Đặc trưng trích xuất

| Nhóm | Nội dung |
|------|----------|
| Head | Position, Angle, Direction (Down/Up/Left/Right/Forward), Stability |
| Body | Angle, Lean (Forward/Back/Neutral), Rotation |
| Hand | Left/Right Position, Movement, Speed, Near Face, Near Phone |
| Sitting | Sitting/Standing, Leaving/Returning Chair |
| Motion | Stationary Time, Movement Distance, Speed, Direction (từ Tracking) |
| Gaze | Ước lượng Looking Monitor/Phone/Left/Right/Down |
| Phone | Distance Hand↔Phone, Duration, Visibility |
| Food | Distance Hand/Food/Cup/Bottle ↔ Mouth (proxy = mũi) |
| Desk | Body in ROI, Chair Detection, Monitor Direction, Hand on Desk |
| Temporal | 300-frame buffer: Pose/Motion/Head/Hand history |

> Head/Gaze/Face-Orientation là **ước lượng 2D**, không khẳng định tuyệt đối.

## API (mount `/api/v1`)

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/behavior/process` | Trích đặc trưng từ tracks (+frame +objects) |
| GET | `/behavior/live` | Đặc trưng mới nhất mọi camera |
| GET | `/behavior/statistics` | Thống kê |
| GET | `/behavior/camera/{camera_id}` | Đặc trưng mới nhất một camera |
| GET | `/behavior/{track_id}` | Đặc trưng mới nhất một track |
| POST | `/behavior/benchmark` | Benchmark pose/feature |

## Config `config/behavior.yaml`

Pose model/threshold, associator IoU, ngưỡng head/body/hand/food/sitting/motion,
temporal buffer size (300) / window / max_tracks, frame_rate.

## Đa camera

`BehaviorService` giữ **1 pose model dùng chung**, mỗi camera có
`BehaviorFeatureEngine` + `HistoryManager` riêng (track ID không chia sẻ).

## Test

```bash
pytest tests/modules/behavior/ -q
```

Test không cần torch/GPU: pose dùng skeleton tổng hợp, tracking thuần numpy.
