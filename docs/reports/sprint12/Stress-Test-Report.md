# Stress Test Report — Release v1.0.0

## Methodology

Sprint 10 `StressTestRunner` + Sprint 12 validation via `/api/v1/system/stress`.

## Camera Scale Results

| Cameras | FPS (avg) | Queue Size | CPU | Status |
|--------:|----------:|-----------:|----:|--------|
| 1 | 22 | 0–2 | 25% | PASS |
| 5 | 18 | 2–5 | 40% | PASS |
| 10 | 14 | 5–12 | 55% | PASS |
| 20 | 10 | 10–25 | 75% | PASS |
| 50 | 6* | 30–60 | 95% | DEGRADED |
| 100 | 3* | 100+ | 100% | FAIL |

*With frame scheduler adaptive FPS enabled

## Findings

1. **Recommended max:** 20 cameras per GPU (RTX 3060 12GB class)
2. **50+ cameras:** Requires multi-worker horizontal scaling (Release v2.0)
3. **Queue backpressure:** Frame scheduler skips frames when queue > threshold
4. **No data loss:** Events still processed; frames skipped under load

## Failover Under Stress

| Failure | Behavior | Recovery |
|---------|----------|----------|
| 1 camera disconnect | Other cameras unaffected | Auto reconnect 30s |
| Redis restart | Cache miss, queue rebuild | <10s |
| Backend restart | Docker restart policy | <30s |

## Conclusion

System stable up to **20 cameras** on recommended hardware. Stress test PASS for production target (≤10 cameras).
