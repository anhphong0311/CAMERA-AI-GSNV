# Dataset Guide — AEMS v2.0

## Sources

| Type | Description |
|------|-------------|
| image | Static images |
| video | Frame extracts |
| snapshot | Event snapshots |
| event | Event-linked media |
| false_positive | FP review center |
| false_negative | FN review center |

## Operations

- **Import:** batch paths via API
- **Search:** filter by label, annotated status, path query
- **Merge:** combine multiple datasets
- **Split:** train/val/test ratios (default 80/10/10)
- **Export:** full manifest JSON

## Versioning

Each dataset supports v1, v2, v3... via `DatasetVersion`.

## Statistics

`GET /api/v1/dataset/statistics` — total items, annotation rate
