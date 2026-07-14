# Sprint 10 — Performance Report

Generated as part of Sprint 10 completion checklist.

## System Optimizations Applied

| Area | Optimization | Config |
|------|-------------|--------|
| Inference | PyTorch / ONNX / TensorRT backends via factory | `performance.yaml → backend` |
| Precision | FP16 when `precision: fp16` | `backend.precision` |
| Frame rate | Adaptive skip 30→10 FPS | `frame_scheduler.target_ai_fps` |
| Multi-camera | Per-camera queue + round-robin workers | `detection.yaml → queue` |
| GPU | Multi-GPU discovery + load balance | `gpu.load_balance` |
| Memory | FramePool + BufferPool reuse | `memory.frame_pool_size` |
| Queue | PriorityQueue drop-oldest | `queue.use_priority` |
| Cache | Redis TTL cache | `cache.enabled` |
| Database | Configurable async pool | `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` |
| Pipeline | Async orchestrator Camera→AI | `pipeline.enabled` |

## Monitoring Endpoints

- `GET /api/v1/system/performance` — live snapshot
- `GET /api/v1/system/gpu` — GPU/VRAM/temperature
- `GET /api/v1/system/queue` — scheduler + pool depth
- `GET /api/v1/system/worker` — worker pool throughput

## Test Results

- Unit + integration: **316 passed**
- Performance module: **17 passed**
- Stress scenarios: 1, 5, 10, 20, 50, 100 cameras (synthetic, scheduler-aware)

## Recommendations for Production

1. Set `backend.type: tensorrt` on NVIDIA GPUs after exporting ONNX.
2. Set `frame_scheduler.target_ai_fps: 10` for 30 FPS RTSP streams.
3. Scale `queue.num_workers` with camera count (2–4 per 10 cameras).
4. Enable Redis cache for rule/camera metadata.
5. Monitor `/system/performance` + Prometheus `/metrics`.
