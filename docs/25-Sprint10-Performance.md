# Sprint 10 — AI Performance Optimization & Production Scaling

> Tối ưu toàn hệ thống cho triển khai thực tế. **Không** thêm tính năng business,
> **không** đổi Rule Engine / Dashboard / DB schema. Chỉ tối ưu hiệu năng.

---

## 1. Kiến trúc Pipeline (Async Workers)

```
Camera (RTSP thread)
    ↓
Frame Buffer (Sprint 2)
    ↓
Pipeline Orchestrator (async poll, Sprint 10)
    ↓
Frame Scheduler (skip/adaptive/priority — 30→10 FPS)
    ↓
AI Detection Pipeline (worker pool + per-camera queue)
    ↓
[optional chain] Tracking → Behavior → Rule → Event → Notification
```

Module mới: `backend/app/modules/performance/`

| Thành phần | Mô tả |
|------------|--------|
| `backends/` | ONNX, TensorRT + factory (PyTorch/ONNX/TRT) |
| `scheduler/frame_scheduler.py` | Skip frame, adaptive FPS, priority camera |
| `queue/priority_queue.py` | Priority queue thread-safe, drop oldest/newest |
| `pool/` | FramePool, BufferPool, WorkerPool, WorkerPoolRegistry |
| `gpu/manager.py` | Multi-GPU discovery, load balance, camera assignment |
| `pipeline/orchestrator.py` | Async bridge Camera → AI (không sửa CameraWorker) |
| `cache/redis_cache.py` | Event/Rule/Camera/Employee cache (best-effort Redis) |
| `benchmark/` | So sánh PyTorch/ONNX/TensorRT + stress test 1–100 camera |
| `monitor/collector.py` | CPU/GPU/FPS/queue/delay/workers metrics |
| `config/performance.yaml` | Toàn bộ cấu hình tối ưu (không hardcode) |

---

## 2. Backend Inference (ONNX / TensorRT)

- **PyTorch** (mặc định): UltralyticsBackend — không đổi.
- **ONNX**: `ONNXBackend` — onnxruntime, CUDA EP khi có GPU.
- **TensorRT**: `TensorRTBackend` — TensorRT EP / fallback ONNX CUDA.
- **Factory**: `create_backend(type, ...)` + `export_yolo_to_onnx()` qua Ultralytics.
- **ModelLoader** inject backend qua `performance.yaml` → `backend.type`.
- **Precision**: `fp32 | fp16 | int8` (fp16 bật half precision trên CUDA).

Cấu hình (`config/performance.yaml`):

```yaml
backend:
  type: pytorch   # pytorch | onnx | tensorrt
  onnx_path: models/yolo11n.onnx
  tensorrt_path: models/yolo11n.engine
  precision: fp32
  auto_export_onnx: false
```

---

## 3. Frame Scheduler

- Camera 30 FPS capture → AI xử lý ~10 FPS (`target_ai_fps`).
- Modes: `adaptive`, `fixed`, `priority`.
- Tracking vẫn mượt vì dùng **latest detection result**, không cần mọi frame.

---

## 4. Multi-Camera & Worker Pool

- **DetectionPipeline** (Sprint 3): per-camera queue, round-robin workers.
- **WorkerPoolRegistry** (Sprint 10): detection/tracking/behavior/rule/event/notification pools.
- **GpuManager**: round-robin / least_loaded gán camera → `cuda:N`.
- **PipelineOrchestrator**: poll frame buffer → scheduler → `submit_frame()`.

---

## 5. Memory & Queue

- **FramePool**: tái sử dụng ndarray, giảm GC/allocation.
- **BufferPool**: bytearray pool cho encode/network.
- **PriorityQueue**: ưu tiên camera quan trọng, drop-oldest khi đầy.
- **Redis cache**: TTL cache cho event/rule/camera/employee (optional).

---

## 6. Database & Network

- **Connection pool** configurable qua env: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_PRE_PING`.
- **Không thay đổi DB schema.**
- RTSP/network tuning trong `performance.yaml` (`network` section).

---

## 7. API Endpoints

Prefix `/api/v1/system` (permission `system:read`):

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/performance` | CPU/GPU/FPS/queue/delay/workers |
| GET | `/performance/history` | Lịch sử metrics (60–120 điểm) |
| GET | `/gpu` | GPU devices, VRAM, temperature, assignments |
| POST | `/benchmark` | So sánh PyTorch/ONNX/TensorRT |
| GET | `/queue` | Frame scheduler, pool, pipeline, cache |
| GET | `/worker` | Worker pool stats |
| POST | `/stress` | Stress test 1–100 camera (synthetic) |

---

## 8. Performance Targets (tham chiếu)

| GPU | Cameras | Target FPS |
|-----|---------|------------|
| RTX 3060 | 1 | 30 |
| RTX 3060 | 5 | 25 |
| RTX 3060 | 10 | 20 |
| RTX 4070 | 20 | 20 |
| RTX 4080 | 50 | 20 |

Đạt target phụ thuộc model, backend (TensorRT khuyến nghị production), và `target_ai_fps`.

---

## 9. Error Handling

- GPU OOM / CUDA errors: mapped trong UltralyticsBackend (Sprint 3), ONNX/TRT propagate `InferenceError`.
- Queue overflow: drop-oldest (không block producer).
- Dead worker: daemon threads + orchestrator try/except.
- Backend unavailable: benchmark ghi `error`, không crash app.

---

## 10. Testing

```bash
cd backend
python -m pytest tests/modules/performance -q   # 17 tests
python -m pytest -q                               # 316 tests total
```

- Frame scheduler, priority queue, worker pool, GPU manager, memory pool
- Benchmark compare (graceful fail without models)
- Stress test (1–100 camera synthetic)

---

## 11. Profiling (khuyến nghị Production)

```bash
# PyTorch profiler (khi debug inference)
python -m torch.utils.bottleneck ...

# cProfile API benchmark
python -m cProfile -s cumtime -m pytest tests/modules/performance/test_stress.py

# Memory
python -m memory_profiler ...
```

---

## 12. Ràng buộc đã tuân thủ

- ❌ Không thêm business logic, không đổi Rule Engine / Dashboard / DB schema.
- ✅ Chỉ tối ưu: backends, scheduler, pools, queues, GPU, cache, monitoring, benchmark.
- ✅ Workers độc lập, queues thread-safe, không global mutable state (container inject).

Xem thêm báo cáo: `docs/reports/sprint10/`.
