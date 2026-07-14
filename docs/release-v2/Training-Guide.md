# Training Guide — AEMS v2.0

## Prerequisites

- Admin or Supervisor role
- Dataset with annotated items
- GPU recommended (CPU uses simulated training)

## Workflow

1. **Create Dataset** — `POST /api/v1/dataset`
2. **Import images** — `POST /api/v1/dataset/{id}/import`
3. **Annotate** — `POST /api/v1/annotation` or external tool
4. **Create version** — `POST /api/v1/dataset/{id}/versions`
5. **Split** — `POST /api/v1/dataset/{id}/versions/{vid}/split`
6. **Create training job** — `POST /api/v1/training`
7. **Start** — `POST /api/v1/training/{id}/start`
8. **Evaluate** — `GET /api/v1/training/{id}/evaluate`
9. **Deploy** — `POST /api/v1/deployment/deploy`

## Train Config

```json
{
  "batch_size": 16,
  "epochs": 100,
  "learning_rate": 0.001,
  "optimizer": "AdamW",
  "scheduler": "cosine",
  "image_size": 640,
  "mixed_precision": true,
  "augmentation": {
    "flip": true,
    "mosaic": true,
    "mixup": 0.1
  }
}
```

## Dashboard

Open **AI Training** in sidebar → `/training`

## Rollback

`POST /api/v1/deployment/rollback` with `{"name": "model-name"}`
