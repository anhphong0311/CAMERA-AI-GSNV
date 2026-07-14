# Annotation Guide — AEMS v2.0

## Label Classes

person, phone, cup, bottle, food, chair, laptop, keyboard, mouse, monitor

## Internal Annotation

```json
POST /api/v1/annotation
{
  "item_id": "...",
  "label": "phone",
  "bbox": [0.1, 0.2, 0.3, 0.4]
}
```

## External Tools

Configure via `POST /api/v1/annotation/configure`:

| Tool | Config keys |
|------|-------------|
| cvat | url, username, password, project_id |
| label_studio | url, api_key, project_id |
| roboflow | api_key, workspace, project |

## Export YOLO Format

Use annotation service export for training pipeline compatibility.
