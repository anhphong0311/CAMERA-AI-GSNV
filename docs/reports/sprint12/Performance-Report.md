# Performance Report — Release v1.0.0

Based on Sprint 10 benchmarks + Sprint 12 validation.

## Targets vs Actual

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| AI FPS (1 camera, GPU) | ≥15 | 18–25 | PASS |
| AI FPS (1 camera, CPU) | ≥5 | 6–8 | PASS |
| Detection latency | <100ms | 45–80ms | PASS |
| Tracking latency | <20ms | 8–15ms | PASS |
| Behavior extraction | <30ms | 12–25ms | PASS |
| Rule evaluation | <10ms | 2–5ms | PASS |
| API /health | <100ms | 15–40ms | PASS |
| API /health/full | <500ms | 80–200ms | PASS |
| WebSocket broadcast | <50ms | 10–30ms | PASS |
| Cold start (backend) | <60s | 35–50s | PASS |
| Warm start | <10s | 5–8s | PASS |

## Resource Usage (10 cameras, GPU)

| Resource | Usage |
|----------|-------|
| CPU | 35–55% |
| RAM | 4–6 GB |
| VRAM | 2–4 GB |
| Queue delay | <200ms avg |

## Database

| Operation | Response |
|-----------|----------|
| Event insert | <5ms |
| Event list (100) | <20ms |
| Health SELECT 1 | <2ms |

## Notes

- Performance scales linearly up to ~20 cameras on single GPU
- Frame scheduler reduces load 30→10 FPS under pressure (Sprint 10)
- See Sprint 10 reports for ONNX/TensorRT comparison
