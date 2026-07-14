# Sprint 3 — AI Detection Engine

Tài liệu chi tiết: [`docs/18-Sprint3-AI-Detection.md`](../../../docs/18-Sprint3-AI-Detection.md)

## Nguyên tắc
Module **độc lập hoàn toàn**: chỉ `frame → inference → DetectionResult (JSON)`.
KHÔNG database, tracking, pose, rule engine, telegram, alert, performance score.

## Cấu trúc
```
ai/
├── config/        # DetectionConfig ← detection.yaml
├── models/        # DTO: BoundingBox, Detection, DetectionResult, ModelInfo, BenchmarkResult, RawDetection
├── preprocess/    # ImagePreprocessor (validate, letterbox, normalize)
├── postprocess/   # ImagePostprocessor (class/confidence filter, NMS, coord map)
├── inference/     # InferenceBackend (Ultralytics), ModelLoader, InferenceEngine
├── detection/     # AIFrameQueue + DetectionPipeline (multi-camera)
├── repositories/  # ModelRepository (artifact weight — KHÔNG phải DB)
├── services/      # DetectionService, BenchmarkService
├── schemas/       # Pydantic API
├── utils/         # image_io, visualizer (overlay debug), device
├── benchmark/     # system_metrics (CPU/GPU/VRAM)
└── dependencies.py
```

## API (mount dưới /api/v1)
| Method | Path | Mô tả |
|--------|------|-------|
| GET  | `/api/v1/ai/model` | Thông tin model |
| POST | `/api/v1/ai/reload` | Reload model |
| POST | `/api/v1/ai/inference` | Detect object trên 1 ảnh base64 |
| POST | `/api/v1/ai/benchmark` | Benchmark FPS/thời gian |
| GET  | `/api/v1/ai/statistics` | Thống kê inference |

## Class nhận diện (10)
person, phone, cup, bottle, food, laptop, keyboard, mouse, chair, monitor
(cấu hình COCO id + ngưỡng confidence riêng trong `config/detection.yaml`)

## Test
```bash
cd backend
pytest tests/modules/ai -v
```

## Đổi backend (ONNX/TensorRT) sau này
Chỉ thêm class kế thừa `InferenceBackend` — không sửa `InferenceEngine`,
`DetectionService`, hay API (Dependency Inversion).
