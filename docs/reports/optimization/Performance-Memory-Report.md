# Performance & Memory Report

## Hot-path architecture (unchanged)

```
Camera RTSP → FrameBuffer (preview) → AI Detection → Tracking → Behavior → Rule → Event/Telegram
                                    ↘ EvidenceFrameBuffer (snapshots/video)
```

## Memory — before vs after (config)

| Buffer | Before | After | Notes |
|--------|--------|-------|-------|
| Camera `queue_size` / `buffer_size` | 450 / 450 | **45 / 45** | Preview API only uses `latest()`; evidence has its own buffer |
| Evidence `30s × 15fps` | ~465 frames/cam | unchanged | Needed for AWAY/PHONE snapshots |
| AI detection queue | 5 | unchanged | |
| Dual `push_frame` | Camera sink + AI bridge | **Camera sink only** | Removes duplicate ndarray copies at AI FPS |

### Rough RAM impact (1080p ≈ 6 MB/frame, 4 cameras)

| | Before (worst) | After (est.) |
|--|----------------|--------------|
| Camera buffers | 450 × 4 × 6 MB ≈ **10.8 GB** | 45 × 4 × 6 MB ≈ **1.1 GB** |
| Evidence buffers | ~465 × 4 × 6 MB ≈ **11 GB** | unchanged |
| Duplicate AI push | extra copies | **eliminated** |

> Actual process RSS is often lower if frames are shared/resized, but 450-deep full-res queues were the dominant waste.

## CPU / GPU

| Item | Change |
|------|--------|
| Rule Engine | **No code changes** |
| YOLO / model load | Still once at startup |
| Behavior debug logs | Already gated by LOG_LEVEL=INFO |
| Log rotation | Already configured (`aems_{date}.log`, 30/90 day retention) |

## Profiling (Phase 12) — host metrics

Numeric before/after CPU%/FPS require a sustained load run on the deployment host. After this sprint:

1. `GET /api/v1/ai/statistics` — note `avg_fps`, `avg_inference_ms`
2. `GET /api/v1/system/performance` (if enabled) — queues / GPU
3. Compare dashboard Live FPS (target unchanged)

Expected: **equal or better FPS**, **lower RAM**, same detection behavior.
