# Model Deployment Guide — AEMS v2.0

## After Training

Completed jobs auto-register in Model Registry via Admin `ModelService`.

## Deploy Active Model

```http
POST /api/v1/deployment/deploy
{"model_id": 1}
```

## Rollback

```http
POST /api/v1/deployment/rollback
{"name": "office-detector"}
```

## A/B Testing

```http
POST /api/v1/deployment/ab-test
{
  "name": "phone-detector-ab",
  "model_a_id": 1,
  "model_b_id": 2,
  "traffic_b_pct": 10
}
```

## Benchmark

```http
POST /api/v1/benchmark/run
{"architecture": "yolo11", "runs": 50}
```

Returns FPS, latency, VRAM, accuracy.

## Production Note

After deploy, restart AI worker or call `POST /api/v1/ai/reload` to load new weights.
