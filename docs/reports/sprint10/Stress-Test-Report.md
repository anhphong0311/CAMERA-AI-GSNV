# Sprint 10 — Stress Test Report Template

Run via API:

```http
POST /api/v1/system/stress
Authorization: Bearer <token>
Content-Type: application/json

{
  "camera_counts": [1, 5, 10, 20, 50, 100],
  "duration_s": 5
}
```

## Scenarios

| Cameras | Metric |
|---------|--------|
| 1 | Baseline throughput, queue depth |
| 5 | RTX 3060 target ~25 FPS aggregate |
| 10 | RTX 3060 target ~20 FPS aggregate |
| 20 | RTX 4070 target ~20 FPS aggregate |
| 50 | RTX 4080 target ~20 FPS aggregate |
| 100 | Scale limit test |

## Output Fields

- `submitted` — frames passed frame scheduler + submitted to AI pipeline
- `throughput_fps` — aggregate FPS
- `avg_fps_per_camera` — per-camera average
- `errors` — submission failures (should be 0)

## Pass Criteria (Sprint 10)

- No deadlock under 100-camera synthetic load
- No unbounded memory growth (FramePool caps allocation)
- Queue drop-oldest prevents blocking (no producer stall)
- Worker pools remain alive after stress

## Automated Test

```bash
cd backend
python -m pytest tests/modules/performance/test_stress.py -q
```
