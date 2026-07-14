# Sprint 13 — AI Model Training Platform & Model Management (v2.0)

**Version:** 2.0.0-sprint13  
**Status:** COMPLETED

## Overview

Module **`ml_platform`** — platform quản lý vòng đời AI model, tách biệt khỏi module AI Detection.

## Components

| Component | Service | API Prefix |
|-----------|---------|------------|
| Dataset Manager | `DatasetService` | `/api/v1/dataset` |
| Annotation Manager | `AnnotationService` | `/api/v1/annotation` |
| Training Manager | `TrainingService` | `/api/v1/training` |
| Validation/Evaluation | `ValidationService`, `EvaluationService` | `/api/v1/training/{id}/evaluate` |
| Model Registry | `RegistryService` | `/api/v1/model` |
| Deployment | `DeploymentService` | `/api/v1/deployment` |
| Benchmark | `BenchmarkService` | `/api/v1/benchmark` |
| FP/FN Center | `FpFnService` | `/api/v1/dataset/fp-fn` |
| Active Learning | `ActiveLearningService` | `/api/v1/dataset/active-learning` |

## Features

- Dataset: import, export, search, filter, merge, split, versioning
- Annotation: 10 label classes, CVAT/Label Studio/Roboflow config
- Training: YOLO11, YOLO12, RT-DETR, custom; augmentation; GPU/mixed precision
- Validation: precision, recall, F1, mAP50, mAP50-95, loss curves
- Model registry + version + rollback + A/B testing
- Training dashboard (frontend `/training`)

## Architecture Support

- `yolo11`, `yolo12`, `rt-detr`, `custom`
- Simulated training in CI; real Ultralytics when GPU available

## Database (Migration 005)

- `ml_datasets`, `ml_dataset_versions`, `ml_training_jobs`, `ml_training_epochs`, `ml_fp_fn_cases`

## Integration

- Registers trained models via Admin `ModelService`
- Deploy/rollback via existing `/models` infrastructure
- Does NOT modify Detection/Tracking/Rule Engine

## Documentation

- [Training Guide](../release-v2/Training-Guide.md)
- [Dataset Guide](../release-v2/Dataset-Guide.md)
- [Annotation Guide](../release-v2/Annotation-Guide.md)
- [Model Deployment Guide](../release-v2/Model-Deployment-Guide.md)

## Tests

```bash
cd backend && pytest tests/modules/ml_platform -q
```

---

**Version 2.0 Sprint 13 Completed.**
